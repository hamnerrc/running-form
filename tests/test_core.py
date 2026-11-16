"""Ground-truth tests on synthetic data: every number the pipeline produces should come back to a known value."""
import math

import numpy as np
import pytest

from runform import calib, cleanup, events, filtering, kinematics, metrics
from runform.config import LM, ZONE_LENGTH_M, ZONE_X_45


# ---------- homography ----------

def _camera_H():
    """A plausible side-on camera: ~17.5 m away, hip height, 1920 px wide, zone filling ~2/3 of the frame."""
    f = 1500.0
    K = np.array([[f, 0, 960], [0, f, 540], [0, 0, 1]])
    cam = np.array([4.572, -17.5, 1.0])          # sideline at the 45, 1 m up
    # camera looks along +y (across the field), x to the right, z up → image u right, v down
    R = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)
    tilt = math.radians(3)
    Rx = np.array([[1, 0, 0], [0, math.cos(tilt), -math.sin(tilt)], [0, math.sin(tilt), math.cos(tilt)]])
    R = Rx @ R
    t = -R @ cam
    P = K @ np.c_[R, t]
    return P[:, [0, 1, 3]]                        # ground plane z=0 → homography


def _proj(H, xy):
    p = H @ np.r_[xy, 1.0]
    return p[:2] / p[2]


def test_homography_recovers_holdout():
    from runform.config import YARD
    H = _camera_H()
    world = {"cone_50_hash": (0, 0), "cone_50_in": (0, 1.5), "cone_40_hash": (ZONE_LENGTH_M, 0),
             "cone_40_in": (ZONE_LENGTH_M, 1.5)}
    world.update({f"hash_{yd}": (yd * YARD, 0.0) for yd in (-5, 2, 8, 15)})
    rng = np.random.default_rng(0)
    pts = {k: [*w, *(_proj(H, w) + rng.normal(0, 0.5, 2))] for k, w in world.items()}
    hold = {"l45_hash": [ZONE_X_45, 0.0, *_proj(H, (ZONE_X_45, 0.0))]}
    c = calib.fit(pts, hold)
    assert c.holdout_err_x_m["l45_hash"] < 0.01
    u = _proj(H, (3.0, 0.75))[0]
    assert abs(float(c.x_at_u(np.array([u]))[0]) - 3.0) < 0.02
    a, b = _proj(H, (4.0, 0.75)), _proj(H, (5.0, 0.75))
    assert abs(c.m_per_px(4.5) - 1 / np.linalg.norm(b - a)) / c.m_per_px(4.5) < 0.02
    mc = calib.mc_uncertainty(pts, c.y_run, n=100)
    assert mc["x_err_p95_m"] < 0.02


def test_four_cones_only_is_rejected():
    H = _camera_H()
    world = [(0, 0), (0, 1.5), (ZONE_LENGTH_M, 0), (ZONE_LENGTH_M, 1.5)]
    pts = {str(i): [*w, *_proj(H, w)] for i, w in enumerate(world)}
    with pytest.raises(ValueError, match="two x positions"):
        calib.fit(pts)


# ---------- filtering ----------

def test_residual_cutoff_and_zero_lag():
    fs = 240.0
    t = np.arange(0, 3, 1 / fs)
    true = 0.2 * np.sin(2 * np.pi * 2.0 * t) + 0.05 * np.sin(2 * np.pi * 6 * t)
    rng = np.random.default_rng(1)
    noisy = true + rng.normal(0, 0.004, len(t))
    fc, _, _ = filtering.residual_cutoff(noisy, fs)
    assert 4 <= fc <= 20
    y = filtering.butter_zero_lag(noisy, fs, fc)
    core = slice(48, -48)
    assert np.sqrt(np.mean((y[core] - true[core]) ** 2)) < 0.003
    # zero lag: peak of cross-correlation at 0
    xc = np.correlate(y[core] - y[core].mean(), true[core] - true[core].mean(), "full")
    assert abs(np.argmax(xc) - (len(y[core]) - 1)) <= 1


def test_resample_handles_jitter_and_gaps():
    rng = np.random.default_rng(2)
    t = np.cumsum(np.r_[0, 1 / 240 + rng.normal(0, 0.0002, 499)])
    x = np.sin(t)[:, None]
    x[200:210] = np.nan
    tu, xu = filtering.resample_uniform(t, x, 240.0)
    assert np.allclose(np.diff(tu), 1 / 240)
    assert np.isnan(xu[:, 0]).sum() >= 8
    good = np.isfinite(xu[:, 0])
    assert np.max(np.abs(xu[good, 0] - np.sin(tu[good]))) < 1e-3


# ---------- spring-mass ----------

