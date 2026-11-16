"""Per-step metrics (README §5.10, formulas in 04-analysis-method.md). Mass cancels everywhere.

A "step" starts at one foot's touchdown and ends at the next touchdown of the other foot.
Each row carries a confidence label: near-side leg = high, far-side = low (occlusion), and is downgraded
when the event edges weren't fully observed or the segment-length check fails around the event.
"""
from __future__ import annotations

import math

import numpy as np

from .config import G, ZONE_LENGTH_M
from .events import Contact, foot_low_point


# ---------- spring-mass model (Morin et al. 2005), per kg ----------

def spring_mass(tc: float, tf: float, v: float, leg_length: float) -> dict:
    """Vertical & leg stiffness in N/m per kg body mass. v = running speed (m/s); v=0 → leg stiffness not defined."""
    if not (tc > 0 and tf >= 0):
        return {"Fmax_per_kg": math.nan, "Fmax_bw": math.nan, "dy_m": math.nan, "k_vert_per_kg": math.nan, "dL_m": math.nan, "k_leg_per_kg": math.nan}
    F = G * (math.pi / 2) * (tf / tc + 1)
    # CM drop TD→midstance. Integrating a(t) = (F/m)·sin(πt/tc) − g with symmetric stance gives
    # Δy = (F/m)·tc²/π² − g·tc²/8 (Morin et al. 2005 write it as −(F/m)tc²/π² + g tc²/8, downward negative).
    dy = F * tc ** 2 / math.pi ** 2 - G * tc ** 2 / 8
    k_vert = F / dy if dy > 0 else math.nan
    if v > 0:
        half = v * tc / 2
        dL = leg_length - math.sqrt(max(leg_length ** 2 - half ** 2, 0.0)) + dy
        k_leg = F / dL if dL > 0 else math.nan
    else:
        dL, k_leg = math.nan, math.nan
    return {"Fmax_per_kg": F, "Fmax_bw": F / G, "dy_m": dy, "k_vert_per_kg": k_vert, "dL_m": dL, "k_leg_per_kg": k_leg}


# ---------- zone speed ----------

def zone_speed(t: np.ndarray, x_hip_world: np.ndarray, dir_sign: int) -> dict:
    """Speed from the hip crossing the entry line to crossing the exit line (README §3, 04 'Speed').
    x_hip_world: world x (not direction-flipped). Linear interpolation between frames."""
    def cross(xline):
        d = x_hip_world - xline
        idx = np.nonzero(np.isfinite(d[:-1]) & np.isfinite(d[1:]) & (np.sign(d[:-1]) != np.sign(d[1:])))[0]
        if not len(idx):
            return math.nan
        i = idx[0]
        return float(t[i] + (t[i + 1] - t[i]) * (-d[i]) / (d[i + 1] - d[i]))
    entry, exit_ = (0.0, ZONE_LENGTH_M) if dir_sign > 0 else (ZONE_LENGTH_M, 0.0)
    t0, t1 = cross(entry), cross(exit_)
    dt = t1 - t0
    fs = 1 / np.median(np.diff(t))
    v = ZONE_LENGTH_M / dt if dt > 0 else math.nan
    # ±1 frame at each crossing → ±2/fs on the interval (worst case)
    dv = v * (2 / fs) / dt if dt > 0 else math.nan
    return {"zone_time_s": dt, "zone_speed_ms": v, "zone_speed_unc_ms": dv, "t_entry": t0, "t_exit": t1}


# ---------- per-step table ----------

KNEE_JUMP_DEG_S = 2000.0

def _at(series: np.ndarray, i: int) -> float:
    return float(series[i]) if 0 <= i < len(series) and np.isfinite(series[i]) else math.nan


