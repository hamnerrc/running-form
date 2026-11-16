"""Stages 5–10 for one rep: filter → sagittal metres → angles/COM → events → per-step metrics.

Writes results/<date>/work/analysis/<athlete>_<clip>.npz (series for figures) and returns the step rows.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from . import calib as calib_mod
from . import cleanup, events, filtering, kinematics, metrics, pose, takeoff
from .config import LM, WINTER_LENGTH_RATIOS
from .session import Body, Rep, Session

# "approach_sim" = full-speed run with long-jump approach control, no jump ("fly_control" in the 2026-11-15 data)
SPRINT_TYPES = ("fly", "fly_control", "approach_sim", "stride_75", "stride_90")
TAKEOFF_TYPES = ("takeoff",)          # full approach + takeoff into the pit (camera at the board, own homography)
RUN_TYPES = SPRINT_TYPES + ("mile_pace", "kick_pace")
POGO_TYPES = {"pogo_double": None, "pogo_right": "R", "pogo_left": "L"}


@dataclass
class RepResult:
    rep: Rep
    rows: list[dict]
    info: dict
    series_path: Path


def _fc_range(rep_type: str) -> tuple[float, float]:
    # README §5.5: expect ~10–15 Hz sprinting, ~6–10 Hz mile pace; residual analysis picks within a wider band
    return (6.0, 20.0) if rep_type in SPRINT_TYPES or rep_type.startswith("pogo") else (4.0, 14.0)


def scale_from_height(uv: np.ndarray, height_m: float) -> float:
    """Demo/no-homography fallback: m/px such that median tracked thigh+shank = Winter estimate from height."""
    segs = []
    for s in ("l", "r"):
        th = np.linalg.norm(uv[:, LM[f"{s}_knee"]] - uv[:, LM[f"{s}_hip"]], axis=-1)
        sh = np.linalg.norm(uv[:, LM[f"{s}_ankle"]] - uv[:, LM[f"{s}_knee"]], axis=-1)
        segs.append(th + sh)
    px = np.nanmedian(np.concatenate(segs))
    return (WINTER_LENGTH_RATIOS["thigh"] + WINTER_LENGTH_RATIOS["shank"]) * height_m / px


def _glitch_masks(js: dict, body: Body, tol_shank: float = 0.15, tol_thigh: tuple = (0.78, 1.15),
                  pad: int = 2) -> dict:
    """Per leg: samples where tracked shank is off by >15% or thigh outside 78–115% of the standing reference.
    (Thigh gets a lower floor because hip flexion foreshortens MediaPipe's thigh in normal running: ~0.87–0.95.)"""
    ref = getattr(body, "mp_ref_m", None) or {}
    out = {}
    for s in ("L", "R"):
        th = js[f"thigh_len_{s}"] / ref.get("thigh", body.thigh_m[s])
        sh = js[f"shank_len_{s}"] / ref.get("shank", body.shank_m[s])
        bad = (np.abs(sh - 1) > tol_shank) | (th < tol_thigh[0]) | (th > tol_thigh[1])
        bad &= np.isfinite(th) & np.isfinite(sh)
        if pad:
            bad = np.convolve(bad.astype(float), np.ones(2 * pad + 1), "same") > 0
        out[s] = bad
    return out


def merge_tape(d: dict, tape_npz: Path | None, near: str, min_rate: float = 0.5) -> dict:
    """Use tape-marker positions for near-side joints where detected (README §5.4)."""
    if not tape_npz or not tape_npz.exists():
        return {}
    tp = dict(np.load(tape_npz))
    used = {}
    for joint in ("ankle", "knee", "hip", "shoulder"):
        key = f"{near}_{joint}"
        if key not in tp:
            continue
        tuv = tp[key]
        det = np.isfinite(tuv).all(1)
        rate = float(det.mean())
        if rate >= min_rate:
            j = LM[f"{near.lower()}_{joint}"]
            d["uv"][det, j] = tuv[det]
            d["vis"][det, j] = 1.0
        used[joint] = rate
    return used


def analyze_rep(rep: Rep, pose_npz: Path, body: Body, out_dir: Path, *, calib: calib_mod.Calib | None = None,
                m_per_px: float | None = None, overground: bool = True, belt_speed: float | None = None,
                override: dict | None = None, tape_npz: Path | None = None,
                body_mass_kg: float | None = None, board_x_world: float | None = None,
                best_sprint_ms: float | None = None) -> RepResult:
    d, clean_rep = cleanup.clean(pose.load(pose_npz), height_m=body.height_m)
    # camera on the runner's right when running → (field setup); a pit camera can be on either side, so a rep
    # line may set `near_side: R|L` explicitly (session.yaml)
    exp_near = rep.extra.get("near_side") or ("R" if rep.dir_sign > 0 else "L")
    tape_used = merge_tape(d, tape_npz, exp_near)   # tape positions are unambiguous: applied after swap-fixing
    sm = filtering.smooth_track(d["t"], d["uv"], d["ok"], d["vis"],
                                fc_range=_fc_range("fly" if rep.type in TAKEOFF_TYPES else rep.type))
    t, fs, uv = sm["t"], sm["fs"], sm["uv"]

    is_takeoff = rep.type in TAKEOFF_TYPES
    if calib is not None:
        mpp = calib.m_per_px(board_x_world - 2.0 * rep.dir_sign) if (is_takeoff and board_x_world is not None) else calib.m_per_px()
        sag = kinematics.Sagittal(rep.dir_sign, mpp, calib=calib)
        scale_src = f"homography (setup {calib.setup}, holdout {calib.holdout_err_m})"
    else:
        s = m_per_px or scale_from_height(uv, body.height_m)
        sag = kinematics.Sagittal(rep.dir_sign, s, ground=kinematics.fit_ground_line(uv))
        scale_src = "given m/px" if m_per_px else "estimated from height (Winter thigh+shank) — demo only"
    P = sag.xy(uv)
    js = kinematics.joint_series(P)
    com = kinematics.center_of_mass(P)
    near = kinematics.near_side(d["vis"], d["world"], rep.dir_sign)
    if near.get("expected") != exp_near:
        near["expected"] = exp_near
        near["agree"] = near.get("detected") == exp_near
    seg = kinematics.segment_check(js, body)
    seg_flags = {s: np.maximum(seg[f"thigh_{s}"]["flag_mask"], seg[f"shank_{s}"]["flag_mask"]).astype(float)
                 for s in ("L", "R")}

    # speed: zone timing when calibrated, else hip velocity
    if calib is not None and overground and not is_takeoff:
        zs = metrics.zone_speed(t, rep.dir_sign * js["hip_mid"][:, 0], rep.dir_sign)
        speed = zs["zone_speed_ms"]
    else:
        zs = {}
        speed = belt_speed if not overground else float(np.nanmedian(np.gradient(js["hip_mid"][:, 0], 1 / fs)))

    contacts, diag = [], {}
    t_clip = np.interp(np.arange(int(d["frame"].max()) + 1), d["frame"], d["t"])
    for side in ("L", "R"):
        if override and side in override:
            contacts += events.from_override(t_clip, t, side, override[side])
            diag[side] = {"source": "override"}
        else:
            cs, dg = events.detect(t, js, side, fs, overground=overground,
                                   runner_speed=speed if overground and np.isfinite(speed) else None,
                                   min_contact_s=max(0.04, 2.5 / fs))
            contacts += cs
            diag[side] = {"source": "auto", "offset_m": dg.get("offset_m"), "threshold_m": dg.get("threshold_m"),
                          "n_contacts": len(cs), "n_complete": sum(c.complete for c in cs)}

    tk = None
    if is_takeoff:
        tk = takeoff.takeoff_metrics(t, js, com, contacts, fs=fs, height_m=body.height_m,
                                     board_x=(rep.dir_sign * board_x_world) if board_x_world is not None else None,
                                     official_m=rep.extra.get("official_m"), best_sprint_ms=best_sprint_ms)
        tk.update({"athlete": rep.athlete, "rep": rep.name, "type": rep.type, "direction": rep.direction or "",
                   "jump_notes": rep.notes, **{k: v for k, v in rep.extra.items() if k != "official_m"}})
        speed = tk.get("approach_speed_ms", speed)
    if rep.type in POGO_TYPES:
        rows = metrics.pogo_table(contacts, single=POGO_TYPES[rep.type])
    else:
        sp = speed if np.isfinite(speed) else 0.0
        rows = metrics.step_table(t, js, com, contacts, fs=fs, near=exp_near, speed=sp,
                                  leg_length=body.leg_length_m, height=body.height_m, overground=overground,
                                  belt_speed=belt_speed, seg_flags=seg_flags, glitch=_glitch_masks(js, body))
    if tk and "t_td_s" in tk:      # keep the approach running steps only (not the takeoff contact or landing)
        rows = [r for r in rows if r["t_td_s"] < tk["t_td_s"] - 1e-6]
        for r in rows:
            r["steps_before_takeoff"] = sum(1 for q in rows if q["t_td_s"] > r["t_td_s"]) + 1
    metrics.add_absolute(rows, body_mass_kg)
    for r in rows:
        r.update({"athlete": rep.athlete, "rep": rep.name, "type": rep.type, "direction": rep.direction or "",
                  "speed_ms": speed, "anthropometrics": body.source,
                  # a ±1-frame touchdown error moves the hips by speed/fs (tests/test_core.py)
                  "foot_ahead_unc_m": (speed / fs) if np.isfinite(speed) else math.nan})

    cut = sm["cutoffs"]
    key_joints = {"hip": (LM["l_hip"], LM["r_hip"]), "knee": (LM["l_knee"], LM["r_knee"]),
                  "ankle": (LM["l_ankle"], LM["r_ankle"]), "toe": (LM["l_toe"], LM["r_toe"])}
    cut_report = {name: {"used_hz": [round(cut[(j, ax)][0], 1) for j in js_ for ax in (0, 1)],
                         "residual_raw_hz": [round(cut[(j, ax)][1], 1) if np.isfinite(cut[(j, ax)][1]) else None
                                             for j in js_ for ax in (0, 1)]}
                  for name, js_ in key_joints.items()}
    info = {
        "rep": rep.name, "athlete": rep.athlete, "type": rep.type, "direction": rep.direction,
        "fps": fs, "frames_tracked": int(len(d["t"])), "detect_rate": float(d["ok"].mean()),
        "scale_m_per_px": sag.m_per_px, "scale_source": scale_src, "speed_ms": speed, **zs,
        "near_side": near, "tape_detect_rate": tape_used, "cleanup": clean_rep,
        "segment_check": {k: {kk: vv for kk, vv in v.items() if kk != "flag_mask"} for k, v in seg.items()},
        "events": diag, "cutoffs_hz": cut_report, "n_rows": len(rows),
        "contacts": [{"foot": c.foot, "t_td": c.t_td, "t_to": c.t_to, "complete": c.complete,
                      "td_frame": int(d["frame"][np.argmin(np.abs(d["t"] - c.t_td))]),
                      "to_frame": int(d["frame"][np.argmin(np.abs(d["t"] - c.t_to))])} for c in contacts],
        "anthropometrics": body.source, "takeoff": tk,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    sp = out_dir / f"{rep.athlete}_{rep.name}.npz"
    np.savez_compressed(sp, t=t, P=P, com=com, uv=uv, orig_frame=d["frame"], orig_t=d["t"],
                        **{k: v for k, v in js.items() if isinstance(v, np.ndarray)})
    (out_dir / f"{rep.athlete}_{rep.name}.json").write_text(json.dumps(info, indent=2, default=_json_default))
    return RepResult(rep, rows, info, sp)


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, float) and math.isnan(o):
        return None
    return str(o)


def load_overrides(sess: Session) -> dict:
    p = sess.root / "events_override.yaml"
    return (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}
