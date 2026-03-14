from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np

from core.constants import ANODES
from core.stripping import rachinger_correction
from core.hanawalt import extract_top_peaks
from core.simulator import simulate_theoretical

class DrxRequest(BaseModel):
    anode: str
    two_theta: List[float]
    intensity: List[float]
    is_stripped: bool

app = FastAPI(title="DRX Math Engine")

@app.get("/api/math/simulate")
def simulate(a: float, b: float, c: float, alpha: float, beta: float, gamma: float, anode: str, tmin: float, tmax: float):
    wl = ANODES.get(anode, ANODES["Cu"])["ka1"]
    
    x_theor = np.linspace(tmin, tmax, 2000)
    y_theor = np.zeros_like(x_theor)
    
    d_spacings = [a, b, c, a/2, b/2, c/2] 
    
    for d in d_spacings:
        if d <= 0: continue
        sin_theta = wl / (2 * d)
        if sin_theta > 1: continue
        
        tth = np.degrees(np.arcsin(sin_theta)) * 2
        if tmin <= tth <= tmax:
            y_theor += 1000 * np.exp(-((x_theor - tth)**2) / (2 * 0.1**2))
            
    return {"x": x_theor.tolist(), "y": y_theor.tolist()} 

@app.post("/api/math/process") 
def process_drx(data: DrxRequest):
    if data.anode not in ANODES:
        raise HTTPException(status_code=400, detail="Ánodo no soportado")
    
    wl_k1 = ANODES[data.anode]["ka1"]
    wl_k2 = ANODES[data.anode]["ka2"]

    x = np.array(data.two_theta)
    y = np.array(data.intensity)

    if not data.is_stripped:
        y_final = rachinger_correction(x, y, wl_k1, wl_k2)
    else:
        y_final = y 

    top_peaks = extract_top_peaks(x, y_final, wl_k1, num_peaks=3)

    return {
        "status": "success",
        "anode_used": data.anode,
        "wavelengths": {"ka1": wl_k1, "ka2": wl_k2},
        "cleaned_intensity": y_final.tolist(),
        "top_peaks": top_peaks
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)