def test_spring_mass_known_values():
    # Morin 2005-style check: tc=0.10, tf=0.12 → F/m = g·π/2·(2.2)
    r = metrics.spring_mass(0.10, 0.12, 9.0, 0.93)
    F = 9.81 * math.pi / 2 * 2.2
    assert math.isclose(r["Fmax_per_kg"], F, rel_tol=1e-9)
    dy = F * 0.01 / math.pi ** 2 - 9.81 * 0.01 / 8
    assert math.isclose(r["dy_m"], dy, rel_tol=1e-9)
    assert 0.01 < r["dy_m"] < 0.03                     # a sprinter's CM drop is ~1–3 cm
    dL = 0.93 - math.sqrt(0.93 ** 2 - (9.0 * 0.10 / 2) ** 2) + dy
    assert math.isclose(r["k_leg_per_kg"], F / dL, rel_tol=1e-9)


# ---------- synthetic runner: events + step metrics ----------

def synthetic_run(fs=240.0, v=8.5, tc=0.100, tf=0.125, n_steps=8, landing=0.30, leg=0.93):
    """Sagittal kinematics with exactly known contacts. Feet are planted (stationary) during stance at
    positions spaced by v·(tc+tf); in flight they swing forward in an arc."""
    step_t = tc + tf
    T = n_steps * step_t + 0.3
    t = np.arange(0, T, 1 / fs)
    N = len(t)
    hip = np.c_[v * t, 0.95 + 0.02 * np.cos(2 * np.pi * t / step_t)]
    feet = {}
    truth = []
    for s, phase in (("R", 0.0), ("L", step_t)):
        x = np.full(N, np.nan); y = np.full(N, np.nan)
        tds = np.arange(0.05 + phase, T - 0.05, 2 * step_t)
        for k, td in enumerate(tds):
            to = td + tc
            xfoot = v * td + landing                  # lands `landing` m ahead of the hip
            st = (t >= td) & (t <= to)
            x[st] = xfoot; y[st] = 0.0
            truth.append((s, td, to, xfoot))
            if k + 1 < len(tds):
                nxt_td = tds[k + 1]; nxt_x = v * nxt_td + landing
                sw = (t > to) & (t < nxt_td)
                ph = (t[sw] - to) / (nxt_td - to)
                x[sw] = xfoot + (nxt_x - xfoot) * (1 - np.cos(np.pi * ph)) / 2
                y[sw] = 0.35 * np.sin(np.pi * ph)
        feet[s] = np.c_[x, y]
    js = {"hip_mid": hip}
    for s in ("L", "R"):
        heel = feet[s] + [-0.05, 0.0]; toe = feet[s] + [0.15, 0.0]
        js[f"heel_{s}"], js[f"toe_{s}"] = heel, toe
        js[f"ankle_{s}"] = feet[s] + [0.0, 0.08]
        knee = (hip + js[f"ankle_{s}"]) / 2 + [0.1, 0.0]
        js[f"knee_{s}"] = knee
        js[f"thigh_{s}"] = kinematics.seg_angle_from_down(hip, knee)
        js[f"shin_{s}"] = kinematics.seg_angle_from_down(knee, js[f"ankle_{s}"])
        js[f"knee_flex_{s}"] = 180 - kinematics.included_angle(hip, knee, js[f"ankle_{s}"])
    js["trunk_lean"] = np.full(N, 5.0)
    return t, js, hip.copy(), truth


def test_events_and_steps_recover_truth():
    fs = 240.0
    t, js, com, truth = synthetic_run(fs=fs)
    contacts = []
    for s in ("L", "R"):
        cs, _ = events.detect(t, js, s, fs, overground=True, runner_speed=8.5)
        contacts += cs
    complete = [c for c in contacts if c.complete]
    assert len(complete) >= 5      # first/last contact per foot are edge-truncated by design
    tr = {(s, round(td, 3)): (td, to) for s, td, to, _ in truth}
    for c in complete:
        td, to = min(((td, to) for (s, _), (td, to) in tr.items() if s == c.foot), key=lambda p: abs(p[0] - c.t_td))
        assert abs(c.t_td - td) <= 1.01 / fs           # ±1 frame
        assert abs(c.t_to - to) <= 1.01 / fs
    rows = metrics.step_table(t, js, com, contacts, fs=fs, near="R", speed=8.5, leg_length=0.93, height=1.753)
    full = [r for r in rows if "flight_ms" in r]
    assert full
    for r in full:
        assert abs(r["contact_ms"] - 100) <= 2 * 1000 / fs + 1e-6
        assert abs(r["flight_ms"] - 125) <= 2 * 1000 / fs + 1e-6
        assert abs(r["step_length_m"] - 8.5 * 0.225) < 0.02
        # heel lands first: truth 0.30 − 0.05 = 0.25 m. Tolerance: ±1 frame of hip travel at 8.5 m/s (3.5 cm)
        assert abs(r["foot_ahead_of_hip_td_m"] - 0.25) <= 8.5 / fs + 0.005
        assert r["confidence"] == ("high" if r["foot"] == "R" else "low")


