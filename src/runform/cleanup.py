"""Stage 3b: clean raw MediaPipe tracks before filtering.

Side-on running is MediaPipe's weak spot: the near and far legs cross every step and the model often swaps
their labels for a few frames, plus occasional gross misfits (an "ankle" at head height).
1. Outliers: per joint, frames far from a running median (> outlier_frac × body height) → NaN.
2. Left/right swaps: walk frames in order; swap the leg (and, separately, the arm) chains when the crossed
   assignment fits a constant-velocity prediction clearly better. Within each continuous run, the overall
   labelling is set by majority vote of MediaPipe's own raw labels (it's right most of the time).
3. Outliers again on the swap-corrected tracks.
Everything removed or swapped is counted and reported.
"""
from __future__ import annotations

import numpy as np

from .config import LM

LEG = [("l_knee", "r_knee"), ("l_ankle", "r_ankle"), ("l_heel", "r_heel"), ("l_toe", "r_toe")]
ARM = [("l_elbow", "r_elbow"), ("l_wrist", "r_wrist"), ("l_index", "r_index")]
EXTRA_ARM = [(17, 18), (21, 22)]  # pinky, thumb
EXTRA_LEG: list[tuple[int, int]] = []


def _pairs(chain, extra):
    return [(LM[a], LM[b]) for a, b in chain] + list(extra)


def reject_outliers(uv: np.ndarray, body_h: np.ndarray, fps: float, height_m: float = 1.75,
                    accel_max: float = 400.0, base_m: float = 0.04) -> tuple[np.ndarray, int]:
    """Spike detection: a point is an outlier when it is far from the line between its neighbours at ±k
    frames (k = 1, 2; the smaller deviation is used, so one bad neighbour doesn't condemn a good point).
    Allowed deviation = base_m + ½·accel_max·(k/fps)² — real feet/hands peak at a few hundred m/s² in
    sprinting — converted to px with the runner's height."""
    uv = uv.copy()
    px_per_m = body_h / height_m
    removed = 0
    n = len(uv)
    for j in range(uv.shape[1]):
        x = uv[:, j]
        ratio = np.full(n, np.inf)        # deviation / allowed, best (smallest) over k
        for k in (1, 2):
            if n <= 2 * k:
                continue
            mid = (x[:-2 * k] + x[2 * k:]) / 2
            d = np.linalg.norm(x[k:-k] - mid, axis=1)
            lim = (base_m + 0.5 * accel_max * (k / fps) ** 2) * px_per_m[k:-k]
            r = np.where(np.isfinite(d), d / lim, np.inf)
            ratio[k:-k] = np.minimum(ratio[k:-k], r)
        bad = np.isfinite(ratio) & (ratio > 1.0)
        removed += int(bad.sum())
        uv[bad, j] = np.nan
    return uv, removed


def fix_swaps(uv: np.ndarray, ok: np.ndarray, pairs: list[tuple[int, int]], margin: float = 0.7,
              max_gap: int = 3) -> tuple[np.ndarray, np.ndarray, int]:
    """Continuity-based label swap correction. Returns (uv, swapped_mask, n_segments_flipped)."""
    uv = uv.copy()
    li = [a for a, _ in pairs]
    ri = [b for _, b in pairs]
    swapped = np.zeros(len(uv), bool)
    hist: list[int] = []      # indices of accepted frames in the current run
    runs: list[list[int]] = []
    for i in range(len(uv)):
        L, R = uv[i, li], uv[i, ri]
        if not ok[i] or not (np.isfinite(L).any() and np.isfinite(R).any()):
            continue
        if hist and i - hist[-1] > max_gap:
            runs.append(hist); hist = []
        if hist:
            p1 = hist[-1]
            if len(hist) >= 2:
                p0 = hist[-2]
                step = (i - p1) / max(p1 - p0, 1)
                predL = uv[p1, li] + (uv[p1, li] - uv[p0, li]) * step
                predR = uv[p1, ri] + (uv[p1, ri] - uv[p0, ri]) * step
            else:
                predL, predR = uv[p1, li], uv[p1, ri]
            keep = np.nansum(np.linalg.norm(L - predL, axis=1)) + np.nansum(np.linalg.norm(R - predR, axis=1))
            cross = np.nansum(np.linalg.norm(L - predR, axis=1)) + np.nansum(np.linalg.norm(R - predL, axis=1))
            if cross < margin * keep:
                uv[i, li], uv[i, ri] = R.copy(), L.copy()
                swapped[i] = True
        hist.append(i)
    if hist:
        runs.append(hist)
    # anchor each run's global labelling to the majority of raw MediaPipe labels
    flipped = 0
    for run in runs:
        idx = np.array(run)
        if swapped[idx].mean() > 0.5:
            uv[idx[:, None], li], uv[idx[:, None], ri] = uv[idx[:, None], ri].copy(), uv[idx[:, None], li].copy()
            swapped[idx] = ~swapped[idx]
            flipped += 1
    return uv, swapped, flipped


def clean(d: dict, body_h_px: float | None = None, height_m: float = 1.75) -> tuple[dict, dict]:
    """d: pose.load() dict. Returns (cleaned copy, report)."""
    uv = d["uv"].copy()
    ok = d["ok"].copy()
    uv[~ok] = np.nan
    fps = d["fps"]
    if body_h_px is None:
        ys = uv[:, :, 1]
        body_h_px = float(np.nanmedian(np.nanmax(ys, 1) - np.nanmin(ys, 1)) * 1.12)
    bh = np.full(len(uv), body_h_px)
    uv, out1 = reject_outliers(uv, bh, fps, height_m)
    uv, sw_leg, fl_leg = fix_swaps(uv, ok, _pairs(LEG, EXTRA_LEG))
    uv, sw_arm, fl_arm = fix_swaps(uv, ok, _pairs(ARM, EXTRA_ARM))
    uv, out2 = reject_outliers(uv, bh, fps, height_m)
    # swap the per-landmark visibility/world along with positions
    vis, world = d["vis"].copy(), d["world"].copy()
    for sw, pairs in ((sw_leg, _pairs(LEG, EXTRA_LEG)), (sw_arm, _pairs(ARM, EXTRA_ARM))):
        li = [a for a, _ in pairs]; ri = [b for _, b in pairs]
        vis[np.ix_(sw, li)], vis[np.ix_(sw, ri)] = vis[np.ix_(sw, ri)].copy(), vis[np.ix_(sw, li)].copy()
        world[np.ix_(sw, li)], world[np.ix_(sw, ri)] = world[np.ix_(sw, ri)].copy(), world[np.ix_(sw, li)].copy()
    out = dict(d)
    out.update(uv=uv, vis=vis, world=world)
    rep = {"body_h_px": body_h_px, "outliers_removed": out1 + out2, "leg_swap_frames": int(sw_leg.sum()),
           "arm_swap_frames": int(sw_arm.sum()), "frames": int(ok.sum()),
           "leg_swap_rate": float(sw_leg[ok].mean()) if ok.any() else 0.0}
    return out, rep
