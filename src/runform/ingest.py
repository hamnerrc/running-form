"""Stage 1: ingest and verify (README §5.1).

Probes every clip listed in session.yaml, checks real capture fps from PTS, lists what's missing
(clips, measurements, photos, session fields). Writes results/<date>/qa/ingest.{json,md}.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import MIN_FPS
from .session import Session
from .video import probe

EXPECTED_PHOTOS_A = ["front", "side_R", "back", "natural_side", "ktw_R", "ktw_L"]
PHOTO_EXT = (".jpg", ".jpeg", ".heic", ".png", ".JPG", ".JPEG", ".HEIC", ".PNG")
KEY_SESSION_FIELDS = [("zone", "across_m"), ("phone_model",), ("camera", "distance_to_running_line_m")]


def _get(d: dict, keys: tuple) -> object:
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def run(sess: Session, allow_low_fps: bool = False) -> dict:
    problems: list[str] = []
    clips = []
    for rep in sess.reps:
        p = sess.clip_path(rep)
        entry = {"athlete": rep.athlete, "file": rep.file, "type": rep.type, "direction": rep.direction}
        if not p.exists():
            entry["status"] = "MISSING"
            problems.append(f"MISSING clip {rep.file} ({rep.athlete} {rep.type})")
        else:
            info = probe(p)
            entry.update(info.to_dict())
            if sess.slomo_capture_fps:
                entry["fps_real"] = sess.slomo_capture_fps
                entry["timebase"] = f"slo-mo render: playback {info.fps_measured:.0f} fps, 1 frame = 1/{sess.slomo_capture_fps:.0f} s"
            fps_ok = (sess.slomo_capture_fps or info.fps_measured) >= MIN_FPS
            if not fps_ok:
                entry["status"] = "LOW_FPS"
                problems.append(
                    f"LOW FPS {rep.file}: {info.fps_measured:.1f} fps measured from PTS (need ≥{MIN_FPS:.0f}). "
                    "Re-send the original (AirDrop / 'All Photos Data').")
            else:
                entry["status"] = "OK"
            if info.dropped_suspect:
                problems.append(f"{rep.file}: {info.dropped_suspect} frame intervals >1.5× median (dropped frames?)")
        clips.append(entry)

    # Files present on disk but not listed in session.yaml
    listed = {(sess.root / r.file).resolve() for r in sess.reps}
    for ext in ("*.MOV", "*.mov", "*.mp4", "*.MP4", "*.m4v"):
        for f in sess.root.rglob(ext):
            if f.resolve() not in listed:
                problems.append(f"UNLISTED clip on disk: {f.relative_to(sess.root)} (map it under reps: in session.yaml)")

    # Measurements
    meas = {}
    for ath in sorted({r.athlete for r in sess.reps if r.athlete != "both"} | {"A", "B"}):
        m = sess.measurements(ath)
        meas[ath] = m
        if not m:
            problems.append(f"MISSING {ath}/measurements.yaml")
            continue
        if m.get("height_cm") is None:
            problems.append(f"{ath}: height_cm missing")
        if ath == "A":
            for side in ("right", "left"):
                for k, v in (m.get(side) or {}).items():
                    if v is None:
                        problems.append(f"A {side}.{k} is null")

    # Photos (Athlete A)
    pdir = sess.root / "A" / "photos"
    present = {f.stem for f in pdir.iterdir() if f.suffix in PHOTO_EXT} if pdir.exists() else set()
    missing_photos = [p for p in EXPECTED_PHOTOS_A if p not in present]
    for p in missing_photos:
        problems.append(f"MISSING photo A/photos/{p}.*")

    for keys in KEY_SESSION_FIELDS:
        if _get(sess.meta, keys) is None:
            problems.append(f"session.yaml: {'.'.join(keys)} is null")

    low = [c for c in clips if c.get("status") == "LOW_FPS"]
    report = {"date": sess.date, "clips": clips, "problems": problems, "photos_present": sorted(present)}
    out = sess.results / "qa"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ingest.json").write_text(json.dumps(report, indent=2, default=str))
    (out / "ingest.md").write_text(_markdown(report))
    print(_markdown(report))
    if low and not allow_low_fps:
        raise SystemExit(f"{len(low)} clip(s) under {MIN_FPS:.0f} fps. Stopping (README §5.1).")
    return report


def _markdown(r: dict) -> str:
    lines = [f"# Ingest check: {r['date']}", "", "| clip | athlete | type | dir | status | fps (PTS) | res | dur s | jitter ms |",
             "|---|---|---|---|---|---|---|---|---|"]
    for c in r["clips"]:
        fps = (f"{c['fps_measured']:.0f} → real {c['fps_real']:.0f}" if "fps_real" in c else f"{c['fps_measured']:.1f}") if "fps_measured" in c else ""
        res = f"{c['width']}×{c['height']}" if "width" in c else ""
        dur = f"{c['duration_s']:.2f}" if "duration_s" in c else ""
        jit = f"{c['dt_jitter_ms']:.2f}" if "dt_jitter_ms" in c else ""
        lines.append(f"| {c['file']} | {c['athlete']} | {c['type']} | {c['direction'] or ''} | {c['status']} | {fps} | {res} | {dur} | {jit} |")
    lines += ["", "## Problems", ""] + ([f"- {p}" for p in r["problems"]] or ["- none"])
    return "\n".join(lines) + "\n"
