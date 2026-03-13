import numpy as np
from scipy.interpolate import interp1d

def rachinger_correction(two_theta: np.ndarray, intensity: np.ndarray, wl_k1: float, wl_k2: float) -> np.ndarray:
    """ Sustrae la contribución del doblete K-alpha 2 """
    theta_rad = np.radians(two_theta / 2.0)
    theta1_rad = np.arcsin((wl_k1 / wl_k2) * np.sin(theta_rad))
    two_theta_shifted = np.degrees(theta1_rad) * 2.0
    
    i_clean = np.copy(intensity)
    ratio = 0.5 
    
    for i in range(len(two_theta)):
        interpolator = interp1d(two_theta, i_clean, kind='linear', bounds_error=False, fill_value=0.0)
        i_ka1_previous = interpolator(two_theta_shifted[i])
        i_clean[i] = intensity[i] - (ratio * i_ka1_previous)
        
    return np.clip(i_clean, 0, None)