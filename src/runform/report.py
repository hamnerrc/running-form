"""Stage 12 (data part): metrics CSV, summary tables, figures, QA sheets → results/<date>/.

This writes `report_<athlete>_data.md` — the measured numbers with uncertainty and data-quality notes.
The interpreted `report_<athlete>.md` (plain-language summary, reference comparisons, ranked recommendations)
is written afterwards by the analyst/agent from these numbers, per README §5.11–12.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import qa
from .metrics import summarize
from . import takeoff as tko

STEP_KEYS = [
    "contact_ms", "flight_ms", "step_time_ms", "step_rate_hz", "step_length_m", "step_length_over_leg", "duty_factor",
    "foot_ahead_of_hip_td_m", "foot_ahead_of_com_td_m", "foot_speed_td_ms", "foot_speed_rel_hip_td_ms",
    "shin_td_deg", "shin_to_deg", "thigh_td_deg", "thigh_to_deg", "knee_flex_td_deg", "knee_flex_to_deg",
    "knee_flex_max_stance_deg", "trunk_td_deg", "thigh_max_swing_deg", "thigh_rom_deg",
    "com_osc_m", "com_osc_over_height", "braking_dv_ms", "braking_pct", "Fmax_bw", "k_vert_per_kg", "k_leg_per_kg",
    "Fmax_N", "k_vert_kN_m", "k_leg_kN_m",
    "knee_flex_max_swing_deg", "foot_angle_td_deg",
    "shoulder_flex_max_deg", "shoulder_ext_max_deg", "shoulder_rom_deg", "elbow_front_deg", "elbow_back_deg",
    "elbow_min_deg", "elbow_max_deg", "elbow_rom_deg", "hand_height_front_m", "hand_behind_hip_m", "arm_leg_timing_ms",
]
POGO_KEYS = ["contact_ms", "flight_ms", "jump_height_m", "rsi", "Fmax_bw", "k_vert_per_kg", "k_vert_kN_m"]
PRETTY = {
    "contact_ms": "Contact time (ms)", "flight_ms": "Flight time (ms)", "step_time_ms": "Step time (ms)",
    "step_rate_hz": "Step rate (steps/s)", "step_length_m": "Step length (m)", "step_length_over_leg": "Step length ÷ leg length",
    "duty_factor": "Duty factor", "foot_ahead_of_hip_td_m": "Touchdown distance: foot ahead of hips (m)",
    "foot_ahead_of_com_td_m": "Touchdown distance: foot ahead of CM (m)", "foot_speed_td_ms": "Foot horiz. speed at TD (m/s, − = backward)",
    "foot_speed_rel_hip_td_ms": "Foot speed rel. hips at TD (m/s)", "shin_td_deg": "Shin angle at TD (°, + = ankle ahead)",
    "shin_to_deg": "Shin angle at TO (°)", "thigh_td_deg": "Thigh angle at TD (°)", "thigh_to_deg": "Thigh angle at TO (°)",
    "knee_flex_td_deg": "Knee flexion at TD (°)", "knee_flex_to_deg": "Knee flexion at TO (°)",
    "knee_flex_max_stance_deg": "Max knee flexion in stance (°)", "trunk_td_deg": "Trunk lean at TD (°)",
    "thigh_max_swing_deg": "Max thigh angle in swing (knee lift, °)", "thigh_rom_deg": "Thigh range of motion (°)",
    "com_osc_m": "CM vertical oscillation per step (m)", "com_osc_over_height": "CM oscillation ÷ height",
    "braking_dv_ms": "Braking: CM speed dip after TD (m/s)", "braking_pct": "Braking (% of speed)",
    "Fmax_bw": "Peak vertical force (× body weight, spring-mass est.)", "Fmax_N": "Peak vertical force (N, est.)",
    "k_vert_kN_m": "Vertical stiffness (kN/m)", "k_leg_kN_m": "Leg stiffness (kN/m)",
    "k_vert_per_kg": "Vertical stiffness (N/m/kg)", "k_leg_per_kg": "Leg stiffness (N/m/kg)",
    "jump_height_m": "Jump height (m)", "rsi": "RSI (m/s)",
    "knee_flex_max_swing_deg": "Max knee flexion in swing (heel recovery, °)",
    "foot_angle_td_deg": "Foot angle at TD (°, + = toes up / rearfoot)",
    "shoulder_flex_max_deg": "Arm swing forward: shoulder flexion (°)",
    "shoulder_ext_max_deg": "Arm swing back: shoulder extension (°)",
    "shoulder_rom_deg": "Shoulder range of motion (°)",
    "elbow_front_deg": "Elbow angle, arm at front (°)", "elbow_back_deg": "Elbow angle, arm at back (°)",
    "elbow_min_deg": "Elbow angle, min (°)", "elbow_max_deg": "Elbow angle, max (°)",
    "elbow_rom_deg": "Elbow range of motion (°)",
    "hand_height_front_m": "Hand height at front of swing, rel. shoulder (m)",
    "hand_behind_hip_m": "Hand behind hip at back of swing (m)",
    "arm_leg_timing_ms": "Arm–leg timing: arm furthest back → same-side knee furthest forward (ms)",
}


def _fmt(s: dict, key: str) -> str:
    m, sd, n = s["mean"], s["sd"], s["n"]
    if n == 0 or not np.isfinite(m):
        return "—"
    dec = 0 if key.endswith("_ms") or key.endswith("_kg") else 1 if key.endswith("_deg") or key == "braking_pct" else 3 if key in ("duty_factor", "com_osc_over_height") else 2
    sds = f" ± {sd:.{dec}f}" if np.isfinite(sd) else ""
    return f"{m:.{dec}f}{sds} (n={n})"


def summary_table(df: pd.DataFrame, group_cols: list[str], keys: list[str]) -> str:
    groups = list(df.groupby(group_cols, sort=False)) if len(df) else []
    if not groups:
        return "_no rows_\n"
    names = [" · ".join(str(x) for x in (g if isinstance(g, tuple) else (g,))) for g, _ in groups]
    lines = ["| metric | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for k in keys:
        if k not in df:
            continue
        cells = [_fmt(summarize(sub.to_dict("records"), [k])[k], k) for _, sub in groups]
        if all(c == "—" for c in cells):
            continue
        lines.append(f"| {PRETTY.get(k, k)} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def asymmetry_table(df: pd.DataFrame, keys: list[str]) -> str:
    """README §5.8: high-confidence values per side come from the reps where that side faced the camera."""
    near = df[df["side_view"] == "near"]
    if near.empty or near["foot"].nunique() < 2:
        return "_Asymmetry needs near-side data from both directions (→ reps give R, ← reps give L)._\n"
    lines = ["| metric | R (→ reps) | L (← reps) | R − L | % diff |", "|---|---|---|---|---|"]
    for k in keys:
        if k not in near:
            continue
        r = summarize(near[near.foot == "R"].to_dict("records"), [k])[k]
        l = summarize(near[near.foot == "L"].to_dict("records"), [k])[k]
        if r["n"] == 0 or l["n"] == 0:
            continue
        diff = r["mean"] - l["mean"]
        pct = 100 * diff / ((abs(r["mean"]) + abs(l["mean"])) / 2) if (r["mean"] or l["mean"]) else math.nan
        lines.append(f"| {PRETTY.get(k, k)} | {_fmt(r, k)} | {_fmt(l, k)} | {diff:+.3g} | {pct:+.1f}% |")
    return "\n".join(lines) + "\n"


def rep_figures(series_npz: Path, info: dict, fig_dir: Path) -> list[Path]:
    z = np.load(series_npz)
    t = z["t"]
    fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
    for s, c in (("L", "#1f77b4"), ("R", "#d62728")):
        conf = "near" if s == info["near_side"]["expected"] else "far (low confidence)"
        ax[0].plot(t, z[f"thigh_{s}"], c=c, label=f"{s} thigh ({conf})")
        ax[1].plot(t, z[f"shin_{s}"], c=c, label=f"{s} shin")
        ax[2].plot(t, z[f"knee_flex_{s}"], c=c, label=f"{s} knee flexion")
    ax[0].set_ylabel("thigh vs vertical (°)\n+ = knee ahead"); ax[1].set_ylabel("shin vs vertical (°)\n+ = ankle ahead")
    ax[2].set_ylabel("knee flexion (°)")
    ax[3].plot(t, z["com"][:, 1], c="k", label="CM height (segmental)")
    ax[3].plot(t, z["hip_mid"][:, 1], c="gray", ls="--", label="hip midpoint")
    ax[3].set_ylabel("height (m)"); ax[3].set_xlabel("time (s)")
    for c in info["contacts"]:
        col = "#1f77b4" if c["foot"] == "L" else "#d62728"
        for a in ax:
            a.axvspan(c["t_td"], c["t_to"], color=col, alpha=0.12 if c["complete"] else 0.05)
    for a in ax:
        a.grid(alpha=0.3); a.legend(loc="upper right", fontsize=8)
    ax[0].set_title(f"{info['athlete']} {info['rep']} ({info['type']}, {info['direction'] or ''}) — shaded = ground contact")
    fig.tight_layout()
    fig_dir.mkdir(parents=True, exist_ok=True)
    p = fig_dir / f"{info['athlete']}_{info['rep']}_traces.png"
    fig.savefig(p, dpi=110); plt.close(fig)
    return [p]


def step_chart(df: pd.DataFrame, athlete: str, fig_dir: Path) -> Path | None:
    if df.empty or "contact_ms" not in df:
        return None
    keys = [k for k in ("contact_ms", "flight_ms", "step_length_m", "step_rate_hz", "foot_ahead_of_hip_td_m", "shin_td_deg") if k in df]
    fig, axes = plt.subplots(len(keys), 1, figsize=(11, 2.2 * len(keys)), sharex=True)
    axes = np.atleast_1d(axes)
    x = np.arange(len(df))
    for a, k in zip(axes, keys):
        for foot, c in (("L", "#1f77b4"), ("R", "#d62728")):
            m = (df.foot == foot).to_numpy()
            near = (df.side_view == "near").to_numpy()
            a.scatter(x[m & near], df[k][m & near], c=c, s=30, label=f"{foot} near")
            a.scatter(x[m & ~near], df[k][m & ~near], facecolors="none", edgecolors=c, s=30, label=f"{foot} far")
        a.set_ylabel(PRETTY.get(k, k), fontsize=8); a.grid(alpha=0.3)
    reps = df["rep"].to_numpy()
    for i in range(1, len(reps)):
        if reps[i] != reps[i - 1]:
            for a in axes:
                a.axvline(i - 0.5, c="k", lw=0.6)
    axes[0].legend(fontsize=7, ncol=4); axes[-1].set_xlabel("step # (vertical lines separate reps; hollow = far side)")
    fig.tight_layout()
    p = fig_dir / f"{athlete}_steps.png"
    fig.savefig(p, dpi=110); plt.close(fig)
    return p


def qa_sheets(clip: Path, series_npz: Path, info: dict, qa_dir: Path, fig_dir: Path) -> None:
    z = np.load(series_npz)
    t, uv = z["t"], z["uv"]
    of, ot = z["orig_frame"], z["orig_t"]
    def uv_at(f):
        k = np.searchsorted(of, f)
        if k >= len(of) or of[k] != f:
            return None
        return uv[int(np.argmin(np.abs(t - ot[k])))]
    contacts = [c for c in info["contacts"] if c["complete"]]
    need = {c[k] + d for c in contacts for k in ("td_frame", "to_frame") for d in range(-3, 4)}
    fuv = {f: u for f in need if (u := uv_at(f)) is not None}
    qa.event_contact_sheet(clip, fuv, contacts, qa_dir / f"{info['athlete']}_{info['rep']}_events.jpg")
    # annotated stills: first complete near-side contact
    near = info["near_side"]["expected"]
    nc = [c for c in contacts if c["foot"] == near]
    if not nc:
        return
    c = nc[0]
    for kind, f in (("touchdown", c["td_frame"]), ("toe-off", c["to_frame"])):
        u = uv_at(f)
        if u is None:
            continue
        i = int(np.argmin(np.abs(t - ot[np.searchsorted(of, f)])))
        lines = [f"{info['athlete']} {info['rep']} {near} {kind} (frame {f})",
                 f"shin {z[f'shin_{near}'][i]:+.0f} deg  thigh {z[f'thigh_{near}'][i]:+.0f} deg",
                 f"knee flex {z[f'knee_flex_{near}'][i]:.0f} deg  trunk {z['trunk_lean'][i]:+.0f} deg"]
        qa.annotated_still(clip, f, u, lines, fig_dir / f"{info['athlete']}_{info['rep']}_{near}_{kind}.jpg")


def goal_table(rep_results: list, goal: dict | None, body) -> list[str]:
    """Zone speed of every sprint rep vs the long-jump goal, via the athlete's speed→distance equation."""
    sp = [(rr.rep, rr.info.get("zone_speed_ms"), rr.info.get("zone_speed_unc_ms")) for rr in rep_results
          if rr.rep.type in ("fly", "fly_control", "approach_sim") and rr.info.get("zone_speed_ms")]
    if not sp or body is None:
        return []
    h_in = body.height_m / 0.0254
    best = max(v for r, v, u in sp if r.type == "fly") if any(r.type == "fly" for r, v, u in sp) else None
    out = ["## Speed vs long-jump goal", "",
           "Distance from the athlete's equation: ft = 1.57 × approach mph − 8.87 + 0.18 × (height in − 70). "
           "It assumes optimal form, so treat it as a ceiling. It applies to *approach* speed: a flying sprint is "
           "faster than a real approach (approaches are typically 92–97% of top speed).", ""]
    g = (goal or {}).get("goal_long_jump_m")
    if g:
        need = tko.equation_speed_mph(g / tko.FT, h_in)
        out += [f"**Goal {tko.ft_in(g)} ({g:.2f} m) needs ≈ {need:.1f} mph ({need * tko.MPH:.2f} m/s) of approach speed.**", ""]
    out += ["| rep | type | zone speed (m/s) | mph | % of best flying sprint | equation distance |", "|---|---|---|---|---|---|"]
    for r, v, u in sp:
        mph = v / tko.MPH
        ft = tko.equation_distance_ft(mph, h_in)
        pct = f"{100 * v / best:.1f}%" if best else "—"
        out.append(f"| {r.name} | {r.type} | {v:.2f} ± {u:.2f} | {mph:.1f} ± {u / tko.MPH:.1f} | {pct} | "
                   f"{tko.ft_in(ft * tko.FT)} ± {1.57 * u / tko.MPH * 12:.0f} in |")
    return out + [""]


