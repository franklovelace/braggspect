from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Any
import numpy as np
import sqlite3

from core.constants import ANODES
from core.stripping import rachinger_correction
from core.hanawalt import extract_top_peaks
from core.scoring import calculate_fast_match
from core.death_match import run_adaptive_death_match 
from core.rietveld_engine import refine_candidate


app = FastAPI(title="DRX Math Engine - Adaptive Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

class DrxRequest(BaseModel):
    anode: str
    two_theta: List[float]
    intensity: List[float]
    is_stripped: bool

class PipelineRequest(BaseModel):
    ids: List[int]      
    x: List[float]      
    y: List[float]      
    anode: str

class SimulationRequest(BaseModel):
    peaks: List[Any]
    anode: str
    tmin: float
    tmax: float

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "online", "mode": "Adaptive-HPC-Active"}

@app.post("/api/math/process") 
def process_drx(data: DrxRequest):
    """Fase inicial: Limpieza y detección de picos para la búsqueda en SQLite"""
    if data.anode not in ANODES:
        raise HTTPException(status_code=400, detail="Ánodo no soportado")
    
    wl_k1 = ANODES[data.anode]["ka1"]
    wl_k2 = ANODES[data.anode]["ka2"]
    x = np.array(data.two_theta)
    y = np.array(data.intensity)

    y_final = rachinger_correction(x, y, wl_k1, wl_k2) if not data.is_stripped else y
    top_peaks = extract_top_peaks(x, y_final, wl_k1, num_peaks=3)

    return {
        "status": "success",
        "cleaned_intensity": y_final.tolist(),
        "top_peaks": top_peaks
    }

@app.post("/api/math/pipeline-score")
def pipeline_score(data: PipelineRequest):
    try:
        conn = sqlite3.connect("HanawaltIndex.db")
        placeholders = ','.join(['?'] * len(data.ids))
        query = f"SELECT cod_id, d_spacing, intensity FROM hanawalt_peaks WHERE cod_id IN ({placeholders})"
        cursor = conn.execute(query, data.ids)
        
        candidates_dict = {}
        for row in cursor:
            cid, d, intensity = row
            if cid not in candidates_dict:
                candidates_dict[cid] = {"id": cid, "theoreticalPeaks": []}
            
            candidates_dict[cid]["theoreticalPeaks"].append({
                "d_spacing": float(d), 
                "intensity": float(intensity)
            })
        conn.close()

        candidate_list = list(candidates_dict.values())
        total_input = len(candidate_list)
        
        x_exp = np.array(data.x)
        y_exp = np.array(data.y)
        y_norm = (y_exp - np.min(y_exp)) / (np.max(y_exp) - np.min(y_exp)) if np.max(y_exp) > np.min(y_exp) else y_exp
        wl = ANODES.get(data.anode, ANODES["Cu"])["ka1"]

        if total_input > 40:
            survivors = run_adaptive_death_match(x_exp, y_norm, candidate_list, wl, target_k=40)
            mode = "ADAPTIVE_DEATH_MATCH"
        else:
            survivors = calculate_fast_match(x_exp, y_exp, candidate_list, wl)
            mode = "FAST_MATCH"

        return {
            "status": "SUCCESS",
            "mode": mode,
            "candidates": survivors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/math/simulate-peaks")
def simulate_peaks(data: SimulationRequest):
    wl = ANODES.get(data.anode, ANODES["Cu"])["ka1"]
    x_theor = np.linspace(data.tmin, data.tmax, 2000)
    y_theor = np.zeros_like(x_theor)
    
    peaks_to_draw = []
    for p in data.peaks:
        if isinstance(p, dict):
            d = p.get('dSpacing') or p.get('d_spacing') or p.get('DSpacing') or p.get('d')
            intensity = p.get('intensity') or p.get('Intensity') or 100.0
        else:
            d = getattr(p, 'dSpacing', getattr(p, 'd_spacing', getattr(p, 'DSpacing', getattr(p, 'd', 0))))
            intensity = getattr(p, 'intensity', getattr(p, 'Intensity', 100.0))
            
        if d and float(d) > 0:
            sin_th = wl / (2.0 * float(d))
            if sin_th <= 1.0:
                tth = np.degrees(np.arcsin(sin_th)) * 2.0
                if data.tmin <= tth <= data.tmax:
                    y_theor += float(intensity) * np.exp(-((x_theor - tth)**2) / (2 * 0.08**2))
    
    if np.max(y_theor) > 0:
        y_theor = (y_theor / np.max(y_theor)) * 1000
            
    return {"x": x_theor.tolist(), "y": y_theor.tolist()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.post("/api/math/rietveld-pruning")
def rietveld_pruning(data: dict):
    x_exp = np.array(data['x'])
    y_exp = np.array(data['y'])
    candidates = data['candidates']
    anode = data['anode']
    wl = ANODES.get(anode, ANODES["Cu"])["ka1"]
    
    refined_results = []
    
    print(f"\n--- INICIANDO PODA CIENTÍFICA (FOM) PARA {len(candidates)} FASES ---")
    
    for c in candidates:
        lattice = {
            'a': c.get('a') or c.get('A'), 
            'b': c.get('b') or c.get('B'), 
            'c': c.get('c') or c.get('C'),
            'alpha': c.get('alpha') or c.get('Alpha') or 90, 
            'beta': c.get('beta') or c.get('Beta') or 90, 
            'gamma': c.get('gamma') or c.get('Gamma') or 90
        }
        
        r_wp, y_fit, p_list, stats = refine_candidate(x_exp, y_exp, lattice, wl)
        
        if r_wp < 999:
            name = c.get('name') or f"COD {c.get('id')}"
            print(f"RESULTADO [{name}] -> FOM: {stats['fom']}% | Corr: {stats['intensity_corr']} | dth: {stats['zero_shift']}°")
            
            refined_results.append({
                **c,
                "fom": stats['fom'],
                "matchScore": stats['fom'], 
                "gof": stats['gof'],
                "r_wp": stats['r_wp'],
                "refined_y": y_fit,
                "is_refined": True,
                "details": {
                    "intensity_corr": stats['intensity_corr'],
                    "density_penalty": stats['density_penalty'],
                    "n_theor": stats['n_theor_peaks'],
                    "zero_shift": stats['zero_shift']
                }
            })

    refined_results.sort(key=lambda x: x['fom'], reverse=True)
    return refined_results