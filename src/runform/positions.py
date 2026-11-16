"""Key positions of the running stride, measured the way published elite studies measure them.

Positions (ALTIS kinogram, McMillan & Pfaff 2018): toe-off · MVP (max vertical projection, top of flight) ·
strike (front foot furthest ahead just before touchdown) · touchdown · full support (CM over the foot).

For each touchdown of foot `s` (stance leg) the other leg `o` is the swing leg. Angles are sagittal, in degrees:
- thigh angle: hip→knee vs vertical, + = knee in front of the hip (Bissas 2022, Clark 2025).
- thigh separation: swing thigh − stance thigh; − = swing knee behind the stance knee (Bissas 2022).
  The "figure 4" at touchdown is a thigh separation near zero (knees together) with the swing heel folded
  high under the hips.
- knee / hip angle: included angles, 180 = straight (hip = trunk–thigh angle, Bissas 2022).
- shank angle: knee→ankle vs vertical, + = ankle ahead of the knee.
- CM–foot angle: CM→contact point vs vertical (Clark 2025 "COM-foot leg angle").

Works from results/<date>/work/analysis/<athlete>_<rep>.{npz,json}; no re-tracking needed.
Formulas and sources: 04-analysis-method.md#key-positions; reference values: 02/03-reference.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

KNEE_JUMP_DEG_S = 2000.0

# ------------------------------------------------------------------ references (value, sd, source, note)
# Sprint, max velocity. Bissas 2022 = 2017 World Championships men's 100 m finalists (11.6 m/s, 3-D, hand
# digitised). Clark 2025 = US intercollegiate men, 240 fps iPhone side view like ours: "fast TF" track & field
# 10.0 m/s, "slow TF" 9.3 m/s, team-sport groups 8.2–9.3 m/s.
SPRINT_REF = {
    "thigh_sep_td_deg": [("world-class 100 m", -9.9, 10.7, "Bissas 2022"), ],
    "swing_thigh_td_deg": [("track 10.0 m/s", 15.4, 13.7, "Clark 2025"), ("track 9.3 m/s", 10.8, 15.6, "Clark 2025"),
                           ("team sport 8.2–9.3 m/s", -9.3, 8.5, "Clark 2025")],
    "swing_knee_td_deg": [("track 10.0 m/s", 49.3, 7.0, "Clark 2025"), ("track 9.3 m/s", 52.6, 8.2, "Clark 2025"),
                          ("team sport 8.2–9.3 m/s", 65.4, 6.6, "Clark 2025")],
    "stance_thigh_td_deg": [("world-class 100 m", 27.4, 4.7, "Bissas 2022")],
    "stance_knee_td_deg": [("world-class 100 m", 156.5, 6.1, "Bissas 2022")],
    "hip_td_deg": [("world-class 100 m", 139.7, 5.0, "Bissas 2022")],
    "shank_td_deg": [("world-class 100 m", 8.7, 3.5, "Bissas 2022")],
    "trunk_td_deg": [("world-class 100 m", 14.5, 3.0, "Bissas 2022")],
    "cm_foot_td_deg": [("track 10.0 m/s", 12.7, 2.4, "Clark 2025"), ("team sport 8.2–9.3 m/s", 17.0, 1.9, "Clark 2025")],
    "toe_ahead_cm_td_m": [("world-class 100 m", 0.38, 0.04, "Bissas 2022")],
    "foot_speed_td_ms": [("world-class 100 m", 2.36, 0.47, "Bissas 2022")],
    "trail_thigh_to_deg": [("world-class 100 m", -25.2, 3.1, "Bissas 2022")],
    "thigh_sep_to_deg": [("world-class 100 m", 93.1, 7.3, "Bissas 2022")],
    "knee_to_deg": [("world-class 100 m", 154.0, 4.2, "Bissas 2022")],
    "hip_to_deg": [("world-class 100 m", 196.3, 2.9, "Bissas 2022")],
    "trunk_to_deg": [("world-class 100 m", 9.3, 3.2, "Bissas 2022")],
    "leg_excursion_deg": [("track 10.0 m/s", 55.9, 4.1, "Clark 2025"), ("team sport 8.2–9.3 m/s", 61.2, 3.7, "Clark 2025")],
    "thigh_flex_max_deg": [("track 10.0 m/s", 76.2, 5.9, "Clark 2025"), ("team sport 8.2–9.3 m/s", 64.0, 5.4, "Clark 2025")],
    "thigh_ext_max_deg": [("track 10.0 m/s", -28.4, 6.8, "Clark 2025"), ("team sport 8.2–9.3 m/s", -34.6, 4.5, "Clark 2025")],
    "thigh_rom_deg": [("track 10.0 m/s", 104.6, 6.7, "Clark 2025"), ("team sport 8.2–9.3 m/s", 98.6, 6.1, "Clark 2025")],
    "front_side_pct": [("track 10.0 m/s", 72.8, None, "from Clark 2025 means"), ("team sport", 65.0, None, "from Clark 2025 means")],
    "thigh_ang_vel_dps": [("track 10.0 m/s", 482.9, 28.9, "Clark 2025"), ("team sport 8.2–9.3 m/s", 428.0, 30.0, "Clark 2025")],
    "thigh_ang_acc_kdps2": [("track 10.0 m/s", 11.0, 0.9, "Clark 2025"), ("team sport 8.2–9.3 m/s", 9.2, 1.0, "Clark 2025")],
}
# Middle distance. Hanley 2023 = 2017 World Championships men's 1500 m final (7.0–7.5 m/s laps).
MILE_REF = {
    "stance_knee_td_deg": [("world 1500 m final", 154.0, None, "Hanley 2023")],
    "hip_td_deg": [("world 1500 m final", 152.0, None, "Hanley 2023")],
    "foot_ahead_cm_td_m": [("world 1500 m final (foot centre)", 0.35, None, "Hanley 2023")],
    "overstride_m": [("world 1500 m final", 0.043, None, "Hanley 2023")],
}

KEYS = ["swing_thigh_td_deg", "stance_thigh_td_deg", "thigh_sep_td_deg", "knee_sep_td_m", "swing_knee_td_deg",
        "swing_heel_behind_hip_td_m", "swing_heel_above_knee_td_m", "stance_knee_td_deg", "hip_td_deg",
        "shank_td_deg", "trunk_td_deg", "cm_foot_td_deg", "foot_ahead_cm_td_m", "toe_ahead_cm_td_m", "overstride_m", "foot_speed_td_ms",
        "trail_thigh_to_deg", "front_thigh_to_deg", "thigh_sep_to_deg", "knee_to_deg", "hip_to_deg", "trunk_to_deg",
        "leg_excursion_deg", "swing_heel_above_knee_fs_m", "swing_knee_ahead_fs_m",
        "thigh_flex_max_deg", "thigh_ext_max_deg", "thigh_rom_deg", "front_side_pct", "thigh_ang_vel_dps",
        "thigh_ang_acc_kdps2", "recovery_thigh_at_heel_max_deg", "recovery_heel_behind_hip_m",
        "thigh_vertical_after_to_ms"]

PRETTY = {
    "swing_thigh_td_deg": "Swing thigh at touchdown (°, + = knee in front of hip)",
    "stance_thigh_td_deg": "Stance thigh at touchdown (°)",
    "thigh_sep_td_deg": "Thigh separation at touchdown (°, − = swing knee behind; 0 = knees together)",
    "knee_sep_td_m": "Swing knee behind (−) / ahead of (+) the stance knee at touchdown (m)",
    "swing_knee_td_deg": "Swing knee angle at touchdown (°, smaller = heel folded tighter)",
    "swing_heel_behind_hip_td_m": "Swing heel behind the hips at touchdown (m)",
    "swing_heel_above_knee_td_m": "Swing heel above the stance knee at touchdown (m)",
    "stance_knee_td_deg": "Stance knee angle at touchdown (°, 180 = straight)",
    "hip_td_deg": "Stance hip angle at touchdown (trunk–thigh, °)",
    "shank_td_deg": "Shin angle at touchdown (°, + = ankle ahead of knee)",
    "trunk_td_deg": "Trunk lean at touchdown (°, + = forward)",
    "cm_foot_td_deg": "Leg angle at touchdown: CM→foot vs vertical (°)",
    "foot_ahead_cm_td_m": "Touchdown distance: middle of the foot ahead of the CM (m)",
    "toe_ahead_cm_td_m": "Touchdown distance: toe tip ahead of the CM (m)",
    "overstride_m": "Overstride: ankle ahead of the knee at touchdown (m)",
    "foot_speed_td_ms": "Foot speed over the ground at touchdown (m/s, + = forward)",
    "trail_thigh_to_deg": "Trailing (push-off) thigh at toe-off (°, − = behind)",
    "front_thigh_to_deg": "Front (swing) thigh at toe-off (°)",
    "thigh_sep_to_deg": "Thigh separation at toe-off (°)",
    "knee_to_deg": "Push-off knee angle at toe-off (°)",
    "hip_to_deg": "Push-off hip angle at toe-off (°, >180 = extended behind)",
    "trunk_to_deg": "Trunk lean at toe-off (°)",
    "leg_excursion_deg": "Leg excursion during contact: CM→foot angle swept (°)",
    "swing_heel_above_knee_fs_m": "Full support: swing heel above the stance knee (m)",
    "swing_knee_ahead_fs_m": "Full support: swing knee ahead of the stance knee (m)",
    "thigh_flex_max_deg": "Knee lift: max thigh angle in front (°)",
    "thigh_ext_max_deg": "Max thigh angle behind (°)",
    "thigh_rom_deg": "Thigh range of motion (°)",
    "front_side_pct": "Front-side share of thigh motion (% in front of vertical)",
    "thigh_ang_vel_dps": "Average thigh angular velocity (°/s)",
    "thigh_ang_acc_kdps2": "Peak thigh angular acceleration (k°/s²)",
    "recovery_thigh_at_heel_max_deg": "Thigh angle when the heel is folded tightest (°)",
    "recovery_heel_behind_hip_m": "Heel behind the hips when folded tightest (m)",
    "thigh_vertical_after_to_ms": "Time from toe-off until the swing thigh passes vertical (ms)",
}


def _foot_pt(z, s):
    return (z[f"heel_{s}"] + z[f"toe_{s}"]) / 2


def _vert(dx, dy):
    """angle of (dx, dy) vs straight down/up in degrees, + = forward."""
    return float(np.degrees(np.arctan2(dx, abs(dy)))) if np.isfinite(dx) and np.isfinite(dy) else math.nan


def masks(z: dict, fs: float, body=None) -> dict:
    """side → bool mask of frames where that leg's tracking is implausible (knee-landmark jump, or segment
    length off when a body reference is given)."""
    out = {}
    for s in ("L", "R"):
        k = np.asarray(z[f"knee_flex_{s}"], float)
        jump = np.abs(np.gradient(k)) * fs > KNEE_JUMP_DEG_S
        jump = np.convolve(np.nan_to_num(jump).astype(float), np.ones(7), "same") > 0
        m = jump | ~np.isfinite(k)
        if body is not None:
            from .analyze import _glitch_masks
            m |= _glitch_masks(z, body)[s]
        out[s] = m
    return out


def _val(z, key, i, mask=None):
    if i is None or not (0 <= i < len(z[key])):
        return math.nan
    if mask is not None and mask[i]:
        return math.nan
    v = z[key][i]
    return float(v) if np.ndim(v) == 0 and np.isfinite(v) else math.nan


def key_positions(z: dict, info: dict, body=None) -> list[dict]:
    """One row per touchdown. z = analysis npz as dict, info = analysis json."""
    T = np.asarray(z["t"], float)
    fs = 1 / np.median(np.diff(T))
    idx = lambda t: int(np.argmin(np.abs(T - t)))
    near = info["near_side"]["detected"]
    cs = sorted([dict(c, i_td=idx(c["t_td"]), i_to=idx(c["t_to"])) for c in info["contacts"] if c["complete"]],
                key=lambda c: c["i_td"])
    mk = masks(z, fs, body)
    com, hip = z["com"], z["hip_mid"]
    rows = []
    for k, c in enumerate(cs):
        s = c["foot"]; o = "L" if s == "R" else "R"
        td, to = c["i_td"], c["i_to"]
        r = {"foot": s, "swing_leg": o, "stance_view": "near" if s == near else "far",
             "swing_view": "near" if o == near else "far", "t_td_s": c["t_td"], "frame_td": int(z["orig_frame"][td]),
             "frame_to": int(z["orig_frame"][to])}
        th_s = _val(z, f"thigh_{s}", td, mk[s]); th_o = _val(z, f"thigh_{o}", td, mk[o])
        r["stance_thigh_td_deg"], r["swing_thigh_td_deg"] = th_s, th_o
        r["thigh_sep_td_deg"] = th_o - th_s
        ks, ko = z[f"knee_{s}"][td], z[f"knee_{o}"][td]
        r["knee_sep_td_m"] = float(ko[0] - ks[0]) if not mk[o][td] else math.nan
        r["swing_knee_td_deg"] = 180 - _val(z, f"knee_flex_{o}", td, mk[o])
        heel_o = z[f"heel_{o}"][td]
        r["swing_heel_behind_hip_td_m"] = float(hip[td, 0] - heel_o[0])
        r["swing_heel_above_knee_td_m"] = float(heel_o[1] - ks[1])
        r["stance_knee_td_deg"] = 180 - _val(z, f"knee_flex_{s}", td, mk[s])
        r["hip_td_deg"] = 180 - _val(z, f"hip_flex_{s}", td, mk[s])
        r["shank_td_deg"] = _val(z, f"shin_{s}", td, mk[s])
        r["trunk_td_deg"] = _val(z, "trunk_lean", td)
        fp = _foot_pt(z, s)
        r["cm_foot_td_deg"] = _vert(fp[td, 0] - com[td, 0], com[td, 1] - fp[td, 1])
        r["foot_ahead_cm_td_m"] = float(fp[td, 0] - com[td, 0])
        r["toe_ahead_cm_td_m"] = float(z[f"toe_{s}"][td, 0] - com[td, 0])
        r["overstride_m"] = float(z[f"ankle_{s}"][td, 0] - ks[0])
        ax = np.gradient(z[f"ankle_{s}"][:, 0], 1 / fs)
        r["foot_speed_td_ms"] = float(ax[td])
        # toe-off of the stance foot: it is now the trailing leg; o is the front leg
        r["trail_thigh_to_deg"] = _val(z, f"thigh_{s}", to, mk[s])
        r["front_thigh_to_deg"] = _val(z, f"thigh_{o}", to, mk[o])
        r["thigh_sep_to_deg"] = r["front_thigh_to_deg"] - r["trail_thigh_to_deg"]
        if r["thigh_sep_to_deg"] < 20:      # legs swapped by the tracker at toe-off (trailing thigh in front)
            for kk in ("trail_thigh_to_deg", "front_thigh_to_deg", "thigh_sep_to_deg", "knee_to_deg", "hip_to_deg"):
                r[kk] = math.nan
        r["knee_to_deg"] = 180 - _val(z, f"knee_flex_{s}", to, mk[s])
        r["hip_to_deg"] = 180 - _val(z, f"hip_flex_{s}", to, mk[s])
        if r["knee_to_deg"] < 120:          # knee landmark jump as the legs cross
            r["knee_to_deg"] = r["hip_to_deg"] = math.nan
        r["trunk_to_deg"] = _val(z, "trunk_lean", to)
        r["leg_excursion_deg"] = r["cm_foot_td_deg"] - _vert(fp[to, 0] - com[to, 0], com[to, 1] - fp[to, 1])
        if not (30 <= r["leg_excursion_deg"] <= 80):   # CM or foot point glitch at an edge frame
            r["leg_excursion_deg"] = math.nan
        # full support: CM directly over the foot
        ii = np.arange(td, to + 1)
        fs_i = int(ii[np.nanargmin(np.abs(com[ii, 0] - fp[ii, 0]))])
        r["frame_fs"] = int(z["orig_frame"][fs_i])
        r["swing_heel_above_knee_fs_m"] = float(z[f"heel_{o}"][fs_i, 1] - z[f"knee_{s}"][fs_i, 1])
        r["swing_knee_ahead_fs_m"] = float(z[f"knee_{o}"][fs_i, 0] - z[f"knee_{s}"][fs_i, 0]) if not mk[o][fs_i] else math.nan
        # stride of leg s: this touchdown → next touchdown of s (its swing is to → next td)
        nxt = next((d for d in cs[k + 1:] if d["foot"] == s), None)
        other_next = next((d for d in cs[k + 1:] if d["foot"] != s), None)
        if nxt is not None:
            sw = slice(to, nxt["i_td"] + 1)
            th = np.array(z[f"thigh_{s}"][td:nxt["i_td"] + 1], float)
            th[mk[s][td:nxt["i_td"] + 1]] = np.nan
            if np.isfinite(th).mean() >= 0.7:
                fmax, emin = float(np.nanmax(th)), float(np.nanmin(th))
                r["thigh_flex_max_deg"], r["thigh_ext_max_deg"] = fmax, emin
                r["thigh_rom_deg"] = fmax - emin
                r["front_side_pct"] = 100 * fmax / (fmax - emin) if fmax > emin else math.nan
                stride_t = nxt["t_td"] - c["t_td"]
                r["thigh_ang_vel_dps"] = r["thigh_rom_deg"] / (stride_t / 2)          # Clark: ROM / step time
                r["thigh_ang_acc_kdps2"] = 2 * math.pi ** 2 * r["thigh_rom_deg"] * (1 / stride_t) ** 2 / 1000
            kf = np.array(z[f"knee_flex_{s}"][sw], float)
            kf[mk[s][sw]] = np.nan
            if np.isfinite(kf).mean() >= 0.7:
                j = to + int(np.nanargmax(kf))
                r["recovery_thigh_at_heel_max_deg"] = _val(z, f"thigh_{s}", j, mk[s])
                r["recovery_heel_behind_hip_m"] = float(hip[j, 0] - z[f"heel_{s}"][j, 0])
            ths = np.array(z[f"thigh_{s}"][sw], float)
            cross = np.nonzero((ths[:-1] < 0) & (ths[1:] >= 0))[0]
            if len(cross):
                r["thigh_vertical_after_to_ms"] = float(cross[0] * 1000 / fs)
        if other_next is not None:
            r["step_time_s"] = other_next["t_td"] - c["t_td"]
        rows.append(r)
    return rows


def summarize(rows: list[dict], keys=KEYS) -> dict:
    out = {}
    for k in keys:
        v = np.array([r.get(k, math.nan) for r in rows], float)
        v = v[np.isfinite(v)]
        out[k] = (float(v.mean()) if len(v) else math.nan, float(v.std(ddof=1)) if len(v) > 1 else math.nan, len(v))
    return out


# which view each metric relies on most: "swing" = the swing leg must be the near leg for good tracking
SWING_KEYS = {"swing_thigh_td_deg", "knee_sep_td_m", "swing_knee_td_deg", "swing_heel_behind_hip_td_m",
              "swing_heel_above_knee_td_m", "front_thigh_to_deg", "swing_heel_above_knee_fs_m", "swing_knee_ahead_fs_m"}
BOTH_KEYS = {"thigh_sep_td_deg", "thigh_sep_to_deg"}


def best_rows(rows: list[dict], key: str) -> list[dict]:
    """Near-view rows for the leg the metric depends on (swing-leg metrics → swing leg near; stance metrics →
    stance leg near). Separation angles use both legs, so every touchdown counts."""
    if key in BOTH_KEYS:
        return rows
    if key in SWING_KEYS:
        return [r for r in rows if r["swing_view"] == "near"]
    return [r for r in rows if r["stance_view"] == "near"]


def load(results: Path, athlete: str, rep: str):
    d = results / "work" / "analysis"
    z = dict(np.load(d / f"{athlete}_{rep}.npz"))
    info = json.loads((d / f"{athlete}_{rep}.json").read_text())
    return z, info


# ------------------------------------------------------------------ outputs

GROUPS = {"fly": "flying sprint", "fly_control": "approach-run simulation", "approach_sim": "approach-run simulation",
          "mile_pace": "mile pace", "kick_pace": "kick", "takeoff": "jump approach"}


def _fmt(m, sd, n, key):
    if not np.isfinite(m):
        return "—"
    d = 2 if key.endswith("_m") or key.endswith("_ms") and "foot_speed" in key else 0
    if key.endswith("_m"):
        d = 2
    if key == "thigh_ang_acc_kdps2" or key == "foot_speed_td_ms":
        d = 1
    sd_s = f" ± {sd:.{d}f}" if np.isfinite(sd) else ""
    return f"{m:.{d}f}{sd_s} (n={n})"


def _ref_str(key, refs):
    out = []
    for lab, v, sd, src in refs.get(key, []):
        d = 2 if key.endswith("_m") else 1 if key in ("thigh_ang_acc_kdps2", "foot_speed_td_ms") else 0
        out.append(f"{lab}: {v:.{d}f}" + (f" ± {sd:.{d}f}" if sd else "") + f" ({src})")
    return "; ".join(out) or "—"


def sheet(clip: Path, z: dict, info: dict, out: Path, rows: list[dict], n_rows: int = 2) -> Path | None:
    """Kinogram: the 5 key positions for the most central touchdowns, one row per touchdown (one with the near
    leg as the stance leg, one with the near leg swinging). Near leg red, far leg blue, thin line = vertical through
    the hips."""
    import cv2
    from .config import LM
    T = np.asarray(z["t"], float)
    near = info["near_side"]["detected"]
    uv, of, com = z["uv"], z["orig_frame"], z["com"]
    i_of = {int(f): i for i, f in enumerate(of)}
    cap = cv2.VideoCapture(str(clip))
    sgn = 1 if info["direction"] == "→" else -1
    mid_t = (T[0] + T[-1]) / 2
    picks = []
    for want in ("near", "far"):
        cand = [r for r in rows if r["stance_view"] == want]
        if cand:
            picks.append(min(cand, key=lambda r: abs(r["t_td_s"] - mid_t)))
    tiles_rows = []
    for r in picks[:n_rows]:
        td_i = i_of[r["frame_td"]]
        prev = [x for x in rows if x["t_td_s"] < r["t_td_s"] and x["foot"] != r["foot"]]
        if not prev:
            continue
        to_i = i_of[prev[-1]["frame_to"]]
        rng = np.arange(to_i, td_i)
        s = r["foot"]
        ax = uv[:, LM[f"{s.lower()}_ankle"], 0]; hx = uv[:, [LM["l_hip"], LM["r_hip"]], 0].mean(1)
        strike = int(rng[np.nanargmax(sgn * (ax[rng] - hx[rng]))]) if len(rng) else td_i
        mvp = int(rng[np.nanargmax(com[rng, 1])]) if len(rng) else td_i
        fs_i = i_of[r["frame_fs"]]
        tiles = []
        for name, i in (("toe-off", to_i), ("top of flight", mvp), ("strike", strike), ("touchdown", td_i),
                        ("full support", fs_i)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(of[i])); ok, img = cap.read()
            if not ok:
                continue
            for side, col in (("L" if near == "R" else "R", (255, 140, 0)), (near, (0, 0, 255))):
                ls = side.lower()
                for chain in ((f"{ls}_shoulder", f"{ls}_hip", f"{ls}_knee", f"{ls}_ankle", f"{ls}_heel", f"{ls}_toe", f"{ls}_ankle"),
                              (f"{ls}_shoulder", f"{ls}_elbow", f"{ls}_wrist")):
                    pts = [tuple(int(v) for v in uv[i, LM[k]]) for k in chain if np.isfinite(uv[i, LM[k]]).all()]
                    for a, b in zip(pts[:-1], pts[1:]):
                        cv2.line(img, a, b, col, 2, cv2.LINE_AA)
            h = uv[i, [LM["l_hip"], LM["r_hip"]]].mean(0)
            cv2.line(img, (int(h[0]), 0), (int(h[0]), img.shape[0]), (230, 230, 230), 1)
            x0 = int(np.clip(h[0] - 150, 0, img.shape[1] - 300)); y0 = int(np.clip(h[1] - 190, 0, img.shape[0] - 380))
            t = cv2.resize(img[y0:y0 + 380, x0:x0 + 300], (390, 494))
            cv2.rectangle(t, (0, 0), (390, 34), (0, 0, 0), -1)
            cv2.putText(t, f"{name}  f{of[i]}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            tiles.append(t)
        if len(tiles) == 5:
            lab = np.zeros((494, 120, 3), np.uint8)
            cv2.putText(lab, f"{s} foot", (8, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
            cv2.putText(lab, "lands" , (8, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
            cv2.putText(lab, f"({r['stance_view']})", (8, 292), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
            tiles_rows.append(np.hstack([lab] + tiles))
    if not tiles_rows:
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), np.vstack(tiles_rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return out


def write_athlete(sess, athlete: str, body=None) -> Path | None:
    """positions_<athlete>.csv (one row per touchdown) + positions_<athlete>.md (summary vs references) +
    figures/kinogram_<athlete>_<rep>.jpg."""
    import csv
    res = sess.results
    reps = [r for r in sess.reps if r.athlete == athlete and r.type in GROUPS
            and (res / "work" / "analysis" / f"{athlete}_{r.name}.json").exists()]
    if not reps:
        return None
    allrows, by_group = [], {}
    for r in reps:
        z, info = load(res, athlete, r.name)
        rows = key_positions(z, info, body)
        for x in rows:
            x.update(rep=r.name, type=r.type, speed_ms=info.get("speed_ms"))
        allrows += rows
        by_group.setdefault(GROUPS[r.type], []).extend(rows)
        sheet(sess.clip_path(r), z, info, res / "figures" / f"kinogram_{athlete}_{r.name}.jpg", rows)
        model_figures(sess.clip_path(r), z, info, rows, res / "figures", f"{athlete}_{r.name}")
    cols = ["rep", "type", "speed_ms", "foot", "swing_leg", "stance_view", "swing_view", "frame_td", "frame_to", "frame_fs"] + KEYS
    with open(res / f"positions_{athlete}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for x in allrows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in x.items()})
    refs = MILE_REF if any(r.type in ("mile_pace", "kick_pace") for r in reps) else SPRINT_REF
    groups = list(by_group)
    L = [f"# Key positions: athlete {athlete} ({sess.date})", "",
         "Mean ± SD (n = touchdowns). Each value uses only touchdowns where the leg it depends on faced the camera "
         "(swing-leg values: swing leg near; stance values: stance leg near; separation angles: all). Angles ± 5° per "
         "touchdown (far leg ± 8°), distances ± 3 cm. Definitions: `04-analysis-method.md#key-positions`.", "",
         "| measure | " + " | ".join(groups) + " | reference |", "|---|" + "---|" * len(groups) + "---|"]
    for k in KEYS:
        cells = []
        for g in groups:
            m, sd, n = summarize(best_rows(by_group[g], k), [k])[k]
            cells.append(_fmt(m, sd, n, k))
        ref = _ref_str(k, refs) if refs is MILE_REF and k in MILE_REF else _ref_str(k, SPRINT_REF)
        L.append(f"| {PRETTY[k]} | " + " | ".join(cells) + f" | {ref} |")
    L += ["", "Sprint references are at 8.2–11.6 m/s; for a miler they apply to the kick only. Sources: "
          "Bissas et al. 2022 (2017 World Championships 100 m finalists), Clark et al. 2025 (240 fps side view, "
          "intercollegiate track and team-sport men), Hanley et al. 2023 (2017 World Championships 1500 m final)."]
    p = res / f"positions_{athlete}.md"
    p.write_text("\n".join(L) + "\n")
    return p


# ------------------------------------------------------------------ published "model" pose for overlays

# Published mean angles at each position (sources in SPRINT_REF). Swing shank at touchdown: from the swing knee
# angle (Clark 2025 fast track group). At toe-off only the thighs, push-off knee and trunk are published.
MODEL_TD = {"stance_thigh": 27.4, "stance_knee": 156.5, "swing_thigh": 27.4 - 9.9, "swing_knee": 49.3, "trunk": 14.5}
MODEL_TO = {"stance_thigh": -25.2, "stance_knee": 154.0, "swing_thigh": -25.2 + 93.1, "swing_knee": None, "trunk": 9.3}


def model_pose(model: dict, ankle_px, seg_px: dict, sgn: int) -> dict:
    """Stick figure (pixel coords) from published angles, sized with the athlete's own segment lengths (px) and
    anchored at the athlete's stance ankle. sgn = +1 if running toward +u. Returns name → (u, v)."""
    def d(angle_from_down):            # unit vector in image coords for a segment pointing "down" at angle
        a = math.radians(angle_from_down)
        return np.array([sgn * math.sin(a), math.cos(a)])
    th, sh, tr = seg_px["thigh"], seg_px["shank"], seg_px["trunk"]
    st_shank = model["stance_thigh"] - (180 - model["stance_knee"])
    ankle = np.asarray(ankle_px, float)
    knee = ankle - sh * d(st_shank)
    hip = knee - th * d(model["stance_thigh"])
    a = math.radians(model["trunk"])
    sho = hip + tr * np.array([sgn * math.sin(a), -math.cos(a)])
    out = {"ankle_s": ankle, "knee_s": knee, "hip": hip, "shoulder": sho}
    out["knee_o"] = hip + th * d(model["swing_thigh"])
    if model.get("swing_knee") is not None:
        out["ankle_o"] = out["knee_o"] + sh * d(model["swing_thigh"] - (180 - model["swing_knee"]))
    return out


