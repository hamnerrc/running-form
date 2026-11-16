"""Narrated analysis videos: slow-motion clips with the pose overlay, freezes and frame-stepping, timed to
Kokoro TTS narration. Shot lists live in results/<date>/video/<name>_shots.yaml.

    .venv/bin/python -m runform.explainer results/2026-11-15/video/RC_shots.yaml

Each shot = one narration line + a list of segments (play at a slowdown, or freeze on a frame). The narration
is synthesised first; the segments are then stretched (freezes first) so the picture lasts as long as the voice.
Slowdown is relative to real life: the clips are 240 fps captures rendered at 30 fps, so plain playback = 8×."""
from __future__ import annotations

import json
import math
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf
import yaml
from PIL import Image, ImageDraw, ImageFont

from . import analyze as an
from . import kinematics
from .session import body_from_measurements, load_session

ROOT = Path(__file__).resolve().parents[2]
OUT_W, OUT_H, OUT_FPS = 1920, 1080, 30
CAPTURE_FPS = 240
BASE_SLOW = CAPTURE_FPS / OUT_FPS          # 8: one source frame per output frame
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

BONES = [(11, 12), (11, 23), (12, 24), (23, 24), (11, 13), (13, 15), (12, 14), (14, 16),
         (23, 25), (25, 27), (27, 29), (29, 31), (27, 31), (24, 26), (26, 28), (28, 30), (30, 32), (28, 32)]
LEFT = {11, 13, 15, 23, 25, 27, 29, 31}
LEG = {"L": {23, 25, 27, 29, 31}, "R": {24, 26, 28, 30, 32}}
COL = {"L": (255, 170, 40), "R": (60, 60, 255), "C": (235, 235, 235), "X": (150, 150, 150)}   # BGR
YELLOW = (0, 220, 255)
LM = {"hip_L": 23, "hip_R": 24, "knee_L": 25, "knee_R": 26, "ankle_L": 27, "ankle_R": 28,
      "heel_L": 29, "heel_R": 30, "toe_L": 31, "toe_R": 32, "sh_L": 11, "sh_R": 12}


# ---------------------------------------------------------------------------------------------- data

