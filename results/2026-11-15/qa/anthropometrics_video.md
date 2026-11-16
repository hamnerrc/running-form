# Athlete B segment lengths from video

Source: `stand_still_calibrate.mov` (real-time 30 fps, 136 frames). Both athletes stand side-on on the running band and then turn around, so each side faces the camera for part of the clip. MediaPipe Heavy ran on every frame: 126 detections of A and 128 of B.

**Why A is the reference.** MediaPipe's "hip" is a hip-joint-centre estimate, not the greater trochanter. Its raw thigh for A is 39.3 cm against the 47.5 cm tape measure. The camera scale at each athlete's depth is also uncertain: the camera had moved 23 px since the empty-field clip. Taking every length relative to the same athlete's MediaPipe eye height, and then comparing B with A, cancels both effects.

| | A: MediaPipe / eye height | B: MediaPipe / eye height | B/A | A tape (cm) | **B estimate (cm)** |
|---|---|---|---|---|---|
| thigh (L/R mean) | 0.2514 | 0.2524 | 1.004 | 47.5 | **47.9 ± 2.5** |
| shank (L/R mean) | 0.2520 | 0.2522 | 1.001 | 41.5 | **41.7 ± 2.5** |
| floor → hip | 0.5559 | 0.5548 | 0.998 | 97.75 | **97.9 ± 3.0** |

Scaled by height ratio 176.0 / 175.3 = 1.004.

**Uncertainty.** The frame-to-frame interquartile range is about ±2.5% for thigh and shank. The method also assumes both athletes' eye height is the same fraction of stature and that MediaPipe's landmark bias is the same for both. Each assumption is probably good to a few percent, so the ± values above are deliberately generous. Foot length could not be measured, so the Winter ratio is used (0.152 H = 26.8 cm).

**Cross-check.** Raw MediaPipe eye heights through the shifted homography are A 1.563 m and B 1.629 m. The expected values are about 1.64 and 1.65 m (0.936 H). The absolute scale in this clip is therefore 1–5% off. That is why the ratio method is used instead of the raw lengths.
