# Backflip (Athlete B): measurement notes

Clip `B/backflip.mov`, frames 860–1140 (240 fps, see `timebase.md`). The flip is on the 25-yard line in the running band, so the main homography applies; camera drift is under 0.5 px. Scale at his depth is 7.36 mm/px.

**Pose.** MediaPipe Heavy loses an inverted body, so every frame was run four times (rotated 0/90/180/270°) and the most confident result kept. Key frames were checked by eye (`figures/B_backflip_keyframes.jpg`) and the skeleton follows the body through the whole flip. The centre of mass uses the Winter segment model and is smoothed at 8 Hz.

**Events**, from foot close-ups: toe-off at frame 935 ± 1, touchdown at 1091 ± 1.

| | value | uncertainty |
|---|---|---|
| Flight time | 0.650 s | ± 0.013 s |
| Gravity from a parabola fit to CM height in flight | 9.31 m/s² | 95% CI 9.12–9.55 (scale ± 3%): consistent with 9.81 at 240 fps; 120 fps would give 2.3 |
| CM vertical velocity at toe-off | 2.6 m/s | ± 0.2 |
| CM rise from toe-off to apex | 0.35 m | ± 0.03 |
| CM apex height above ground | 1.47 m | ± 0.05 |
| CM horizontal travel, toe-off → touchdown | +2 cm (backward) | ± 3 cm |
| Trunk angle at toe-off | 20° past vertical (leaning back) | ± 5° |
| Trunk rotation rate at toe-off | ≈ 490°/s | ± 100 |
| Trunk angle, +0.10 to +0.27 s | flat at 52–53° (no trunk rotation) | ± 5° |
| Tuck starts | ≈ +0.27 s (frame 1000, at the apex) | ± 0.02 s |
| Tightest tuck | hip ≈ 145° flexion, knee ≈ 135° | ± 10° |
| Peak trunk rotation rate | ≈ 830°/s, in the tuck | ± 100 |
| Trunk rotation by touchdown | 266° from upright (94° short of 360°) | ± 8° |
| Knee flexion at touchdown | ≈ 20° (nearly straight) | ± 8° |
| Knee flexion 0.08 s after touchdown | ≈ 75° | ± 8° |

Angles in the tucked and inverted phases are the least reliable (± 10° or more). Overlapping limbs are hard for MediaPipe even after rotation.