def _smooth1d(x, k):
    if k < 2:
        return x
    pad = np.pad(x, (k // 2, k - 1 - k // 2), mode="edge")
    return np.convolve(pad, np.ones(k) / k, mode="valid")


class Track:
    """Pose overlay data for one clip, indexed by source frame."""

    def __init__(self, uv, frames, mask=None, knee=None, extra=None):
        self.f0 = int(frames[0])
        self.uv = uv
        self.n = len(frames)
        self.mask = mask or {"L": np.zeros(self.n, bool), "R": np.zeros(self.n, bool)}
        self.knee = knee or {}
        self.extra = extra or {}
        self.com = kinematics.center_of_mass(uv)
        hip = (uv[:, 23] + uv[:, 24]) / 2
        hu = pd_interp(hip[:, 0]); hv = pd_interp(hip[:, 1])
        self.cam_u = _smooth1d(hu, 31)
        self.cam_v = float(np.nanmedian(hv))

    def i(self, f):
        j = int(f) - self.f0
        return j if 0 <= j < self.n else None

    def p(self, f, name):
        j = self.i(f)
        return None if j is None else self.uv[j, LM[name]]

    def hip(self, f):
        j = self.i(f)
        return None if j is None else (self.uv[j, 23] + self.uv[j, 24]) / 2

    def foot_low(self, f, s):
        j = self.i(f)
        if j is None:
            return None
        h, t = self.uv[j, LM[f"heel_{s}"]], self.uv[j, LM[f"toe_{s}"]]
        return h if h[1] > t[1] else t

    def masked(self, f, s):
        j = self.i(f)
        return True if j is None else bool(self.mask[s][j])


def pd_interp(x):
    x = np.asarray(x, float).copy()
    ok = np.isfinite(x)
    if ok.sum() == 0:
        return np.zeros_like(x)
    x[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), x[ok])
    return x


def load_run_track(date: str, athlete: str, rep: str) -> Track:
    d = np.load(ROOT / f"results/{date}/work/analysis/{athlete}_{rep}.npz")
    sess = load_session(ROOT / f"data/{date}")
    body = body_from_measurements(sess.measurements(athlete))
    js = {k: d[k] for k in d.files}
    gl = an._glitch_masks(js, body)
    mask = {}
    for s in ("L", "R"):
        k = js[f"knee_flex_{s}"]
        jump = np.abs(np.gradient(k)) * CAPTURE_FPS > 2000.0     # MediaPipe knee jump (same rule as metrics)
        jump = np.convolve(np.nan_to_num(jump).astype(float), np.ones(9), "same") > 0
        mask[s] = gl[s] | jump | ~np.isfinite(k)
    extra = {f"shoulder_{s}": js[f"shoulder_{s}"] for s in ("L", "R") if f"shoulder_{s}" in js}
    extra.update({f"elbow_{s}": js[f"elbow_{s}"] for s in ("L", "R") if f"elbow_{s}" in js})
    return Track(d["uv"], d["orig_frame"], mask, {s: js[f"knee_flex_{s}"] for s in ("L", "R")}, extra)


def load_flip_track(date: str) -> Track:
    d = np.load(ROOT / f"results/{date}/work/backflip_pose.npz")
    uv = d["uv"].copy()
    for j in range(33):                       # raw per-frame best-of-4-rotations pose: light smoothing
        for a in range(2):
            x = pd_interp(uv[:, j, a])
            med = np.array([np.median(x[max(0, i - 2):i + 3]) for i in range(len(x))])
            uv[:, j, a] = _smooth1d(med, 3)
    tr = Track(uv, d["frame"], extra={"ang": d["ang"]})
    tr.cam_u = _smooth1d(pd_interp(tr.com[:, 0]), 61)
    tr.cam_v = float(np.nanmedian(tr.com[:, 1])) - 40
    return tr


class Reader:
    """Random-access frame reader with a small LRU cache (sequential reads are cheap, seeks re-decode)."""

    def __init__(self, path: Path, cache: int = 40):
        self.path, self.cap, self.pos = path, None, 0
        self.cache: OrderedDict[int, np.ndarray] = OrderedDict()
        self.size = cache

    def get(self, f: int) -> np.ndarray:
        if f in self.cache:
            self.cache.move_to_end(f)
            return self.cache[f]
        if self.cap is None or f < self.pos:
            if self.cap is not None:
                self.cap.release()
            self.cap, self.pos = cv2.VideoCapture(str(self.path)), 0
        while self.pos < f:
            self.cap.grab(); self.pos += 1
        ok, img = self.cap.read()
        self.pos += 1
        if not ok:
            raise RuntimeError(f"{self.path}: cannot read frame {f}")
        self.cache[f] = img
        if len(self.cache) > self.size:
            self.cache.popitem(last=False)
        return img


# ---------------------------------------------------------------------------------------------- drawing

class View:
    """A camera window on one clip, drawn into a rectangle of the output frame."""

    def __init__(self, spec: dict, date: str, rect: tuple[int, int, int, int]):
        self.spec = spec
        self.anchor = int(spec.get("anchor", 0))
        self.rect = rect                         # x, y, w, h in output
        clip = spec["clip"]
        self.reader = Reader(ROOT / f"data/{date}/{clip}")
        if spec.get("flip"):
            self.track = load_flip_track(date)
        else:
            ath, rep = clip.split("/", 1)
            self.track = load_run_track(date, ath, rep[:-4])   # analysis files are named after the clip minus ".mov"
        self.zoom = float(spec.get("zoom", 2.0))
        self.overlays = spec.get("overlays", [])

    def window(self, f):
        x, y, w, h = self.rect
        cw, ch = w / self.zoom, h / self.zoom
        j = self.track.i(f)
        cu = self.track.cam_u[j] if j is not None else self.track.cam_u[0 if f < self.track.f0 else -1]
        cv_ = self.track.cam_v + float(self.spec.get("cam_dv", -30))
        x0 = float(np.clip(cu - cw / 2, 0, 1920 - cw)); y0 = float(np.clip(cv_ - ch / 2, 0, 1080 - ch))
        return x0, y0, cw, ch

    def render(self, canvas: np.ndarray, f: int, ctx: dict):
        x, y, w, h = self.rect
        x0, y0, cw, ch = self.window(f)
        img = self.reader.get(f)
        M = np.float32([[self.zoom, 0, -x0 * self.zoom], [0, self.zoom, -y0 * self.zoom]])
        sub = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC)
        tf = lambda p: (float((p[0] - x0) * self.zoom), float((p[1] - y0) * self.zoom))
        draw_skeleton(sub, self.track, f, tf)
        texts = []
        for ov in self.overlays:
            OVERLAYS[ov["type"]](sub, self, f, tf, ov, ctx, texts)
        canvas[y:y + h, x:x + w] = sub
        return [(tx + x, ty + y, s, kw) for tx, ty, s, kw in texts]


