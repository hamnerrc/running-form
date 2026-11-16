# Homography check

- **main**: fit RMSE 0.77 px · scale 7.22 mm/px at zone center · click-noise x uncertainty 0.6 cm median / 1.1 cm 95th pct (±0.7 px clicks)

## Drift vs reference frame (px)

- still_calibrate.mov: du -0.1, dv +0.0
- stand_still_calibrate.mov: du -15.8, dv +17.0
- A/sprint_1_right.mov: du -0.5, dv -0.3
- A/sprint_2_left.mov: du -0.1, dv -0.6
- A/sprint_3_right_control.mov: du +0.5, dv -0.9
- A/sprint_4_left_control.mov: du +0.4, dv -1.0
- B/normal_1_right.mov.mov: du -0.2, dv -0.5
- B/normal_2_left.mov.mov: du -0.0, dv -0.1
- B/normal_3_right.mov.mov: du +0.0, dv -0.7
- B/kick_4_right.mov: du +0.2, dv -0.6
- B/backflip.mov: du +0.4, dv +0.2

## Warnings

- stand_still_calibrate.mov: camera moved 23.2 px vs still_calibrate.mov — add a new setup for it
