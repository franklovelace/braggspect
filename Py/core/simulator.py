import numpy as np

def simulate_theoretical(a, b, c, alpha, beta, gamma, anode_wl, tth_min, tth_max):
    """ Genera picos de Bragg basados en los parámetros de red """
    x_theor = np.linspace(tth_min, tth_max, 2000)
    y_theor = np.zeros_like(x_theor)
    
    # Simplificación: Generamos picos basados en las distancias de los ejes
    # En un futuro aquí usaríamos hkl y factores de estructura
    d_spacings = [a, b, c, a/2, b/2, c/2] 
    
    for d in d_spacings:
        if d <= 0: continue
        sin_theta = anode_wl / (2 * d)
        if sin_theta > 1: continue
        
        tth = np.degrees(np.arcsin(sin_theta)) * 2
        
        if tth_min <= tth <= tth_max:
            y_theor += 100 * np.exp(-((x_theor - tth)**2) / (2 * 0.1**2))
            
    return x_theor.tolist(), y_theor.tolist()