def _pt(p):
    return int(round(p[0])), int(round(p[1]))


def dashed(img, a, b, col, th, dash=14):
    a, b = np.array(a, float), np.array(b, float)
    L = np.linalg.norm(b - a)
    if L < 1:
        return
    n = max(1, int(L / dash))
    for k in range(0, n, 2):
        p = a + (b - a) * k / n; q = a + (b - a) * min(n, k + 1) / n
        cv2.line(img, _pt(p), _pt(q), col, th, cv2.LINE_AA)


def draw_skeleton(img, tr: Track, f, tf, th=4):
    j = tr.i(f)
    if j is None:
        return
    uv = tr.uv[j]
    for a, b in BONES:
        pa, pb = uv[a], uv[b]
        if not (np.isfinite(pa).all() and np.isfinite(pb).all()):
            continue
        side = "L" if (a in LEFT and b in LEFT) else "R" if (a not in LEFT and b not in LEFT) else "C"
        leg = next((s for s in ("L", "R") if a in LEG[s] or b in LEG[s]), None)
        if leg and tr.mask[leg][j]:
            dashed(img, tf(pa), tf(pb), COL["X"], 3)
            continue
        cv2.line(img, _pt(tf(pa)), _pt(tf(pb)), (20, 20, 20), th + 3, cv2.LINE_AA)
        cv2.line(img, _pt(tf(pa)), _pt(tf(pb)), COL[side], th, cv2.LINE_AA)
    for k in range(11, 33):
        if k in (17, 18, 19, 20, 21, 22) or not np.isfinite(uv[k]).all():
            continue
        leg = next((s for s in ("L", "R") if k in LEG[s]), None)
        if leg and tr.mask[leg][j]:
            continue
        cv2.circle(img, _pt(tf(uv[k])), th + 2, (20, 20, 20), -1, cv2.LINE_AA)
        cv2.circle(img, _pt(tf(uv[k])), th, COL["L"] if k in LEFT else COL["R"], -1, cv2.LINE_AA)


def _in(f, ov):
    fr = ov.get("frames")
    return fr is None or fr[0] <= f <= fr[1]


def ov_knee(img, v, f, tf, ov, ctx, texts):
    s = ov["side"]
    if not _in(f, ov) or v.track.masked(f, s):
        return
    k = v.track.knee[s][v.track.i(f)]
    p = tf(v.track.p(f, f"knee_{s}"))
    texts.append((p[0] + 26, p[1] - 22, f"knee flexion {k:.0f}°", {"size": 30, "bg": True}))


def ov_contact(img, v, f, tf, ov, ctx, texts):
    td, to = ov["td"], ov["to"]
    if f < td - ov.get("lead", 0):
        return
    ms = (min(max(f, td), to) - td) / CAPTURE_FPS * 1000
    lab = ov.get("label", "foot on the ground")
    texts.append((30, img.shape[0] - 165, f"{lab}: {ms:.0f} ms" + ("  (pushed off)" if f >= to else ""),
                  {"size": 36, "bg": True, "col": (255, 255, 255) if f < to else (120, 255, 150)}))


def ov_flight(img, v, f, tf, ov, ctx, texts):
    to, td = ov["to"], ov["td"]
    if f < to:
        return
    ms = (min(f, td) - to) / CAPTURE_FPS * 1000
    done = f >= td
    texts.append((30, img.shape[0] - 165, f"{ov.get('label', 'in the air')}: {ms:.0f} ms" + ("  (landed)" if done else ""),
                  {"size": 36, "bg": True, "col": (120, 255, 150) if done else (255, 255, 255)}))


def ov_footprints(img, v, f, tf, ov, ctx, texts):
    prints = [(int(a), s) for a, s in ov["prints"]]
    labels = ov.get("labels", [])
    done = [(a, s) for a, s in prints if f >= a]
    pts = []
    for a, s in done:
        p = v.track.foot_low(a, s)
        if p is None:
            continue
        q = tf(p); pts.append(q)
        cv2.ellipse(img, _pt((q[0], q[1] + 6)), (26, 9), 0, 0, 360, (20, 20, 20), -1, cv2.LINE_AA)
        cv2.ellipse(img, _pt((q[0], q[1] + 6)), (22, 6), 0, 0, 360, COL[s], -1, cv2.LINE_AA)
    for k in range(1, len(pts)):
        a, b = pts[k - 1], pts[k]
        yb = max(a[1], b[1]) + 44
        cv2.line(img, _pt((a[0], yb)), _pt((b[0], yb)), (255, 255, 255), 3, cv2.LINE_AA)
        for e in (a, b):
            cv2.line(img, _pt((e[0], yb - 12)), _pt((e[0], yb + 12)), (255, 255, 255), 3, cv2.LINE_AA)
        if k - 1 < len(labels):
            texts.append(((a[0] + b[0]) / 2, yb + 14, labels[k - 1], {"size": 30, "bg": True, "anchor": "mt"}))


