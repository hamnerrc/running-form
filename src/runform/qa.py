"""Visual QA (README §5.7, §5.12): event contact sheets, skeleton overlays, annotated stills."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .video import iter_frames

BONES = [(11, 12), (11, 23), (12, 24), (23, 24), (11, 13), (13, 15), (12, 14), (14, 16),
         (23, 25), (25, 27), (27, 29), (29, 31), (27, 31), (24, 26), (26, 28), (28, 30), (30, 32), (28, 32), (7, 8)]
LEFT = {11, 13, 15, 23, 25, 27, 29, 31, 7}
COL_L, COL_R, COL_C = (255, 160, 0), (0, 0, 255), (0, 255, 0)


def grab(path: Path, frames: set[int]) -> dict[int, np.ndarray]:
    """Decode once, keep only the requested frame indices."""
    out = {}
    if not frames:
        return out
    lo, hi = min(frames), max(frames)
    for i, _, img in iter_frames(path, start=lo, stop=hi + 1):
        if i in frames:
            out[i] = img
    return out


def draw_skeleton(img: np.ndarray, uv: np.ndarray, thick: int = 2) -> np.ndarray:
    vis = img.copy()
    for a, b in BONES:
        pa, pb = uv[a], uv[b]
        if np.isfinite(pa).all() and np.isfinite(pb).all():
            col = COL_L if (a in LEFT and b in LEFT) else COL_R if (a not in LEFT and b not in LEFT) else COL_C
            cv2.line(vis, tuple(int(x) for x in pa), tuple(int(x) for x in pb), col, thick, cv2.LINE_AA)
    for j in range(uv.shape[0]):
        if j > 10 and np.isfinite(uv[j]).all():
            cv2.circle(vis, tuple(int(x) for x in uv[j]), thick + 1, COL_L if j in LEFT else COL_R, -1)
    return vis


def crop_around(img: np.ndarray, cu: float, cv_: float, side: float, out: int = 360) -> np.ndarray:
    H, W = img.shape[:2]
    s = int(side)
    x0, y0 = int(cu - s / 2), int(cv_ - s / 2)
    canvas = np.zeros((s, s, 3), np.uint8)
    sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(W, x0 + s), min(H, y0 + s)
    if sx1 > sx0 and sy1 > sy0:
        canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
    return cv2.resize(canvas, (out, out))


def label(img: np.ndarray, text: str, color=(255, 255, 255)) -> np.ndarray:
    cv2.putText(img, text, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(img, text, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)
    return img


def event_contact_sheet(clip: Path, frames_uv: dict[int, np.ndarray], contacts: list[dict], out_path: Path,
                        half: int = 3, tile: int = 220, max_events: int = 12) -> None:
    """One row per event (TD or TO), ±half frames, cropped on the contacting foot, skeleton overlaid.
    The centre tile is outlined: that's the detected event frame."""
    evs = []
    for c in contacts[:max_events]:
        evs.append((c["foot"], "TD", c["td_frame"]))
        evs.append((c["foot"], "TO", c["to_frame"]))
    need = {f + k for _, _, f in evs for k in range(-half, half + 1)}
    imgs = grab(clip, need)
    rows = []
    for foot, kind, f in evs:
        uvf = frames_uv.get(f)
        if uvf is None:
            continue
        j = 27 if foot == "L" else 28
        hip = np.nanmean(uvf[[23, 24]], 0)
        side = 1.6 * max(np.linalg.norm(uvf[j] - hip), 20) if np.isfinite(uvf[j]).all() else 200
        cu, cv_ = (uvf[j] if np.isfinite(uvf[j]).all() else hip)
        tiles = []
        for k in range(-half, half + 1):
            im = imgs.get(f + k)
            if im is None:
                tiles.append(np.zeros((tile, tile, 3), np.uint8)); continue
            u = frames_uv.get(f + k)
            if u is not None:
                im = draw_skeleton(im, u, 1)
            t = crop_around(im, cu, cv_, side, tile)
            label(t, f"{foot} {kind} {k:+d} (#{f + k})", (0, 255, 255) if k == 0 else (255, 255, 255))
            if k == 0:
                cv2.rectangle(t, (0, 0), (tile - 1, tile - 1), (0, 255, 255), 3)
            tiles.append(t)
        rows.append(np.hstack(tiles))
    if rows:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), np.vstack(rows))


def overlay_strip(clip: Path, frames_uv: dict[int, np.ndarray], frames: list[int], out_path: Path,
                  tile: int = 300, crop: bool = True) -> None:
    imgs = grab(clip, set(frames))
    tiles = []
    for f in frames:
        im = imgs.get(f)
        if im is None:
            continue
        u = frames_uv.get(f)
        if u is not None:
            im = draw_skeleton(im, u)
            if crop and np.isfinite(u).any():
                pts = u[np.isfinite(u).all(1)]
                cu, cv_ = pts.mean(0)
                side = 1.4 * (pts[:, 1].max() - pts[:, 1].min())
                im = crop_around(im, cu, cv_, side, tile)
        if not crop:
            im = cv2.resize(im, (tile, int(tile * im.shape[0] / im.shape[1])))
        tiles.append(label(im, f"#{f}"))
    if tiles:
        h = min(t.shape[0] for t in tiles)
        per_row = 6
        rows = [np.hstack([t[:h] for t in tiles[i:i + per_row]]) for i in range(0, len(tiles), per_row)]
        w = max(r.shape[1] for r in rows)
        rows = [np.pad(r, ((0, 0), (0, w - r.shape[1]), (0, 0))) for r in rows]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), np.vstack(rows))


def annotated_still(clip: Path, frame: int, uv: np.ndarray, text_lines: list[str], out_path: Path) -> None:
    img = grab(clip, {frame}).get(frame)
    if img is None:
        return
    img = draw_skeleton(img, uv, 2)
    pts = uv[np.isfinite(uv).all(1)]
    cu, cv_ = pts.mean(0)
    side = 1.5 * (pts[:, 1].max() - pts[:, 1].min())
    im = crop_around(img, cu, cv_, side, 600)
    for k, line in enumerate(text_lines):
        y = 26 + 24 * k
        cv2.putText(im, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(im, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1, cv2.LINE_AA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), im)
