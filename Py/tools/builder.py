import sqlite3
import requests
import numpy as np
import mysql.connector
from pymatgen.io.cif import CifParser
from pymatgen.analysis.diffraction.xrd import XRDCalculator
import warnings
import io
import time
import sys
import multiprocessing as mp
from queue import Empty

warnings.filterwarnings("ignore")

DB_PATH = "HanawaltIndex.db"
COD_BASE_URL = "http://www.crystallography.net/cod/"
WAVELENGTH = 1.54060
MAX_PEAKS = 3 
COMMIT_INTERVAL = 5000 

NUM_WORKERS = 8 

def get_all_valid_cod_ids():
    """Descarga la lista maestra de IDs desde MySQL"""
    print("Conectando al servidor MySQL de la COD (Puede tardar 10-20 seg)...")
    try:
        db = mysql.connector.connect(
            host="sql.crystallography.net",
            user="cod_reader",
            password="",
            database="cod",
            port=3306
        )
        cursor = db.cursor()
        cursor.execute("SELECT file FROM data WHERE a IS NOT NULL AND a > 0 ORDER BY file ASC")
        ids = [row[0] for row in cursor.fetchall()]
        db.close()
        print(f"Catálogo Maestro descargado: {len(ids)} materiales.")
        return ids
    except Exception as e:
        print(f"Error conectando a MySQL: {e}")
        sys.exit(1)

def sqlite_writer(queue: mp.Queue, total_expected: int):
    """
    EL CONSUMIDOR (Único proceso que toca el SSD)
    Escucha la cola y guarda los resultados en SQLite.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode = WAL') # WAL es más rápido para concurrencia que MEMORY
    conn.execute('PRAGMA synchronous = NORMAL')
    
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS materials (cod_id INTEGER PRIMARY KEY, formula TEXT, name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS hanawalt_peaks (cod_id INTEGER, d_spacing REAL, intensity REAL, rank INTEGER, FOREIGN KEY(cod_id) REFERENCES materials(cod_id))''')
    conn.commit()
    
    processed = 0
    start_time = time.time()
    
    while True:
        try:
            msg = queue.get(timeout=10)
            
            if msg == "DONE":
                break
                
            cod_id, formula, peaks = msg
            
            cursor.execute("INSERT OR IGNORE INTO materials (cod_id, formula, name) VALUES (?, ?, ?)", 
                         (cod_id, formula, "COD Auto"))
            
            for p in peaks:
                cursor.execute("INSERT INTO hanawalt_peaks (cod_id, d_spacing, intensity, rank) VALUES (?, ?, ?, ?)",
                             (cod_id, p["d_spacing"], p["intensity"], p["rank"]))
            
            processed += 1
            
            if processed % 100 == 0:
                elapsed = time.time() - start_time
                speed = processed / elapsed
                sys.stdout.write(f"\rGuardados en SSD: {processed}/{total_expected} | Velocidad: {speed:.1f} mats/seg")
                sys.stdout.flush()
                
            if processed % COMMIT_INTERVAL == 0:
                conn.commit()
                
        except Empty:
            continue
        except Exception as e:
            print(f"\nError en Writer SQLite: {e}")
            
    conn.commit()
    print("\n--- Workers terminaron. Creando Índices B-Tree (Esto puede tardar unos minutos) ---")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_d_spacing ON hanawalt_peaks(d_spacing)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cod_id ON hanawalt_peaks(cod_id)')
    conn.commit()
    conn.close()
    print("\n¡Índice SQLite completado y cerrado con éxito!")

def cif_worker(worker_id: int, tasks_chunk: list, queue: mp.Queue):
    """
    EL PRODUCTOR (8 en paralelo)
    Descarga el CIF, simula XRD y envía [ID, Formula, Picos] a la cola.
    """
    session = requests.Session()
    xrd_calc = XRDCalculator(wavelength="CuKa")
    
    for cod_id in tasks_chunk:
        try:
            response = session.get(f"{COD_BASE_URL}{cod_id}.cif", timeout=4)
            if response.status_code != 200: continue
            
            file_like = io.StringIO(response.text)
            parser = CifParser(file_like)
            structure = parser.get_structures(primitive=False)[0]
            
            pattern = xrd_calc.get_pattern(structure)
            valid_indices = np.where(pattern.y > 1.0)[0]
            if len(valid_indices) == 0: continue
                
            sort_idx = np.argsort(pattern.y[valid_indices])[::-1]
            
            top_peaks = []
            rank = 1
            for idx in sort_idx:
                if rank > MAX_PEAKS: break
                tth = pattern.x[valid_indices][idx]
                inty = pattern.y[valid_indices][idx]
                d_spacing = WAVELENGTH / (2.0 * np.sin(np.radians(tth / 2.0)))
                
                top_peaks.append({"d_spacing": round(float(d_spacing), 4), "intensity": round(float(inty), 1), "rank": rank})
                rank += 1
                
            formula = structure.composition.reduced_formula
            
            queue.put((cod_id, formula, top_peaks))
            
        except Exception:
            pass 

def start_engine():
    all_ids = get_all_valid_cod_ids()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS materials (cod_id INTEGER PRIMARY KEY, formula TEXT, name TEXT)''')
    cursor.execute("SELECT cod_id FROM materials")
    already_indexed = set(row[0] for row in cursor.fetchall())
    conn.close()
    
    pending_ids = [cid for cid in all_ids if cid not in already_indexed]
    total_pending = len(pending_ids)
    
    if total_pending == 0:
        print("La base de datos ya está 100% indexada.")
        return
        
    print(f"Estructuras pendientes: {total_pending}")
    print(f"Iniciando {NUM_WORKERS} Workers en tu Ryzen 7 5700G...")

    chunk_size = (total_pending // NUM_WORKERS) + 1
    chunks = [pending_ids[i:i + chunk_size] for i in range(0, total_pending, chunk_size)]

    manager = mp.Manager()
    queue = manager.Queue()

    writer_process = mp.Process(target=sqlite_writer, args=(queue, total_pending))
    writer_process.start()

    workers = []
    for i in range(NUM_WORKERS):
        p = mp.Process(target=cif_worker, args=(i, chunks[i], queue))
        p.start()
        workers.append(p)

    for p in workers:
        p.join()

    queue.put("DONE")
    writer_process.join()
    
    print("\nProceso Masivo Terminado.")

if __name__ == "__main__":
    start_engine()