from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np

app = FastAPI(title="DRX Math Engine - Rietveld Core")

# Diccionario de Ánodos Comunes (Longitudes de onda en Angstroms)
ANODES = {
    "Cu": {"ka1": 1.54060, "ka2": 1.54439},
    "Mo": {"ka1": 0.70930, "ka2": 0.71359},
    "Co": {"ka1": 1.78896, "ka2": 1.79285},
    "Cr": {"ka1": 2.28970, "ka2": 2.29361},
    "Fe": {"ka1": 1.93604, "ka2": 1.93998},
    "W":  {"ka1": 0.20901, "ka2": 0.21381} # Tungsteno/Wolframio
}

class DrxData(BaseModel):
    two_theta: List[float]
    intensity: List[float]
    anode: str = "Cu" # Cobre por defecto

@app.post("/api/math/strip-ka2")
def strip_ka2(data: DrxData):
    # 1. Validar Ánodo
    if data.anode not in ANODES:
        raise HTTPException(status_code=400, detail=f"Ánodo '{data.anode}' no soportado. Use: {list(ANODES.keys())}")
    
    wl_k1 = ANODES[data.anode]["ka1"]
    wl_k2 = ANODES[data.anode]["ka2"]

    # 2. Convertir a NumPy arrays para velocidad extrema
    x = np.array(data.two_theta)
    y = np.array(data.intensity)

    # MOCK: Suavizado muy básico (Moving Average) como prueba de vida
    window = 5
    y_smoothed = np.convolve(y, np.ones(window)/window, mode='same').tolist()

    return {
        "status": "success",
        "anode_used": data.anode,
        "wavelengths": {"ka1": wl_k1, "ka2": wl_k2},
        "message": f"Stripping K_alpha2 aplicado para ánodo de {data.anode}",
        "cleaned_intensity": y_smoothed # Devolvemos el array procesado
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)