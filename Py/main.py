from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from scipy.interpolate import interp1d

app = FastAPI(title="DRX Math Engine - Rietveld Core")

ANODES = {
    "Cu": {"ka1": 1.54060, "ka2": 1.54439},
    "Mo": {"ka1": 0.70930, "ka2": 0.71359},
    "Co": {"ka1": 1.78896, "ka2": 1.79285},
    "Cr": {"ka1": 2.28970, "ka2": 2.29361},
    "Fe": {"ka1": 1.93604, "ka2": 1.93998},
    "W":  {"ka1": 0.20901, "ka2": 0.21381}
}

class DrxData(BaseModel):
    two_theta: List[float]
    intensity: List[float]
    anode: str = "Cu"

def rachinger_correction(two_theta: np.ndarray, intensity: np.ndarray, wl_k1: float, wl_k2: float):
    """
    Aplica el método de Rachinger para sustraer la contribución K_alpha2.
    """
    theta_rad = np.radians(two_theta / 2.0)
    
    theta1_rad = np.arcsin((wl_k1 / wl_k2) * np.sin(theta_rad))
    two_theta_shifted = np.degrees(theta1_rad) * 2.0
    
    i_clean = np.copy(intensity)
    
    ratio = 0.5 
    
    for i in range(len(two_theta)):
        interpolator = interp1d(two_theta, i_clean, kind='linear', bounds_error=False, fill_value=0.0)
        
        i_ka1_previous = interpolator(two_theta_shifted[i])
        
        i_clean[i] = intensity[i] - (ratio * i_ka1_previous)
        
    i_clean = np.clip(i_clean, 0, None)
    
    return i_clean

@app.post("/api/math/strip-ka2")
def strip_ka2(data: DrxData):
    if data.anode not in ANODES:
        raise HTTPException(status_code=400, detail="Ánodo no soportado")
    
    wl_k1 = ANODES[data.anode]["ka1"]
    wl_k2 = ANODES[data.anode]["ka2"]

    x = np.array(data.two_theta)
    y = np.array(data.intensity)

    y_cleaned = rachinger_correction(x, y, wl_k1, wl_k2)

    return {
        "status": "success",
        "anode_used": data.anode,
        "wavelengths": {"ka1": wl_k1, "ka2": wl_k2},
        "cleaned_intensity": y_cleaned.tolist()
    }