def ov_hip_foot(img, v, f, tf, ov, ctx, texts):
    if f != ov["frame"] and not (ov.get("hold") and ov["frame"] <= f <= ov["frame"] + ov["hold"]):
        return
    fr, s = ov["frame"], ov["side"]
    hip, foot = v.track.hip(fr), v.track.foot_low(fr, s)
    if hip is None or foot is None:
        return
    H, Fp = tf(hip), tf(foot)
    top, bot = H[1] - 60, Fp[1] + 10
    dashed(img, (H[0], top), (H[0], bot), (255, 255, 255), 3)
    dashed(img, (Fp[0], top), (Fp[0], bot), YELLOW, 3)
    yb = bot + 30
    cv2.arrowedLine(img, _pt((H[0], yb)), _pt((Fp[0], yb)), YELLOW, 4, cv2.LINE_AA, tipLength=0.12)
    texts.append(((H[0] + Fp[0]) / 2, yb + 12, ov["label"], {"size": 30, "bg": True, "anchor": "mt", "col": (255, 220, 0)}))
    texts.append((H[0], top - 8, "hips", {"size": 26, "bg": True, "anchor": "mb"}))
    if ov.get("arrow"):
        sgn = 1 if Fp[0] > H[0] else -1
        cv2.arrowedLine(img, _pt((Fp[0] - sgn * 10, Fp[1] - 40)), _pt((Fp[0] + sgn * 70, Fp[1] - 40)), (120, 255, 150),
                        4, cv2.LINE_AA, tipLength=0.3)
        texts.append((Fp[0] + sgn * 80, Fp[1] - 58, ov["arrow"], {"size": 26, "bg": True,
                                                                  "anchor": "lm" if sgn > 0 else "rm", "col": (150, 255, 170)}))


def ov_shin(img, v, f, tf, ov, ctx, texts):
    if not _in(f, ov):
        return
    s = ov["side"]
    if v.track.masked(f, s):
        return
    K, A = tf(v.track.p(f, f"knee_{s}")), tf(v.track.p(f, f"ankle_{s}"))
    L = math.dist(K, A)
    dashed(img, K, (K[0], K[1] + L * 1.15), (255, 255, 255), 2)
    cv2.line(img, _pt(K), _pt((K[0] + (A[0] - K[0]) * 1.15, K[1] + (A[1] - K[1]) * 1.15)), YELLOW, 4, cv2.LINE_AA)
    if ov.get("label"):
        texts.append((max(K[0], A[0]) + 30, (K[1] + A[1]) / 2, ov["label"], {"size": 28, "bg": True, "anchor": "lm",
                                                                         "col": (255, 220, 0)}))


def ov_com(img, v, f, tf, ov, ctx, texts):
    tr = v.track
    j = tr.i(f)
    if j is None:
        return
    W = int(ov.get("window", 80))
    lo = max(0, j - W)
    seg = tr.com[lo:j + 1]
    pts = [tf(p) for p in seg if np.isfinite(p).all()]
    for k in range(1, len(pts)):
        a = k / len(pts)
        col = tuple(int(c * a + 40 * (1 - a)) for c in YELLOW)
        cv2.line(img, _pt(pts[k - 1]), _pt(pts[k]), col, 4, cv2.LINE_AA)
    if ov.get("band", True) and len(pts) > W // 2:
        ys = [p[1] for p in pts]
        x1 = pts[-1][0]
        for yy in (min(ys), max(ys)):
            cv2.line(img, _pt((x1 - 260, yy)), _pt((x1 + 120, yy)), (255, 255, 255), 2, cv2.LINE_AA)
        if ov.get("label"):
            texts.append((x1 + 130, (min(ys) + max(ys)) / 2, ov["label"], {"size": 30, "bg": True, "anchor": "lm",
                                                                       "col": (255, 220, 0)}))
    if pts:
        cv2.circle(img, _pt(pts[-1]), 13, (20, 20, 20), -1, cv2.LINE_AA)
        cv2.circle(img, _pt(pts[-1]), 10, YELLOW, -1, cv2.LINE_AA)


