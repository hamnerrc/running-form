# running-form

Research-grade, video-based running form analysis for two athletes. Videos, photos and measurements go into `data/`. An agent (e.g. Claude Code) runs the analysis and writes reports to `results/`.

> **Agent: start here.** This README is your full brief. Read it all, then [02](02-reference-sprint-longjump.md) and [03](03-reference-miler.md) for the reference values and [04](04-analysis-method.md) for formulas. Field instructions for the humans are in [01](01-plan-and-setup.md).

---

## 1. Athletes

| | Athlete A (jumper) | Athlete B (miler) |
|---|---|---|
| Event | Long jump, **right-foot takeoff** | Mile |
| Height | 5'9" (1.753 m) | 5'10" (1.778 m) |
| Current | PR 19'3" (5.87 m) | ~5:15 mile (estimated) |
| Goal | 22 ft (6.71 m) → needs ~8.5–9 m/s controlled approach speed | Sub-5:00 |
| Style | Elastic, technique-based (short contacts, bounce), not a power jumper | — |
| Measurements | **Full** (tape-measure segments, landmark tape, photos) | **Height only** → use anthropometric estimates, lower accuracy |
| Analysis focus | Max-velocity sprint mechanics for long jump; right vs left asymmetry | Economy at mile pace + speed mechanics; **filmed fatigued** (meet the day before) |
| This phase | No approach runs or jumps yet (cleared later); no spikes | — |

Health context (Athlete A's right ankle and left shin; Athlete B's shins) is in [02](02-reference-sprint-longjump.md), [01](01-plan-and-setup.md) and the session notes. Treat it as context for interpreting asymmetries and loading. **Never as a diagnosis.**

---

## 2. Filming setup (football field)

High-school football field (Santa Cruz High: artificial turf). Yard lines give exact distances, so no tape measure is needed for the zone.

```
 G1 goal line                                  50                 40 (G2 side)          G2 goal line   G2 end line
   |----------------------- 50 yd (45.7 m) ------|=== ZONE 10 yd ===|----- 40 yd -------------|--- 10 yd --|
   →  start here for → reps                       [cone]      [cone]           start here for ← reps (end line)  ←
                                                  [cone]      [cone]   ← 1.5 m (measured) across
                                                        📷  camera on the sideline at the G2-side 45, ~17–18 m away
```

- **Camera zone:** between the **50-yard line and the G2-side 40-yard line**, i.e. 50–60 yd from the G1 goal line. **10 yd = 9.144 m**, measured line center to line center. The **45-yard line** inside the zone is a free calibration check.
- **Run-ups on both sides:** → reps start at the G1 goal line (45.7 m before the zone). ← reps start at the G2 end line, the back of the end zone (also 45.7 m before the zone). Each athlete can start closer if he wants. For Athlete A, the last ~20 m before the zone is the "fly".
- **Running line:** along the near hash marks (~16 m from the sideline on high-school fields).
- **4 cones:** on the 50 and the 40, one at the hash line and one **1.5 m** further toward the field's center (measure it exactly). The athlete runs between them.
- **Camera:** tripod just behind the sideline at the 45-yard line in the zone (the G2-side 45), square to the running line, at hip height. Use the sideline on the runner's right when running → (G1 → G2). Sun not in the lens.
- **Camera settings:**
  - **Slo-mo 240 fps** (1080p is fine; 240 fps matters more than 4K)
  - Main **1×** lens or tele, **never the 0.5× ultra-wide** (lens distortion)
  - Lock focus/exposure (long-press)
  - Never move or re-zoom between reps
- **Optional 2nd phone** at the end of the running line facing the runner, at shin height (ankle rolling in or out).

---

## 3. What gets recorded

**Before the session (indoors, any time):**
1. **Tape-measure segments** (Athlete A, both sides, barefoot): height; floor → greater trochanter (leg length); trochanter → lateral knee joint line (thigh); knee joint line → lateral malleolus (shank); floor → lateral malleolus; foot length (heel → longest toe).
2. **Measurement photos** (Athlete A): front, right side and back in A-pose, from 3–4 m, camera at hip height, a known-length tape on the floor. Plus a natural-standing side photo.
3. **Knee-to-wall photos**, both feet, from the side, in the test position. (A: known 3" right vs 4.5" left.)

