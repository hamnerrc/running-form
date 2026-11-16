"""Stage 2: ground-plane homography (README §5.2).

Pixel positions of the cones and yard-line/hash intersections live in data/<date>/calib.yaml:

    setups:
      main:                         # one entry per camera position; add another if the camera moved
        reference: A/video/calib.MOV
        frame: 0
        clips: all                  # or a list of clip files
        points:                     # name: [x_m, y_m, u_px, v_px]   (y_m: use zone.across_m for the inner row)
          cone_50_hash: [0.0,   0.0, 412, 801]
          cone_50_in:   [0.0,   1.5, 398, 742]
          cone_40_hash: [9.144, 0.0, 1534, 806]
          cone_40_in:   [9.144, 1.5, 1541, 746]
          hash_55:      [-4.572, 0.0, ...]   # 5-yard lines × near hash, and 1-yard hash ticks, as many as visible
          hash_35:      [13.716, 0.0, ...]
        holdout:                    # NOT used in the fit; reprojection error reported
          hash_45:      [4.572, 0.0, 973, 803]

WHY so many points: from hip height at ~17.5 m the ground is seen nearly edge-on (1.5 m across the field ≈ 7 px),
so the 4 zone cones alone give a badly conditioned homography — simulated ±0.5 px clicks → ~24 cm median /
63 cm 95th-pct error along the running line. Adding points spread ALONG the line (yard lines 55/45/35 × hash,
1-yard hash ticks) brings that to < 1 cm (tests/test_core.py). `mc_uncertainty` repeats this check on the
real points and is reported with every calibration.

Points are entered by hand (`calib-click` GUI, or by reading `calib-sheet` zoom crops), then refined to the
nearest cone blob when `refine_cones` is on. World frame: config.py.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import yaml

from .config import ZONE_LENGTH_M, ZONE_X_45
from .session import Session
from .video import iter_frames, read_frame


@dataclass
class Calib:
    H: np.ndarray            # world (x, y) m → image (u, v) px
    Hinv: np.ndarray
    y_run: float             # running-line y (m), midway between cone rows unless overridden
    fit_rmse_px: float
    holdout_err_px: dict
    holdout_err_m: dict
    setup: str
    holdout_err_x_m: dict | None = None   # along the running line only (what step length / speed depend on)

    def to_image(self, xy: np.ndarray) -> np.ndarray:
        xy = np.atleast_2d(xy).astype(float)
        return cv2.perspectiveTransform(xy[None], self.H)[0]

    def to_world(self, uv: np.ndarray) -> np.ndarray:
        uv = np.atleast_2d(uv).astype(float)
        return cv2.perspectiveTransform(uv[None], self.Hinv)[0]

    def ground_v(self, u: np.ndarray, y: float | None = None) -> np.ndarray:
        """Image row of the running line (world y = y_run) at image column(s) u."""
        y = self.y_run if y is None else y
        a = self.to_image(np.array([[-5.0, y], [ZONE_LENGTH_M + 5, y]]))
        (u0, v0), (u1, v1) = a
        return v0 + (np.asarray(u, float) - u0) * (v1 - v0) / (u1 - u0)

    def x_at_u(self, u: np.ndarray, y: float | None = None) -> np.ndarray:
        """World x where the vertical image line at column u meets the running line.
        Used for points above the ground (hip, CM): the camera is level and square, so
        world verticals are ~image verticals."""
        u = np.asarray(u, float)
        v = self.ground_v(u, y)
        return self.to_world(np.c_[u.ravel(), v.ravel()])[:, 0].reshape(u.shape)

    def m_per_px(self, x: float | None = None) -> float:
        """Local horizontal scale on the running line at world x (default: zone center).
        Applied to the runner's body in the sagittal plane (square pixels, camera square to the line)."""
        x = ZONE_LENGTH_M / 2 if x is None else x
        a = self.to_image(np.array([[x - 0.5, self.y_run], [x + 0.5, self.y_run]]))
        return 1.0 / float(np.linalg.norm(a[1] - a[0]))

    def to_dict(self) -> dict:
        return {"H": self.H.tolist(), "y_run": self.y_run, "fit_rmse_px": self.fit_rmse_px,
                "holdout_err_px": self.holdout_err_px, "holdout_err_m": self.holdout_err_m,
                "holdout_err_x_m": self.holdout_err_x_m or {},
                "m_per_px_zone_center": self.m_per_px(), "setup": self.setup}

    @classmethod
    def from_dict(cls, d: dict) -> "Calib":
        H = np.array(d["H"], float)
        return cls(H=H, Hinv=np.linalg.inv(H), y_run=d["y_run"], fit_rmse_px=d["fit_rmse_px"],
                   holdout_err_px=d["holdout_err_px"], holdout_err_m=d["holdout_err_m"], setup=d["setup"],
                   holdout_err_x_m=d.get("holdout_err_x_m"))