def ov_flip(img, v, f, tf, ov, ctx, texts):
    tr = v.track
    j = tr.i(f)
    if j is None:
        return
    to = ov["toe_off"]
    ang = tr.extra["ang"][j]                     # trunk angle from upright, negative = leaning back
    hip, sh = (tr.uv[j, 23] + tr.uv[j, 24]) / 2, (tr.uv[j, 11] + tr.uv[j, 12]) / 2
    H, S = tf(hip), tf(sh)
    cv2.line(img, _pt(H), _pt((H[0] + (S[0] - H[0]) * 1.6, H[1] + (S[1] - H[1]) * 1.6)), YELLOW, 5, cv2.LINE_AA)
    c = tf(tr.com[j])
    if f >= to:
        rot = max(0.0, -ang)
        sgn = ov.get("arc_sign", -1)
        cv2.ellipse(img, _pt(c), (150, 150), 0, -90, -90 + sgn * min(rot, 360), (120, 255, 150), 6, cv2.LINE_AA)
        dashed(img, c, (c[0], c[1] - 175), (255, 255, 255), 2)
        texts.append((c[0], c[1] - 190, f"turned {rot:.0f}° of 360°", {"size": 32, "bg": True, "anchor": "mb",
                                                                    "col": (150, 255, 170)}))
    texts.append((30, img.shape[0] - 165, f"upper body: {abs(ang):.0f}° {'back' if ang < 0 else 'forward'} from upright",
                  {"size": 34, "bg": True}))


def ov_arm(img, v, f, tf, ov, ctx, texts):
    """Live shoulder angle (arm swing, + = in front of the trunk) and elbow angle next to the shoulder."""
    s = ov["side"]
    if not _in(f, ov) or f"shoulder_{s}" not in v.track.extra:
        return
    j = v.track.i(f)
    a, e = v.track.extra[f"shoulder_{s}"][j], v.track.extra[f"elbow_{s}"][j]
    if not (np.isfinite(a) and np.isfinite(e)):
        return
    S, E = tf(v.track.p(f, f"sh_{s}")), tf(v.track.uv[j, 14 if s == "R" else 13])
    cv2.line(img, _pt(S), _pt(E), YELLOW, 6, cv2.LINE_AA)
    word = "in front of" if a >= 0 else "behind"
    texts.append((S[0] + 40, S[1] - 70, f"arm {abs(a):.0f}° {word} the trunk · elbow {e:.0f}°",
                  {"size": 30, "bg": True, "col": (255, 220, 0)}))


def ov_legend(img, v, f, tf, ov, ctx, texts):
    texts.append((img.shape[1] - 24, 22, "red = right leg   blue = left leg", {"size": 26, "bg": True, "anchor": "ra"}))


def ov_label(img, v, f, tf, ov, ctx, texts):
    texts.append((ov.get("x", 30), ov.get("y", 24), ov["text"], {"size": ov.get("size", 34), "bg": True, "bold": True}))


def _sgn(tr: Track) -> int:
    hu = pd_interp(((tr.uv[:, 23] + tr.uv[:, 24]) / 2)[:, 0])
    return 1 if hu[-1] > hu[0] else -1


def _seg_px(tr: Track) -> dict:
    if not hasattr(tr, "_segpx"):
        L = lambda a, b: float(np.nanmedian(np.linalg.norm(tr.uv[:, a] - tr.uv[:, b], axis=-1)))
        hipm = (tr.uv[:, 23] + tr.uv[:, 24]) / 2; shm = (tr.uv[:, 11] + tr.uv[:, 12]) / 2
        tr._segpx = {"thigh": (L(23, 25) + L(24, 26)) / 2, "shank": (L(25, 27) + L(26, 28)) / 2,
                     "trunk": float(np.nanmedian(np.linalg.norm(shm - hipm, axis=-1)))}
    return tr._segpx


