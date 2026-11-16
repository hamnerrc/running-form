"""Stage 3: pose (README §5.3). MediaPipe Pose Landmarker Heavy.

Two passes per clip:
  1. locate — IMAGE mode on every k-th frame, up to 3 people; link detections into tracks and pick the
     runner (the track with most leg motion + travel; bystanders and coaches stand still).
  2. track  — VIDEO mode on every frame, on a square crop that follows the runner (interpolated from
     pass 1) and is upscaled, because at ~17 m the runner is only ~150–300 px tall.
Raw landmarks (full-frame pixels) + visibility + MediaPipe world landmarks are saved to
results/<date>/work/pose/<athlete>_<clip>.npz.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision

from .session import REPO
from .video import iter_frames, real_frame_times

MODEL = REPO / "models" / "pose_landmarker_heavy.task"
CROP_PX = 512           # crops are resized to this (upscaled if smaller)
CROP_SCALE = 1.6        # crop side = CROP_SCALE × body height
LOCATE_HZ = 30.0        # pass-1 sampling rate (real time)


def _landmarker(mode: str, num_poses: int):
    if not MODEL.exists():
        raise FileNotFoundError(f"{MODEL} missing — see README §7")
    rm = vision.RunningMode.VIDEO if mode == "video" else vision.RunningMode.IMAGE
    opts = vision.PoseLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path=str(MODEL)), running_mode=rm, num_poses=num_poses,
        min_pose_detection_confidence=0.4, min_pose_presence_confidence=0.4, min_tracking_confidence=0.4)
    return vision.PoseLandmarker.create_from_options(opts)


def _to_mp(img_bgr: np.ndarray) -> mp.Image:
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))


def _pose_arrays(res, w: int, h: int, ox: float = 0, oy: float = 0, s: float = 1.0):
    """Landmarks of every detected pose → list of (uv[33,2] full-frame px, vis[33], world[33,3])."""
    out = []
    for i, pl in enumerate(res.pose_landmarks):
        uv = np.array([[p.x * w, p.y * h] for p in pl]) / s + [ox, oy]
        vis = np.array([p.visibility for p in pl])
        wl = res.pose_world_landmarks[i] if res.pose_world_landmarks else []
        world = np.array([[p.x, p.y, p.z] for p in wl]) if wl else np.full((33, 3), np.nan)
        out.append((uv, vis, world))
    return out


def _body_box(uv: np.ndarray, vis: np.ndarray) -> tuple[float, float, float]:
    """(center_u, center_v, body_height_px) from confident landmarks."""
    good = vis > 0.3
    pts = uv[good] if good.sum() >= 8 else uv
    top, bot = pts[:, 1].min(), pts[:, 1].max()
    hgt = (bot - top) * 1.12  # landmarks stop at the eyes/heels
    return float(np.median(pts[:, 0])), float((top + bot) / 2), float(hgt)


@dataclass
class Located:
    frames: np.ndarray       # sampled frame indices where the runner was found
    cu: np.ndarray
    cv: np.ndarray
    hgt: np.ndarray
    score: float


def locate(path: Path, fps: float, roi: tuple[int, int, int, int] | None = None) -> Located:
    step = max(1, int(round(fps / LOCATE_HZ)))
    tracks: list[dict] = []
    with _landmarker("image", 3) as lmk:
        for i, _, img in iter_frames(path, step=step):
            H, W = img.shape[:2]
            ox, oy = 0, 0
            if roi:
                x0, y0, x1, y1 = roi
                img, ox, oy = img[y0:y1, x0:x1], x0, y0
            dets = _detect_tiled(lmk, img, ox, oy)
            for uv, vis, _ in dets:
                cu, cv_, hg = _body_box(uv, vis)
                hip = uv[[23, 24]].mean(0)
                ank = uv[[27, 28]] - hip
                # link to the nearest live track
                best, bd = None, 1e9
                for t in tracks:
                    if i - t["f"][-1] > fps * 0.5:          # allow ~0.5 s occlusion gaps
                        continue
                    ref_h = float(np.median(t["h"][-15:]))  # robust to partial-body detections
                    d = np.hypot(cu - t["u"][-1], cv_ - t["v"][-1])
                    if d < 0.6 * max(hg, ref_h) and d < bd:
                        best, bd = t, d
                if best is None:
                    best = {"f": [], "u": [], "v": [], "h": [], "ank": []}
                    tracks.append(best)
                best["f"].append(i); best["u"].append(cu); best["v"].append(cv_)
                best["h"].append(hg); best["ank"].append(ank.ravel() / max(hg, 1))
    if not tracks:
        raise RuntimeError(f"No person found in {path.name}. Try --roi x0,y0,x1,y1 around the running line.")
    for t in tracks:
        ank = np.array(t["ank"])
        leg_motion = float(np.nanstd(ank, axis=0).mean()) if len(ank) > 2 else 0.0
        travel = (max(t["u"]) - min(t["u"])) / max(np.median(t["h"]), 1)
        t["score"] = len(t["f"]) * (leg_motion + 0.05 * travel)
    best = max(tracks, key=lambda t: t["score"])
    best = _absorb_fragments(best, tracks)
    return Located(np.array(best["f"]), np.array(best["u"]), np.array(best["v"]), np.array(best["h"]), best["score"])


def _detect_tiled(lmk, img: np.ndarray, ox: float, oy: float) -> list:
    """IMAGE-mode detection on overlapping square tiles (side = image height), so a runner who is only
    ~200 px tall in a 1920-px-wide frame is still big enough for the detector. Duplicates (same person
    in two tiles) are merged by keeping the more confident one."""
    h, w = img.shape[:2]
    side = min(h, w)
    xs = [0] if w <= side else list(np.linspace(0, w - side, int(np.ceil((w - side) / (0.55 * side))) + 1).astype(int))
    dets = []
    for x0 in xs:
        tile = img[:, x0:x0 + side]
        s = 1.0
        if side < 1000:  # small tiles: upscale so a small runner still gets detected
            s = 1000 / side
            tile = cv2.resize(tile, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        res = lmk.detect(_to_mp(tile))
        dets += _pose_arrays(res, tile.shape[1], tile.shape[0], ox + x0, oy, s)
    keep = []
    for d in sorted(dets, key=lambda d: -float(np.mean(d[1]))):
        cu, cv_, hg = _body_box(d[0], d[1])
        if all(np.hypot(cu - k[3], cv_ - k[4]) > 0.3 * max(hg, k[5]) for k in keep):
            keep.append((*d, cu, cv_, hg))
    return [k[:3] for k in keep]


def _absorb_fragments(best: dict, tracks: list[dict]) -> dict:
    """Merge other tracks that are the same runner split by an occlusion: no time overlap with the
    chosen track, and they start/end near where it is at that time."""
    merged = {k: list(v) for k, v in best.items() if isinstance(v, list)}
    ref_h = float(np.median(best["h"]))
    for t in sorted(tracks, key=lambda t: t["f"][0]):
        if t is best or len(t["f"]) < 2:
            continue
        mf = np.array(merged["f"])
        if np.any((mf >= t["f"][0]) & (mf <= t["f"][-1])):
            continue
        # compare positions at the closest-in-time pair (fragment endpoint, merged sample)
        best_pair = min(((abs(mf[j] - t["f"][k]), j, k) for k in (0, -1) for j in range(len(mf))))
        _, j, k = best_pair
        d = np.hypot(t["u"][k] - merged["u"][j], t["v"][k] - merged["v"][j])
        if d < 0.6 * ref_h:
            for key in ("f", "u", "v", "h", "ank"):
                merged[key] += t[key]
            order = np.argsort(merged["f"])
            for key in ("f", "u", "v", "h", "ank"):
                merged[key] = [merged[key][o] for o in order]
    merged["score"] = best["score"]
    return merged


def _running_median(x: np.ndarray, k: int) -> np.ndarray:
    k = min(k, len(x)) | 1
    pad = np.pad(x, (k // 2, k // 2), mode="edge")
    return np.array([np.median(pad[i:i + k]) for i in range(len(x))])


def _smooth(x: np.ndarray, k: int) -> np.ndarray:
    if len(x) < 3 or k < 2:
        return x
    k = min(k, len(x))
    pad = np.pad(x, (k // 2, k - 1 - k // 2), mode="edge")
    return np.convolve(pad, np.ones(k) / k, mode="valid")


def track(path: Path, out_npz: Path, roi: tuple[int, int, int, int] | None = None, margin_s: float = 0.15,
          frame_range: tuple[int, int] | None = None, slomo_capture_fps: float | None = None) -> dict:
    t_all = real_frame_times(path, slomo_capture_fps)
    fps = 1 / np.median(np.diff(t_all))
    loc = locate(path, fps, roi)
    n = len(t_all)
    pad = int(margin_s * fps)
    f0, f1 = max(0, loc.frames[0] - pad), min(n, loc.frames[-1] + pad + 1)
    if frame_range:
        f0, f1 = max(f0, frame_range[0]), min(f1, frame_range[1])
    idx = np.arange(f0, f1)
    k = max(1, len(loc.frames) // 10)
    cu = np.interp(idx, loc.frames, _smooth(loc.cu, k))
    cv_ = np.interp(idx, loc.frames, _smooth(loc.cv, k))
    hg = np.interp(idx, loc.frames, _running_median(loc.hgt, max(5, int(LOCATE_HZ))))

    N = len(idx)
    uv = np.full((N, 33, 2), np.nan)
    vis = np.zeros((N, 33))
    world = np.full((N, 33, 3), np.nan)
    crops = np.zeros((N, 4))
    ok = np.zeros(N, bool)
    ts = t_all[idx]
    last_ms = -1
    with _landmarker("video", 2) as lmk:
        for j, (i, _, img) in enumerate(iter_frames(path, start=f0, stop=f1)):
            H, W = img.shape[:2]
            side = CROP_SCALE * hg[j]
            x0, y0 = int(round(cu[j] - side / 2)), int(round(cv_[j] - side / 2))
            sz = int(round(side))
            # pad with black when the crop leaves the frame
            crop = np.zeros((sz, sz, 3), np.uint8)
            sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(W, x0 + sz), min(H, y0 + sz)
            if sx1 > sx0 and sy1 > sy0:
                crop[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
            s = CROP_PX / sz
            crop = cv2.resize(crop, (CROP_PX, CROP_PX), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
            ms = int(round(ts[j] * 1000))
            if ms <= last_ms:   # VIDEO mode needs strictly increasing timestamps (240 fps ≈ 4.17 ms)
                ms = last_ms + 1
            last_ms = ms
            res = lmk.detect_for_video(_to_mp(crop), ms)
            dets = _pose_arrays(res, CROP_PX, CROP_PX, x0, y0, s)
            if dets:
                # the pose nearest the expected runner center
                d = [np.hypot(*(_body_box(u, v)[:2] - np.array([cu[j], cv_[j]]))) for u, v, _ in dets]
                u_, v_, w_ = dets[int(np.argmin(d))]
                uv[j], vis[j], world[j], ok[j] = u_, v_, w_, True
            crops[j] = [x0, y0, sz, sz]
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_npz, frame=idx, t=ts, uv=uv, vis=vis, world=world, crop=crops, ok=ok,
                        fps=fps, width=W, height=H)
    info = {"clip": str(path), "fps": float(fps), "frames": [int(f0), int(f1)], "n": int(N),
            "detected": int(ok.sum()), "detect_rate": float(ok.mean()) if N else 0.0,
            "runner_height_px_median": float(np.median(hg)), "locate_score": loc.score}
    out_npz.with_suffix(".json").write_text(json.dumps(info, indent=2))
    return info


def load(npz: Path) -> dict:
    d = dict(np.load(npz))
    for k in ("fps", "width", "height"):
        d[k] = d[k].item()
    return d
