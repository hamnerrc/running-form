"""Synthetic ground truth for the arm-action metrics, the takeoff analysis and the speed→distance equation."""
import math

import numpy as np

from runform import kinematics, metrics, takeoff
from runform.config import LM
from runform.events import Contact


def _pose(n):
    P = np.full((n, 33, 2), np.nan)
    return P


def test_arm_angles_sign_and_elbow():
    # upright trunk; arm swings forward/back; elbow fixed at 90°
    n = 200
    P = _pose(n)
    fs = 240.0
    for s, ph in (("l", 0.0), ("r", math.pi)):
        P[:, LM[f"{s}_hip"]] = [0.0, 1.0]
        P[:, LM[f"{s}_shoulder"]] = [0.0, 1.5]
        a = np.radians(60 * np.sin(2 * np.pi * np.arange(n) / 100 + ph))      # ±60° about hanging
        E = np.c_[0.3 * np.sin(a), 1.5 - 0.3 * np.cos(a)]
        P[:, LM[f"{s}_elbow"]] = E
        # forearm perpendicular to upper arm, pointing forward/up
        P[:, LM[f"{s}_wrist"]] = E + 0.25 * np.c_[np.cos(a), np.sin(a)]
        for j in ("knee", "ankle", "heel", "toe"):
            P[:, LM[f"{s}_{j}"]] = [0.0, 0.5]
        P[:, LM[f"{s}_heel"]] = [0.0, 0.0]; P[:, LM[f"{s}_toe"]] = [0.2, 0.0]
    js = kinematics.joint_series(P)
    assert abs(np.nanmax(js["shoulder_L"]) - 60) < 0.5 and abs(np.nanmin(js["shoulder_L"]) + 60) < 0.5
    assert np.allclose(js["elbow_L"], 90, atol=0.5)
    assert np.allclose(js["foot_angle_L"], 0, atol=1e-6)
    r = metrics.arm_stride(js, "L", slice(0, 100), fs)
    assert abs(r["shoulder_rom_deg"] - 120) < 1
    assert abs(r["elbow_front_deg"] - 90) < 1 and abs(r["elbow_rom_deg"]) < 1


def test_equation_round_trip():
    h_in = 69.0
    ft = takeoff.equation_distance_ft(19.6, h_in)
    assert abs(ft - (1.57 * 19.6 - 8.87 - 0.18)) < 1e-9
    assert abs(takeoff.equation_speed_mph(ft, h_in) - 19.6) < 1e-9
    assert takeoff.ft_in(21.75 * takeoff.FT) == "21'9\""


def test_takeoff_metrics_recover_truth():
    fs = 240.0
    n = 480
    t = np.arange(n) / fs
    vx = 8.0
    com = np.c_[vx * t, np.full(n, 1.0)]
    # three running contacts then takeoff at frames 300–330, flight afterwards with vy = 3.0, vx drop to 7.0
    cs = [Contact("R", 60, 85, t[60], t[85], True), Contact("L", 120, 145, t[120], t[145], True),
          Contact("R", 180, 205, t[180], t[205], True), Contact("L", 240, 265, t[240], t[265], True),
          Contact("R", 300, 330, t[300], t[330], True)]
    # CM lowered 5 cm across the last two steps
    com[240:301, 1] = np.linspace(1.0, 0.95, 61)
    com[301:331, 1] = 0.95
    # during takeoff contact: vx 8 → 7, vy 0 → 3
    for i in range(300, 331):
        f = (i - 300) / 30
        com[i, 0] = com[300, 0] + (8 - 0.5 * f) * (i - 300) / fs
    for i in range(331, n):
        dt = (i - 330) / fs
        com[i] = [com[330, 0] + 7.0 * dt, 0.95 + 3.0 * dt - 4.905 * dt ** 2]
    js = {"trunk_lean": np.zeros(n)}
    for s in ("L", "R"):
        foot = np.c_[com[:, 0] + 0.3, np.zeros(n)]
        js[f"heel_{s}"] = foot; js[f"toe_{s}"] = foot + [0.2, 0]; js[f"ankle_{s}"] = foot + [0.0, 0.08]
        js[f"knee_flex_{s}"] = np.full(n, 20.0); js[f"thigh_{s}"] = np.zeros(n); js[f"shin_{s}"] = np.zeros(n)
    out = takeoff.takeoff_metrics(t, js, com, cs, fs=fs, height_m=1.753, board_x=float(com[300, 0]) + 0.6,
                                  official_m=6.4, best_sprint_ms=8.5)
    assert out["takeoff_foot"] == "R"
    assert abs(out["takeoff_contact_ms"] - 125) < 1
    assert abs(out["vy_to_ms"] - 3.0) < 0.2 and abs(out["vx_to_ms"] - 7.0) < 0.2
    assert abs(out["takeoff_angle_deg"] - math.degrees(math.atan2(3, 7))) < 1.5
    assert abs(out["com_lowering_m"] - 0.05) < 0.005
    assert abs(out["approach_speed_ms"] - 8.0) < 0.1
    # board 0.6 m ahead of CM, toe 0.5 m ahead of CM → 0.1 m behind the board
    assert abs(out["toe_to_board_m"] - 0.1) < 0.01 and not out["foul"]
    assert abs(out["effective_m"] - 6.5) < 0.01
    # touchdown angle: ankle 0.3 m ahead of and 0.87 m below the CM → atan(0.87/0.3)
    assert abs(out["touchdown_angle_deg"] - math.degrees(math.atan2(0.95 - 0.08, 0.3))) < 1.0