def ov_model(img, v, f, tf, ov, ctx, texts):
    """Published world-class pose (positions.MODEL_TD / MODEL_TO) in white, sized to the athlete, anchored at the
    stance ankle. Shown in `frames` [a, b] (default: only at `frame`)."""
    from . import positions
    fr = ov.get("frames") or [ov["frame"], ov["frame"]]
    if not (fr[0] <= f <= fr[1]):
        return
    if ov.get("segs") is not None and ctx["seg"] not in ov["segs"]:
        return
    model = positions.MODEL_TD if ov.get("pos", "td") == "td" else positions.MODEL_TO
    ank = v.track.p(f, f"ankle_{ov['stance']}")
    if ank is None or not np.isfinite(ank).all():
        return
    m = positions.model_pose(model, ank, _seg_px(v.track), _sgn(v.track))
    segs = [("ankle_s", "knee_s"), ("knee_s", "hip"), ("hip", "shoulder"), ("hip", "knee_o")]
    if "ankle_o" in m:
        segs.append(("knee_o", "ankle_o"))
    ovl = img.copy()
    for a, b in segs:
        cv2.line(ovl, _pt(tf(m[a])), _pt(tf(m[b])), (20, 20, 20), 15, cv2.LINE_AA)
        cv2.line(ovl, _pt(tf(m[a])), _pt(tf(m[b])), (255, 255, 255), 10, cv2.LINE_AA)
    for k in m:
        cv2.circle(ovl, _pt(tf(m[k])), 9, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.addWeighted(ovl, 0.8, img, 0.2, 0, dst=img)
    lab = ov.get("label", "white = world-class average")
    p = tf(m["shoulder"])
    texts.append((p[0], p[1] - 30, lab, {"size": 30, "bg": True, "anchor": "mb"}))


def ov_kneegap(img, v, f, tf, ov, ctx, texts):
    """Horizontal gap between the swing knee and the stance knee (figure-4 check)."""
    fr = ov.get("frames") or [ov["frame"], ov["frame"]]
    if not (fr[0] <= f <= fr[1]):
        return
    sw, st = ov["swing"], ov["stance"]
    a, b = v.track.p(f, f"knee_{sw}"), v.track.p(f, f"knee_{st}")
    if a is None or b is None:
        return
    A, B = tf(a), tf(b)
    y = max(A[1], B[1]) + 70
    for P_ in (A, B):
        dashed(img, P_, (P_[0], y + 12), (255, 255, 255), 3)
    cv2.arrowedLine(img, _pt((B[0], y)), _pt((A[0], y)), YELLOW, 5, cv2.LINE_AA, tipLength=0.15)
    texts.append(((A[0] + B[0]) / 2, y + 16, ov["label"], {"size": 30, "bg": True, "anchor": "mt", "col": (255, 220, 0)}))


def ov_joint(img, v, f, tf, ov, ctx, texts):
    """Included angle at a knee or hip with a label, e.g. push-off knee at toe-off."""
    fr = ov.get("frames") or [ov["frame"], ov["frame"]]
    if not (fr[0] <= f <= fr[1]):
        return
    s, jn = ov["side"], ov.get("joint", "knee")
    j = v.track.i(f)
    if j is None:
        return
    idx = {"knee": (23, 25, 27), "hip": (11, 23, 25)} if s == "L" else {"knee": (24, 26, 28), "hip": (12, 24, 26)}
    a, b, c = (v.track.uv[j, k] for k in idx[jn])
    if not all(np.isfinite(x).all() for x in (a, b, c)):
        return
    A, B, C = tf(a), tf(b), tf(c)
    for P_ in (A, C):
        cv2.line(img, _pt(B), _pt(P_), YELLOW, 6, cv2.LINE_AA)
    ang = math.degrees(math.acos(np.clip(np.dot(np.subtract(A, B), np.subtract(C, B)) /
                                         (math.dist(A, B) * math.dist(C, B)), -1, 1)))
    lab = ov.get("label", "{a:.0f}°").format(a=ang)
    dx = ov.get("dx", 40)
    texts.append((B[0] + dx, B[1] + ov.get("dy", 0), lab, {"size": 30, "bg": True, "anchor": "lm" if dx > 0 else "rm",
                                                       "col": (255, 220, 0)}))


def ov_thigh(img, v, f, tf, ov, ctx, texts):
    """Live thigh angle vs vertical (+ = knee in front of the hip) with a vertical reference through the hip."""
    if not _in(f, ov):
        return
    s = ov["side"]
    j = v.track.i(f)
    if j is None or v.track.masked(f, s):
        return
    h, k = v.track.uv[j, 23 if s == "L" else 24], v.track.uv[j, 25 if s == "L" else 26]
    if not (np.isfinite(h).all() and np.isfinite(k).all()):
        return
    H, K = tf(h), tf(k)
    L = math.dist(H, K)
    dashed(img, H, (H[0], H[1] + L * 1.1), (255, 255, 255), 2)
    cv2.line(img, _pt(H), _pt((H[0] + (K[0] - H[0]) * 1.1, H[1] + (K[1] - H[1]) * 1.1)), YELLOW, 6, cv2.LINE_AA)
    a = math.degrees(math.atan2(_sgn(v.track) * (k[0] - h[0]), k[1] - h[1]))
    word = "in front" if a >= 0 else "behind"
    texts.append((30, img.shape[0] - 165, f"{ov.get('label', 'thigh')}: {abs(a):.0f}° {word}",
                  {"size": 36, "bg": True, "col": (255, 220, 0)}))


OVERLAYS = {"thigh": ov_thigh, "model": ov_model, "kneegap": ov_kneegap, "joint": ov_joint, "knee": ov_knee, "contact": ov_contact, "flight": ov_flight, "footprints": ov_footprints,
            "hip_foot": ov_hip_foot, "shin": ov_shin, "com": ov_com, "flip": ov_flip, "legend": ov_legend,
            "label": ov_label, "arm": ov_arm}

_fonts: dict = {}


def font(size, bold=False):
    k = (size, bold)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONT_B if bold else FONT, size)
    return _fonts[k]


