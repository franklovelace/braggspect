import numpy as np
from scipy.signal import find_peaks

def extract_top_peaks(two_theta: np.ndarray, intensity: np.ndarray, wl_k1: float, num_peaks: int = 3) -> list:
    """ Encuentra los picos más altos y aplica la Ley de Bragg """
    
    prominence_threshold = np.max(intensity) * 0.05 
    peaks_indices, _ = find_peaks(intensity, prominence=prominence_threshold)
    
    peak_intensities = intensity[peaks_indices]
    peak_2thetas = two_theta[peaks_indices]
    
    sorted_indices = np.argsort(peak_intensities)[::-1]
    top_indices = sorted_indices[:num_peaks]
    
    top_peaks = []
    for idx in top_indices:
        tth = peak_2thetas[idx]
        inty = peak_intensities[idx]
        
        theta_rad = np.radians(tth / 2.0)
        d_spacing = wl_k1 / (2.0 * np.sin(theta_rad))
        
        top_peaks.append({
            "two_theta": round(float(tth), 4),
            "d_spacing": round(float(d_spacing), 4),
            "intensity": round(float(inty), 2)
        })

    return top_peaks