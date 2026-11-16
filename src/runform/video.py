"""Video probing and frame iteration with real per-frame timestamps (PTS).

iPhone slo-mo can have slightly variable frame timing, so everything downstream uses PTS,
never nominal fps (README §5.1). ffprobe is used when on PATH; PyAV (bundled FFmpeg) otherwise.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

import av
import numpy as np


@dataclass
class ClipInfo:
    path: str
    codec: str
    width: int
    height: int
    rotation: int            # degrees, as displayed
    n_frames: int
    duration_s: float
    fps_nominal: float
    fps_measured: float      # 1 / median frame interval from PTS
    dt_min_ms: float
    dt_max_ms: float
    dt_jitter_ms: float      # SD of frame intervals
    dropped_suspect: int     # intervals > 1.5× median
    probe_tool: str

    def to_dict(self) -> dict:
        return asdict(self)


def _rotation_ffprobe(path: Path) -> int | None:
    if not shutil.which("ffprobe"):
        return None
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream_side_data=rotation:stream_tags=rotate", "-of", "json", str(path)],
        capture_output=True, text=True)
    try:
        st = json.loads(out.stdout)["streams"][0]
    except (KeyError, IndexError, json.JSONDecodeError):
        return None
    for sd in st.get("side_data_list", []) or []:
        if "rotation" in sd:
            return int(sd["rotation"])
    if "rotate" in (st.get("tags") or {}):
        return int(st["tags"]["rotate"])
    return 0


def frame_times(path: str | Path) -> np.ndarray:
    """Presentation timestamps (s) of every decoded video frame, starting at 0."""
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        # demux only (no decode) — fast even for big 240 fps clips
        ts = [p.pts * p.time_base for p in c.demux(s) if p.pts is not None and p.size > 0]
    t = np.sort(np.array(ts, dtype=float))
    return t - t[0] if len(t) else t


def real_frame_times(path: str | Path, slomo_capture_fps: float | None = None) -> np.ndarray:
    """Real-world time of each frame.

    Normally the PTS. For an iPhone slo-mo that was *rendered* to a 30 fps file (Photos export / AirDrop without
    "All Photos Data"), every frame of the slow section is one captured frame, so real t = index / capture fps.
    Only valid if the clip contains no speed ramp: check that the runner's px/frame is constant (ingest does
    not do this for you)."""
    t = frame_times(path)
    if slomo_capture_fps:
        return np.arange(len(t)) / float(slomo_capture_fps)
    return t


def probe(path: str | Path) -> ClipInfo:
    path = Path(path)
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        codec = s.codec_context.name
        w, h = s.codec_context.width, s.codec_context.height
        nominal = float(s.average_rate) if s.average_rate else float("nan")
    t = frame_times(path)
    d = np.diff(t)
    med = float(np.median(d)) if len(d) else float("nan")
    rot = _rotation_ffprobe(path)
    tool = "ffprobe+pyav" if rot is not None else "pyav"
    if rot is None:
        rot = _rotation_pyav(path)
    return ClipInfo(
        path=str(path), codec=codec, width=w, height=h, rotation=rot, n_frames=len(t),
        duration_s=float(t[-1]) if len(t) else 0.0, fps_nominal=nominal,
        fps_measured=1 / med if med else float("nan"),
        dt_min_ms=float(d.min() * 1e3) if len(d) else float("nan"),
        dt_max_ms=float(d.max() * 1e3) if len(d) else float("nan"),
        dt_jitter_ms=float(d.std() * 1e3) if len(d) else float("nan"),
        dropped_suspect=int((d > 1.5 * med).sum()) if len(d) else 0,
        probe_tool=tool,
    )


def _rotation_pyav(path: Path) -> int:
    with av.open(str(path)) as c:
        for f in c.decode(video=0):
            return int(getattr(f, "rotation", 0) or 0)
    return 0


def iter_frames(path: str | Path, start: int = 0, stop: int | None = None,
                step: int = 1) -> Iterator[tuple[int, float, np.ndarray]]:
    """Yield (frame_index, t_seconds_from_first_frame, BGR uint8 image), display-rotated."""
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        s.thread_type = "AUTO"
        t0 = None
        for i, f in enumerate(c.decode(s)):
            if t0 is None:
                t0 = f.pts * f.time_base if f.pts is not None else 0
            if i < start:
                continue
            if stop is not None and i >= stop:
                break
            if (i - start) % step:
                continue
            img = f.to_ndarray(format="bgr24")
            rot = int(getattr(f, "rotation", 0) or 0)
            if rot:
                # PyAV reports the counter-clockwise rotation needed for display
                img = np.ascontiguousarray(np.rot90(img, k=(rot // 90) % 4))
            t = float(f.pts * f.time_base - t0) if f.pts is not None else float("nan")
            yield i, t, img


def read_frame(path: str | Path, index: int) -> np.ndarray:
    for _, _, img in iter_frames(path, start=index, stop=index + 1):
        return img
    raise IndexError(f"frame {index} not in {path}")