def fit(points: dict, holdout: dict | None = None, y_run: float | None = None, setup: str = "main") -> Calib:
    """points/holdout: name → [x_m, y_m, u_px, v_px]. Needs ≥4 non-collinear points."""
    arr = np.array(list(points.values()), float)
    if len(arr) < 4:
        raise ValueError(f"Need ≥4 calibration points, got {len(arr)}")
    world, img = arr[:, :2], arr[:, 2:]
    if len(set(np.round(world[:, 0], 3))) < 3:
        raise ValueError("Calibration points sit on only two x positions (e.g. just the 4 zone cones). Add points "
                         "along the running line — yard lines × hash, 1-yard hash ticks — see calib.py docstring.")
    H, _ = cv2.findHomography(world, img, method=0)
    if H is None:
        raise ValueError("Homography fit failed (points collinear?)")
    Hinv = np.linalg.inv(H)
    proj = cv2.perspectiveTransform(world[None], H)[0]
    rmse = float(np.sqrt(np.mean(np.sum((proj - img) ** 2, axis=1))))
    if y_run is None:
        ys = sorted(set(np.round(world[:, 1], 4)))
        y_run = float((min(ys) + max(ys)) / 2)
    c = Calib(H=H, Hinv=Hinv, y_run=y_run, fit_rmse_px=rmse, holdout_err_px={}, holdout_err_m={}, setup=setup)
    for name, (x, y, u, v) in (holdout or {}).items():
        pu = c.to_image(np.array([[x, y]]))[0]
        pw = c.to_world(np.array([[u, v]]))[0]
        c.holdout_err_px[name] = float(np.linalg.norm(pu - [u, v]))
        c.holdout_err_m[name] = float(np.linalg.norm(pw - [x, y]))
        c.holdout_err_x_m = c.holdout_err_x_m or {}
        # x error at fixed y: where the clicked pixel's image column meets world y of the held-out point
        c.holdout_err_x_m[name] = float(abs(c.x_at_u(np.array([u]), y=y)[0] - x))
    return c


def mc_uncertainty(points: dict, y_run: float, click_sd_px: float = 0.7, n: int = 300, seed: int = 0) -> dict:
    """Jitter every clicked pixel by N(0, click_sd_px), refit, and measure how much world x on the running
    line moves across the zone (−1 m … zone+1 m). Returns median and 95th percentile of the max deviation (m)."""
    rng = np.random.default_rng(seed)
    base = fit(points, None, y_run)
    xs = np.linspace(-1.0, ZONE_LENGTH_M + 1.0, 9)
    uvs = base.to_image(np.c_[xs, np.full_like(xs, y_run)])
    devs = []
    for _ in range(n):
        jit = {k: [x, y, u + rng.normal(0, click_sd_px), v + rng.normal(0, click_sd_px)] for k, (x, y, u, v) in points.items()}
        c = fit(jit, None, y_run)
        devs.append(float(np.max(np.abs(c.x_at_u(uvs[:, 0]) - base.x_at_u(uvs[:, 0])))))
    return {"click_sd_px": click_sd_px, "x_err_median_m": float(np.median(devs)), "x_err_p95_m": float(np.percentile(devs, 95))}


