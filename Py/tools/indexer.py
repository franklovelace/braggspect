import os
import sqlite3
import numpy as np
import multiprocessing as mp
from pymatgen.io.cif import CifParser
from pymatgen.analysis.diffraction.xrd import XRDCalculator
import io
import sys
import mysql.connector
import warnings
import logging
import json 
from tqdm import tqdm

warnings.filterwarnings("ignore")
logging.getLogger("pymatgen").setLevel(logging.CRITICAL)

CIF_ROOT = r"RUTA_DE_CIF_ROOT" 
DB_PATH = "HanawaltIndex.db"
FAILED_LOG_PATH = "failed_cifs.json" 
NUM_WORKERS = 15 
WAVELENGTH = 1.54060
MAX_PEAKS = 3

def get_path_for_id(cod_id):
    s = str(cod_id).zfill(7)
    return os.path.join(CIF_ROOT, s[0], s[1:3], s[3:5], f"{cod_id}.cif")

def process_single_cif(cod_id):
    """Procesador Bulletproof para UN SOLO archivo"""
    warnings.filterwarnings("ignore")
    logging.getLogger("pymatgen").setLevel(logging.CRITICAL)
    
    path = get_path_for_id(cod_id)
    if not os.path.exists(path):
        return {"status": "error", "id": cod_id, "reason": "File not found on disk"}
        
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        parser = CifParser(io.StringIO(content))
        struct = parser.get_structures(primitive=False)[0]
        
        xrd_calc = XRDCalculator(wavelength="CuKa")
        pattern = xrd_calc.get_pattern(struct)
        
        valid_indices = np.where(pattern.y > 1.0)[0]
        if len(valid_indices) == 0:
            return {"status": "error", "id": cod_id, "reason": "No diffraction peaks found (I > 1%)"}
            
        idx = np.argsort(pattern.y[valid_indices])[::-1]
        top_peaks = []
        
        for i in range(min(MAX_PEAKS, len(idx))):
            tth = pattern.x[valid_indices][idx[i]]
            inty = pattern.y[valid_indices][idx[i]]
            d = WAVELENGTH / (2.0 * np.sin(np.radians(tth / 2.0)))
            top_peaks.append((round(float(d), 4), round(float(inty), 1), i+1))
        
        return {"status": "success", "id": cod_id, "formula": struct.composition.reduced_formula, "peaks": top_peaks}
        
    except Exception as e:
        return {"status": "error", "id": cod_id, "reason": f"Pymatgen Parse Error: {str(e)[:100]}"}

def writer_task(queue, total_to_process):
    """Proceso que escribe en SQLite y en el JSON de errores"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode = WAL')
    conn.execute('PRAGMA synchronous = OFF')
    conn.execute('PRAGMA cache_size = -100000') 
    
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS materials (cod_id INTEGER PRIMARY KEY, formula TEXT, name TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS hanawalt_peaks (cod_id INTEGER, d_spacing REAL, intensity REAL, rank INTEGER)')
    
    failed_records = []
    if os.path.exists(FAILED_LOG_PATH):
        try:
            with open(FAILED_LOG_PATH, 'r') as f:
                failed_records = json.load(f)
        except:
            pass

    pbar = tqdm(total=total_to_process, desc="Indexando", unit="mat")
    count = 0
    errors_count = 0
    
    while True:
        msg = queue.get()
        if msg == "DONE": 
            break
        
        if msg["status"] == "error":
            failed_records.append({"id": msg["id"], "reason": msg["reason"]})
            errors_count += 1
            count += 1
            pbar.set_postfix({"Errores": errors_count}) 
            pbar.update(1)
            
            if errors_count % 500 == 0:
                with open(FAILED_LOG_PATH, 'w') as f:
                    json.dump(failed_records, f, indent=4)
            continue

        cid = msg["id"]
        form = msg["formula"]
        peaks = msg["peaks"]
        
        try:
            cursor.execute("INSERT OR IGNORE INTO materials (cod_id, formula, name) VALUES (?, ?, ?)", (cid, form, ""))
            for p in peaks:
                cursor.execute("INSERT INTO hanawalt_peaks VALUES (?,?,?,?)", (cid, p[0], p[1], p[2]))
            
            count += 1
            pbar.update(1) 
            
            if count % 2000 == 0:
                conn.commit()
                
        except Exception:
            continue
            
    conn.commit()
    with open(FAILED_LOG_PATH, 'w') as f:
        json.dump(failed_records, f, indent=4)
        
    pbar.close()
    print(f"\nProceso terminado. Se registraron {errors_count} archivos corruptos/faltantes en {FAILED_LOG_PATH}.")
    print("Creando índices B-Tree de alta velocidad...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_d ON hanawalt_peaks(d_spacing)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cod_id ON hanawalt_peaks(cod_id)')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Conectando a la COD para obtener la lista maestra de IDs...")
    db = mysql.connector.connect(host="sql.crystallography.net", user="cod_reader", password="", database="cod")
    cursor = db.cursor()
    cursor.execute("SELECT file FROM data WHERE a IS NOT NULL")
    all_ids = [r[0] for r in cursor.fetchall()]
    db.close()
    print(f"Catálogo descargado: {len(all_ids)} estructuras en la COD.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS materials (cod_id INTEGER PRIMARY KEY, formula TEXT, name TEXT)')
    cursor.execute("SELECT cod_id FROM materials")
    already_indexed = set(r[0] for r in cursor.fetchall())
    conn.close()

    already_failed = set()
    if os.path.exists(FAILED_LOG_PATH):
        try:
            with open(FAILED_LOG_PATH, 'r') as f:
                failed_data = json.load(f)
                already_failed = {item["id"] for item in failed_data}
        except:
            pass

    pending_ids = [cid for cid in all_ids if cid not in already_indexed and cid not in already_failed]
    total = len(pending_ids)

    if total == 0:
        print("La base de datos local ya está 100% actualizada.")
        sys.exit(0)

    print(f"Estructuras pendientes de indexar: {total}")
    
    manager = mp.Manager()
    queue = manager.Queue(maxsize=10000)
    writer = mp.Process(target=writer_task, args=(queue, total))
    writer.start()
    
    print(f"Lanzando Pool de {NUM_WORKERS} procesos trabajadores a máxima potencia...")
    
    with mp.Pool(processes=NUM_WORKERS) as pool:
        for result in pool.imap_unordered(process_single_cif, pending_ids, chunksize=20):
            if result is not None:
                queue.put(result)
    
    queue.put("DONE")
    writer.join()
    print("\n¡Listo! Revisa failed_cifs.json para ver las estructuras que requieren atención manual.")