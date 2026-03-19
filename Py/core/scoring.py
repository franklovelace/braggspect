import numpy as np

def calculate_fast_match(x_exp, y_exp, candidates, anode_wl):
    """
    Algoritmo de Embudo (Funneling) para Identificación de Fases.
    Fase 1: Posición (Theta)
    Fase 2: Topología (Intensidad Relativa)
    Fase 3: Veracidad (Penalización por Fantasmas)
    """
    survivors = []
    
    y_min, y_max = np.min(y_exp), np.max(y_exp)
    if y_max == y_min: return [] 
    
    y_norm = (y_exp - y_min) / (y_max - y_min) 
    
    NOISE_THRESHOLD = 0.05 
    
    for c in candidates:
        peaks = c.get('theoreticalPeaks') or c.get('TheoreticalPeaks') or []
        if not peaks: continue

        valid_peaks = []
        for p in peaks:
            d = p.get('dSpacing') or p.get('d_spacing') or p.get('DSpacing')
            raw_i = p.get('intensity') or p.get('Intensity') or 100.0
            
            if d is None or d <= 0: continue
            sin_th = anode_wl / (2.0 * d)
            if sin_th > 1.0: continue
            
            tth = np.degrees(np.arcsin(sin_th)) * 2.0
            valid_peaks.append({"tth": tth, "intensity": float(raw_i) / 100.0})
            
        if not valid_peaks: continue

        position_score = 0.0
        matched_peaks = []
        
        valid_peaks.sort(key=lambda x: x['intensity'], reverse=True)
        
        top_3_theor = valid_peaks[:3]
        passed_phase_1 = False
        
        for p in top_3_theor:
            tth_t = p['tth']
            i_t = p['intensity']
            
            window = 0.15
            mask = (x_exp >= tth_t - window) & (x_exp <= tth_t + window)
            
            if np.any(mask):
                i_exp = np.max(y_norm[mask])
                if i_exp > NOISE_THRESHOLD:
                    passed_phase_1 = True
                    position_score += i_exp * i_t
                    matched_peaks.append({"tth": tth_t, "i_exp": i_exp, "i_t": i_t})

        if not passed_phase_1:
            continue

        topology_score = 1.0
        if len(matched_peaks) > 1:
            ratio_teorico = matched_peaks[0]['i_t'] / (matched_peaks[1]['i_t'] + 1e-5)
            ratio_exp = matched_peaks[0]['i_exp'] / (matched_peaks[1]['i_exp'] + 1e-5)
            
            ratio_diff = abs(np.log(ratio_teorico + 1e-5) - np.log(ratio_exp + 1e-5))
            
            if ratio_diff > 1.5: 
                topology_score = 0.5 
            elif ratio_diff > 3.0:
                continue 

        ghost_penalty = 0.0
        
        for p in valid_peaks:
            tth_t = p['tth']
            i_t = p['intensity']
            
            if i_t < 0.1: continue
                
            window = 0.15
            mask = (x_exp >= tth_t - window) & (x_exp <= tth_t + window)
            
            if np.any(mask):
                i_exp = np.max(y_norm[mask])
                if i_exp < NOISE_THRESHOLD:
                    ghost_penalty += i_t * 2.0 
            else:
                ghost_penalty += i_t * 1.0

        raw_score = (position_score * topology_score) - ghost_penalty
        
        weight_sum = sum(p['intensity'] for p in top_3_theor)
        final_score = (raw_score / weight_sum) * 100.0 if weight_sum > 0 else 0
        
        final_score = max(0.0, min(100.0, final_score))

        if final_score > 5.0:
            survivors.append({**c, "match_score": round(final_score, 1)})

    survivors.sort(key=lambda x: x['match_score'], reverse=True)
    
    return survivors[:50]