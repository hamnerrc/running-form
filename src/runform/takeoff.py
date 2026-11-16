"""Long-jump takeoff analysis (rep type `takeoff`): the last steps of the approach and the takeoff itself.

Standard terms used (see 02-reference-sprint-longjump.md for the professional values):
- takeoff contact: the takeoff foot's ground contact on the board. The contact before it is the penultimate
  contact. Last step = penultimate contact → takeoff contact; penultimate step = the step before that.
  (Skilled jumpers: penultimate step longer, last step shorter.)
- approach speed: horizontal CM speed over the last two steps before the takeoff touchdown. (Professionals are
  usually measured 11–6 m before the board; our camera sees the last ~8 m, so ours is a little later.)
- touchdown (plant) angle: angle between the ground and the line from the CM to the takeoff ankle at touchdown,
  measured on the side facing the pit (≈ 58–62° in skilled jumpers).
- takeoff angle: direction of the CM velocity at toe-off above horizontal (≈ 18–24°).
- horizontal velocity loss: CM horizontal speed at takeoff touchdown minus at toe-off.
- CM lowering: how much lower the CM is at the takeoff touchdown than at the touchdown of the contact two
  before it (skilled jumpers lower the CM over the last two steps, mostly on the penultimate step).
- toe-to-board distance: how far behind the board's front edge the takeoff toe lands (+ = behind the board,
  distance lost; − = foul). Effective distance = official distance + toe-to-board distance.
"""
from __future__ import annotations

import math

import numpy as np

from .config import G
from .events import Contact, foot_low_point

MPH = 0.44704         # m/s per mph
FT = 0.3048           # m per ft


def equation_distance_ft(speed_mph: float, height_in: float) -> float:
    """Athlete A's own conversion from approach speed to long-jump distance (assumes human-optimal form, so it
    is a ceiling: real form needs slightly more speed for the same distance)."""
    return 1.57 * speed_mph - 8.87 + 0.18 * (height_in - 70.0)


def equation_speed_mph(distance_ft: float, height_in: float) -> float:
    """Inverse of equation_distance_ft: approach speed (mph) needed for a distance."""
    return (distance_ft + 8.87 - 0.18 * (height_in - 70.0)) / 1.57


def ft_in(m: float) -> str:
    """Metres → feet and inches, e.g. 6.63 → 21'9\"."""
    if not np.isfinite(m):
        return "—"
    inches = m / 0.0254
    f, i = divmod(round(inches), 12)
    return f"{int(f)}'{int(i)}\""


def find_takeoff(contacts: list[Contact], com: np.ndarray, t: np.ndarray, fs: float,
                 min_flight_s: float = 0.25) -> int | None:
    """Index (in time-sorted complete contacts) of the takeoff contact: the contact followed by the longest
    airborne gap (≥ min_flight_s, or to the end of the clip) with the CM rising at toe-off."""
    cs = sorted([c for c in contacts if c.complete], key=lambda c: c.td)
    best, best_gap = None, 0.0
    vy = np.gradient(com[:, 1], 1 / fs)
    for k, c in enumerate(cs):
        nxt = cs[k + 1].t_td if k + 1 < len(cs) else t[-1]
        gap = nxt - c.t_to
        if gap >= min_flight_s and gap > best_gap and np.isfinite(vy[c.to]) and vy[c.to] > 0.5:
            best, best_gap = k, gap
    return best


def _at(x: np.ndarray, i: int) -> float:
    return float(x[i]) if 0 <= i < len(x) and np.isfinite(x[i]) else math.nan


