"""Pixel tracks → sagittal-plane coordinates (metres), joint angles, centre of mass, segment check.

Sagittal frame per rep: X forward (in the running direction), Y up, origin on the ground.
- With a homography: X = world x of the vertical through the point (calib.x_at_u), Y = height above the
  running line's image (ground_v) × local scale. Points on the ground map exactly; body points carry the
  small error of assuming world-vertical ≈ image-vertical and a single depth (the running line).
- Without one (demo / treadmill): a constant m/px scale and a ground line fitted to the feet.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import LM, SEGMENT_TOLERANCE, WINTER_SEGMENTS, lm


@dataclass
class Sagittal:
    dir_sign: int
    m_per_px: float
    calib: object | None = None               # calib.Calib
    ground: tuple[float, float] | None = None  # (a, b): v_ground = a + b·u, when no calib

    def ground_v(self, u: np.ndarray) -> np.ndarray:
        if self.calib is not None:
            return self.calib.ground_v(u)
        a, b = self.ground
        return a + b * np.asarray(u, float)

    def xy(self, uv: np.ndarray) -> np.ndarray:
        """uv (..., 2) px → (..., 2) [X forward m, Y up m]."""
        u, v = uv[..., 0], uv[..., 1]
        if self.calib is not None:
            fin = np.isfinite(u)
            X = np.full(u.shape, np.nan)
            X[fin] = self.calib.x_at_u(u[fin])
        else:
            X = u * self.m_per_px
        Y = (self.ground_v(u) - v) * self.m_per_px
        return np.stack([self.dir_sign * X, Y], axis=-1)


def fit_ground_line(uv: np.ndarray, q: float = 92.0, bins: int = 12) -> tuple[float, float]:
    """Ground line v = a + b·u from the lowest foot points (heel/toe, both feet), robust per u-bin."""
    feet = uv[:, [LM["l_heel"], LM["r_heel"], LM["l_toe"], LM["r_toe"]], :].reshape(-1, 2)
    feet = feet[np.isfinite(feet).all(1)]
    if len(feet) < 10:
        raise ValueError("Not enough foot points to fit a ground line")
    edges = np.linspace(feet[:, 0].min(), feet[:, 0].max() + 1e-6, bins + 1)
    pu, pv = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        s = feet[(feet[:, 0] >= lo) & (feet[:, 0] < hi)]
        if len(s) >= 5:
            pu.append(s[:, 0].mean()); pv.append(np.percentile(s[:, 1], q))
    if len(pu) < 2:
        return float(np.percentile(feet[:, 1], q)), 0.0
    b, a = np.polyfit(pu, pv, 1)
    return float(a), float(b)


def seg_angle_from_down(p_prox: np.ndarray, p_dist: np.ndarray) -> np.ndarray:
    """Angle (deg) of prox→dist vs straight down; + when the distal end is forward. Thigh, shin."""
    d = p_dist - p_prox
    return np.degrees(np.arctan2(d[..., 0], -d[..., 1]))


def seg_angle_from_up(p_low: np.ndarray, p_high: np.ndarray) -> np.ndarray:
    """Angle (deg) of low→high vs straight up; + when leaning forward. Trunk."""
    d = p_high - p_low
    return np.degrees(np.arctan2(d[..., 0], d[..., 1]))


def included_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Angle ABC (deg)."""
    v1, v2 = a - b, c - b
    cos = np.sum(v1 * v2, -1) / (np.linalg.norm(v1, axis=-1) * np.linalg.norm(v2, axis=-1))
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def joint_series(P: np.ndarray) -> dict:
    """P: (N,33,2) sagittal metres. Returns per-frame angle/position series keyed by name and side."""
    out = {}
    sh = (P[:, LM["l_shoulder"]] + P[:, LM["r_shoulder"]]) / 2
    hip = (P[:, LM["l_hip"]] + P[:, LM["r_hip"]]) / 2
    out["hip_mid"] = hip
    out["shoulder_mid"] = sh
    out["trunk_lean"] = seg_angle_from_up(hip, sh)
    for s in ("L", "R"):
        H, K, A = P[:, lm(s, "hip")], P[:, lm(s, "knee")], P[:, lm(s, "ankle")]
        heel, toe = P[:, lm(s, "heel")], P[:, lm(s, "toe")]
        out[f"thigh_{s}"] = seg_angle_from_down(H, K)
        out[f"shin_{s}"] = seg_angle_from_down(K, A)
        out[f"knee_flex_{s}"] = 180.0 - included_angle(H, K, A)
        out[f"hip_flex_{s}"] = out[f"thigh_{s}"] + out["trunk_lean"]   # thigh relative to trunk
        out[f"ankle_{s}"], out[f"heel_{s}"], out[f"toe_{s}"] = A, heel, toe
        out[f"knee_{s}"] = K
        out[f"thigh_len_{s}"] = np.linalg.norm(K - H, axis=-1)
        out[f"shank_len_{s}"] = np.linalg.norm(A - K, axis=-1)
        # foot angle: heel→toe line vs the ground; + = toes up (heel lands first), − = toes down (forefoot first)
        d = toe - heel
        out[f"foot_angle_{s}"] = np.degrees(np.arctan2(d[:, 1], np.abs(d[:, 0])))
        # arm: shoulder angle = upper arm relative to the trunk (0 = hanging along the trunk, + = elbow in front
        # of the trunk line, − = behind it); elbow angle = included angle (180 = straight arm, ~90 = right angle)
        S, E, W = P[:, lm(s, "shoulder")], P[:, lm(s, "elbow")], P[:, lm(s, "wrist")]
        out[f"shoulder_{s}"] = _signed_from_down(E - S) - _signed_from_down(hip - sh)
        out[f"elbow_{s}"] = included_angle(S, E, W)
        out[f"wrist_{s}"], out[f"shoulder_pt_{s}"], out[f"elbow_pt_{s}"] = W, S, E
        out[f"upper_arm_len_{s}"] = np.linalg.norm(E - S, axis=-1)
        out[f"forearm_len_{s}"] = np.linalg.norm(W - E, axis=-1)
    return out