def draw_texts(canvas: np.ndarray, items) -> np.ndarray:
    """items: (x, y, text, opts). opts: size, bold, bg, col (RGB), anchor, box (wrap width px)."""
    im = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    dr = ImageDraw.Draw(im, "RGBA")
    for x, y, text, o in items:
        ft = font(o.get("size", 32), o.get("bold", False))
        anchor = o.get("anchor", "la")
        if o.get("box"):
            text = wrap(dr, text, ft, o["box"])
        bb = dr.multiline_textbbox((x, y), text, font=ft, anchor=anchor, spacing=8)
        if o.get("bg"):
            pad = o.get("pad", 8)
            dr.rounded_rectangle((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad), radius=8,
                                 fill=o.get("bgcol", (0, 0, 0, 175)))
        dr.multiline_text((x, y), text, font=ft, anchor=anchor, fill=o.get("col", (255, 255, 255)), spacing=8)
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)


def wrap(dr, text, ft, width):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split():
            t = (line + " " + w).strip()
            if dr.textlength(t, font=ft) > width and line:
                out.append(line); line = w
            else:
                line = t
        out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------- timing

def plan_frames(segs: list[dict], target_s: float) -> list[tuple[int, float, dict]]:
    """→ list of (source offset frame, slowdown shown, seg) per output frame, lasting ≈ target_s."""
    base_play = sum((s["to"] - s["from"] + 1) * s.get("slow", 8) / BASE_SLOW for s in segs if "freeze" not in s)
    frz = [s for s in segs if "freeze" in s]
    base_frz = sum(s.get("min", 0.8) for s in frz) * OUT_FPS
    target = target_s * OUT_FPS
    stretch, extra = 1.0, 0.0
    if target > base_play + base_frz:
        if frz:
            extra = target - base_play - base_frz
        else:
            stretch = target / base_play
    elif target < base_play + base_frz:
        stretch = max(0.6, (target - base_frz) / base_play) if base_play else 1.0
    wsum = sum(s.get("w", 1.0) for s in frz) or 1.0
    out = []
    for s in segs:
        if "freeze" in s:
            n = int(round(s.get("min", 0.8) * OUT_FPS + extra * s.get("w", 1.0) / wsum))
            out += [(int(s["freeze"]), math.inf, s)] * max(1, n)
        else:
            slow = s.get("slow", 8) * stretch
            n = int(round((s["to"] - s["from"] + 1) * slow / BASE_SLOW))
            src = np.linspace(s["from"], s["to"] + 1, n, endpoint=False)
            out += [(int(math.floor(x)), slow, s) for x in src]
    return out


def speed_badge(slow: float) -> str:
    if math.isinf(slow):
        return "paused"
    if slow >= 40:
        return "frame by frame"
    nice = min([8, 10, 12, 16, 20, 24, 32], key=lambda x: abs(x - slow))
    return f"{nice}× slower than real life"


# ---------------------------------------------------------------------------------------------- main

