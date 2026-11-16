# Athlete A: baseline sprint analysis (2026-11-15)

Long jumper, right-foot takeoff · 175.3 cm · 61.7 kg (136.0 lb) · long-jump spikes · goal **21'9" (6.63 m)** · 4 runs through the 10-yard zone, filmed side-on at 240 fps: 2 **flying sprints** (top speed after a running start) and 2 **approach-run simulations** (full speed with long-jump approach control, no jump).
All numbers come from `metrics_A.csv` and `report_A_data.md`. How they were measured is under "Confidence and data quality" at the end; the terms are defined in `04-analysis-method.md`.

## Summary

- **Not yet fast enough for 21'9": the approach needs about 0.9 mph more.** His own speed-to-distance equation (`02-reference`, optimal form) needs an **approach speed of 19.6 mph (8.77 m/s)** for 21'9". His approach-run simulations were **8.21 and 8.54 m/s** (± 0.07), on average **18.7 mph**, which the equation turns into about **20'4"** (± 3 in from the speed measurement alone, and less with imperfect form). His flying sprints were **8.49 and 8.83 m/s** (19.0 and 19.75 mph; the faster one was the ← run, with the slight tailwind). Averaged over the wind that is about **19.4 mph**, so even an approach at full sprint speed would predict only about 21'5".
- **His approach is already a high share of his top speed.** In both directions the approach-run simulation was **96.7%** of the flying sprint in the same direction (same wind). Professionals approach at about 92–97% of top speed, so the extra speed has to come from a faster top speed: about **20.2 mph** if he keeps 97%.
- **His running is elastic.** **Ground contact time** (how long the foot is on the ground) is **107 ± 10 ms**. The knee bends only about **4° more after touchdown** (26° at touchdown, 30° at most). **Thigh range of motion** is **100°**, the same as elite men. Protect this.
- **Step length is the gap; step rate is not.** **Step rate** is **4.5 steps per second**, close to the elite 4.7. **Step length** is **1.93 m = 1.98 × leg length**, against about 2.39 × for elite men. A longer step comes from more force into the ground, which is a job for strength training rather than a form cue (#1).
- **Touchdown distance is large:** the foot lands **0.38 ± 0.06 m ahead of the hips**, and is still moving forward over the ground (about +3 m/s) when it lands. This is the one leg-action item to work on (#2).
- **The arm swing is small in front.** The arm swings back well (about **68°** behind the trunk) but forward only to about **8°** in front, with the hand at mid-chest. Total shoulder range of motion is **76° ± 8°**, smaller than the 118–135° reported for Olympic 200 m finalists, and the arms stay in time with the legs. A low-confidence item to test (#4).
- **Right and left look the same.** Every right-minus-left difference is smaller than the normal step-to-step variation, including the right (takeoff, previously injured) foot.
- **In the approach-run simulations the flight time is longer.** Step length stays the same (1.95 vs 1.93 m), but **flight time** (time in the air each step) is 22 ms longer, so step rate drops from 4.5 to 4.1 per second (#3).

## Speed and the goal

| run | zone speed | mph | % of flying sprint, same direction | distance by his equation |
|---|---|---|---|---|
| flying sprint → (slight headwind) | 8.49 ± 0.07 m/s | 19.0 | — | 20'9" |
| flying sprint ← (slight tailwind) | 8.83 ± 0.07 m/s | 19.8 | — | 22'0" |
| approach-run simulation → | 8.21 ± 0.06 m/s | 18.4 | 96.7% | 19'10" |
| approach-run simulation ← | 8.54 ± 0.07 m/s | 19.1 | 96.7% | 21'0" |
| **needed for 21'9"** | **8.77 m/s** | **19.6** | — | 21'9" |

The equation applies to approach speed, so the approach-run rows are the ones to compare with the goal; the flying-sprint rows show his ceiling. Each distance is ± 3 in from the speed uncertainty, and the equation assumes optimal form, so it is a ceiling. The wind was slight and not measured.

## Metrics (near-side leg, mean ± SD across steps)

| metric | flying sprint | approach-run simulation | elite men, max velocity (02-reference) |
|---|---|---|---|
| Ground contact time (ms) | 107 ± 10 (n=7) | 109 ± 15 (n=6) | 90 (typ. 80–100) |
| Flight time (ms) | 115 ± 17 (n=6) | 137 ± 11 (n=6) | 124 |
| Step rate (steps/s) | 4.51 ± 0.35 | 4.07 ± 0.23 | ≈ 4.7 |
| Step length (m) | 1.93 ± 0.05 | 1.95 ± 0.10 | — |
| Step length ÷ leg length | 1.98 ± 0.05 | 1.99 ± 0.10 | ≈ 2.39 |
| Touchdown distance: foot ahead of hips (m) | 0.38 ± 0.06 | 0.39 ± 0.07 | "close under the body" |
| Foot speed over the ground at touchdown (m/s, + = forward) | ≈ +3 ± 1 | ≈ +3 ± 1 | fast backward sweep before touchdown |
| Shin angle at touchdown (°, + = ankle ahead of knee) | 5.5 ± 5.5 | 6.4 ± 4.9 | — |
| Knee flexion at touchdown / max during contact (°) | 26 / 30 | 27 / 35 | little knee bend during contact |
| Knee flexion at toe-off (°) | 11 ± 4 (n=5) | 14 ± 3 (n=4) | leave before the knee fully straightens |
| Heel recovery: max knee flexion in swing (°) | 150 ± 1 (n=5) | 150 ± 1 (n=4) | — |
| Thigh range of motion (°) | 100 ± 6 (n=5) | 90 ± 20 (n=4) | ≈ 100 |
| Knee drive: max thigh angle in front (°) | 67 ± 4 | 65 ± 2 | — |
| Trunk lean at touchdown (°, + = forward) | 8.5 ± 4 | 9.4 ± 4 | — |
| Foot strike | midfoot (6 of 7) | midfoot (5 of 6) | forefoot/midfoot at top speed |
| Peak vertical force (× body weight, model) | 3.3 ± 0.3 | 3.6 ± 0.4 | — |
| Vertical stiffness (kN/m, model) | 87 ± 14 | 82 ± 20 | — |

The force and stiffness rows come from the spring-mass model (Morin 2005), computed from contact time, flight time and speed. They are estimates, not force-plate measurements. Foot strike comes from the angle of the heel-to-toe line at touchdown (−1 ± 4°); MediaPipe's heel and toe points are rough, so treat it as low confidence.

### Arm action (near-side arm, flying sprints, n = 5 strides)

| measure | RC | reference (02-reference) |
|---|---|---|
| Arm swing forward: shoulder flexion, upper arm in front of the trunk (°) | 8 ± 5 | — |
| Arm swing back: shoulder extension, upper arm behind the trunk (°) | 68 ± 5 | — |
| Shoulder range of motion (°) | 76 ± 8 | ≈ 118 (slower) – 135 (faster) Olympic 200 m finalists* |
| Elbow angle at the front of the swing (°) | 62 ± 7 | ≈ 85–90 (coaching guidance) |
| Elbow angle at the back of the swing (°) | 128 ± 13 (opens to 152 ± 8 at most) | ≈ 95–100 (coaching guidance) |
| Elbow range of motion (°) | 98 ± 6 | ≈ 67 (slower) – 84 (faster)* |
| Hand height at the front, relative to the shoulder (m) | −0.13 ± 0.04 (mid-chest) | — |
| Hand behind the hips at the back (m) | 0.33 ± 0.11 | — |
| Arm–leg timing: arm furthest back → same-side knee furthest forward (ms) | −11 ± 5 (in time) | ≈ 0 |

*Mann's data, quoted second-hand; their angle definitions may differ from ours, so compare the pattern, not the exact numbers. The approach-run simulations had only 2 clean arm strides (shoulder range of motion 74°, the same pattern). Angles ± 5–10° per stride.

**Reading:** the arms move in time with the legs, which is what they are for. The swing is lopsided: it goes well behind the body, but forward the arm stops at about the side of the trunk with the hand at mid-chest, and the elbow opens almost straight at the back. The research does not support "pump the arms harder" as a speed fix (the arms mostly balance the legs), but his legs already move through an elite range while his arms move through a smaller one.

### Right vs left (near-side values; the right leg is seen on the → runs, the left on the ← runs)

| | R | L | R − L |
|---|---|---|---|
| Ground contact time (ms) | 108 ± 11 | 108 ± 14 | −1 |
| Step length (m) | 1.96 ± 0.09 | 1.92 ± 0.04 | +0.05 |
| Touchdown distance (m) | 0.39 ± 0.05 | 0.38 ± 0.08 | +0.02 |
| Knee flexion at touchdown (°) | 28.8 ± 5.4 | 24.2 ± 3.6 | +4.6 |
| Max knee flexion during contact (°) | 33 ± 5 | 29 ± 5 | +4 |
| Heel recovery (°) | 150 | 150 | 0 |
| Shoulder range of motion (°) | 74 | 78 | −4 |
| Peak force (× body weight) | 3.40 ± 0.24 | 3.46 ± 0.50 | −0.06 |

**Reading:** no asymmetry stands out from the noise. The right knee is about 4° more bent at touchdown and during contact, which is worth re-checking, but at n = 6–7 it can't be told apart from zero. Side is also mixed up with wind: all right-leg data come from headwind runs and all left-leg data from tailwind runs. The next session's 2 runs each way helps separate them.

## Recommendations (ranked)

### 1. Longer steps come from force, not a form cue (confidence: medium-high)
His step rate is close to elite, but his step is about 17% shorter relative to leg length. His contacts are already short and stiff, so the way to a longer step is more force into the ground in the same short contact. Telling him to "push longer" would trade away the elasticity. This goes to his **Romanian deadlift and broad-jump training**, not to a cue. It is also the route to the 21'9" speed: step rate is already near elite, so the roughly 4% of extra top speed (19.4 → about 20.2 mph, keeping his 97% approach) has to come mostly from a longer step (about 1.93 → 2.01 m at the same rate).
- **Track:** step length ÷ leg length at each retest. It should rise as strength rises, with ground contact time staying around 100–110 ms.

### 2. Reduce touchdown distance with an active foot strike (confidence: medium)
**What we see:** at touchdown the foot is 0.38 m ahead of the hips (± 0.04 m from the ±1-frame timing) and still moving forward over the ground. Shin and knee angles are fine (shin about 5° past vertical, knee 26°); the foot is simply placed out in front instead of swept back into the ground. The centre of mass (CM) loses about 6% of its speed just after touchdown (**braking**). That estimate is noisy (± 3%), but it points the same way.
**Why:** faster sprinters land closer under the body and sweep the foot backward before touchdown (02-reference: Sides; J Hum Kinet).
- **Cue:** "Step down and back. Hit the ground under your hips."
- **Drills:** (a) A-skips → straight-leg bounds, focusing on pulling the foot back, 2 × 20 m. (b) Wicket runs: 8–10 mini-hurdles about 1.9–2.0 m apart (his current step), at about 90% speed, 3–4 runs. The wickets stop the step from reaching out in front.
- **Retest target:** touchdown distance going down while ground contact time does **not** go up.

### 3. In approach runs, control with rhythm rather than longer flight (confidence: low-medium)
**What we see:** the approach-run simulations keep the same step length but add about 22 ms of flight time to every step (137 vs 115 ms), so step rate drops from 4.5 to 4.1 per second and speed drops 0.3 m/s. "Control" currently means bouncing higher and slower.
**Why it may matter:** a long-jump approach is built on a consistent, quick rhythm, and his elastic profile suits a frequency-driven approach (Lewis model, 02-reference). With only 6 steps per condition, this is something to test, not a finding.
- **Cue for approach runs:** "Quick and relaxed. Same rhythm, just don't strain."
- **Drill:** approach runs to a clap or metronome at his flying-sprint step rate (about 4.5 steps per second); compare flight time at the next session.

### 4. Arm swing: let the hands come up in front (confidence: low)
**What we see:** shoulder range of motion of 76°, almost all of it behind the trunk; in front, the hand stops at mid-chest. The elbow opens to about 150° at the back.
**Why it may matter:** faster sprinters in Mann's data had a larger arm swing at the shoulder; the arms balance the legs, and his leg range of motion is already elite-sized. The evidence on arms is thin (Macadam 2018), so this is a test, not a fix: if it costs relaxation or rhythm, drop it.
- **Cue:** "Hip to lip": the hand passes the hip pocket at the back and comes up to chin height in front, elbow staying about 90°.
- **Drill:** seated or standing arm swings at sprint rhythm, 3 × 10 s, then 2–3 relaxed strides carrying the same swing.
- **Retest target:** shoulder flexion in front going up (toward 30°+), with step rate and ground contact time unchanged or better.

**Not recommended:** anything that lengthens ground contact. Trunk lean, knee drive (67°), heel recovery (150°) and thigh range of motion (100°) are all in a normal or good range.

## Confidence and data quality

- **Timing.** Every frame of the slo-mo renders is 1/240 s. That was verified: no speed ramps, and gravity from Athlete B's backflip comes out right only at 240 fps (`qa/timebase.md`). Contact and flight times are ± 4 ms per edge, ± 8 ms worst case.
- **Distances.** Homography from the 20/25/30 yard lines, the painted cone line and the 3 m far markers. Fit RMSE 0.8 px. Click-noise sensitivity is 0.6 cm (median) along the running line. Independent check: the 1-yard ticks on the far hash, 10 m beyond the calibration points, come out at 0.915 m spacing (true 0.914). Zone speed is ± 0.07 m/s.
- **Events.** Auto-detected events were spot-checked on foot close-ups to within ±1 frame. Three contacts were wrong, all where the white spikes were over white paint (the 20, the "0", the 25-yard line), and were corrected by hand in `data/2026-11-15/events_override.yaml`. In those same frames MediaPipe's knee also jumped, so late-contact joint angles for those steps are left blank, not guessed. That is why some n values are 4–5.
- **Joint angles.** Pose from MediaPipe Heavy, without landmark tape (none was worn). Leg angles are about ± 5° per step, arm angles ± 5–10° per stride (arm frames with implausible arm lengths are dropped). The thigh landmark is not the bony trochanter, which the segment check accounts for. The far-side leg is reported separately and is lower confidence.
- **Forces and stiffness.** Spring-mass model estimates. Mass is 61.7 ± 0.5 kg (136.0 lb).
- **Small n.** 2 runs per condition and 6–7 near-side steps each. Treat differences of a few ms or a few degrees as noise.

## Next session (≈ mid-December; plan in `01-plan-and-setup.md`)
Same field and setup, plus a ribbon on the far marker to show the wind. **2 flying sprints and 2 approach-run simulations each way** (separates right/left from wind), then **2 full jumps into the pit**, filmed from a second camera at the board. Send the **original** slo-mo files ("All Photos Data" on), wear a fitted short-sleeve shirt so the arms are visible, and write down the official distance of each jump.
- **Field:** step length ÷ leg length, touchdown distance and ground contact time on the flying sprints; flight time, step rate, and speed as a % of the flying sprint on the approach runs; arm swing in front.
- **Goal check:** approach-run speed against the **19.6 mph (8.77 m/s)** needed for 21'9".
- **Pit (new):** approach speed over the last two steps, penultimate vs last step length, centre-of-mass lowering, takeoff contact time (pros 0.12–0.13 s), touchdown (plant) angle (pros ≈ 58–62°), takeoff angle (pros ≈ 18–24°), vertical speed at takeoff, speed lost in the takeoff, and how far behind the board he takes off, compared with the official distance and the equation's prediction.
