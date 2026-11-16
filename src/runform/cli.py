"""Command line. From the repo root:

  .venv/bin/python -m runform ingest      data/2026-11-15            # §5.1 verify clips/measurements
  .venv/bin/python -m runform calib-sheet data/2026-11-15            # gridded frame(s) to read calib pixels off
  .venv/bin/python -m runform calib-click data/2026-11-15            # GUI: click calibration points → calib.yaml
  .venv/bin/python -m runform calib       data/2026-11-15            # §5.2 homography + checks
  .venv/bin/python -m runform pose        data/2026-11-15 [--athlete A] [--only fly1]
  .venv/bin/python -m runform tape        data/2026-11-15            # §5.4 (needs tape_colors in session.yaml)
  .venv/bin/python -m runform analyze     data/2026-11-15            # §5.5–5.12 data part → results/<date>/
  .venv/bin/python -m runform positions   data/2026-11-15            # key positions vs elite (from analysis files)
  .venv/bin/python -m runform all         data/2026-11-15
  .venv/bin/python -m runform demo  <clip> --height 1.80 --direction ← [--treadmill 3.0] [--out DIR]

PYTHONPATH must include src/ (python -m runform works from the repo root via the sitecustomize below,
or run with PYTHONPATH=src).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

from . import analyze as an
from . import calib as calib_mod
from . import ingest, pose, positions, report, tape
from .session import Rep, body_from_measurements, load_session
from .video import iter_frames, read_frame


def _reps(sess, args, types=None):
    reps = sess.reps_for(args.athlete, types)
    if args.only:
        reps = [r for r in reps if r.name in args.only.split(",")]
    return [r for r in reps if sess.clip_path(r).exists()]


def cmd_ingest(args):
    ingest.run(load_session(args.session), allow_low_fps=args.allow_low_fps)


def cmd_calib_sheet(args):
    sess = load_session(args.session)
    out = sess.results / "qa" / "calib_sheets"
    out.mkdir(parents=True, exist_ok=True)
    clips = [r for r in sess.reps if r.type == "calibration" and sess.clip_path(r).exists()] or \
            [r for r in sess.reps if sess.clip_path(r).exists()][:1]
    for r in clips:
        img = read_frame(sess.clip_path(r), 0)
        calib_mod.contact_sheet_for_clicking(img, out / f"{r.athlete}_{r.name}_grid.jpg")
        # 2× zoom tiles along the ground band for precise reading
        h, w = img.shape[:2]
        band = img[int(h * 0.45):int(h * 0.95)]
        for k, x0 in enumerate(range(0, w, w // 4)):
            tile = band[:, x0:x0 + w // 4]
            big = __import__("cv2").resize(tile, None, fx=2, fy=2, interpolation=1)
            calib_mod.contact_sheet_for_clicking(big, out / f"{r.athlete}_{r.name}_zoom{k}_x{x0}_y{int(h*0.45)}.jpg", grid=50)
        print(f"wrote {out}  (zoom tiles: pixel = x0 + gx/2, y0 + gy/2)")


def cmd_calib_click(args):
    sess = load_session(args.session)
    across = (sess.meta.get("zone") or {}).get("across_m")
    if across is None:
        sys.exit("Set zone.across_m in session.yaml first (measured cone spacing).")
    ref = next(r for r in sess.reps if r.type == "calibration" and sess.clip_path(r).exists())
    img = read_frame(sess.clip_path(ref), 0)
    pts_w, hold_w = calib_mod.default_point_names(float(across))
    names = list(pts_w) + list(hold_w)
    got = calib_mod.click_tool(img, names)
    cfg = {"setups": {"main": {"reference": ref.file, "frame": 0, "clips": "all",
                               "points": {n: [*pts_w[n], *got[n]] for n in pts_w if n in got},
                               "holdout": {n: [*hold_w[n], *got[n]] for n in hold_w if n in got}}}}
    (sess.root / "calib.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    print(f"wrote {sess.root / 'calib.yaml'}")


def cmd_calib(args):
    calib_mod.run(load_session(args.session), refine=not args.no_refine)


def cmd_pose(args):
    sess = load_session(args.session)
    for r in _reps(sess, args):
        out = sess.work("pose") / f"{r.athlete}_{r.name}.npz"
        if out.exists() and not args.force:
            print(f"skip {out.name} (exists; --force to redo)"); continue
        roi = tuple(int(v) for v in args.roi.split(",")) if args.roi else None
        info = pose.track(sess.clip_path(r), out, roi=roi, slomo_capture_fps=sess.slomo_capture_fps)
        print(f"{r.athlete} {r.name}: {info['detected']}/{info['n']} frames, runner ~{info['runner_height_px_median']:.0f} px tall")


def cmd_tape(args):
    sess = load_session(args.session)
    rows = []
    for r in _reps(sess, args):
        colors = ((sess.meta.get("athletes") or {}).get(r.athlete) or {}).get("tape_colors")
        pz = sess.work("pose") / f"{r.athlete}_{r.name}.npz"
        if not colors or not pz.exists() or r.type == "calibration":
            continue
        d = pose.load(pz)
        near = "R" if r.dir_sign > 0 else "L"
        tr = tape.track(sess.clip_path(r), d, colors, near, sess.work("tape") / pz.name)
        c = calib_mod.load(sess, r.file)
        mpp = c.m_per_px() if c else float("nan")
        rows += [{"rep": r.name, **e} for e in tape.error_table(d, tr, mpp)]
    if rows:
        import pandas as pd
        (sess.results / "qa").mkdir(exist_ok=True)
        md = pd.DataFrame(rows).round(2).to_markdown(index=False) if hasattr(pd.DataFrame, "to_markdown") else pd.DataFrame(rows).round(2).to_string()
        (sess.results / "qa" / "tape_vs_pose.md").write_text("# Landmark tape vs MediaPipe\n\n" + md + "\n")
        print(md)
    else:
        print("No tape colours configured (athletes.<X>.tape_colors in session.yaml) or no pose tracks.")


def cmd_analyze(args):
    sess = load_session(args.session)
    overrides = an.load_overrides(sess)
    athletes = [args.athlete] if args.athlete else sorted({r.athlete for r in sess.reps if r.athlete != "both"})
    for ath in athletes:
        m = sess.measurements(ath)
        if not m:
            print(f"{ath}: no measurements.yaml — skipping"); continue
        body = body_from_measurements(m)
        results = []
        notes = []
        reps = _reps(sess, argparse.Namespace(athlete=ath, only=args.only),
                     tuple(an.RUN_TYPES) + tuple(an.POGO_TYPES) + tuple(an.TAKEOFF_TYPES))
        reps = sorted(reps, key=lambda r: r.type in an.TAKEOFF_TYPES)    # takeoffs last: they use the best fly speed
        for r in reps:
            pz = sess.work("pose") / f"{r.athlete}_{r.name}.npz"
            if not pz.exists():
                notes.append(f"{r.name}: no pose track (run `pose` first)"); continue
            c = calib_mod.load(sess, r.file)
            if c is None:
                notes.append(f"{r.name}: NO homography — positions/speeds use a height-based scale (low accuracy)")
            tz = sess.work("tape") / pz.name
            best_fly = max([x.info.get("zone_speed_ms") or 0 for x in results if x.rep.type == "fly"] or [0]) or None
            rr = an.analyze_rep(r, pz, body, sess.work("analysis"), calib=c, override=overrides.get(r.file),
                                tape_npz=tz if tz.exists() else None, body_mass_kg=m.get("body_mass_kg"),
                                board_x_world=_board_x(sess, r.file), best_sprint_ms=best_fly)
            if r.type in an.TAKEOFF_TYPES and (rr.info.get("takeoff") or {}).get("error"):
                notes.append(f"{r.name}: {rr.info['takeoff']['error']} — add the takeoff contact to events_override.yaml")
            results.append(rr)
            report.qa_sheets(sess.clip_path(r), rr.series_path, rr.info, sess.results / "qa", sess.results / "figures")
            if not rr.info["near_side"]["agree"]:
                notes.append(f"{r.name}: near side detected {rr.info['near_side']['detected']} but setup says "
                             f"{rr.info['near_side']['expected']} — check direction in session.yaml")
            print(f"{ath} {r.name}: {len(rr.rows)} rows")
        if results:
            p = report.write_athlete(sess.results, ath, results, notes, goal=sess.meta.get("athletes", {}).get(ath, {}),
                                     body=body)
            print(f"wrote {p}")
            pp = positions.write_athlete(sess, ath, body)
            if pp:
                print(f"wrote {pp}")


def cmd_positions(args):
    """Key positions (touchdown, toe-off, full support, swing) from existing analysis files: no re-tracking."""
    sess = load_session(args.session)
    athletes = [args.athlete] if args.athlete else sorted({r.athlete for r in sess.reps if r.athlete != "both"})
    for ath in athletes:
        m = sess.measurements(ath)
        pp = positions.write_athlete(sess, ath, body_from_measurements(m) if m else None)
        print(f"wrote {pp}" if pp else f"{ath}: no analysed runs")


def _board_x(sess, clip_file: str) -> float | None:
    """World x of the takeoff board's front edge for this clip's camera setup (calib.yaml `board_x_m`)."""
    import json
    p = sess.results / "work" / "calib.json"
    if not p.exists():
        return None
    setup = json.loads(p.read_text())["clip_setup"].get(clip_file)
    if not setup:
        return None
    v = calib_mod.load_calib_yaml(sess)["setups"][setup].get("board_x_m")
    return float(v) if v is not None else None


def cmd_all(args):
    for f in (cmd_ingest, cmd_calib, cmd_pose, cmd_tape, cmd_analyze):
        f(args)


def cmd_demo(args):
    """Whole pipeline on one arbitrary clip, without a session/homography. For testing only."""
    clip = Path(args.clip).resolve()
    out = Path(args.out or (Path.cwd() / "demo_out")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rep = Rep("demo", clip.name, args.type, args.direction)
    pz = out / "work" / f"demo_{rep.name}.npz"
    if not pz.exists() or args.force:
        print(pose.track(clip, pz))
    body = body_from_measurements({"height_cm": args.height * 100})
    rr = an.analyze_rep(rep, pz, body, out / "work", overground=args.treadmill is None, belt_speed=args.treadmill)
    report.qa_sheets(clip, rr.series_path, rr.info, out / "qa", out / "figures")
    p = report.write_athlete(out, "demo", [rr], ["DEMO run: no homography; scale from height; not a real session."])
    print(f"wrote {p}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="runform", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("ingest", cmd_ingest), ("calib-sheet", cmd_calib_sheet), ("calib-click", cmd_calib_click),
                     ("calib", cmd_calib), ("pose", cmd_pose), ("tape", cmd_tape), ("analyze", cmd_analyze), ("positions", cmd_positions), ("all", cmd_all)):
        p = sub.add_parser(name)
        p.add_argument("session")
        p.add_argument("--athlete"); p.add_argument("--only", help="comma-separated clip names (stems)")
        p.add_argument("--force", action="store_true"); p.add_argument("--roi", help="x0,y0,x1,y1 for runner search")
        p.add_argument("--allow-low-fps", action="store_true"); p.add_argument("--no-refine", action="store_true")
        p.set_defaults(fn=fn)
    p = sub.add_parser("demo")
    p.add_argument("clip"); p.add_argument("--height", type=float, required=True)
    p.add_argument("--direction", default="→"); p.add_argument("--type", default="fly")
    p.add_argument("--treadmill", type=float, help="belt speed m/s (disables overground contact logic)")
    p.add_argument("--out"); p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_demo)
    args = ap.parse_args(argv)
    args.fn(args)
