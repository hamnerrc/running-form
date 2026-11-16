import math

import numpy as np

from runform import positions as P


def test_model_pose_straight_leg_is_vertical():
    m = {"stance_thigh": 0, "stance_knee": 180, "swing_thigh": 0, "swing_knee": 180, "trunk": 0}
    pose = P.model_pose(m, (100, 500), {"thigh": 50, "shank": 40, "trunk": 60}, 1)
    assert np.allclose(pose["knee_s"], (100, 460)) and np.allclose(pose["hip"], (100, 410))
    assert np.allclose(pose["shoulder"], (100, 350))


def test_model_pose_forward_is_running_direction():
    # thigh +30° (knee in front) must put the knee at larger u when running toward +u, smaller u when running toward −u
    m = dict(P.MODEL_TD)
    a = P.model_pose(m, (0, 0), {"thigh": 50, "shank": 40, "trunk": 60}, 1)
    b = P.model_pose(m, (0, 0), {"thigh": 50, "shank": 40, "trunk": 60}, -1)
    assert a["knee_o"][0] - a["hip"][0] > 0 > b["knee_o"][0] - b["hip"][0]
    # world-class touchdown: swing heel folded behind and above the swing knee (figure 4)
    assert a["ankle_o"][0] < a["knee_o"][0] and a["ankle_o"][1] < a["knee_o"][1]


def test_published_references_consistent():
    # front-side share and angular velocity formulas reproduce Clark 2025's fast track group
    fmax, emin = 76.16, -28.44
    assert abs(100 * fmax / (fmax - emin) - P.SPRINT_REF["front_side_pct"][0][1]) < 0.1
    # Bissas hip angle at touchdown = 180 − (thigh + trunk lean)
    assert abs(180 - (27.4 + 14.5) - 139.7) < 2


def _synthetic(sep_deg=-30.0, n=200, fs=240.0):
    """Two legs in a constant pose; one complete contact of R at frame 100–125 with L swinging."""
    t = np.arange(n) / fs
    z = {"t": t, "orig_frame": np.arange(n), "trunk_lean": np.full(n, 10.0)}
    hip = np.column_stack([np.linspace(0, 2, n), np.full(n, 0.9)])
    z["hip_mid"] = hip; z["com"] = hip + [0, 0.1]
    th = {"R": 25.0, "L": 25.0 + sep_deg}
    for s in ("L", "R"):
        a = math.radians(th[s])
        knee = hip + 0.45 * np.array([math.sin(a), -math.cos(a)])
        ankle = knee + [0, -0.42]
        z[f"thigh_{s}"] = np.full(n, th[s]); z[f"knee_flex_{s}"] = np.full(n, 20.0)
        z[f"hip_flex_{s}"] = z[f"thigh_{s}"] + 10; z[f"shin_{s}"] = np.zeros(n)
        z[f"knee_{s}"] = knee; z[f"ankle_{s}"] = ankle
        z[f"heel_{s}"] = ankle + [-0.05, -0.05]; z[f"toe_{s}"] = ankle + [0.15, -0.07]
    info = {"near_side": {"detected": "R"}, "contacts": [
        {"foot": "R", "t_td": t[100], "t_to": t[125], "complete": True}]}
    return z, info


def test_thigh_separation_sign():
    z, info = _synthetic(-30.0)
    r = P.key_positions(z, info)[0]
    assert abs(r["thigh_sep_td_deg"] + 30) < 1e-6
    assert r["knee_sep_td_m"] < 0                      # swing knee behind
    assert r["swing_view"] == "far" and r["stance_view"] == "near"
