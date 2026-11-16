"""Stage 7: touchdown / toe-off per foot (README §5.7).

Contact = the foot's lowest point (heel or toe) is near the ground AND (overground) the foot is nearly
stationary horizontally. The ground offset per foot is learned from the data, because MediaPipe's heel/toe
landmarks sit a few cm above the shoe sole.
Manual corrections: data/<date>/events_override.yaml  →  {<clip file>: {R: [[td_frame, to_frame], ...], L: [...]}}
(frame numbers in the original clip), applied instead of auto-detection for that clip/foot.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .filtering import _runs


@dataclass
class Contact:
    foot: str
    td: int          # index into the resampled series
    to: int          # last contact sample (inclusive)
    t_td: float
    t_to: float
    complete: bool   # both edges observed inside tracked, non-gap data

    @property
    def tc(self) -> float:
        return self.t_to - self.t_td


def foot_low_point(js: dict, side: str) -> np.ndarray:
    """(N,2) sagittal coords of whichever of heel/toe is lower in each frame."""
    heel, toe = js[f"heel_{side}"], js[f"toe_{side}"]
    pick_toe = toe[:, 1] < heel[:, 1]
    return np.where(pick_toe[:, None], toe, heel)


def detect(t: np.ndarray, js: dict, side: str, fs: float, *, overground: bool = True,
           runner_speed: float | None = None, min_contact_s: float = 0.04, merge_gap_s: float = 0.10,
           h_thr_min: float = 0.02) -> tuple[list[Contact], dict]:
    low = foot_low_point(js, side)
    h_raw = low[:, 1]
    fin = np.isfinite(h_raw)
    if fin.sum() < 10:
        return [], {"reason": "no foot data"}
    # per-foot ground offset: stance occupies ≥ ~30% of the cycle in sprinting, so a low percentile is stance
    offset = float(np.nanpercentile(h_raw, 10))
    h = h_raw - offset
    stance_band = h[fin][h[fin] <= np.nanpercentile(h, 25)]
    noise = float(np.std(stance_band)) if len(stance_band) > 3 else 0.01
    thr = max(h_thr_min, 3 * noise)
    contact = fin & (h < thr)
    vx = np.gradient(low[:, 0], 1 / fs)
    if overground:
        vref = runner_speed if runner_speed else float(np.nanmedian(np.abs(np.gradient(js["hip_mid"][:, 0], 1 / fs))))
        contact &= np.abs(vx) < 0.35 * vref
    # clean: merge short gaps (a foot's swing lasts ≥ ~0.25 s in any running, so a 'flight' of the same foot
    # under 0.1 s is a tracking dropout mid-stance, e.g. white shoe over white paint), drop short blips
    for s, e in _runs(~contact):
        if 0 < s and e < len(contact) and (e - s) / fs <= merge_gap_s:
            contact[s:e] = True
    contacts = []
    for s, e in _runs(contact):
        if (e - s) / fs < min_contact_s:
            continue
        complete = s > 0 and e < len(contact) and fin[max(0, s - 2):min(len(fin), e + 2)].all()
        contacts.append(Contact(side, int(s), int(e - 1), float(t[s]), float(t[e - 1]), bool(complete)))
    diag = {"offset_m": offset, "threshold_m": thr, "noise_m": noise, "h": h, "vx": vx}
    return contacts, diag


def from_override(t_clip: np.ndarray, t: np.ndarray, side: str, pairs: list) -> list[Contact]:
    """Override pairs are original-clip frame numbers → map to the resampled grid by time."""
    out = []
    for td_f, to_f in pairs:
        ttd, tto = float(t_clip[td_f]), float(t_clip[to_f])
        i, j = int(np.argmin(np.abs(t - ttd))), int(np.argmin(np.abs(t - tto)))
        out.append(Contact(side, i, j, ttd, tto, True))
    return out
