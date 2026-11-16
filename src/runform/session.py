"""Session folder layout: data/<date>/session.yaml, <athlete>/measurements.yaml, clips."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import WINTER_LENGTH_RATIOS

REPO = Path(__file__).resolve().parents[2]


@dataclass
class Rep:
    athlete: str
    file: str
    type: str
    direction: str | None
    notes: str = ""
    extra: dict = field(default_factory=dict)   # any other keys on the rep line (e.g. official_m, runup_steps)

    @property
    def name(self) -> str:
        return Path(self.file).stem

    @property
    def dir_sign(self) -> int:
        """+1 for → (toward +x world), -1 for ←. Calibration/pogo clips default to +1."""
        return -1 if self.direction in ("←", "<-", "left", "L") else 1


@dataclass
class Session:
    root: Path
    meta: dict
    reps: list[Rep] = field(default_factory=list)

    @property
    def date(self) -> str:
        return self.root.name

    @property
    def results(self) -> Path:
        p = REPO / "results" / self.date
        p.mkdir(parents=True, exist_ok=True)
        return p

    def work(self, *parts: str) -> Path:
        """Intermediate files (pose tracks etc.). Lives under results/<date>/work/, git-ignored."""
        p = self.results / "work"
        for part in parts:
            p = p / part
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def slomo_capture_fps(self) -> float | None:
        """Set when clips are 30 fps renders of slo-mo (session.yaml slomo_render: true + capture_fps)."""
        return float(self.meta["capture_fps"]) if self.meta.get("slomo_render") else None

    def clip_path(self, rep: Rep) -> Path:
        return self.root / rep.file

    def measurements(self, athlete: str) -> dict:
        p = self.root / athlete / "measurements.yaml"
        if not p.exists():
            return {}
        return yaml.safe_load(p.read_text()) or {}

    def reps_for(self, athlete: str | None = None, types: tuple[str, ...] | None = None) -> list[Rep]:
        out = self.reps
        if athlete:
            out = [r for r in out if r.athlete == athlete]
        if types:
            out = [r for r in out if r.type in types]
        return out


def load_session(path: str | Path) -> Session:
    root = Path(path).resolve()
    sy = root / "session.yaml"
    if not sy.exists():
        raise FileNotFoundError(f"{sy} missing. Copy data/_template/session.yaml and fill it in.")
    meta = yaml.safe_load(sy.read_text()) or {}
    core = ("athlete", "file", "type", "direction", "notes")
    reps = [Rep(**{k: r.get(k) for k in core[:4]}, notes=r.get("notes") or "",
                extra={k: v for k, v in r.items() if k not in core})
            for r in meta.get("reps") or []]
    return Session(root=root, meta=meta, reps=reps)


@dataclass
class Body:
    """Anthropometrics for one athlete, with provenance so reports can label estimates."""
    height_m: float
    leg_length_m: float          # floor → greater trochanter
    thigh_m: dict                # side → length
    shank_m: dict
    foot_m: dict
    source: str                  # "measured" | "estimated (Winter ratios from height)" | "mixed"
    # What MediaPipe's landmarks give for this athlete standing still (its "hip" is not the trochanter, so the
    # tracked thigh is systematically shorter than the tape thigh). Used as the segment-check reference if set.
    mp_ref_m: dict | None = None


def body_from_measurements(m: dict, height_m_fallback: float | None = None) -> Body:
    """Measured values where present, Winter ratios from height otherwise (README §5.6)."""
    h_cm = m.get("height_cm")
    if h_cm is None and height_m_fallback is None:
        raise ValueError("Need at least height (measurements.yaml height_cm).")
    H = h_cm / 100 if h_cm else height_m_fallback
    used_est = False
    used_meas = False

    def side_val(side: str, key: str, ratio_key: str) -> float:
        nonlocal used_est, used_meas
        v = (m.get(side) or {}).get(key)
        if v is None:
            used_est = True
            return WINTER_LENGTH_RATIOS[ratio_key] * H
        used_meas = True
        return v / 100

    thigh = {s[0].upper(): side_val(s, "thigh_trochanter_to_knee_line_cm", "thigh") for s in ("right", "left")}
    shank = {s[0].upper(): side_val(s, "shank_knee_line_to_malleolus_cm", "shank") for s in ("right", "left")}
    foot = {s[0].upper(): side_val(s, "foot_length_cm", "foot") for s in ("right", "left")}
    if m.get("average_sides"):
        # L/R differences within measurement error: use the mean for both sides (raw values stay in the yaml)
        thigh, shank, foot = ({k: sum(d.values()) / 2 for k in d} for d in (thigh, shank, foot))
    legs = [side_val(s, "leg_length_floor_to_trochanter_cm", "trochanter_height") for s in ("right", "left")]
    source = "measured" if not used_est else ("mixed" if used_meas else "estimated (Winter ratios from height)")
    if m.get("segments_source"):           # e.g. segments estimated from video rather than tape-measured
        source = f"{m['segments_source']}" + (" + Winter ratios" if used_est else "")
    return Body(height_m=H, leg_length_m=sum(legs) / 2, thigh_m=thigh, shank_m=shank, foot_m=foot, source=source,
                mp_ref_m=m.get("mediapipe_standing_segments_m"))
