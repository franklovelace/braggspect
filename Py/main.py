from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np

from core.constants import ANODES
from core.stripping import rachinger_correction
from core.hanawalt import extract_top_peaks
from core.simulator import simulate_theoretical

app = FastAPI(title="DRX Math Engine")

@app.get("/api/math/simulate")
def simulate(a: float, b: float, c: float, alpha: float, beta: float, gamma: float, anode: str, tmin: float, tmax: float):
    wl = ANODES.get(anode, ANODES["Cu"])["ka1"]
    x, y = simulate_theoretical(a, b, c, alpha, beta, gamma, wl, tmin, tmax)
    return {"x": x, "y": y}

class DrxRequest(BaseModel):
    two_theta: List[float]
    intensity: List[float]
    anode: str = "Cu"
    is_stripped: bool = False  

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