def test_zone_speed():
    fs = 240.0
    t = np.arange(0, 2, 1 / fs)
    x = -1.0 + 8.5 * t
    zs = metrics.zone_speed(t, x, +1)
    assert abs(zs["zone_speed_ms"] - 8.5) < 0.01
    zs = metrics.zone_speed(t, ZONE_LENGTH_M + 1 - 8.5 * t, -1)
    assert abs(zs["zone_speed_ms"] - 8.5) < 0.01


def test_pogo_rsi():
    fs = 240.0
    cs = []
    t0 = 0.1
    for k in range(6):
        cs.append(events.Contact("L", 0, 0, t0, t0 + 0.18, True))
        cs.append(events.Contact("R", 0, 0, t0 + 0.004, t0 + 0.18, True))
        t0 += 0.18 + 0.40
    rows = metrics.pogo_table(cs)
    assert len(rows) == 5
    h = 9.81 * 0.40 ** 2 / 8
    assert all(abs(r["jump_height_m"] - h) < 0.005 and abs(r["rsi"] - h / 0.18) < 0.05 for r in rows)


# ---------- cleanup: L/R swap repair ----------

def test_swap_repair():
    fs = 240.0
    n = 240
    t = np.arange(n) / fs
    uv = np.full((n, 33, 2), np.nan)
    base = np.zeros((33, 2)) + [500, 300]
    for i in range(n):
        uv[i] = base
        ph = 2 * np.pi * 1.2 * t[i]
        for s, sgn in (("l", 1), ("r", -1)):
            for name, r in (("knee", 60), ("ankle", 120), ("heel", 125), ("toe", 130)):
                uv[i, LM[f"{s}_{name}"]] = [500 + sgn * r * np.sin(ph) * 0.8, 300 + r]
    truth = uv.copy()
    swapped = uv.copy()
    for a, b in ((30, 36), (100, 104), (170, 181)):
        for s1, s2 in cleanup.LEG:
            i1, i2 = LM[s1], LM[s2]
            swapped[a:b, [i1, i2]] = swapped[a:b, [i2, i1]]
    fixed, mask, _ = cleanup.fix_swaps(swapped, np.ones(n, bool), cleanup._pairs(cleanup.LEG, []))
    legs = [LM[x] for p in cleanup.LEG for x in p]
    # frames where the legs are far apart must be restored exactly; near crossings either labelling is fine
    apart = np.abs(truth[:, LM["l_ankle"], 0] - truth[:, LM["r_ankle"], 0]) > 30
    assert np.allclose(fixed[apart][:, legs], truth[apart][:, legs])


def test_outlier_spike_removed():
    fs = 240.0
    n = 100
    uv = np.zeros((n, 33, 2)) + np.linspace(0, 300, n)[:, None, None]
    uv[50, LM["l_ankle"]] += [0, -150]
    out, k = cleanup.reject_outliers(uv, np.full(n, 300.0), fs)
    assert np.isnan(out[50, LM["l_ankle"]]).all()
    assert k <= 3


def test_angles_sign_conventions():
    hip = np.array([0.0, 1.0]); knee_fwd = np.array([0.2, 0.55]); ankle_fwd = np.array([0.4, 0.1])
    assert kinematics.seg_angle_from_down(hip, knee_fwd) > 0       # knee ahead → +thigh
    assert kinematics.seg_angle_from_down(knee_fwd, ankle_fwd) > 0  # ankle ahead of knee → +shin (04)
    assert abs(kinematics.included_angle(hip, np.array([0, 0.5]), np.array([0, 0.0])) - 180) < 1e-9
    assert kinematics.seg_angle_from_up(hip, hip + [0.1, 0.5]) > 0  # forward lean +


# ---------- tape markers ----------

def test_tape_marker_found_near_landmark():
    import cv2
    from runform import tape
    img = np.full((200, 200, 3), 60, np.uint8)
    cv2.circle(img, (120, 90), 4, (0, 220, 0), -1)        # green marker (BGR)
    cv2.circle(img, (30, 30), 4, (0, 220, 0), -1)         # decoy far away
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    c = tape.find_marker(hsv, "green", np.array([115.0, 95.0]), radius=20)
    assert np.allclose(c, [120, 90], atol=0.6)
    assert np.isnan(tape.find_marker(hsv, "pink", np.array([115.0, 95.0]), 20)).all()