def refine_to_cones(img: np.ndarray, pts: dict, radius: int = 25) -> dict:
    """Snap each 'cone_*' pixel to the base of the nearest saturated orange/red/yellow blob.
    Returns updated copy; points with no blob in range are left unchanged."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = (((hsv[..., 0] < 35) | (hsv[..., 0] > 165)) & (hsv[..., 1] > 120) & (hsv[..., 2] > 90)).astype(np.uint8)
    out = {}
    for name, (x, y, u, v) in pts.items():
        if not name.startswith("cone"):
            out[name] = [x, y, u, v]
            continue
        u0, v0 = int(round(u)), int(round(v))
        sub = mask[max(0, v0 - radius):v0 + radius, max(0, u0 - radius):u0 + radius]
        n, lab, stats, cent = cv2.connectedComponentsWithStats(sub)
        if n <= 1:
            out[name] = [x, y, u, v]
            continue
        k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        ys, xs = np.nonzero(lab == k)
        # cone base center: bottom row of the blob, mean column there
        bottom = ys.max()
        uc = xs[ys >= bottom - 1].mean() + max(0, u0 - radius)
        vc = bottom + max(0, v0 - radius)
        out[name] = [x, y, float(uc), float(vc)]
    return out


def drift_px(ref: np.ndarray, img: np.ndarray, band: tuple[float, float] = (0.0, 1.0)) -> tuple[float, float]:
    """Global translation (du, dv) of img vs ref by phase correlation. A moving runner adds a little noise;
    the static field dominates. `band` restricts to a horizontal strip (fractions of height)."""
    h = ref.shape[0]
    a, b = int(band[0] * h), int(band[1] * h)
    g1 = cv2.cvtColor(ref[a:b], cv2.COLOR_BGR2GRAY).astype(np.float32)
    g2 = cv2.cvtColor(img[a:b], cv2.COLOR_BGR2GRAY).astype(np.float32)
    win = cv2.createHanningWindow(g1.shape[::-1], cv2.CV_32F)
    (du, dv), _ = cv2.phaseCorrelate(g1, g2, win)
    return float(du), float(dv)


def load_calib_yaml(sess: Session) -> dict:
    p = sess.root / "calib.yaml"
    if not p.exists():
        raise FileNotFoundError(f"{p} missing. Create it with `calib-click` or by hand (see calib.py docstring).")
    return yaml.safe_load(p.read_text())


def run(sess: Session, refine: bool = True, drift_tol_px: float = 2.0) -> dict:
    cfg = load_calib_yaml(sess)
    out_dir = sess.results / "qa"
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {"setups": {}, "clip_setup": {}, "drift": {}, "warnings": []}
    for name, st in cfg["setups"].items():
        ref_img = read_frame(sess.root / st["reference"], int(st.get("frame", 0)))
        pts = dict(st["points"])
        if refine:
            pts = refine_to_cones(ref_img, pts)
        c = fit(pts, st.get("holdout"), st.get("y_run"), setup=name)
        result["setups"][name] = c.to_dict()
        mc = mc_uncertainty(pts, c.y_run)
        result["setups"][name]["mc_uncertainty"] = mc
        if mc["x_err_p95_m"] > 0.03:
            result["warnings"].append(f"setup {name}: click-noise sensitivity {mc['x_err_p95_m']*100:.1f} cm (95th pct) "
                                      "along the line — add more points spread along x")
        _draw_check(ref_img, c, pts, st.get("holdout") or {}, out_dir / f"homography_{name}.jpg")
        # "all" = every clip not listed explicitly by another setup (e.g. a second camera position at the pit)
        listed = {f for o in cfg["setups"].values() if o.get("clips", "all") != "all" for f in o["clips"]}
        clips = [r.file for r in sess.reps if r.file not in listed] if st.get("clips", "all") == "all" else st["clips"]
        for f in clips:
            p = sess.root / f
            if not p.exists():
                continue
            result["clip_setup"][f] = name
            first = next(iter_frames(p, stop=1))[2]
            if first.shape != ref_img.shape:
                result["warnings"].append(f"{f}: frame size {first.shape} ≠ reference {ref_img.shape}")
                continue
            du, dv = drift_px(ref_img, first)
            result["drift"][f] = [du, dv]
            if np.hypot(du, dv) > drift_tol_px:
                result["warnings"].append(
                    f"{f}: camera moved {np.hypot(du, dv):.1f} px vs {st['reference']} — add a new setup for it")
        for hn, e in (c.holdout_err_x_m or {}).items():
            if e > 0.05:
                result["warnings"].append(f"setup {name}: holdout {hn} along-line error {e*100:.1f} cm (>5 cm) — re-check points")
    (sess.results / "work").mkdir(exist_ok=True)
    (sess.results / "work" / "calib.json").write_text(json.dumps(result, indent=2))
    lines = ["# Homography check", ""]
    for n, d in result["setups"].items():
        mc = d.get("mc_uncertainty", {})
        lines.append(f"- **{n}**: fit RMSE {d['fit_rmse_px']:.2f} px · scale {d['m_per_px_zone_center']*1000:.2f} mm/px at zone center"
                     f" · click-noise x uncertainty {mc.get('x_err_median_m', float('nan'))*100:.1f} cm median / "
                     f"{mc.get('x_err_p95_m', float('nan'))*100:.1f} cm 95th pct (±{mc.get('click_sd_px', 0)} px clicks)")
        for hn in d["holdout_err_px"]:
            lines.append(f"  - held-out {hn}: {d['holdout_err_px'][hn]:.2f} px · along the line "
                         f"{d['holdout_err_x_m'].get(hn, float('nan'))*100:.1f} cm · total {d['holdout_err_m'][hn]*100:.1f} cm "
                         "(cross-field error is expected: the ground is seen nearly edge-on)")
    lines += ["", "## Drift vs reference frame (px)", ""] + [f"- {f}: du {d[0]:+.1f}, dv {d[1]:+.1f}" for f, d in result["drift"].items()]
    lines += ["", "## Warnings", ""] + ([f"- {w}" for w in result["warnings"]] or ["- none"])
    (out_dir / "homography.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return result


def load(sess: Session, clip_file: str) -> Calib | None:
    p = sess.results / "work" / "calib.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    setup = d["clip_setup"].get(clip_file)
    return Calib.from_dict(d["setups"][setup]) if setup else None


def _draw_check(img: np.ndarray, c: Calib, pts: dict, holdout: dict, path: Path) -> None:
    vis = img.copy()
    xs = [p[0] for p in pts.values()]
    x0, x1 = min(xs) - 2, max(xs) + 2
    for x in np.arange(x0, x1 + 0.01, 1.0):   # 1 m grid on the ground
        a = c.to_image(np.array([[x, -1.0], [x, 2.5]])).astype(int)
        cv2.line(vis, tuple(a[0]), tuple(a[1]), (255, 255, 0), 1)
    for yy in (0.0, c.y_run, max(p[1] for p in pts.values())):
        a = c.to_image(np.array([[x0, yy], [x1, yy]])).astype(int)
        cv2.line(vis, tuple(a[0]), tuple(a[1]), (0, 255, 255) if yy == c.y_run else (255, 255, 0), 1)
    for n, (x, y, u, v) in pts.items():
        cv2.circle(vis, (int(u), int(v)), 6, (0, 255, 0), 2)
    for n, (x, y, u, v) in holdout.items():
        cv2.circle(vis, (int(u), int(v)), 6, (0, 0, 255), 2)
        pu = c.to_image(np.array([[x, y]]))[0].astype(int)
        cv2.drawMarker(vis, tuple(pu), (255, 0, 255), cv2.MARKER_CROSS, 14, 2)
    cv2.imwrite(str(path), vis)


def contact_sheet_for_clicking(img: np.ndarray, path: Path, grid: int = 100) -> None:
    """Frame with a labelled pixel grid, so points can be read off by eye (agent workflow without a GUI)."""
    vis = img.copy()
    h, w = vis.shape[:2]
    for x in range(0, w, grid):
        cv2.line(vis, (x, 0), (x, h), (0, 255, 255), 1)
        cv2.putText(vis, str(x), (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    for y in range(0, h, grid):
        cv2.line(vis, (0, y), (w, y), (0, 255, 255), 1)
        cv2.putText(vis, str(y), (2, y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    cv2.imwrite(str(path), vis)


def click_tool(img: np.ndarray, names: list[str]) -> dict:
    """Minimal OpenCV GUI: click each named point in order (zoom with the window). Esc skips one."""
    got: dict = {}
    win = "calib: click " + ", ".join(names)
    state = {"i": 0}

    def cb(ev, x, y, *_):
        if ev == cv2.EVENT_LBUTTONDOWN and state["i"] < len(names):
            got[names[state["i"]]] = (float(x), float(y))
            state["i"] += 1

    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, cb)
    while state["i"] < len(names):
        vis = img.copy()
        cv2.putText(vis, f"click: {names[state['i']]}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        for (u, v) in got.values():
            cv2.circle(vis, (int(u), int(v)), 5, (0, 255, 0), 2)
        cv2.imshow(win, vis)
        k = cv2.waitKey(30)
        if k == 27:
            state["i"] += 1
    cv2.destroyWindow(win)
    return got


def default_point_names(across_m: float) -> tuple[dict, dict]:
    """Click list for calib-click. Points out of frame can be skipped with Esc."""
    from .config import YARD
    pts = {"cone_50_hash": [0.0, 0.0], "cone_50_in": [0.0, across_m],
           "cone_40_hash": [ZONE_LENGTH_M, 0.0], "cone_40_in": [ZONE_LENGTH_M, across_m],
           "cone_45_in": [ZONE_X_45, across_m]}
    for yd in (-5, -4, -3, -2, -1, 1, 2, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15):   # yards from the 50 toward G2
        pts[f"hash_{yd:+d}yd"] = [yd * YARD, 0.0]
    hold = {"hash_45": [ZONE_X_45, 0.0], "hash_+3yd": [3 * YARD, 0.0]}
    return pts, hold
