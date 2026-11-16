"""Constants shared across stages. Sources are cited inline."""

G = 9.81  # m/s²

# Zone geometry (README §2). World frame: x along the running line, 0 at the 50-yard line,
# +x toward the G2-side 40. y across the field, 0 at the near hash, +y toward the field center.
YARD = 0.9144
ZONE_LENGTH_M = 10 * YARD          # 9.144
ZONE_X_45 = 5 * YARD               # 45-yard line, held-out calibration check
MIN_FPS = 120.0                    # README §5.1: fail loudly below this

# MediaPipe Pose landmark indices (33-point model).
LM = {
    "nose": 0, "l_ear": 7, "r_ear": 8,
    "l_shoulder": 11, "r_shoulder": 12, "l_elbow": 13, "r_elbow": 14,
    "l_wrist": 15, "r_wrist": 16, "l_index": 19, "r_index": 20,
    "l_hip": 23, "r_hip": 24, "l_knee": 25, "r_knee": 26,
    "l_ankle": 27, "r_ankle": 28, "l_heel": 29, "r_heel": 30,
    "l_toe": 31, "r_toe": 32,  # "foot_index" in MediaPipe
}
SIDES = ("L", "R")


def lm(side: str, name: str) -> int:
    return LM[f"{side.lower()}_{name}"]


# Winter (2009) Biomechanics and Motor Control of Human Movement, 4th ed., Table 4.1.
# (segment, mass fraction, COM fraction from proximal end). Proximal→distal endpoints are
# resolved in kinematics.py. Head-neck COM is taken at the ear midpoint (Winter: 1.000 from C7 to ear canal).
WINTER_SEGMENTS = {
    "head_neck": (0.081, 1.000),
    "trunk":     (0.497, 0.500),   # glenohumeral → greater trochanter
    "upper_arm": (0.028, 0.436),
    "forearm":   (0.016, 0.430),
    "hand":      (0.006, 0.506),
    "thigh":     (0.100, 0.433),
    "shank":     (0.0465, 0.433),
    "foot":      (0.0145, 0.500),
}

# Winter (2009) Fig. 4.1 segment lengths as fractions of height (README §5.6, used for Athlete B).
WINTER_LENGTH_RATIOS = {
    "thigh": 0.245,
    "shank": 0.246,
    "trochanter_height": 0.530,
    "foot": 0.152,
}

SEGMENT_TOLERANCE = 0.05  # flag frames where tracked segment length differs > 5% from measured