def build(spec_path: Path):
    spec = yaml.safe_load(spec_path.read_text())
    date, name = spec["date"], spec["name"]
    work = spec_path.parent / f"{name}_work"
    work.mkdir(parents=True, exist_ok=True)

    # 1. narration
    lines = [{"id": f"s{i + 1}", "text": sh.get("tts", sh["say"])} for i, sh in enumerate(spec["shots"])]
    (work / "lines.json").write_text(json.dumps(lines, indent=1))
    old = work / "lines_done.json"
    if not (old.exists() and json.loads(old.read_text()) == lines and (work / "durations.json").exists()):
        subprocess.run([str(ROOT / ".venv-tts/bin/python"), str(ROOT / "src/runform/tts_kokoro.py"),
                        str(work / "lines.json"), str(work), spec.get("voice", "am_michael"),
                        str(spec.get("speed", 1.0))], check=True)
        old.write_text(json.dumps(lines, indent=1))
    durs = json.loads((work / "durations.json").read_text())

    # 2. picture
    import imageio_ffmpeg
    lead, tail = 0.35, 0.55
    audio_parts, srt, t_now = [], [], 0.0
    sr = None
    silent_mp4 = work / f"{name}_silent.mp4"
    wr = imageio_ffmpeg.write_frames(str(silent_mp4), (OUT_W, OUT_H), fps=OUT_FPS, codec="libx264",
                                     pix_fmt_out="yuv420p", quality=8, macro_block_size=8)
    wr.send(None)
    for i, sh in enumerate(spec["shots"]):
        sid = f"s{i + 1}"
        target = lead + durs[sid] + tail
        frames = plan_frames(sh["segments"], target)
        views = sh["views"]
        if len(views) == 1:
            rects = [(0, 0, OUT_W, OUT_H)]
        else:
            rects = [(0, 0, OUT_W // 2, OUT_H), (OUT_W // 2, 0, OUT_W // 2, OUT_H)]   # side by side
        V = [View(vs, date, r) for vs, r in zip(views, rects)]
        nseg = {id(s): k for k, s in enumerate(sh["segments"])}
        for n, (off, slow, seg) in enumerate(frames):
            canvas = np.zeros((OUT_H, OUT_W, 3), np.uint8)
            texts = []
            for v in V:
                texts += v.render(canvas, v.anchor + off, {"seg": nseg[id(seg)]})
                if len(V) > 1 and v.spec.get("tag"):
                    x, y, w, h = v.rect
                    texts.append((x + w // 2, 140, v.spec["tag"],
                                  {"size": 36, "bold": True, "bg": True, "anchor": "ma"}))
            if len(V) > 1:
                cv2.line(canvas, (OUT_W // 2, 0), (OUT_W // 2, OUT_H), (255, 255, 255), 4)
            texts.append((24, 22, spec["title"], {"size": 30, "bold": True, "bg": True}))
            texts.append((24, 72, speed_badge(slow), {"size": 28, "bg": True, "col": (255, 220, 0)}))
            for c in sh.get("cards", []):
                segs = c.get("segs")
                if segs is None or nseg[id(seg)] in segs:
                    texts.append((OUT_W - 60, c.get("y", 150), c["text"],
                                  {"size": c.get("size", 40), "bold": True, "bg": True, "anchor": "ra", "box": 760,
                                   "pad": 18, "bgcol": (0, 0, 0, 195)}))
            if sh.get("caption"):
                texts.append((OUT_W // 2, OUT_H - 26, sh["caption"], {"size": 28, "bg": True, "anchor": "md", "box": OUT_W - 120,
                                                                     "col": (225, 225, 225), "bgcol": (0, 0, 0, 200)}))
            canvas = draw_texts(canvas, texts)
            wr.send(np.ascontiguousarray(canvas[:, :, ::-1]))
        dur = len(frames) / OUT_FPS
        a, sr = sf.read(work / f"{sid}.wav")
        buf = np.zeros(int(round(dur * sr)))
        s0 = int(lead * sr)
        buf[s0:s0 + len(a)] = a[:max(0, len(buf) - s0)]
        audio_parts.append(buf)
        # subtitles: split the line into sentences, timed by character count
        sents = [x.strip() for x in sh["say"].replace("? ", "?|").replace(". ", ".|").replace("! ", "!|").split("|") if x.strip()]
        tot = sum(len(x) for x in sents); tt = t_now + lead
        for x in sents:
            d = durs[sid] * len(x) / tot
            srt.append((tt, tt + d, x)); tt += d
        print(f"{sid}: narration {durs[sid]:.1f}s, picture {dur:.1f}s", flush=True)
        t_now += dur
    wr.close()

    wav = work / f"{name}.wav"
    sf.write(wav, np.concatenate(audio_parts), sr)
    out_mp4 = spec_path.parent / f"video_{name}.mp4"
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(silent_mp4), "-i", str(wav), "-c:v", "libx264", "-crf", "25", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", str(out_mp4)], check=True)
    fmt = lambda s: f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d},{int(round(s % 1 * 1000)) % 1000:03d}"
    (spec_path.parent / f"video_{name}.srt").write_text(
        "\n".join(f"{k + 1}\n{fmt(a)} --> {fmt(b)}\n{x}\n" for k, (a, b, x) in enumerate(srt)))
    print(f"wrote {out_mp4} ({t_now:.1f} s)")


if __name__ == "__main__":
    build(Path(sys.argv[1]))