def takeoff_section(rep_results: list, results: Path, athlete: str) -> list[str]:
    tks = [rr.info["takeoff"] for rr in rep_results if rr.info.get("takeoff")]
    if not tks:
        return []
    pd.DataFrame(tks).to_csv(results / f"takeoff_{athlete}.csv", index=False)
    good = [t for t in tks if not t.get("error")]
    out = ["## Takeoffs", "", f"Per jump (`takeoff_{athlete}.csv`). Event timing ±1 frame "
           f"(±{1000 / 240:.0f} ms at 240 fps); touchdown velocity from a 3-sample CM derivative, toe-off velocity from a fit to the first 50 ms of flight (≈ ±0.1–0.2 m/s).", ""]
    for t in tks:
        if t.get("error"):
            out.append(f"- {t.get('rep')}: {t['error']}")
    if good:
        out += ["| metric | " + " | ".join(t["rep"] for t in good) + " |", "|---|" + "---|" * len(good)]
        for k in tko.TAKEOFF_KEYS:
            vals = [t.get(k) for t in good]
            if all(v is None or (isinstance(v, float) and not np.isfinite(v)) for v in vals):
                continue
            fmt = lambda v: "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else (
                f"{v:.0f}" if k.endswith("_ms") and "speed" not in k and not k.startswith("v") and "velocity" not in k
                else f"{v:.1f}" if k.endswith("_deg") or k.endswith("_ft") or k.endswith("pct_of_sprint") or k.endswith("mph")
                else f"{v:.2f}")
            out.append(f"| {tko.TAKEOFF_PRETTY.get(k, k)} | " + " | ".join(fmt(v) for v in vals) + " |")
    return out + [""]


