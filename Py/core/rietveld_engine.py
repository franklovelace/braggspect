from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares
from scipy.signal import find_peaks
from scipy.stats import pearsonr
from numpy.polynomial.chebyshev import Chebyshev



def _metric_tensor_inv(a, b, c, alpha, beta, gamma) -> np.ndarray:
    ar, br, gr = np.radians([alpha, beta, gamma])
    G = np.array([
        [a**2,           a*b*np.cos(gr), a*c*np.cos(br)],
        [a*b*np.cos(gr), b**2,           b*c*np.cos(ar)],
        [a*c*np.cos(br), b*c*np.cos(ar), c**2          ],
    ])
    return np.linalg.inv(G)



def generate_hkl_reflections(
    a, b, c, alpha, beta, gamma, wl, tth_max
) -> tuple[np.ndarray, np.ndarray]:
    G_inv = _metric_tensor_inv(a, b, c, alpha, beta, gamma)
    limit = min(int(np.ceil(2 * max(a, b, c) / wl)) + 1, 20)

    d_mult: dict[float, int] = {}
    for h in range(-limit, limit + 1):
        for k in range(-limit, limit + 1):
            for l in range(-limit, limit + 1):
                if h == k == l == 0:
                    continue
                hkl    = np.array([h, k, l], dtype=float)
                inv_d2 = hkl @ G_inv @ hkl
                if inv_d2 <= 0:
                    continue
                d      = np.sqrt(1.0 / inv_d2)
                sin_th = wl / (2.0 * d)
                if sin_th > 1.0:
                    continue
                tth = float(np.degrees(np.arcsin(sin_th)) * 2.0)
                if tth > tth_max:
                    continue
                key = round(d, 4)
                d_mult[key] = d_mult.get(key, 0) + 1

    if not d_mult:
        return np.array([]), np.array([])

    d_arr  = np.array(list(d_mult.keys()))
    mult   = np.array(list(d_mult.values()), dtype=float)
    sin_th = wl / (2.0 * d_arr)
    tth    = np.degrees(np.arcsin(np.clip(sin_th, 0, 1))) * 2.0
    order  = np.argsort(tth)
    return tth[order], mult[order]



def _caglioti_fwhm(tth_deg: np.ndarray, U, V, W) -> np.ndarray:
    th     = np.radians(tth_deg / 2.0)
    tan_th = np.tan(th)
    return np.sqrt(np.clip(U * tan_th**2 + V * tan_th + W, 1e-8, None))


def _pseudo_voigt(x, center, fwhm, eta) -> np.ndarray:
    sigma = fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    G = np.exp(-((x - center)**2) / (2.0 * sigma**2))
    L = 1.0 / (1.0 + ((x - center) / (fwhm / 2.0))**2)
    return eta * L + (1.0 - eta) * G


def _lp_correction(tth_deg: np.ndarray) -> np.ndarray:
    th     = np.radians(tth_deg / 2.0)
    cos2th = np.cos(np.radians(tth_deg))
    lp     = (1.0 + cos2th**2) / np.clip(np.sin(th)**2 * np.cos(th), 1e-10, None)
    return lp / lp.max()



def _build_unscaled_pattern(
    x_exp: np.ndarray,
    tth_arr: np.ndarray,
    mult_arr: np.ndarray,
    zero: float = 0.0,
    U: float = 0.01,
    V: float = -0.01,
    W: float = 0.04,
    eta: float = 0.3,
) -> np.ndarray:
    """
    Devuelve y_sim SIN escalar (max ≈ 1).
    Separar la construcción de la escala es la clave para estimar scale0 correctamente.
    """
    if len(tth_arr) == 0:
        return np.zeros_like(x_exp)

    fwhm_arr = _caglioti_fwhm(tth_arr, U, V, W)
    lp_arr   = _lp_correction(tth_arr)
    x_min, x_max = x_exp[0], x_exp[-1]

    y_sim = np.zeros_like(x_exp, dtype=np.float64)
    for i, tth_c in enumerate(tth_arr):
        center = tth_c + zero
        if center < x_min - 2 or center > x_max + 2:
            continue
        y_sim += mult_arr[i] * lp_arr[i] * _pseudo_voigt(x_exp, center, fwhm_arr[i], eta)

    peak = y_sim.max()
    return y_sim / peak if peak > 0 else y_sim



