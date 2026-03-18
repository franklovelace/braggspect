import os
import sys
import sqlite3
import torch
import numpy as np
import json
import io
import mysql.connector
import warnings
import logging
from datetime import datetime
from pymatgen.io.cif import CifParser
from pymatgen.analysis.diffraction.xrd import ATOMIC_SCATTERING_PARAMS

warnings.filterwarnings("ignore")
logging.getLogger("pymatgen").setLevel(logging.CRITICAL)

CIF_ROOT = r"Ruta_de_cif" 
DB_PATH = "HanawaltIndex.db"
FAILED_LOG_PATH = "failed_cifs.json"
WAVELENGTH = 1.54060

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"--- MOTOR HPC INICIALIZADO EN: {device.type.upper()} ---")

def _get_scattering_tables():
    elems = list(ATOMIC_SCATTERING_PARAMS.keys())
    a_list, b_list, c_list = [], [], []
    sym_to_idx = {}
    
    for i, sym in enumerate(elems):
        p = ATOMIC_SCATTERING_PARAMS[sym]
        a_vals = [0.0] * 4
        b_vals = [0.0] * 4
        
        raw_c = p[-1]
        c_val = float(raw_c[0] if isinstance(raw_c, (list, np.ndarray)) else raw_c)
        
        pairs = p[:-1]
        for j in range(min(4, len(pairs))):
            a_vals[j] = float(pairs[j][0])
            b_vals[j] = float(pairs[j][1])
            
        a_list.append(a_vals)
        b_list.append(b_vals)
        c_list.append(c_val)
        sym_to_idx[sym] = i
        
    return (torch.tensor(a_list, device=device, dtype=torch.float32),
            torch.tensor(b_list, device=device, dtype=torch.float32),
            torch.tensor(c_list, device=device, dtype=torch.float32),
            sym_to_idx)

A_TAB, B_TAB, C_TAB, SYM_MAP = _get_scattering_tables()

@torch.no_grad()
def fast_xrd_calc(structure):
    frac_coords = torch.tensor(structure.frac_coords, dtype=torch.float32, device=device)
    
    z_indices = []
    for site in structure:
        try:
            dominant_el = max(site.species.items(), key=lambda x: x[1])[0]
            sym = dominant_el.symbol
        except:
            sym = "H" 
            
        idx = SYM_MAP.get(sym)
        if idx is None: 
            try: sym = dominant_el.element.symbol
            except: sym = "H"
            idx = SYM_MAP.get(sym, 0)
        z_indices.append(idx)
    
    z_indices = torch.tensor(z_indices, device=device)
    lat_mat = torch.tensor(structure.lattice.matrix, dtype=torch.float32, device=device)
    rec_mat = torch.linalg.inv(lat_mat).t()

    max_hkl = min(int(max(structure.lattice.abc) / 1.0), 15)
    r = torch.arange(-max_hkl, max_hkl + 1, device=device)
    hkl = torch.cartesian_prod(r, r, r).float()
    hkl = hkl[(hkl != 0).any(dim=1)]

    ghkl = hkl @ rec_mat
    d_inv = torch.norm(ghkl, dim=1)
    d_spacing = 1.0 / d_inv
    mask = (d_spacing >= 1.0) & (d_spacing < 20.0)
    hkl, d_spacing, d_inv = hkl[mask], d_spacing[mask], d_inv[mask]
    
    if len(hkl) == 0: return []

    s = d_inv / 2.0
    s2 = s**2
    a, b, c = A_TAB[z_indices], B_TAB[z_indices], C_TAB[z_indices]
    
    intensities = torch.zeros(len(hkl), device=device)
    CHUNK = 256 
    TWO_PI = 2.0 * torch.pi

    for i in range(0, len(hkl), CHUNK):
        end = i + CHUNK
        h_chunk, s2_chunk = hkl[i:end], s2[i:end]
        f_ij = (a.unsqueeze(0) * torch.exp(-b.unsqueeze(0) * s2_chunk.unsqueeze(1).unsqueeze(2))).sum(dim=2) + c.unsqueeze(0)
        phases = TWO_PI * (h_chunk @ frac_coords.t())
        real = (f_ij * torch.cos(phases)).sum(dim=1)
        imag = (f_ij * torch.sin(phases)).sum(dim=1)
        intensities[i:end] = real**2 + imag**2

    d_rounded = (d_spacing * 1000).round()
    unique_d_vals, inv_idx = torch.unique(d_rounded, return_inverse=True)
    final_inty = torch.zeros_like(unique_d_vals).scatter_add_(0, inv_idx, intensities)
    
    final_d = unique_d_vals / 1000.0
    sin_th = ( (1.0/(2.0*final_d)) * WAVELENGTH ).clamp(-1.0, 1.0)
    theta = torch.asin(sin_th)
    lp = (1 + torch.cos(2*theta)**2) / (torch.sin(theta)**2 * torch.cos(theta))
    final_inty *= lp

    k_peaks = min(3, len(final_inty))
    top_v, top_i = torch.topk(final_inty, k=k_peaks)
    max_v = top_v[0] if len(top_v) > 0 else 1.0
    
    return [{"d": float(final_d[idx]), "intensity": float(v/max_v*100)} for v, idx in zip(top_v, top_i)]

