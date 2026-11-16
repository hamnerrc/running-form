"""Stage 4: landmark tape (README §5.4).

Colours are set in session.yaml:
    athletes:
      A:
        tape_colors: {ankle: green, knee: pink, hip: yellow, shoulder: blue}   # near side; names from PALETTE
Each marker is searched for near the matching MediaPipe landmark (near side), by HSV threshold +
connected components. Output: results/<date>/work/tape/<athlete>_<clip>.npz with the tape pixel track per
joint, and a per-joint error table vs MediaPipe (px and cm) in qa/tape_vs_pose.md.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .config import LM
from .video import iter_frames

# OpenCV HSV: H 0–179. Ranges are deliberately generous; tune per session lighting if needed.
PALETTE = {
    "green":  [((40, 80, 70), (85, 255, 255))],
    "pink":   [((140, 60, 120), (172, 255, 255))],
    "yellow": [((20, 100, 120), (35, 255, 255))],
    "blue":   [((95, 120, 60), (125, 255, 255))],
    "orange": [((5, 140, 140), (19, 255, 255))],
    "red":    [((0, 140, 90), (5, 255, 255)), ((172, 140, 90), (179, 255, 255))],
}


def color_mask(hsv: np.ndarray, color: str) -> np.ndarray:
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in PALETTE[color]:
        m |= cv2.inRange(hsv, np.array(lo), np.array(hi))
    return m


def find_marker(hsv: np.ndarray, color: str, near_uv: np.ndarray, radius: float, min_area: int = 4) -> np.ndarray:
    """Centroid (u, v) of the colour blob nearest near_uv within radius px, or NaNs."""
    if not np.isfinite(near_uv).all():
        return np.full(2, np.nan)
    H, W = hsv.shape[:2]
    r = int(radius)
    u0, v0 = int(near_uv[0]), int(near_uv[1])
    x0, y0, x1, y1 = max(0, u0 - r), max(0, v0 - r), min(W, u0 + r), min(H, v0 + r)
    if x1 <= x0 or y1 <= y0:
        return np.full(2, np.nan)
    m = color_mask(hsv[y0:y1, x0:x1], color)
    n, _, stats, cent = cv2.connectedComponentsWithStats(m)
    best, bd = None, 1e9
    for k in range(1, n):
        if stats[k, cv2.CC_STAT_AREA] < min_area:
            continue
        c = cent[k] + [x0, y0]
        d = np.hypot(*(c - near_uv))
        if d < bd and d <= radius:
            best, bd = c, d
    return np.asarray(best, float) if best is not None else np.full(2, np.nan)


def track(clip: Path, pose_d: dict, colors: dict, near: str, out_npz: Path) -> dict:
    """pose_d: pose.load() dict (raw or cleaned). colors: joint → palette name."""
    fidx = {int(f): j for j, f in enumerate(pose_d["frame"])}
    N = len(pose_d["frame"])
    tracks = {f"{near}_{jn}": np.full((N, 2), np.nan) for jn in colors}
    f0, f1 = int(pose_d["frame"][0]), int(pose_d["frame"][-1]) + 1
    for i, _, img in iter_frames(clip, start=f0, stop=f1):
        j = fidx.get(i)
        if j is None or not pose_d["ok"][j]:
            continue
        uv = pose_d["uv"][j]
        ys = uv[np.isfinite(uv).all(1), 1]
        body_h = (ys.max() - ys.min()) * 1.12 if len(ys) else 200
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        for jn, col in colors.items():
            tracks[f"{near}_{jn}"][j] = find_marker(hsv, col, uv[LM[f"{near.lower()}_{jn}"]], 0.08 * body_h)
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_npz, frame=pose_d["frame"], **tracks)
    return tracks


def error_table(pose_d: dict, tracks: dict, m_per_px: float) -> list[dict]:
    rows = []
    for key, tuv in tracks.items():
        side, jn = key.split("_", 1)
        mp_uv = pose_d["uv"][:, LM[f"{side.lower()}_{jn}"]]
        both = np.isfinite(tuv).all(1) & np.isfinite(mp_uv).all(1)
        e = np.linalg.norm(tuv[both] - mp_uv[both], axis=1)
        rows.append({"joint": key, "tape_detect_rate": float(np.isfinite(tuv).all(1).mean()), "n": int(both.sum()),
                     "err_px_median": float(np.median(e)) if len(e) else np.nan,
                     "err_px_p90": float(np.percentile(e, 90)) if len(e) else np.nan,
                     "err_cm_median": float(np.median(e) * m_per_px * 100) if len(e) else np.nan,
                     "err_cm_p90": float(np.percentile(e, 90) * m_per_px * 100) if len(e) else np.nan})
    return rows