def _estimate_zero_and_scale(
    x_exp: np.ndarray,
    y_exp: np.ndarray,
    tth_arr: np.ndarray,
    mult_arr: np.ndarray,
) -> tuple[float, float]:
    """
    1. Busca el zero-shift que maximiza correlación cruzada (±0.5° en pasos de 0.02°)
    2. Con ese zero, estima scale = dot(y_exp, y_sim) / dot(y_sim, y_sim)
       — mínimos cuadrados de 1 parámetro, solución analítica exacta.
    """
    if len(tth_arr) == 0:
        return 0.0, float(np.max(y_exp))

    offsets     = np.arange(-0.5, 0.51, 0.02)
    best_offset = 0.0
    best_corr   = -np.inf

    for offset in offsets:
        y_sim = _build_unscaled_pattern(x_exp, tth_arr, mult_arr, zero=offset)
        if y_sim.max() == 0:
            continue
        corr = float(np.corrcoef(y_exp, y_sim)[0, 1])
        if corr > best_corr:
            best_corr   = corr
            best_offset = float(offset)

    bg_est  = float(np.percentile(y_exp, 5))
    y_exp_c = y_exp - bg_est  
    y_sim   = _build_unscaled_pattern(x_exp, tth_arr, mult_arr, zero=best_offset)

    denom   = float(np.dot(y_sim, y_sim))
    scale0  = float(np.dot(y_exp_c, y_sim)) / denom if denom > 0 else float(np.max(y_exp))
    scale0  = max(scale0, 1.0)

    return best_offset, scale0



def _count_exp_peaks(y_exp: np.ndarray) -> int:
    noise      = np.percentile(y_exp, 25)
    height_thr = noise + (y_exp.max() - noise) * 0.05
    peaks, _   = find_peaks(y_exp, height=height_thr, distance=5)
    return max(len(peaks), 1)


def _intensity_correlation(
    x_exp: np.ndarray,
    y_exp: np.ndarray,
    tth_theor: np.ndarray,
    theor_weight: np.ndarray,
    window: float = 0.15,
) -> float:
    tw, ew = [], []
    for i, tth_c in enumerate(tth_theor):
        mask = (x_exp >= tth_c - window) & (x_exp <= tth_c + window)
        if mask.any():
            tw.append(theor_weight[i])
            ew.append(float(np.max(y_exp[mask])))
    if len(tw) < 3:
        return 0.0
    r, _ = pearsonr(tw, ew)
    return max(0.0, float(r))


def _density_penalty(n_theor: int, n_exp: int, k: float = 0.5) -> float:
    ratio = max(1.0, n_theor / n_exp)
    return 1.0 / (1.0 + k * np.log(ratio))


def composite_fom(
    r_wp: float,
    r_exp: float,
    i_corr: float,
    density: float,
    w_gof: float     = 0.50,
    w_corr: float    = 0.30,
    w_density: float = 0.20,
) -> float:
    gof       = r_wp / max(r_exp, 0.1)
    gof_score = min(1.0 / max(gof, 0.1), 1.0)
    return (w_gof * gof_score + w_corr * i_corr + w_density * density) * 100.0



