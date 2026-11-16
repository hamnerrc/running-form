# Ingest check: 2026-11-15

| clip | athlete | type | dir | status | fps (PTS) | res | dur s | jitter ms |
|---|---|---|---|---|---|---|---|---|
| still_calibrate.mov | both | calibration |  | OK | 30 → real 240 | 1920×1080 | 37.40 | 0.00 |
| stand_still_calibrate.mov | both | calibration_stand |  | OK | 30 → real 240 | 1920×1080 | 4.67 | 6.29 |
| A/sprint_1_right.mov | A | fly | → | OK | 30 → real 240 | 1920×1080 | 14.92 | 1.19 |
| A/sprint_2_left.mov | A | fly | ← | OK | 30 → real 240 | 1920×1080 | 13.93 | 1.05 |
| A/sprint_3_right_control.mov | A | fly_control | → | OK | 30 → real 240 | 1920×1080 | 15.03 | 0.75 |
| A/sprint_4_left_control.mov | A | fly_control | ← | OK | 30 → real 240 | 1920×1080 | 13.88 | 1.54 |
| B/normal_1_right.mov.mov | B | mile_pace | → | OK | 30 → real 240 | 1920×1080 | 23.03 | 0.47 |
| B/normal_2_left.mov.mov | B | mile_pace | ← | OK | 30 → real 240 | 1920×1080 | 22.41 | 0.98 |
| B/normal_3_right.mov.mov | B | mile_pace | → | OK | 30 → real 240 | 1920×1080 | 22.37 | 1.12 |
| B/kick_4_right.mov | B | kick_pace | → | OK | 30 → real 240 | 1920×1080 | 16.79 | 1.26 |
| B/backflip.mov | B | backflip |  | OK | 30 → real 240 | 1920×1080 | 58.78 | 0.76 |

## Problems

- stand_still_calibrate.mov: 5 frame intervals >1.5× median (dropped frames?)
- MISSING photo A/photos/front.*
- MISSING photo A/photos/side_R.*
- MISSING photo A/photos/back.*
- MISSING photo A/photos/natural_side.*
- MISSING photo A/photos/ktw_R.*
- MISSING photo A/photos/ktw_L.*
- session.yaml: camera.distance_to_running_line_m is null