def step_table(t: np.ndarray, js: dict, com: np.ndarray, contacts: list[Contact], *, fs: float, near: str,
               speed: float, leg_length: float, height: float, overground: bool = True,
               belt_speed: float | None = None, seg_flags: dict | None = None,
               glitch: dict | None = None) -> list[dict]:
    """glitch: side → bool mask of samples where that leg's tracking is implausible (segment length off by
    >15%, typically the knee landmark jumping when the legs cross or a white shoe over white paint).
    That leg's joint angles are set to NaN there, so a glitch gives a missing value, not a wrong one."""
    js_raw = js
    if glitch:
        js = dict(js)
        for side, m in glitch.items():
            for key in (f"shin_{side}", f"thigh_{side}", f"knee_flex_{side}", f"hip_flex_{side}"):
                if key in js:
                    a = np.array(js[key], float); a[m[:len(a)]] = np.nan; js[key] = a
    cs = sorted([c for c in contacts if c.complete], key=lambda c: c.td)
    hip = js["hip_mid"]
    vcom = np.gradient(com[:, 0], 1 / fs)
    vhip = np.gradient(hip[:, 0], 1 / fs)
    frame_unc_ms = 1000 / fs
    rows = []
    for k, c in enumerate(cs):
        s = c.foot
        nxt = next((d for d in cs[k + 1:] if d.foot != s), None)
        same_next = next((d for d in cs[k + 1:] if d.foot == s), None)
        low = foot_low_point(js, s)
        td, to = c.td, c.to
        row = {"foot": s, "side_view": "near" if s == near else "far", "t_td_s": c.t_td, "t_to_s": c.t_to,
               "contact_ms": c.tc * 1000, "event_unc_ms": frame_unc_ms}

        # flight / step
        if nxt is not None:
            tf = nxt.t_td - c.t_to
            st = nxt.t_td - c.t_td
            row.update(flight_ms=tf * 1000, step_time_ms=st * 1000, step_rate_hz=1 / st,
                       duty_factor=c.tc / (c.tc + tf) if tf > 0 else math.nan)
            if overground:
                mid = lambda cc: slice(cc.td + (cc.to - cc.td) // 3, cc.to - (cc.to - cc.td) // 3 + 1)
                x0 = np.nanmean(low[mid(c), 0])
                x1 = np.nanmean(foot_low_point(js, nxt.foot)[mid(nxt), 0])
                row["step_length_m"] = float(x1 - x0)
            elif belt_speed:
                row["step_length_m"] = belt_speed * st
            else:
                row["step_length_m"] = math.nan
            row["step_length_over_leg"] = row["step_length_m"] / leg_length
        else:
            tf = math.nan

        # touchdown geometry
        row["foot_ahead_of_hip_td_m"] = _at(low[:, 0], td) - _at(hip[:, 0], td)
        row["foot_ahead_of_com_td_m"] = _at(low[:, 0], td) - _at(com[:, 0], td)
        ax = np.gradient(js[f"ankle_{s}"][:, 0], 1 / fs)
        row["foot_speed_td_ms"] = _at(ax, td) - (0.0 if overground else -(belt_speed or 0.0))  # − = sweeping back
        row["foot_speed_rel_hip_td_ms"] = _at(ax, td) - _at(vhip, td)
        # Knee-landmark jumps in stance (the swing knee passing the stance knee): knee flexion changing faster
        # than 2000°/s inside stance is not physiological (stance peaks are a few hundred °/s). From the first
        # such sample to toe-off+3, this leg's angles are treated as missing for this step.
        jr = js
        kseg = np.asarray(js_raw[f"knee_flex_{s}"][td:to + 4], float)
        if len(kseg) >= 3:
            on = list(np.nonzero(np.abs(np.gradient(kseg)) * fs > KNEE_JUMP_DEG_S)[0])
            if glitch and s in glitch:
                on += list(np.nonzero(glitch[s][td:to + 4])[0])
            on = sorted(on)
            if len(on):
                g = td + max(0, int(on[0]) - 1)
                jr = dict(js)
                for key in (f"shin_{s}", f"thigh_{s}", f"knee_flex_{s}"):
                    a = np.array(js[key], float); a[g:to + 4] = np.nan; jr[key] = a
                row["knee_jump_masked_from_ms"] = (g - td) * 1000 / fs
        for nm, key in (("shin", f"shin_{s}"), ("thigh", f"thigh_{s}"), ("knee_flex", f"knee_flex_{s}"), ("trunk", "trunk_lean")):
            row[f"{nm}_td_deg"] = _at(jr[key], td)
            row[f"{nm}_to_deg"] = _at(jr[key], to)
        stance = slice(td, to + 1)
        # Glitched samples are already NaN (see `glitch`); a 5-sample running median removes single-frame noise.
        kf = jr[f"knee_flex_{s}"][stance]
        if len(kf) >= 5:
            kf = np.array([np.nanmedian(kf[max(0, i - 2):i + 3]) for i in range(len(kf))])
        row["knee_flex_max_stance_deg"] = float(np.nanmax(kf)) if np.isfinite(kf).mean() >= 0.7 else math.nan
        if glitch and s in glitch:
            row["glitch_frac_stance"] = float(np.mean(glitch[s][stance]))

        # swing of the same leg: max knee lift and thigh range over its full stride
        if same_next is not None:
            swing = slice(to, same_next.td + 1)
            stride = slice(td, same_next.td + 1)
            row["thigh_max_swing_deg"] = float(np.nanmax(js[f"thigh_{s}"][swing]))
            row["thigh_rom_deg"] = float(np.nanmax(js[f"thigh_{s}"][stride]) - np.nanmin(js[f"thigh_{s}"][stride]))
            row["knee_height_max_m"] = float(np.nanmax(js[f"knee_{s}"][swing, 1]))
            # heel recovery: how far the knee folds during swing (standard: max knee flexion in swing)
            ks = js[f"knee_flex_{s}"][swing]
            row["knee_flex_max_swing_deg"] = float(np.nanmax(ks)) if np.isfinite(ks).mean() >= 0.7 else math.nan
            row.update(arm_stride(js, s, stride, fs))
        row["foot_angle_td_deg"] = _at(js_raw.get(f"foot_angle_{s}", np.full(len(t), np.nan)), td)
        fa = row["foot_angle_td_deg"]
        row["foot_strike"] = ("rearfoot" if fa > FOOT_STRIKE_DEG else "forefoot" if fa < -FOOT_STRIKE_DEG
                              else "midfoot") if np.isfinite(fa) else ""
        # CM: vertical oscillation over the step, braking in the first half of stance
        if nxt is not None:
            step = slice(td, nxt.td + 1)
            osc = float(np.nanmax(com[step, 1]) - np.nanmin(com[step, 1]))
            row["com_osc_m"] = osc
            row["com_osc_over_height"] = osc / height
        half = slice(td, td + max(1, (to - td) // 2) + 1)
        v_td = _at(vcom, td)
        vmin = float(np.nanmin(vcom[half]))
        row["braking_dv_ms"] = v_td - vmin
        row["braking_pct"] = 100 * (v_td - vmin) / v_td if v_td and v_td > 0 else math.nan
        row["hip_braking_dv_ms"] = _at(vhip, td) - float(np.nanmin(vhip[half]))
        row["hip_osc_m"] = float(np.nanmax(hip[stance, 1]) - np.nanmin(hip[stance, 1]))

        # spring-mass
        if np.isfinite(tf):
            row.update(spring_mass(c.tc, tf, speed, leg_length))

        # confidence
        conf = "high" if s == near else "low"
        if seg_flags is not None:
            fl = seg_flags.get(s)
            if fl is not None and np.nanmean(fl[max(0, td - 2):to + 3]) > 0.5:
                conf = "low" if conf == "high" else "very low"
                row["seg_flag"] = True
        row["confidence"] = conf
        rows.append(row)
    return rows


# ---------- arm action ----------

FOOT_STRIKE_DEG = 5.0    # foot angle at touchdown beyond ±5° → rearfoot / forefoot strike, else midfoot
ARM_LEN_TOL = 0.25       # arm frames whose upper-arm or forearm length is >25% off the rep median are dropped


def arm_masks(js: dict) -> dict:
    """side → bool mask of implausible arm frames (no standing reference for arms: compare with the rep median)."""
    out = {}
    for s in ("L", "R"):
        if f"upper_arm_len_{s}" not in js:
            continue
        bad = np.zeros(len(js[f"upper_arm_len_{s}"]), bool)
        for k in (f"upper_arm_len_{s}", f"forearm_len_{s}"):
            L = np.asarray(js[k], float)
            med = np.nanmedian(L)
            bad |= ~np.isfinite(L) | (np.abs(L / med - 1) > ARM_LEN_TOL)
        out[s] = bad
    return out


def arm_stride(js: dict, s: str, stride: slice, fs: float, min_valid: float = 0.7) -> dict:
    """Arm action of the same-side arm over one stride of leg `s` (touchdown → next touchdown of that foot).
    Shoulder angle: + = upper arm in front of the trunk line, − = behind. Elbow: included angle.
    Hand height is wrist height relative to the shoulder (− = below); hand behind hip is how far the wrist
    passes behind the hip line on the backswing. Arm–leg timing: time from the arm's furthest-back position to
    the same-side thigh's furthest-forward position (opposite arm and leg move together, so ≈ 0 is in sync)."""
    if f"shoulder_{s}" not in js:
        return {}
    sh = np.array(js[f"shoulder_{s}"][stride], float)
    el = np.array(js[f"elbow_{s}"][stride], float)
    bad = arm_masks(js).get(s)
    if bad is not None:
        sh[bad[stride]] = np.nan; el[bad[stride]] = np.nan
    if np.isfinite(sh).mean() < min_valid:
        return {}
    i_f, i_b = int(np.nanargmax(sh)), int(np.nanargmin(sh))
    o = stride.start
    W, S = js[f"wrist_{s}"], js[f"shoulder_pt_{s}"]
    hip = js["hip_mid"]
    th = np.array(js[f"thigh_{s}"][stride], float)
    out = {"shoulder_flex_max_deg": float(sh[i_f]), "shoulder_ext_max_deg": float(-sh[i_b]),
           "shoulder_rom_deg": float(sh[i_f] - sh[i_b]),
           "elbow_front_deg": float(el[i_f]), "elbow_back_deg": float(el[i_b]),
           "elbow_min_deg": float(np.nanmin(el)), "elbow_max_deg": float(np.nanmax(el)),
           "elbow_rom_deg": float(np.nanmax(el) - np.nanmin(el)),
           "hand_height_front_m": float(W[o + i_f, 1] - S[o + i_f, 1]),
           "hand_behind_hip_m": float(hip[o + i_b, 0] - W[o + i_b, 0])}
    if np.isfinite(th).mean() >= min_valid:
        out["arm_leg_timing_ms"] = float((int(np.nanargmax(th)) - i_b) * 1000 / fs)
    return out


# ---------- pogo ----------

def pogo_table(contacts: list[Contact], *, single: str | None = None, tol_s: float = 0.03) -> list[dict]:
    """Pogo hops: contact, flight, h = g·tf²/8, RSI = h/tc, vertical stiffness (v=0).
    Double-leg: a hop's contact = union of overlapping L/R contacts. Single-leg: that foot only."""
    cs = [c for c in contacts if c.complete and (single is None or c.foot == single)]
    cs.sort(key=lambda c: c.t_td)
    hops = []
    for c in cs:
        if single is None and hops and c.t_td <= hops[-1][1] + tol_s:
            hops[-1] = (min(hops[-1][0], c.t_td), max(hops[-1][1], c.t_to))
        else:
            hops.append((c.t_td, c.t_to))
    rows = []
    for (a0, a1), (b0, _) in zip(hops[:-1], hops[1:]):
        tc, tf = a1 - a0, b0 - a1
        h = G * tf ** 2 / 8
        sm = spring_mass(tc, tf, 0.0, 1.0)
        rows.append({"contact_ms": tc * 1000, "flight_ms": tf * 1000, "jump_height_m": h, "rsi": h / tc,
                     "Fmax_per_kg": sm["Fmax_per_kg"], "Fmax_bw": sm["Fmax_bw"],
                     "k_vert_per_kg": sm["k_vert_per_kg"], "leg": single or "both"})
    return rows


def add_absolute(rows: list[dict], mass_kg: float | None) -> None:
    """With body mass (measurements.yaml body_mass_kg), per-kg values → newtons and kN/m. Mass is a pure scale
    factor here: it adds no information about technique, only units comparable to force-plate literature."""
    if not mass_kg:
        return
    for r in rows:
        if "Fmax_per_kg" in r:
            r["Fmax_N"] = r["Fmax_per_kg"] * mass_kg
        for k in ("k_vert", "k_leg"):
            if f"{k}_per_kg" in r:
                r[f"{k}_kN_m"] = r[f"{k}_per_kg"] * mass_kg / 1000


def summarize(rows: list[dict], keys: list[str]) -> dict:
    """mean ± SD and n for each key (finite values only)."""
    out = {}
    for k in keys:
        v = np.array([r.get(k, math.nan) for r in rows], float)
        v = v[np.isfinite(v)]
        out[k] = {"mean": float(v.mean()) if len(v) else math.nan,
                  "sd": float(v.std(ddof=1)) if len(v) > 1 else math.nan, "n": int(len(v))}
    return out