def seg_lengths_px(uv, near: str) -> dict:
    from .config import LM
    n = near.lower()
    L = lambda a, b: float(np.nanmedian(np.linalg.norm(uv[:, LM[a]] - uv[:, LM[b]], axis=-1)))
    hipm = (uv[:, LM["l_hip"]] + uv[:, LM["r_hip"]]) / 2
    shm = (uv[:, LM["l_shoulder"]] + uv[:, LM["r_shoulder"]]) / 2
    return {"thigh": L(f"{n}_hip", f"{n}_knee"), "shank": L(f"{n}_knee", f"{n}_ankle"),
            "trunk": float(np.nanmedian(np.linalg.norm(shm - hipm, axis=-1)))}


def compare_figure(clip: Path, z: dict, info: dict, frame: int, stance: str, model: dict, out: Path,
                   title: str, scale: float = 2.2, half: tuple = (170, 210)) -> Path:
    """One frame of the athlete with the published model pose (white) overlaid, anchored at the stance ankle."""
    import cv2
    from .config import LM
    of = list(map(int, z["orig_frame"])); i = of.index(int(frame))
    uv = z["uv"]; near = info["near_side"]["detected"]
    sgn = 1 if info["direction"] == "→" else -1
    cap = cv2.VideoCapture(str(clip)); cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame)); ok, img = cap.read()
    h = uv[i, [LM["l_hip"], LM["r_hip"]]].mean(0)
    x0 = int(np.clip(h[0] - half[0], 0, img.shape[1] - 2 * half[0])); y0 = int(np.clip(h[1] - half[1] * 0.85, 0, img.shape[0] - 2 * half[1]))
    crop = cv2.resize(img[y0:y0 + 2 * half[1], x0:x0 + 2 * half[0]], None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    P = lambda p: (int((p[0] - x0) * scale), int((p[1] - y0) * scale))
    for side, col in (("L" if near == "R" else "R", (255, 150, 30)), (near, (40, 40, 235))):
        ls = side.lower()
        for chain in ((f"{ls}_shoulder", f"{ls}_hip", f"{ls}_knee", f"{ls}_ankle", f"{ls}_heel", f"{ls}_toe", f"{ls}_ankle"),):
            pts = [P(uv[i, LM[k]]) for k in chain if np.isfinite(uv[i, LM[k]]).all()]
            for a, b in zip(pts[:-1], pts[1:]):
                cv2.line(crop, a, b, col, 4, cv2.LINE_AA)
    m = model_pose(model, uv[i, LM[f"{stance.lower()}_ankle"]], seg_lengths_px(uv, near), sgn)
    segs = [("ankle_s", "knee_s"), ("knee_s", "hip"), ("hip", "shoulder"), ("hip", "knee_o")]
    if "ankle_o" in m:
        segs.append(("knee_o", "ankle_o"))
    ov = crop.copy()
    for a, b in segs:
        cv2.line(ov, P(m[a]), P(m[b]), (0, 0, 0), 11, cv2.LINE_AA)
        cv2.line(ov, P(m[a]), P(m[b]), (255, 255, 255), 7, cv2.LINE_AA)
    for k in m:
        cv2.circle(ov, P(m[k]), 7, (255, 255, 255), -1, cv2.LINE_AA)
    crop = cv2.addWeighted(ov, 0.75, crop, 0.25, 0)
    cv2.rectangle(crop, (0, 0), (crop.shape[1], 44), (0, 0, 0), -1)
    cv2.putText(crop, title, (10, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return out


def model_figures(clip: Path, z: dict, info: dict, rows: list[dict], outdir: Path, tag: str) -> list[Path]:
    """Touchdown and toe-off frames nearest the middle of the clip with the published model overlaid.
    Touchdown: a touchdown where the swing leg faces the camera (the swing leg is what the figure 4 is about).
    Toe-off: a toe-off of the near leg."""
    T = np.asarray(z["t"], float); mid = (T[0] + T[-1]) / 2
    out = []
    td = [r for r in rows if r["swing_view"] == "near" and np.isfinite(r.get("swing_thigh_td_deg", math.nan))]
    if td:
        r = min(td, key=lambda r: abs(r["t_td_s"] - mid))
        out.append(compare_figure(clip, z, info, r["frame_td"], r["foot"], MODEL_TD, outdir / f"model_td_{tag}.jpg",
                                  "touchdown  |  white = world-class sprinter (avg)"))
    to = [r for r in rows if r["stance_view"] == "near" and np.isfinite(r.get("knee_to_deg", math.nan))]
    if to:
        r = min(to, key=lambda r: abs(r["t_td_s"] - mid))
        out.append(compare_figure(clip, z, info, r["frame_to"], r["foot"], MODEL_TO, outdir / f"model_to_{tag}.jpg",
                                  "toe-off  |  white = world-class sprinter (avg)"))
    return out