def _signed_from_down(v: np.ndarray) -> np.ndarray:
    """Angle of vector v from straight down, degrees, + = pointing forward (X+)."""
    return np.degrees(np.arctan2(v[..., 0], -v[..., 1]))


def center_of_mass(P: np.ndarray, min_mass: float = 0.9) -> np.ndarray:
    """2-D segmental COM (Winter 2009 Table 4.1). P: (N,33,2). Returns (N,2)."""
    def mid(a, b):
        return (P[:, LM[a]] + P[:, LM[b]]) / 2

    segs = []  # (mass fraction, proximal, distal, com fraction)
    m, c = WINTER_SEGMENTS["head_neck"]; segs.append((m, mid("l_shoulder", "r_shoulder"), mid("l_ear", "r_ear"), c))
    m, c = WINTER_SEGMENTS["trunk"]; segs.append((m, mid("l_shoulder", "r_shoulder"), mid("l_hip", "r_hip"), c))
    for s in ("l", "r"):
        for name, a, b in (("upper_arm", "shoulder", "elbow"), ("forearm", "elbow", "wrist"), ("hand", "wrist", "index"),
                           ("thigh", "hip", "knee"), ("shank", "knee", "ankle"), ("foot", "heel", "toe")):
            m, c = WINTER_SEGMENTS[name]
            segs.append((m, P[:, LM[f"{s}_{a}"]], P[:, LM[f"{s}_{b}"]], c))
    # Segments missing in a frame (an occluded far-side hand, say) are dropped and the mass renormalised,
    # as long as ≥ min_mass of the body is present; otherwise the frame is NaN.
    N = P.shape[0]
    acc = np.zeros((N, 2)); mass = np.zeros(N)
    for m, p, d, c in segs:
        pos = p + c * (d - p)
        ok = np.isfinite(pos).all(1)
        acc[ok] += m * pos[ok]; mass[ok] += m
    total = sum(m for m, *_ in segs)
    com = np.full((N, 2), np.nan)
    good = mass >= min_mass * total
    com[good] = acc[good] / mass[good, None]
    return com


def near_side(vis: np.ndarray, world: np.ndarray, dir_sign: int) -> dict:
    """Which body side faces the camera. Expected from setup (camera on the runner's right when running →),
    detected from MediaPipe depth (world z: smaller = closer to camera) and visibility."""
    expected = "R" if dir_sign > 0 else "L"
    li = [LM["l_hip"], LM["l_knee"], LM["l_ankle"]]
    ri = [LM["r_hip"], LM["r_knee"], LM["r_ankle"]]
    zl, zr = np.nanmean(world[:, li, 2]), np.nanmean(world[:, ri, 2])
    vl, vr = np.nanmean(vis[:, li]), np.nanmean(vis[:, ri])
    detected = "L" if zl < zr else "R"
    return {"expected": expected, "detected": detected, "z_L": float(zl), "z_R": float(zr),
            "vis_L": float(vl), "vis_R": float(vr), "agree": expected == detected}


def segment_check(js: dict, body, sides=("L", "R")) -> dict:
    """Tracked thigh/shank length vs reference — fraction of frames off by > 5%. The reference is the athlete's
    MediaPipe standing segment length when known (body.mp_ref_m), else the measured / Winter value."""
    out = {}
    for s in sides:
        mp = getattr(body, "mp_ref_m", None) or {}
        for seg, ref in (("thigh", mp.get("thigh", body.thigh_m[s])), ("shank", mp.get("shank", body.shank_m[s]))):
            L = js[f"{seg}_len_{s}"]
            fin = np.isfinite(L)
            err = (L[fin] - ref) / ref
            out[f"{seg}_{s}"] = {
                "reference_m": ref, "tracked_median_m": float(np.median(L[fin])) if fin.any() else float("nan"),
                "median_err_pct": float(np.median(err) * 100) if fin.any() else float("nan"),
                "frac_frames_over_5pct": float(np.mean(np.abs(err) > SEGMENT_TOLERANCE)) if fin.any() else float("nan"),
                "flag_mask": np.r_[np.abs((L - ref) / ref) > SEGMENT_TOLERANCE],
            }
    return out
