# Analysis method

## Pipeline
1. **Check the video.** `ffprobe` checks the real capture frame rate (slo-mo files are sometimes re-timed to 30 fps). Stop and ask for originals if it isn't ≥120 fps.
2. **Perspective correction.** Click the 4 zone markers in one frame and compute a ground-plane homography (OpenCV). That maps pixel foot positions to meters along and across the line. With the camera 15–20 m away and square to the zone, sagittal joint angles from the image have small error. Remaining error is reported.
3. **Pose tracking.** MediaPipe Pose Landmarker (Heavy), 33 landmarks including heel and toe, run frame by frame in VIDEO mode. Landmarks are smoothed with a low-pass filter (Butterworth ~10–12 Hz for sprinting; lower for the mile). Fallback: manual marking of joints on the key frames.
   - Model file: `pose_landmarker_heavy.task` (~30 MB, not stored in this repo). From [Hugging Face mirror](https://huggingface.co/spaces/AleNunezArroyo/pose-detection-mediapipe/tree/main/models) or [Google](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task).
4. **Event detection.** Touchdown and toe-off for each foot, from foot height and speed, checked against the frames by eye.
5. **Metrics.** Per step: contact time, flight time, step length, step rate, foot landing distance ahead of the hips, shin / thigh / knee / trunk angles at touchdown and toe-off, thigh range of motion, hip vertical oscillation, hip horizontal speed dip (braking). Then left/right averages and asymmetry.
6. **Compare** against the reference files ([02](02-reference-sprint-longjump.md), [03](03-reference-miler.md)). Normalize by leg length / height where the references do.
7. **Report** in `results/YYYY-MM-DD/`: annotated stills (touchdown, toe-off, max knee lift, each leg), metrics table, 1–3 ranked fixes with cues and drills, and the retest plan.

## Formulas
- **Speed** = 10 m ÷ time from hip crossing the first marker line to crossing the last (homography-corrected).
- **Duty factor** = contact time ÷ (contact time + flight time), per step.
- **Spring-mass stiffness** (Morin et al. 2005 sine-wave method; mass cancels when expressed per kg):
  - Peak force per kg: F/m = g · (π/2) · (t_flight / t_contact + 1)
  - CM vertical drop: Δy = (F/m) · t_c² / π² + g · t_c² / 8
  - Vertical stiffness per kg: k_vert = (F/m) / Δy
  - Leg compression: ΔL = L − √(L² − (v · t_c / 2)²) + Δy, with leg length L ≈ 0.53 × height
  - Leg stiffness per kg: k_leg = (F/m) / ΔL
- **Shin angle at touchdown:** knee–ankle line vs vertical (positive = ankle ahead of the knee).
- **Foot landing distance:** horizontal distance from the hip midpoint to the touching foot (heel or toe, whichever lands first) at touchdown, in meters via the homography.

## Limits
- 2D, single camera: rotations out of the sagittal plane (pelvis drop, foot turn-out) are not measured. The optional front camera shows them qualitatively.
- Pose models are least accurate at the feet and during fast leg swing. Key-frame values get a visual check.
- Research links are mostly correlational: recommendations are hypotheses we test with retests.
