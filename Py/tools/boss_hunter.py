import os
import sqlite3
import numpy as np
import json
import io
import mysql.connector
import warnings
import logging
from datetime import datetime
from pymatgen.io.cif import CifParser
from pymatgen.analysis.diffraction.xrd import XRDCalculator

warnings.filterwarnings("ignore")
logging.getLogger("pymatgen").setLevel(logging.CRITICAL)

CIF_ROOT = r"/Ruta_de_cif"
DB_PATH = "HanawaltIndex.db"
FAILED_LOG_PATH = "failed_cifs.json"
WAVELENGTH = 1.54060

def get_path_for_id(cod_id):
    s = str(cod_id).zfill(7)
    return os.path.join(CIF_ROOT, s[0], s[1:3], s[3:5], f"{cod_id}.cif")

def log_failure(cod_id, reason):
    """Añade el error al JSON de forma persistente"""
    failed_data = []
    if os.path.exists(FAILED_LOG_PATH):
        try:
            with open(FAILED_LOG_PATH, 'r') as f:
                failed_data = json.load(f)
        except: pass
    
    if not any(item['id'] == cod_id for item in failed_data):
        failed_data.append({
            "id": cod_id, 
            "reason": reason, 
            "timestamp": datetime.now().isoformat()
        })
        with open(FAILED_LOG_PATH, 'w') as f:
            json.dump(failed_data, f, indent=4)

def process_one(cod_id, conn):
    """Procesamiento individual con reporte de átomos"""
    path = get_path_for_id(cod_id)
    if not os.path.exists(path):
        log_failure(cod_id, "File not found")
        return

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        parser = CifParser(io.StringIO(content))
        struct = parser.get_structures(primitive=False)[0]
        num_atoms = len(struct)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ID: {cod_id} | Átomos: {num_atoms:4} | ", end="", flush=True)

        xrd_calc = XRDCalculator(wavelength="CuKa")
        pattern = xrd_calc.get_pattern(struct)
        
        valid_indices = np.where(pattern.y > 1.0)[0]
        if len(valid_indices) == 0:
            log_failure(cod_id, "No detectable peaks")
            print("⚠️ SIN PICOS")
            return

        idx = np.argsort(pattern.y[valid_indices])[::-1]
        top_peaks = []
        for i in range(min(3, len(idx))):
            tth = pattern.x[valid_indices][idx[i]]
            inty = pattern.y[valid_indices][idx[i]]
            d = WAVELENGTH / (2.0 * np.sin(np.radians(tth / 2.0)))
            top_peaks.append((round(float(d), 4), round(float(inty), 1), i+1))
        
        formula = struct.composition.reduced_formula
        conn.execute("INSERT OR IGNORE INTO materials VALUES (?,?,?)", (cod_id, formula, ""))
        for p in top_peaks:
            conn.execute("INSERT INTO hanawalt_peaks VALUES (?,?,?,?)", (cod_id, p[0], p[1], p[2]))
        conn.commit()
        
        print("OK")

    except Exception as e:
        msg = str(e)[:50]
        log_failure(cod_id, f"Error: {msg}")
        print(f"FALLÓ ({msg})")

if __name__ == "__main__":
    print("--- PREPARANDO  ---")
    
    db_cod = mysql.connector.connect(host="sql.crystallography.net", user="cod_reader", password="", database="cod")
    cursor_cod = db_cod.cursor()
    cursor_cod.execute("SELECT file FROM data WHERE a IS NOT NULL")
    all_ids = [r[0] for r in cursor_cod.fetchall()]
    db_cod.close()

    conn = sqlite3.connect(DB_PATH)
    indexed_ids = {r[0] for r in conn.execute("SELECT cod_id FROM materials")}
    
    failed_ids = set()
    if os.path.exists(FAILED_LOG_PATH):
        try:
            with open(FAILED_LOG_PATH, 'r') as f:
                failed_ids = {item['id'] for item in json.load(f)}
        except: pass

    pending = [cid for cid in all_ids if cid not in indexed_ids and cid not in failed_ids]
    
    if not pending:
        print("¡Increíble! No quedan materiales pendientes. Todo está en la DB o en el log de errores.")
    else:
        print(f"Detectados {len(pending)} materiales pendientes. Empezando...")
        for cid in pending:
            process_one(cid, conn)

    conn.close()
    print("\n--- FIN DEL PROCESO ---")