def log_failed(cod_id, reason):
    data = []
    if os.path.exists(FAILED_LOG_PATH):
        try:
            with open(FAILED_LOG_PATH, 'r') as f: data = json.load(f)
        except: pass
    if not any(x['id'] == cod_id for x in data):
        data.append({"id": cod_id, "reason": reason, "ts": datetime.now().isoformat()})
        with open(FAILED_LOG_PATH, 'w') as f: json.dump(data, f, indent=4)

def get_path_for_id(cod_id):
    s = str(cod_id).zfill(7)
    return os.path.join(CIF_ROOT, s[0], s[1:3], s[3:5], f"{cod_id}.cif")

if __name__ == "__main__":
    print("Conectando a la COD para obtener catálogo maestro...")
    try:
        db_cod = mysql.connector.connect(host="sql.crystallography.net", user="cod_reader", password="", database="cod")
        cur_cod = db_cod.cursor()
        cur_cod.execute("SELECT file FROM data WHERE a IS NOT NULL")
        all_ids = [r[0] for r in cur_cod.fetchall()]
        db_cod.close()
    except Exception as e:
        print(f"Error de conexión: {e}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    indexed = {r[0] for r in conn.execute("SELECT cod_id FROM materials")}
    
    failed_ids = set()
    if os.path.exists(FAILED_LOG_PATH):
        try:
            with open(FAILED_LOG_PATH, 'r') as f:
                failed_ids = {x['id'] for x in json.load(f)}
        except: pass

    pending = [cid for cid in all_ids if cid not in indexed and cid not in failed_ids]
    
    if not pending:
        print("¡Misión cumplida! Todo está indexado.")
    else:
        print(f"--- INICIANDO CAZA DE {len(pending)} MATERIALES ---")

        for cid in pending:
            path = get_path_for_id(cid)
            if not os.path.exists(path):
                log_failed(cid, "File not found")
                continue

            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if not content.strip(): raise Exception("Empty file")
                    parser = CifParser(io.StringIO(content))
                
                structures = parser.get_structures(primitive=False)
                if not structures: raise Exception("No structure in CIF")
                
                struct = structures[0]
                num_atoms = len(struct)
                formula = struct.composition.reduced_formula

                print(f"[{datetime.now().strftime('%H:%M:%S')}] ID: {cid} | Átomos: {num_atoms:5} | {formula:15} | ", end="", flush=True)

                peaks = fast_xrd_calc(struct)
                
                if not peaks:
                    log_failed(cid, "No peaks found")
                    print("SIN PICOS")
                    continue

                conn.execute("INSERT OR IGNORE INTO materials VALUES (?,?,?)", (cid, formula, ""))
                for i, p in enumerate(peaks):
                    conn.execute("INSERT INTO hanawalt_peaks VALUES (?,?,?,?)", (cid, p['d'], p['intensity'], i+1))
                conn.commit()
                print("OK")

            except Exception as e:
                log_failed(cid, str(e))
                print(f"ERROR: {str(e)[:40]}")

    conn.close()
    print("--- PROCESO TERMINADO ---")