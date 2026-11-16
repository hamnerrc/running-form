"""Stage 5: filtering (README §5.5).

- Resample onto a uniform time grid from the real PTS (iPhone slo-mo timing can jitter).
- Short gaps (≤ max_gap_s) are filled by PCHIP; longer gaps stay NaN and each contiguous run is filtered alone.
- Zero-lag 4th-order Butterworth = 2nd-order filtered forward + backward, with Winter's (2009 §3.4.4.3)
  correction so the -3 dB point of the *combined* filter sits at the requested cutoff.
- Cutoff per signal by Winter residual analysis.
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.signal import butter, filtfilt

C_DOUBLE_PASS = 0.802  # Winter: (2^(1/n) - 1)^(1/4) for n=2 passes of a 2nd-order filter


def resample_uniform(t: np.ndarray, x: np.ndarray, fs: float | None = None) -> tuple[np.ndarray, np.ndarray]:
    """x: (N, ...) sampled at times t. Returns uniform grid (tu, xu). NaNs are preserved where data is missing."""
    if fs is None:
        fs = 1 / np.median(np.diff(t))
    tu = np.arange(t[0], t[-1] + 0.5 / fs, 1 / fs)
    flat = x.reshape(len(t), -1)
    out = np.full((len(tu), flat.shape[1]), np.nan)
    for c in range(flat.shape[1]):
        good = np.isfinite(flat[:, c])
        if good.sum() < 2:
            continue
        out[:, c] = np.interp(tu, t[good], flat[good, c])
        # re-insert gaps: grid points whose nearest original sample is missing
        nearest = np.clip(np.searchsorted(t, tu), 0, len(t) - 1)
        prev = np.clip(nearest - 1, 0, len(t) - 1)
        pick = np.where(np.abs(t[prev] - tu) < np.abs(t[nearest] - tu), prev, nearest)
        out[~good[pick], c] = np.nan
    return tu, out.reshape((len(tu),) + x.shape[1:])


def fill_gaps(x: np.ndarray, fs: float, max_gap_s: float) -> np.ndarray:
    """PCHIP-fill NaN runs no longer than max_gap_s in a 1-D signal."""
    x = x.copy()
    bad = ~np.isfinite(x)
    if not bad.any() or bad.all():
        return x
    idx = np.arange(len(x))
    f = PchipInterpolator(idx[~bad], x[~bad], extrapolate=False)
    max_gap = int(round(max_gap_s * fs))
    for s, e in _runs(bad):
        if e - s <= max_gap and s > 0 and e < len(x):
            x[s:e] = f(idx[s:e])
    return x


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """[start, end) of True runs."""
    d = np.diff(np.r_[0, mask.astype(int), 0])
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def butter_zero_lag(x: np.ndarray, fs: float, fc: float) -> np.ndarray:
    """Zero-lag 4th-order low-pass on each finite run of a 1-D signal (runs too short stay unfiltered)."""
    y = np.full_like(x, np.nan, dtype=float)
    wc = fc / C_DOUBLE_PASS
    wn = min(wc / (fs / 2), 0.99)
    b, a = butter(2, wn)
    padlen = 3 * max(len(a), len(b))
    for s, e in _runs(np.isfinite(x)):
        seg = x[s:e]
        y[s:e] = filtfilt(b, a, seg, padlen=min(padlen, len(seg) - 1)) if len(seg) > padlen else seg
    return y


def residual_cutoff(x: np.ndarray, fs: float, fmin: float = 1.0, fmax: float | None = None,
                    tail: tuple[float, float] = (0.5, 1.0)) -> tuple[float, np.ndarray, np.ndarray]:
    """Winter residual analysis. Returns (fc, freqs, residuals).
    The linear (noise) region is fitted over the top part of the frequency range `tail` (fractions);
    fc is where the residual curve meets that line's intercept."""
    fmax = fmax or min(0.4 * fs, 40.0)
    freqs = np.arange(fmin, fmax + 1e-9, 0.5)
    good = np.isfinite(x)
    if good.sum() < 20:
        return float("nan"), freqs, np.full_like(freqs, np.nan)
    res = np.array([np.sqrt(np.nanmean((x - butter_zero_lag(x, fs, f)) ** 2)) for f in freqs])
    lo, hi = int(tail[0] * len(freqs)), int(tail[1] * len(freqs))
    slope, intercept = np.polyfit(freqs[lo:hi], res[lo:hi], 1)
    above = np.nonzero(res <= intercept)[0]
    fc = float(freqs[above[0]]) if len(above) else float(freqs[-1])
    return fc, freqs, res


def smooth_track(t: np.ndarray, uv: np.ndarray, ok: np.ndarray, vis: np.ndarray, *, vis_min: float = 0.2,
                 max_gap_s: float = 0.05, fc: float | dict | None = None,
                 fc_range: tuple[float, float] = (4.0, 20.0), joints: list[int] | None = None) -> dict:
    """Resample + gap-fill + filter landmark pixel tracks.
    uv: (N,33,2). fc: fixed cutoff, per-joint dict, or None → residual analysis per joint & axis
    (clamped to fc_range; raw value also reported)."""
    x = uv.copy().astype(float)
    x[~ok] = np.nan
    x[vis < vis_min] = np.nan
    fs = 1 / np.median(np.diff(t))
    tu, xu = resample_uniform(t, x, fs)
    _, vu = resample_uniform(t, np.where(ok[:, None], vis, 0.0), fs)
    joints = joints if joints is not None else list(range(x.shape[1]))
    out = np.full_like(xu, np.nan)
    cutoffs = {}
    for j in joints:
        for ax in (0, 1):
            sig = fill_gaps(xu[:, j, ax], fs, max(max_gap_s, 2.0 / fs))
            if isinstance(fc, dict):
                f = fc.get(j, 10.0); raw = f
            elif fc is not None:
                f = raw = float(fc)
            else:
                raw, _, _ = residual_cutoff(sig, fs)
                f = float(np.clip(raw, *fc_range)) if np.isfinite(raw) else 10.0
            out[:, j, ax] = butter_zero_lag(sig, fs, f)
            cutoffs[(j, ax)] = (f, raw)
    return {"t": tu, "uv": out, "vis": vu, "fs": fs, "cutoffs": cutoffs}
