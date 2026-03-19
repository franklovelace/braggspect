from __future__ import annotations

import numpy as np
from dataclasses import dataclass



@dataclass
class Rigor:
    penalty_weight:        float = 0.5
    significant_threshold: float = 0.20
    min_score:             float = 0.0
    min_match_ratio:       float = 0.20
    min_matches:           int   = 1

    def tighten(self, step: int) -> "Rigor":
        factor = 1.0 + step * 0.12
        return Rigor(
            penalty_weight        = min(self.penalty_weight        * factor, 4.0),
            significant_threshold = min(self.significant_threshold * factor, 0.6),
            min_score             = min(self.min_score             + step * 3.0, 60.0),
            min_match_ratio       = min(self.min_match_ratio       * factor, 0.75),
            min_matches           = min(self.min_matches           + step // 3, 5),
        )



def _to_2theta(d: float, wl: float) -> float | None:
    s = wl / (2.0 * d)
    return float(np.degrees(np.arcsin(s)) * 2.0) if 0.0 < s <= 1.0 else None


def _dynamic_window(tth: np.ndarray, base: float = 0.10) -> np.ndarray:
    return base * (1.0 + tth / 120.0)


def _score(
    x_exp: np.ndarray,
    y_norm: np.ndarray,
    peaks: list[dict],
    wl: float,
    r: Rigor,
) -> tuple[float, int, int]:
    valid: list[tuple[float, float]] = []
    for p in peaks:
        d   = p.get("d") or p.get("d_spacing")
        raw = p.get("intensity") or p.get("Intensity")
        if not d or not raw or float(d) <= 0:
            continue
        tth = _to_2theta(float(d), wl)
        if tth is None:
            continue
        valid.append((tth, float(raw) / 100.0))

    if not valid:
        return 0.0, 0, 0

    tth_arr   = np.array([v[0] for v in valid])
    theor_arr = np.array([v[1] for v in valid])
    wsum      = theor_arr.sum()
    if wsum == 0:
        return 0.0, 0, 0

    windows  = _dynamic_window(tth_arr)
    diff     = np.abs(x_exp[np.newaxis, :] - tth_arr[:, np.newaxis])
    hit_mask = diff <= windows[:, np.newaxis]
    matched  = hit_mask.any(axis=1)

    exp_i = np.where(
        matched,
        np.max(np.where(hit_mask, y_norm[np.newaxis, :], 0.0), axis=1),
        0.0,
    )
    sig_missing = (~matched) & (theor_arr > r.significant_threshold)
    sc = (exp_i * theor_arr).sum() - theor_arr[sig_missing].sum() * r.penalty_weight

    return float(sc / wsum), int(matched.sum()), len(valid)


def _apply_rigor(
    x_exp: np.ndarray,
    y_norm: np.ndarray,
    candidates: list[dict],
    wl: float,
    r: Rigor,
) -> list[dict]:
    survivors: list[dict] = []
    for c in candidates:
        peaks = c.get("theoreticalPeaks") or c.get("TheoreticalPeaks") or []
        if not peaks:
            continue
        raw, n_match, n_valid = _score(x_exp, y_norm, peaks, wl, r)
        if n_valid == 0:
            continue
        ratio = n_match / n_valid
        if raw <= 0 or n_match < r.min_matches or ratio < r.min_match_ratio:
            continue
        final = round(max(0.0, min(100.0, raw * 100.0)), 1)
        if final < r.min_score:
            continue
        survivors.append({
            **c,
            "match_score":   final,
            "peaks_matched": n_match,
            "peaks_valid":   n_valid,
            "match_ratio":   round(ratio, 3),
        })
    survivors.sort(key=lambda x: x["match_score"], reverse=True)
    return survivors



def run_adaptive_death_match(
    x_exp: np.ndarray,
    y_norm: np.ndarray,
    candidates: list[dict],
    anode_wl: float,
    target_k: int = 40,
    max_steps: int = 30,
    verbose: bool = False,
) -> list[dict]:
    """
    Death Match adaptativo: aprieta los criterios iterativamente hasta obtener
    exactamente `target_k` candidatos (o el mínimo seguro si no es posible).

    Garantía de seguridad
    ---------------------
    Nunca devuelve menos de `target_k` candidatos mientras existan suficientes
    en `candidates`. Si al apretar se cae por debajo del target, recupera el
    último resultado estable con >= target_k supervivientes.

    Parámetros
    ----------
    x_exp      : array 2theta experimental (grados).
    y_norm     : intensidades normalizadas [0, 1].
    candidates : todos los candidatos de la base de datos.
    anode_wl   : longitud de onda en Angstrom (p.ej. 1.5406 Cu Ka).
    target_k   : candidatos refinados deseados (default 40).
    max_steps  : límite de iteraciones.
    verbose    : imprime el progreso de cada paso.

    Devuelve
    --------
    Lista de hasta `target_k` candidatos ordenados por `match_score`,
    con campos extra: `peaks_matched`, `peaks_valid`, `match_ratio`.
    """
    x_exp  = np.asarray(x_exp,  dtype=np.float64)
    y_norm = np.asarray(y_norm, dtype=np.float64)

    rigor = Rigor()
    last_stable: list[dict] = []

    for step in range(max_steps + 1):
        result = _apply_rigor(x_exp, y_norm, candidates, anode_wl, rigor)
        n = len(result)

        if verbose:
            print(
                f"[step {step:02d}] n={n:4d} | "
                f"penalty={rigor.penalty_weight:.2f}  "
                f"min_score={rigor.min_score:.1f}  "
                f"min_ratio={rigor.min_match_ratio:.2f}  "
                f"sig_thresh={rigor.significant_threshold:.2f}  "
                f"min_matches={rigor.min_matches}"
            )

        if n >= target_k:
            last_stable = result[:target_k]

        if n == target_k:
            if verbose:
                print(f"[converged] exactamente {target_k} en paso {step}.")
            return last_stable

        if n < target_k:
            if verbose:
                print(
                    f"[safety] paso {step} cayó a {n} < {target_k}. "
                    f"Recuperando último estado estable."
                )
            if last_stable:
                return last_stable
            return result

        rigor = rigor.tighten(step + 1)

    if verbose:
        print(f"[max_steps] devolviendo último estado estable.")
    if last_stable:
        return last_stable
    return _apply_rigor(x_exp, y_norm, candidates, anode_wl, Rigor())[:target_k]