def write_athlete(results: Path, athlete: str, rep_results: list, extra_notes: list[str] | None = None,
                  goal: dict | None = None, body=None) -> Path:
    rows = [r for rr in rep_results for r in rr.rows]
    df = pd.DataFrame(rows)
    df.to_csv(results / f"metrics_{athlete}.csv", index=False)
    fig_dir, qa_dir = results / "figures", results / "qa"
    lines = [f"# {athlete}: measured data ({results.name})", "",
             "Auto-generated from the pipeline. Numbers only, no interpretation: see `report_" + athlete + ".md` for that.",
             "Mean ± SD across steps (n = steps). Event timing ±1 frame per event; contact/flight worst case ±2 frames.", ""]
    lines += ["## Data quality", "", "| rep | fps | tracked | detect | leg swaps fixed | near side (exp/det) | scale | speed (m/s) | cutoffs used (Hz) |",
              "|---|---|---|---|---|---|---|---|---|"]
    for rr in rep_results:
        i = rr.info
        ns = i["near_side"]
        cu = sorted({c for v in i["cutoffs_hz"].values() for c in v["used_hz"]})
        spd = i.get("zone_speed_ms", i.get("speed_ms"))
        unc = i.get("zone_speed_unc_ms")
        spd_s = f"{spd:.2f}" + (f" ± {unc:.2f}" if unc and np.isfinite(unc) else "") if spd is not None and np.isfinite(spd) else "—"
        lines.append(f"| {i['rep']} | {i['fps']:.0f} | {i['frames_tracked']} | {i['detect_rate']:.0%} | "
                     f"{i['cleanup']['leg_swap_rate']:.0%} of frames | {ns['expected']}/{ns['detected']}{'' if ns['agree'] else ' ⚠'} | "
                     f"{i['scale_m_per_px']*1000:.2f} mm/px | {spd_s} | {cu[0]:.1f}–{cu[-1]:.1f} |")
        rep_figures(rr.series_path, i, fig_dir)
    lines += ["", "Segment-length check (tracked vs reference, median error; share of frames off by >5%):", ""]
    for rr in rep_results:
        sc = rr.info["segment_check"]
        lines.append(f"- {rr.info['rep']}: " + ", ".join(
            f"{k} {v['median_err_pct']:+.0f}% ({v['frac_frames_over_5pct']:.0%})" for k, v in sc.items()))
    src = {rr.info["anthropometrics"] for rr in rep_results}
    lines += ["", f"Anthropometrics: {', '.join(sorted(src))}.", ""]
    if extra_notes:
        lines += ["## Notes", ""] + [f"- {n}" for n in extra_notes] + [""]
    run_df = df[~df["type"].astype(str).str.startswith("pogo")] if len(df) else df
    pogo_df = df[df["type"].astype(str).str.startswith("pogo")] if len(df) else df
    if len(run_df):
        lines += ["## By rep type, near-side leg only (high confidence)", "",
                  summary_table(run_df[run_df.side_view == "near"], ["type"], STEP_KEYS),
                  "## By rep", "", summary_table(run_df, ["rep", "side_view"], STEP_KEYS),
                  "## Right vs left (near-side values only)", "", asymmetry_table(run_df, STEP_KEYS)]
        sc = step_chart(run_df.reset_index(drop=True), athlete, fig_dir)
        if sc:
            lines += [f"![steps](figures/{sc.name})", ""]
    lines += goal_table(rep_results, goal, body)
    lines += takeoff_section(rep_results, results, athlete)
    if len(pogo_df):
        lines += ["## Pogo hops", "", summary_table(pogo_df, ["type"], POGO_KEYS)]
    p = results / f"report_{athlete}_data.md"
    p.write_text("\n".join(lines))
    return p