def refine_candidate(
    x_exp: np.ndarray,
    y_exp: np.ndarray,
    lattice: dict,
    anode_wl: float,
    cell_tolerance: float = 0.03,
    n_bg_terms: int = 4,
) -> tuple[float, list, list, dict]:
    """
    Devuelve (Rwp, y_fit, params, metrics).
    Ordenar siempre por metrics["fom"] descendente — nunca por Rwp crudo.
    No hay corte duro: el filtrado lo hace el caller con FOM si lo necesita.
    """
    a0 = lattice['a'];  b0 = lattice['b'];  c0 = lattice['c']
    al = lattice.get('alpha', 90.0)
    be = lattice.get('beta',  90.0)
    ga = lattice.get('gamma', 90.0)

    x_exp  = np.asarray(x_exp,  dtype=np.float64)
    y_exp  = np.asarray(y_exp,  dtype=np.float64)
    x_min, x_max = float(x_exp[0]), float(x_exp[-1])
    x_norm = 2.0 * (x_exp - x_min) / (x_max - x_min) - 1.0

    n_exp_peaks = _count_exp_peaks(y_exp)
    weights     = 1.0 / np.maximum(y_exp, 1.0)

    tth_peaks:  list[float] = []
    mult_peaks: list[float] = []
    lattice_ref = [a0, b0, c0]

    t0, m0 = generate_hkl_reflections(a0, b0, c0, al, be, ga, anode_wl, x_max + 2)
    tth_peaks.extend(t0);  mult_peaks.extend(m0)

    tth_arr0  = np.array(tth_peaks)
    mult_arr0 = np.array(mult_peaks)

    zero_est, scale_est = _estimate_zero_and_scale(
        x_exp, y_exp, tth_arr0, mult_arr0
    )
    bg0 = float(np.percentile(y_exp, 5))

    def _ycalc(p: np.ndarray) -> np.ndarray:
        a, b, c, zero, scale, U, V, W, eta = p[:9]
        bg = p[9:]

        if not np.allclose([a, b, c], lattice_ref, rtol=1e-5):
            t, m = generate_hkl_reflections(a, b, c, al, be, ga, anode_wl, x_max + 2)
            tth_peaks.clear();  tth_peaks.extend(t)
            mult_peaks.clear(); mult_peaks.extend(m)
            lattice_ref[0], lattice_ref[1], lattice_ref[2] = a, b, c

        tth_arr  = np.array(tth_peaks)
        mult_arr = np.array(mult_peaks)
        bg_curve = Chebyshev(bg)(x_norm)

        if len(tth_arr) == 0:
            return bg_curve

        y_sim = _build_unscaled_pattern(x_exp, tth_arr, mult_arr, zero, U, V, W, eta)
        return y_sim * scale + bg_curve

    def objective(p):
        return (y_exp - _ycalc(p)) * np.sqrt(weights)

    lo = [a0*(1-cell_tolerance), b0*(1-cell_tolerance), c0*(1-cell_tolerance),
          -0.5, 1.0, 0.0, -0.1, 0.001, 0.0, *[-5000.0]*n_bg_terms]
    hi = [a0*(1+cell_tolerance), b0*(1+cell_tolerance), c0*(1+cell_tolerance),
           0.5, scale_est * 5, 0.2, 0.05, 0.2, 1.0, *[5000.0]*n_bg_terms]

    zero_starts = sorted({zero_est, 0.0, zero_est + 0.1, zero_est - 0.1})

    best_res = None
    best_rwp = np.inf

    for z_start in zero_starts:
        z_init = float(np.clip(z_start, lo[3], hi[3]))
        p0 = [
            a0, b0, c0,
            z_init, scale_est,
            0.01, -0.01, 0.04, 0.3,
            bg0, 0.0, 0.0, 0.0,
            *([0.0] * max(0, n_bg_terms - 4))
        ]
        try:
            res = least_squares(
                objective, p0, bounds=(lo, hi),
                method='trf', ftol=1e-3, xtol=1e-3, gtol=1e-3, max_nfev=400,
            )
            residuals_raw = res.fun / np.sqrt(weights)
            rwp_this = np.sqrt(
                np.sum(weights * residuals_raw**2) / np.sum(weights * y_exp**2)
            ) * 100.0
            if rwp_this < best_rwp:
                best_rwp = rwp_this
                best_res = res
        except Exception:
            continue

    if best_res is None:
        return 999.0, [], [], {"error": "all starts failed", "fom": 0.0}

    res = best_res
    residuals_raw = res.fun / np.sqrt(weights)
    r_wp  = np.sqrt(np.sum(weights * residuals_raw**2) / np.sum(weights * y_exp**2)) * 100.0
    r_exp = np.sqrt((len(y_exp) - len(lo)) / np.sum(weights * y_exp**2)) * 100.0
    gof   = r_wp / max(r_exp, 0.1)

    tth_arr  = np.array(tth_peaks)
    mult_arr = np.array(mult_peaks)
    lp_arr   = _lp_correction(tth_arr) if len(tth_arr) > 0 else np.array([])
    theor_w  = mult_arr * lp_arr if len(tth_arr) > 0 else np.array([])

    i_corr  = _intensity_correlation(x_exp, y_exp, tth_arr, theor_w)
    density = _density_penalty(len(tth_arr), n_exp_peaks)
    fom     = composite_fom(r_wp, r_exp, i_corr, density)

    y_fit = _ycalc(res.x).tolist()

    return r_wp, y_fit, res.x.tolist(), {
        "r_wp":            round(r_wp,    3),
        "r_exp":           round(r_exp,   3),
        "gof":             round(gof,     3),
        "intensity_corr":  round(i_corr,  3),
        "density_penalty": round(density, 3),
        "fom":             round(fom,     2),
        "n_theor_peaks":   len(tth_arr),
        "n_exp_peaks":     n_exp_peaks,
        "zero_shift":      round(float(res.x[3]), 4),
        "zero_initial":    round(zero_est,  4),
        "scale_initial":   round(scale_est, 2),
        "cell":            {"a": res.x[0], "b": res.x[1], "c": res.x[2]},
    }