**At the field (in this order):**
1. **Calibration stand:** each athlete stands still sideways in the middle of the zone for 3 s, landmark tape on.
2. **Warm-up strides filmed:** A at 75% and 90% (one each through the zone).
3. **Athlete A:** 3 × flies through the zone, **alternating directions: rep 1 →, rep 2 ←, rep 3 →**. Put the camera on the sideline that's on the runner's **right** when running →. Then → reps film the right side (takeoff leg, twice) and the ← rep films the left. Confirm which side faces the camera in the video. 4–5 min rest.
4. **Athlete B:** 3 × mile pace (alternate directions if possible) · optional 1 × kick pace. He's already fatigued, so a separate "tired" pass isn't needed.
5. *(Optional, A, only if pain-free)* **pogo hops:** 10 on both legs, then 5 per leg, side-on in the zone.
6. *(Optional, A)* **one standing broad jump** in the zone, side-on.

**Landmark tape** (both athletes if possible, both sides): lateral malleolus, lateral knee joint line, greater trochanter, acromion, plus the heel of the shoe if possible. Use colors that stand out against the clothing.

Target times through the 10 yd zone: **A** 9 m/s → 1.02 s, 8.5 m/s → 1.08 s. **B** 5:15 pace = 5.11 m/s → 1.79 s; 5:00 pace = 5.36 m/s → 1.71 s.

---

## 4. Data intake (where to put files)

```
data/
  2026-11-15/                      ← one folder per session date
    session.yaml                   ← fill from data/_template/session.yaml
    A/
      measurements.yaml            ← tape measures (template provided)
      photos/      front.jpg side_R.jpg back.jpg natural_side.jpg ktw_R.jpg ktw_L.jpg
      video/       calib.MOV stride75.MOV stride90.MOV fly1.MOV fly2.MOV fly3.MOV pogo2.MOV pogoR.MOV pogoL.MOV broad.MOV
      video_front/ (optional 2nd phone, same names)
    B/
      measurements.yaml            ← height only is fine
      video/       calib.MOV mile1.MOV mile2.MOV mile3.MOV kick.MOV
models/
  pose_landmarker_heavy.task       ← not in git (see §7)
```

- **Video must be the original files** (AirDrop, or Share → Options → "All Photos Data"). Re-encoded files often lose 240 fps.
- **Raw videos and photos are git-ignored.** GitHub rejects files over 100 MB, and 240 fps clips get big. Keep them in `data/` locally; only `.yaml` files and `results/` get committed. If the raw files need a backup, use Git LFS or a cloud folder, and say which in `session.yaml`.
- If a file is named differently, map it in `session.yaml` under `reps:` rather than renaming originals.

---

## 5. Analysis pipeline (agent instructions)

Work in `src/` (Python). Make each stage a script that reads `data/<date>/` and writes `results/<date>/`, so it can be re-run.

