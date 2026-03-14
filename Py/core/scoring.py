import numpy as np

def calculate_fast_match(x_exp, y_exp, candidates, anode_wl):
    """
    Puntúa candidatos basándose en la coincidencia de picos teóricos 
    con la intensidad experimental.
    """
    scored_results = []
    
    y_norm = (y_exp - np.min(y_exp)) / (np.max(y_exp) - np.min(y_exp))
    
    for c in candidates:
        d_vals = [c.get('a'), c.get('b'), c.get('c')]
        tth_teoricos = []
        
        for d in d_vals:
            if d is None or d <= 0: continue
            sin_theta = anode_wl / (2 * d)
            if sin_theta <= 1:
                tth_teoricos.append(np.degrees(np.arcsin(sin_theta)) * 2)
        
        score = 0
        window = 0.15 
        
        for p_tth in tth_teoricos:
            mask = (x_exp >= p_tth - window) & (x_exp <= p_tth + window)
            if np.any(mask):
                score += np.max(y_norm[mask])
        
        final_score = (score / len(tth_teoricos) * 100) if tth_teoricos else 0
        
        scored_results.append({
            **c,
            "match_score": round(final_score, 1)
        })

    scored_results.sort(key=lambda x: x['match_score'], reverse=True)
    return scored_results