def takeoff_metrics(t: np.ndarray, js: dict, com: np.ndarray, contacts: list[Contact], *, fs: float,
                    height_m: float, board_x: float | None = None, official_m: float | None = None,
                    best_sprint_ms: float | None = None, win: int = 3) -> dict:
    """All takeoff numbers for one jump. Positions are sagittal metres (X toward the pit, Y up).
    board_x: sagittal X of the board's front edge (from calib), official_m: tape-measured official distance."""
    cs = sorted([c for c in contacts if c.complete], key=lambda c: c.td)
    k = find_takeoff(cs, com, t, fs)
    if k is None:
        return {"error": "no takeoff found (no contact followed by ≥ 0.25 s of flight with the CM rising)"}
    tk = cs[k]
    s = tk.foot
    o = "L" if s == "R" else "R"
    vx = np.gradient(com[:, 0], 1 / fs)
    vy = np.gradient(com[:, 1], 1 / fs)
    sm = lambda x, i: float(np.nanmean(x[max(0, i - win // 2):i + win // 2 + 1]))   # ±1 sample average
    out: dict = {"takeoff_foot": s, "t_td_s": tk.t_td, "t_to_s": tk.t_to,
                 "takeoff_contact_ms": tk.tc * 1000, "event_unc_ms": 1000 / fs}

    # last steps (foot position = foot low point at mid-contact)
    mid = lambda c: (c.td + c.to) // 2
    pos = lambda c: float(foot_low_point(js, c.foot)[mid(c), 0])
    prev = cs[max(0, k - 3):k + 1]
    names = ["3rd_last", "penultimate", "last"][-(len(prev) - 1):] if len(prev) > 1 else []
    for nm, a, b in zip(names, prev[:-1], prev[1:]):
        out[f"{nm}_step_length_m"] = pos(b) - pos(a)
        out[f"{nm}_step_time_ms"] = (b.t_td - a.t_td) * 1000
        out[f"{nm}_step_speed_ms"] = (pos(b) - pos(a)) / (b.t_td - a.t_td)
    if k >= 1:
        out["contact_penultimate_ms"] = cs[k - 1].tc * 1000
    if k >= 2:
        out["contact_3rd_last_ms"] = cs[k - 2].tc * 1000
    if k >= 2:
        a = cs[k - 2]
        out["approach_speed_ms"] = float((com[tk.td, 0] - com[a.td, 0]) / (tk.t_td - a.t_td))
    elif k >= 1:
        a = cs[k - 1]
        out["approach_speed_ms"] = float((com[tk.td, 0] - com[a.td, 0]) / (tk.t_td - a.t_td))
    if "approach_speed_ms" in out:
        out["approach_speed_mph"] = out["approach_speed_ms"] / MPH
        h_in = height_m / 0.0254
        out["equation_distance_ft"] = equation_distance_ft(out["approach_speed_mph"], h_in)
        if best_sprint_ms:
            out["approach_pct_of_sprint"] = 100 * out["approach_speed_ms"] / best_sprint_ms
    if k >= 2:
        out["com_lowering_m"] = _at(com[:, 1], cs[k - 2].td) - _at(com[:, 1], tk.td)
        out["com_lowering_penultimate_m"] = _at(com[:, 1], cs[k - 2].td) - _at(com[:, 1], cs[k - 1].td)
    out["com_height_td_m"] = _at(com[:, 1], tk.td)
    out["com_height_to_m"] = _at(com[:, 1], tk.to)
    out["com_height_td_over_h"] = out["com_height_td_m"] / height_m

    # takeoff contact
    A = js[f"ankle_{s}"]
    d = A[tk.td] - com[tk.td]
    out["touchdown_angle_deg"] = float(np.degrees(np.arctan2(-d[1], d[0]))) if d[0] > 0 else math.nan
    out["foot_ahead_of_com_td_m"] = float(d[0])
    kf = np.asarray(js[f"knee_flex_{s}"], float)
    st = kf[tk.td:tk.to + 1]
    out["knee_flex_td_deg"] = _at(kf, tk.td)
    out["knee_flex_max_deg"] = float(np.nanmax(st)) if np.isfinite(st).mean() >= 0.7 else math.nan
    out["knee_flex_to_deg"] = _at(kf, tk.to)
    out["trunk_td_deg"] = _at(js["trunk_lean"], tk.td)
    out["trunk_to_deg"] = _at(js["trunk_lean"], tk.to)
    out["free_thigh_to_deg"] = _at(js[f"thigh_{o}"], tk.to)       # swing (free) leg knee drive at toe-off
    out["shin_td_deg"] = _at(js[f"shin_{s}"], tk.td)

    # CM velocity. At toe-off: fitted to the first ~50 ms of flight (x linear, y a parabola with known g),
    # which is far less noisy than differentiating at the instant of toe-off.
    vx_td = sm(vx, tk.td)
    vx_to, vy_to = sm(vx, tk.to), sm(vy, tk.to)
    nf = int(round(0.05 * fs))
    seg = slice(tk.to, min(len(t), tk.to + nf + 1))
    tt = t[seg] - t[tk.to]
    xs, ys = com[seg, 0], com[seg, 1]
    ok = np.isfinite(xs) & np.isfinite(ys)
    if ok.sum() >= 6:
        vx_to = float(np.polyfit(tt[ok], xs[ok], 1)[0])
        vy_to = float(np.polyfit(tt[ok], ys[ok] + 0.5 * G * tt[ok] ** 2, 1)[0])
        out["takeoff_velocity_method"] = f"flight fit, {ok.sum()} samples"
    out["vx_td_ms"], out["vx_to_ms"], out["vy_to_ms"] = vx_td, vx_to, vy_to
    out["vy_td_ms"] = sm(vy, tk.td)
    out["horizontal_velocity_loss_ms"] = vx_td - vx_to
    out["takeoff_speed_ms"] = math.hypot(vx_to, vy_to)
    out["takeoff_angle_deg"] = math.degrees(math.atan2(vy_to, vx_to))
    # CM flight: peak height gained, and the projectile range to the same CM height (comparison only —
    # the landing CM is lower, so the real flight distance is longer)
    out["com_rise_flight_m"] = vy_to ** 2 / (2 * G) if vy_to > 0 else math.nan
    out["flight_range_same_height_m"] = 2 * vx_to * vy_to / G if vy_to > 0 else math.nan

    # board
    if board_x is not None:
        toe = js[f"toe_{s}"]
        out["toe_to_board_m"] = float(board_x - toe[tk.td, 0])
        out["foul"] = bool(out["toe_to_board_m"] < 0)
    if official_m is not None:
        out["official_m"] = official_m
        out["official_ft"] = official_m / FT
        if "toe_to_board_m" in out:
            out["effective_m"] = official_m + max(0.0, out["toe_to_board_m"])
            out["effective_ft"] = out["effective_m"] / FT
    return out


TAKEOFF_KEYS = [
    "approach_speed_ms", "approach_speed_mph", "approach_pct_of_sprint", "equation_distance_ft",
    "3rd_last_step_length_m", "penultimate_step_length_m", "last_step_length_m",
    "penultimate_step_speed_ms", "last_step_speed_ms", "contact_3rd_last_ms", "contact_penultimate_ms",
    "takeoff_contact_ms", "com_lowering_m", "com_lowering_penultimate_m", "com_height_td_over_h",
    "touchdown_angle_deg", "foot_ahead_of_com_td_m", "knee_flex_td_deg", "knee_flex_max_deg", "knee_flex_to_deg",
    "trunk_td_deg", "trunk_to_deg", "free_thigh_to_deg",
    "vx_td_ms", "vx_to_ms", "vy_to_ms", "horizontal_velocity_loss_ms", "takeoff_speed_ms", "takeoff_angle_deg",
    "com_rise_flight_m", "toe_to_board_m", "official_m", "effective_m", "official_ft", "effective_ft",
]

TAKEOFF_PRETTY = {
    "approach_speed_ms": "Approach speed, last 2 steps (m/s)", "approach_speed_mph": "Approach speed (mph)",
    "approach_pct_of_sprint": "Approach speed as % of best flying sprint",
    "equation_distance_ft": "Distance predicted by the speed equation (ft, optimal form)",
    "3rd_last_step_length_m": "3rd-last step length (m)", "penultimate_step_length_m": "Penultimate step length (m)",
    "last_step_length_m": "Last step length (m)", "penultimate_step_speed_ms": "Penultimate step speed (m/s)",
    "last_step_speed_ms": "Last step speed (m/s)", "contact_3rd_last_ms": "3rd-last contact time (ms)",
    "contact_penultimate_ms": "Penultimate contact time (ms)", "takeoff_contact_ms": "Takeoff contact time (ms)",
    "com_lowering_m": "CM lowering over the last two steps (m)",
    "com_lowering_penultimate_m": "CM lowering on the penultimate step (m)",
    "com_height_td_over_h": "CM height at takeoff touchdown ÷ standing height",
    "touchdown_angle_deg": "Touchdown (plant) angle (°)", "foot_ahead_of_com_td_m": "Takeoff foot ahead of CM at touchdown (m)",
    "knee_flex_td_deg": "Takeoff knee flexion at touchdown (°)", "knee_flex_max_deg": "Takeoff knee max flexion (°)",
    "knee_flex_to_deg": "Takeoff knee flexion at toe-off (°)", "trunk_td_deg": "Trunk lean at touchdown (°, + = forward)",
    "trunk_to_deg": "Trunk lean at toe-off (°)", "free_thigh_to_deg": "Free-leg thigh angle at toe-off (knee drive, °)",
    "vx_td_ms": "Horizontal CM velocity at touchdown (m/s)", "vx_to_ms": "Horizontal CM velocity at toe-off (m/s)",
    "vy_to_ms": "Vertical CM velocity at toe-off (m/s)", "horizontal_velocity_loss_ms": "Horizontal velocity loss in takeoff (m/s)",
    "takeoff_speed_ms": "Takeoff speed (m/s)", "takeoff_angle_deg": "Takeoff angle (°)",
    "com_rise_flight_m": "CM rise after takeoff (m)", "toe_to_board_m": "Toe-to-board distance (m, + = behind board)",
    "official_m": "Official distance (m)", "effective_m": "Effective distance (m)",
    "official_ft": "Official distance (ft)", "effective_ft": "Effective distance (ft)",
}
