import sqlite3
import requests
import numpy as np
from pymatgen.io.cif import CifParser
from pymatgen.analysis.diffraction.xrd import XRDCalculator
import warnings
import io

warnings.filterwarning("ignore")

DB_PATH = "HanawaltIndex.db"
COD_BASE_URL = "http://www.crystallography.net/cod/"
WAVELENGTH = 1.54060 
MAX_PEAKS = 3 
COMMIT_INTERVAL = 1000 

def setup_database():
    """Crea la estructura SQLite con Pragmas para velocidad extrema de inserción"""
    conn = sqlite3.connect(DB_PATH)
    
    conn.execute('PRAGMA journal_mode = MEMORY')
    conn.execute('PRAGMA synchronous = OFF')
    
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            cod_id INTEGER PRIMARY KEY,
            formula TEXT,
            name TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hanawalt_peaks (
            cod_id INTEGER,
            d_spacing REAL,
            intensity REAL,
            rank INTEGER,
            FOREIGN KEY(cod_id) REFERENCES materials(cod_id)
        )
    ''')
    
    conn.commit()
    return conn

def download_cif(cod_id: int):
    """Descarga el CIF directo a la memoria"""
    url = f"{COD_BASE_URL}{cod_id}.cif"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
        return None
    except:
        return None

def process_cif_in_memory(cif_string: str):
    """
    Procesa el CIF usando StringIO para mantener todo en RAM.
    Calcula d_spacing desde el 2Theta de Pymatgen.
    """
    try:
        file_like_object = io.StringIO(cif_string)
        parser = CifParser(file_like_object)
        structure = parser.get_structures(primitive=False)[0]
        
        xrd_calc = XRDCalculator(wavelength="CuKa")
        pattern = xrd_calc.get_pattern(structure)
        
        two_thetas = pattern.x
        intensities = pattern.y
        
        valid_indices = np.where(intensities > 1.0)[0]
        if len(valid_indices) == 0:
            return None, []
            
        valid_tth = two_thetas[valid_indices]
        valid_inty = intensities[valid_indices]
        
        sort_idx = np.argsort(valid_inty)[::-1]
        
        top_peaks = []
        rank = 1
        for idx in sort_idx:
            if rank > MAX_PEAKS: break
            
            tth = valid_tth[idx]
            inty = valid_inty[idx]
            
            theta_rad = np.radians(tth / 2.0)
            d_spacing = WAVELENGTH / (2.0 * np.sin(theta_rad))
            
            top_peaks.append({
                "d_spacing": round(float(d_spacing), 4),
                "intensity": round(float(inty), 1),
                "rank": rank
            })
            rank += 1
            
        formula = structure.composition.reduced_formula
        return formula, top_peaks
        
    except Exception as e:
        return None, []

def index_cod_list(cod_ids: list):
    """Bucle principal con Bulk Commits"""
    conn = setup_database()
    cursor = conn.cursor()
    
    print(f"Iniciando indexación en memoria de {len(cod_ids)} estructuras...")
    
    cursor.execute("SELECT cod_id FROM materials")
    already_indexed = set(row[0] for row in cursor.fetchall())
    
    processed_count = 0
    success_count = 0
    
    for cod_id in cod_ids:
        if cod_id in already_indexed:
            continue
            
        cif_data = download_cif(cod_id)
        if not cif_data:
            print(f"[{cod_id}] Error 404/Timeout.")
            continue
            
        formula, peaks = process_cif_in_memory(cif_data)
        
        if formula and len(peaks) > 0:
            cursor.execute("INSERT INTO materials (cod_id, formula, name) VALUES (?, ?, ?)",
                         (cod_id, formula, "Auto-Indexado"))
            
            for p in peaks:
                cursor.execute("INSERT INTO hanawalt_peaks (cod_id, d_spacing, intensity, rank) VALUES (?, ?, ?, ?)",
                             (cod_id, p["d_spacing"], p["intensity"], p["rank"]))
            
            success_count += 1
            print(f"[{cod_id}] OK | {formula} | d1: {peaks[0]['d_spacing']} Å")
        else:
            print(f"[{cod_id}] Falló el cálculo cristalino.")
        
        processed_count += 1
        
        if processed_count % COMMIT_INTERVAL == 0:
            conn.commit()
            print(f"--- COMMIT a disco ({processed_count} procesados) ---")
            
    conn.commit()
    
    print("Creando índices B-Tree para búsquedas ultra-rápidas...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_d_spacing ON hanawalt_peaks(d_spacing)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cod_id ON hanawalt_peaks(cod_id)')
    conn.commit()
    
    conn.close()
    print(f"Índice completado. {success_count} materiales nuevos guardados con éxito.")

if __name__ == "__main__":
    lista_prueba = [
        9009666, 
        1010928, 
        9008566, 
        1011031, 
        9009054  
    ]
    
    index_cod_list(lista_prueba)