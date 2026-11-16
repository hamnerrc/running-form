# Analysis method

## Pipeline
1. **Check the video.** `ffprobe` checks the real capture frame rate (slo-mo files are sometimes re-timed to 30 fps). Stop and ask for originals if it isn't ≥120 fps.
2. **Perspective correction.** Click the 4 zone markers in one frame and compute a ground-plane homography (OpenCV). That maps pixel foot positions to meters along and across the line. With the camera 15–20 m away and square to the zone, sagittal joint angles from the image have small error. Remaining error is reported.
3. **Pose tracking.** MediaPipe Pose Landmarker (Heavy), 33 landmarks including heel and toe, run frame by frame in VIDEO mode. Landmarks are smoothed with a low-pass filter (Butterworth ~10–12 Hz for sprinting; lower for the mile). Fallback: manual marking of joints on the key frames.
   - Model file: `pose_landmarker_heavy.task` (~30 MB, not stored in this repo). From [Hugging Face mirror](https://huggingface.co/spaces/AleNunezArroyo/pose-detection-mediapipe/tree/main/models) or [Google](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task).
4. **Event detection.** Touchdown and toe-off for each foot, from foot height and speed, checked against the frames by eye.
5. **Metrics.** Per step: contact time, flight time, step length, step rate, touchdown distance, shin / thigh / knee / trunk angles at touchdown and toe-off, thigh range of motion, heel recovery, foot strike, CM vertical oscillation, braking, arm action. Per takeoff: the takeoff measures below. Then left/right averages and asymmetry.
6. **Compare** against the reference files ([02](02-reference-sprint-longjump.md), [03](03-reference-miler.md)). Normalize by leg length / height where the references do.
7. **Report** in `results/YYYY-MM-DD/`: annotated stills (touchdown, toe-off, max knee lift, each leg), metrics table, 1–3 ranked fixes with cues and drills, and the retest plan.

## Formulas
- **Speed** = zone length (10 yd = 9.144 m) ÷ time from hip crossing the first marker line to crossing the last (homography-corrected).
- **Duty factor** = contact time ÷ (contact time + flight time), per step.
- **Spring-mass stiffness** (Morin et al. 2005 sine-wave method; mass cancels when expressed per kg):
  - Peak force per kg: F/m = g · (π/2) · (t_flight / t_contact + 1)
  - CM vertical drop: Δy = (F/m) · t_c² / π² − g · t_c² / 8  (magnitude; Morin writes it as −(F/m)t_c²/π² + g t_c²/8 with downward negative)
  - Vertical stiffness per kg: k_vert = (F/m) / Δy
  - Leg compression: ΔL = L − √(L² − (v · t_c / 2)²) + Δy, with leg length L ≈ 0.53 × height
  - Leg stiffness per kg: k_leg = (F/m) / ΔL
- **Shin angle at touchdown:** knee–ankle line vs vertical (positive = ankle ahead of the knee).
- **Foot landing distance:** horizontal distance from the hip midpoint to the touching foot (heel or toe, whichever lands first) at touchdown, in meters via the homography.

- **Arm action** (near-side arm, per stride of the same-side leg; `metrics.arm_stride`): shoulder angle = upper arm (shoulder → elbow) relative to the trunk line (hip → shoulder), 0° = hanging along the trunk, + = in front (shoulder flexion), − = behind (shoulder extension). Shoulder range of motion = max − min over the stride. Elbow angle = included angle shoulder–elbow–wrist (180° = straight), read at the front and back of the swing. Hand height = wrist height relative to the shoulder at the front of the swing; hand behind hip = horizontal distance of the wrist behind the hip midpoint at the back of the swing. Arm–leg timing = time from the arm's furthest-back position to the same-side thigh's furthest-forward position (≈ 0 ms = in sync). Frames where the upper arm or forearm length is > 25% off the rep median are dropped.
- **Heel recovery** = maximum knee flexion during swing.
- **Foot strike** from the foot angle at touchdown (heel → toe line vs ground): > +5° rearfoot, < −5° forefoot, otherwise midfoot. MediaPipe's heel and toe points are rough, so this is low confidence.
- **Takeoff** (`takeoff.py`): the takeoff contact is the contact followed by the longest flight with the CM rising. Approach speed = CM horizontal displacement ÷ time over the last two steps before the takeoff touchdown. Step lengths from mid-contact foot positions. CM lowering = CM height at the touchdown two contacts before the takeoff minus CM height at the takeoff touchdown. Touchdown (plant) angle = angle between the ground and the CM → takeoff-ankle line, at touchdown. Takeoff velocity from the first 50 ms of flight (x: straight-line fit; y: straight-line fit of y + ½gt²), which is much less noisy than a derivative at toe-off. Takeoff angle = atan(v_y / v_x). Horizontal velocity loss = v_x at touchdown − v_x at toe-off. Toe-to-board distance = board front edge − toe position at touchdown (+ = behind the board). Effective distance = official distance + toe-to-board distance.
- **Key positions** (`positions.py`, one row per touchdown, `positions_<athlete>.csv/.md`). Stance leg = the foot that
  lands; swing leg = the other. Positions: touchdown and toe-off from the contact events; full support = the frame in
  the contact where the CM is closest to directly above the middle of the foot; top of flight = highest CM between
  toe-off and the next touchdown; strike = the frame before touchdown with the landing ankle furthest ahead of the hips.
  - Thigh angle = hip → knee vs vertical (+ = knee in front of the hip). **Thigh separation** = swing thigh − stance
    thigh (Bissas 2022: − = swing knee behind the stance knee). Knee separation = horizontal distance swing knee −
    stance knee.
  - Knee and hip angles are included angles, 180° = straight (hip = trunk–thigh angle = 180 − (thigh angle + trunk
    lean)); > 180° at toe-off = thigh extended behind the trunk line.
  - Leg angle at touchdown = CM → middle-of-foot line vs vertical (Clark 2025); leg excursion = that angle at
    touchdown minus the same angle at toe-off.
  - Overstride = ankle ahead of the stance knee at touchdown (Hanley 2023).
  - Swing (per stride of each leg): knee lift = max thigh angle, max thigh angle behind, thigh range of motion,
    front-side share = max in front ÷ range, average thigh angular velocity = range ÷ step time, peak thigh angular
    acceleration = 2π² × range × stride frequency² (Clark 2025's sine-wave formula).
  - Recovery: thigh angle and heel-behind-hips distance at the moment of maximum knee flexion in swing; time from
    toe-off until the swing thigh passes vertical.
  - Which touchdowns count: a value uses only touchdowns where the leg it depends on faced the camera (swing-leg values
    → swing leg near; stance values → stance leg near); separation angles use both legs and every touchdown.
    Tracking glitches (knee jump as the legs cross; legs swapped at toe-off, i.e. separation < 20°; leg excursion
    outside 30–80°) are left blank, not guessed.
  - Published model pose for overlays (`positions.MODEL_TD`, `MODEL_TO`): the published mean angles drawn with the
    athlete's own segment lengths, anchored at the stance ankle. It shows the average position, not one athlete.
- **Speed → distance (Athlete A's equation):** distance (ft) = 1.57 × approach speed (mph) − 8.87 + 0.18 × (height (in) − 70). Optimal-form ceiling; applies to approach speed, not flying-sprint speed.

## Terms
Use these standard sprint and jump terms in every report and video, and define them in plain words the first time. Don't invent new terms.

| term | meaning |
|---|---|
| flying sprint | a sprint timed after a running start, at top speed (the "fly" reps) |
| approach-run simulation | a full long-jump approach run without jumping (the "approach sim" reps) |
| ground contact time | how long the foot is on the ground each step |
| flight time | time in the air between one foot leaving and the other landing |
| step / stride | step = one foot's touchdown to the other foot's touchdown; stride = two steps (same foot to same foot) |
| step length, step rate (cadence) | distance per step; steps per second (or per minute) |
| touchdown distance | how far ahead of the CM the foot lands (we give the middle of the foot and the toe tip) |
| key positions | toe-off, top of flight, strike, touchdown, full support: the five frames coaches judge a stride by |
| top of flight (MVP) | the highest point between toe-off and the next touchdown (ALTIS: maximal vertical projection) |
| strike | the moment just before touchdown when the landing leg is furthest forward |
| full support | the moment in ground contact when the CM is directly over the foot |
| swing leg / stance leg | the leg in the air / the leg on the ground |
| thigh separation | angle between the two thighs (at touchdown: − = swing knee still behind the stance knee) |
| figure 4 | at touchdown, swing knee level with (or ahead of) the stance knee, swing heel folded high under the hips: from the side the legs make a "4" |
| recovery | bringing the swing leg forward after toe-off (heel up and the thigh pulled through) |
| front-side / back-side mechanics | how much of the leg's motion happens in front of the body vs trailing behind it |
| push-off (toe-off) extension | how straight the hip and knee are when the foot leaves the ground |
| thigh angular velocity | how fast the thighs scissor (degrees per second) |
| overstride | the ankle landing ahead of the knee (Hanley's definition) |
| duty factor | contact time ÷ (contact time + flight time) |
| vertical oscillation | how far the centre of mass (CM) rises and falls each step |
| centre of mass (CM) | the body's balance point, from a segment model |
| braking | the drop in forward speed just after touchdown |
| heel recovery | how far the knee folds as the leg swings through |
| knee drive / thigh angle | how high the swing thigh comes forward |
| shin angle at touchdown | shin vs vertical when the foot lands (+ = ankle ahead of the knee) |
| trunk lean | trunk vs vertical (+ = forward) |
| foot strike | rearfoot / midfoot / forefoot: which part lands first |
| arm swing (shoulder flexion / extension), elbow angle | how far the arm swings forward / back from the shoulder; the bend at the elbow |
| leg stiffness, vertical stiffness | spring-mass model: how much the leg / CM compresses for the force produced |
| penultimate step, last step | the step before the last; the last step onto the board |
| takeoff contact, takeoff angle | the takeoff foot's contact on the board; the CM's direction of travel at toe-off above horizontal |
| touchdown (plant) angle | angle between the ground and the CM → takeoff-ankle line at touchdown |
| horizontal velocity loss | forward speed lost during the takeoff contact |
| CM lowering | how much the CM drops over the last two steps |
| toe-to-board distance; official / effective distance | how far behind the board the takeoff toe lands; measured distance / distance from the actual takeoff point |

## Limits
- 2D, single camera: rotations out of the sagittal plane (pelvis drop, foot turn-out) are not measured. The optional front camera shows them qualitatively.
- Pose models are least accurate at the feet and during fast leg swing. Key-frame values get a visual check.
- Research links are mostly correlational: recommendations are hypotheses we test with retests.