1. **Ingest and verify.** Run `ffprobe` on every clip: real capture frame rate, resolution, duration, and **per-frame timestamps** (iPhone slo-mo can have variable timing, so use PTS, not nominal fps). Fail loudly for any clip under 120 fps, and list what's missing against `session.yaml`.
2. **Calibration (homography).** For each clip, mark the 4 cone positions plus the yard-line/hash intersections (a click tool, or detect the painted lines). Fit a ground-plane homography in meters: x along the running line (0 at the zone's entry line), y across. Report the **reprojection error** using the 45-yard line as a held-out check. Re-fit if the camera moved (detect drift between clips).
3. **Pose.**
   - MediaPipe Pose Landmarker Heavy, VIDEO mode, on every frame.
   - Crop/ROI around the runner if he's small in the frame.
   - Store raw landmarks with visibility scores.
4. **Landmark tape check (accuracy).**
   - Detect the tape markers (color threshold + tracking) on the near side.
   - Compare against the matching MediaPipe landmarks: report the error per joint in px and cm.
   - Where tape is reliably detected, **use the tape positions** for the near-side ankle/knee/hip/shoulder. Where it isn't, fall back to MediaPipe.
5. **Filtering.**
   - Zero-lag 4th-order Butterworth.
   - Cutoff chosen per signal by residual analysis (Winter). Expect ~10–15 Hz for sprinting and ~6–10 Hz for mile pace; report the cutoffs used.
6. **Segment-length constraint.**
   - Athlete A: compare the measured thigh and shank lengths with the tracked ones, frame by frame. Flag frames where the error exceeds 5%.
   - Athlete B: use Winter ratios from height instead (thigh 0.245 H, shank 0.246 H, trochanter height 0.530 H, foot 0.152 H) and **label B's results "estimated anthropometrics"**.
7. **Events.**
   - Touchdown and toe-off per foot, from heel/toe height above the ground plane plus vertical velocity.
   - Visually confirm a sample by exporting a contact sheet of ±3 frames around each event to `results/<date>/qa/`.
   - At 240 fps, ±1 frame = ±4.2 ms. Report that uncertainty on contact and flight times.
8. **Near vs far side.** Near-side leg = high confidence; far-side = low confidence (occlusion). Get each side's high-confidence values from the reps where that side faced the camera. Asymmetry = near-side values from → reps vs ← reps.
9. **Center of mass.** Segmental model (de Leva / Winter mass fractions) from landmarks. Also report the hip-midpoint proxy, and say which one each metric used.
10. **Metrics** (formulas in [04](04-analysis-method.md); mass cancels everywhere, no body weight needed):
    - **Sprint / mile, per step:**
      - Speed through the zone, step length, step rate
      - Contact time, flight time, duty factor
      - Foot landing distance ahead of the hips or CM; backward foot speed at touchdown
      - Shin, thigh, knee and trunk angles at touchdown and toe-off; thigh range of motion; max knee lift
      - CM vertical oscillation (÷ height), braking (dip in CM forward speed after touchdown)
      - Spring-mass vertical and leg stiffness per kg
    - **Strides vs flies (A):** how step length and step rate change with speed (his speed strategy).
    - **Pogo:** contact time, flight time, jump height h = g·t_f²/8, **RSI = h / t_c**, vertical stiffness. Right vs left for single-leg.
    - **Broad jump:** distance (takeoff toe → landing heel, via homography); CM takeoff speed and angle; countermovement depth.
    - **Knee-to-wall photos:** shin angle from vertical, each side.
    - **A-pose photos:** segment lengths via the floor-tape scale, as a cross-check against the tape measures.
11. **Compare to references.** A: [02](02-reference-sprint-longjump.md) (Lewis data, elite max-velocity norms, step length ÷ leg length). B: [03](03-reference-miler.md) (Folland economy and performance variables, Hanley 1500 m). Cite the reference behind each comparison.
12. **Report** → `results/<date>/`:
    - `report_A.md`, `report_B.md`: plain-language summary first, then the metrics table, comparisons, **1–3 ranked recommendations** (cue + 1–2 drills each), confidence levels, and the retest plan
    - `metrics_A.csv`, `metrics_B.csv`: one row per step (rep, side, all metrics, confidence)
    - `figures/`: annotated stills (touchdown, toe-off, max knee lift, per leg), angle traces, step-by-step charts
    - `qa/`: event contact sheets, landmark-vs-tape error table, homography check
    - Then tick the status boxes in §8 below and commit.

### Rules for the analysis
- **Never invent or estimate data that wasn't measured.** If something is missing, poor quality, or under 120 fps, say so and skip that metric.
- Every number gets an uncertainty or confidence level. Mean ± SD across steps; n is small, so don't over-claim.
- Research links are correlational. Frame recommendations as "toward what faster athletes do", to be tested at the retest.
- **Athlete A:**
  - Protect elasticity: no cues that trade short contacts for "pushing longer"
  - Strength-limited issues go to his RDL / broad-jump training, not to form cues
  - Watch the right (takeoff, previously injured) foot strike and right vs left asymmetry
- **Athlete B:**
  - Change little; trained runners self-optimize
  - Economy at mile pace, speed at the kick; foot strike gets no cue unless it causes braking
  - Interpret everything as **fatigued** data
- Pain-related observations: note them, recommend a professional if relevant, no medical advice.

---

## 6. Files
1. [01-plan-and-setup.md](01-plan-and-setup.md): field instructions and a glance-able field card
2. [02-reference-sprint-longjump.md](02-reference-sprint-longjump.md): Carl Lewis data and elite max-velocity norms (Athlete A)
3. [03-reference-miler.md](03-reference-miler.md): form research at mile pace (Athlete B)
4. [04-analysis-method.md](04-analysis-method.md): formulas and limits
5. `data/_template/`: `session.yaml` and `measurements.yaml` templates
6. `results/`: one folder per session

## 7. Environment
```bash
pip install mediapipe opencv-python numpy scipy pandas matplotlib pyyaml
# ffmpeg/ffprobe on PATH
mkdir -p models
curl -L -o models/pose_landmarker_heavy.task \
  https://huggingface.co/spaces/AleNunezArroyo/pose-detection-mediapipe/resolve/main/models/pose_landmarker_heavy.task
# official copy: https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task
```

## 8. Status
- [x] Research and reference values
- [x] Session plan, field setup, agent brief
- [ ] Baseline session filmed (2026-11-15)
- [ ] Baseline analysis: Athlete A
- [ ] Baseline analysis: Athlete B
- [ ] Retest (every 3–4 weeks)
- [ ] Athlete A approach / takeoff session (once cleared)
