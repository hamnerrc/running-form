# running-form

Research-grade, video-based running form analysis for two athletes (more may join; add them to `session.yaml`). Videos, photos and measurements go into `data/`. An agent (e.g. Claude Code) runs the analysis and writes reports to `results/`.

> **Agent: start here.** This README is your full brief. Read it all, then [02](02-reference-sprint-longjump.md) and [03](03-reference-miler.md) for the reference values and [04](04-analysis-method.md) for formulas. Field instructions for the humans are in [01](01-plan-and-setup.md).

---

## 1. Athletes

| | Athlete A (jumper) | Athlete B (miler) |
|---|---|---|
| Event | Long jump, **right-foot takeoff** | Mile |
| Height | 5'9" (1.753 m) | 5'10" (1.778 m) |
| Current | PR 19'3" (5.87 m) | ~5:15 mile (estimated) |
| Goal | 21'9" (6.63 m) → needs ≈ 19.6 mph (8.77 m/s) approach speed by his equation (see 02) | Sub-5:00 |
| Style | Elastic, technique-based (short contacts, bounce), not a power jumper | — |
| Measurements | **Full** (tape-measure segments, landmark tape, photos) | **Height only** → use anthropometric estimates, lower accuracy |
| Analysis focus | Max-velocity sprint mechanics for long jump; right vs left asymmetry | Economy at mile pace + speed mechanics; **filmed fatigued** (meet the day before) |
| Next session | ≈ mid-Dec 2026: 4 flying sprints, 4 approach-run simulations, 2 full takeoffs into the pit (long-jump spikes) | to be decided |

Health context (Athlete A's right ankle and left shin; Athlete B's shins) is in [02](02-reference-sprint-longjump.md), [01](01-plan-and-setup.md) and the session notes. Treat it as context for interpreting asymmetries and loading. **Never as a diagnosis.**

---

## 2. Filming setup

The setup used on 2026-11-15 is the standard; repeat it exactly so sessions compare. Step-by-step instructions and the field card are in [01](01-plan-and-setup.md).

**Field (sprints and approach-run simulations).** Santa Cruz High football field (artificial turf).
- **Zone:** 20-yard line → 30-yard line = **10 yd (9.144 m)**, line centre to line centre.
- **Markers:** orange cones on the painted line through the 20 and 30 (near row); red bottle on the 20 and black cylinder on the 30, **3.0 m** further across (far row). A ribbon on the cylinder shows the wind in frame.
- **Camera:** near sideline, square to the 25-yard line, hip height. The 20/25/30 lines and all markers in frame. Calibration = the 6 line × marker-row intersections (`data/<date>/calib.yaml`, setup `main`): fit RMSE 0.8 px, ±0.6 cm along the line on 2026-11-15.
- **Run-ups:** flying sprints start ≥ 30 m before the zone. Approach-run simulations use the full approach with the last step on the far zone line (the 30 for →, the 20 for ←), so the zone is the last 10 yd before the "board".

**Pit (takeoffs).** Camera on the runner's right as he runs toward the pit (takeoff leg toward the camera), ~10 m from the runway centre line, hip height, centred ~2.5 m before the board. Six tape marks on the runway edges at the board's front edge, 2.5 m and 5.0 m before it, plus the measured runway width, give the homography (setup `pit`, `board_x_m: 0`). World x points toward the pit, so takeoff reps are always direction "→" with `near_side: R`.

**Camera settings (both):** slo-mo **240 fps**, 1080p · **1× lens, never 0.5×** · lock focus/exposure · never touch the phone between reps · send the **original files** (AirDrop, "All Photos Data" on).

---

## 3. What gets recorded

Per session (details in [01](01-plan-and-setup.md)):
1. **Calibration clips:** 5 s of the empty zone (field) and of the empty runway with markers (pit); a 3 s standing clip of each athlete, side-on.
2. **Athlete A:** flying sprints (2 →, 2 ←), approach-run simulations (2 →, 2 ←), full takeoffs into the pit (2+), with the official distance, foul or not, and approach length written on each rep line.
3. **Other athletes** as agreed (e.g. Athlete B: 3 × mile pace alternating directions, 1 × kick).
4. **On the day:** body mass, shoes, temperature, wind per rep, effort (1–10) per rep, sleep and soreness.
5. **Optional:** pink landmark tape on the camera side (ankle bone, knee side, hip bone, shoulder top, elbow, wrist); tape-measured segments for any new athlete (else segments come from video, as for B).

Rep types in `session.yaml`: `calibration`, `calibration_stand`, `fly` (flying sprint), `approach_sim` (`fly_control` in 2026-11-15 data), `takeoff`, `mile_pace`, `kick_pace`, `pogo_double|right|left`, `backflip`. Any extra key on a rep line (e.g. `official_m`, `foul`, `approach_steps`, `effort`, `near_side`) is kept and used where relevant.

---

## 4. Data intake (where to put files)

```
data/
  _template/                       ← session.yaml, calib.yaml, measurements.yaml to copy
  <YYYY-MM-DD>/                    ← one folder per session date
    session.yaml                   ← reps, conditions, goals (from the template)
    calib.yaml                     ← homography points per camera setup (main, pit)
    events_override.yaml           ← optional hand-corrected contacts (frame pairs)
    field_calibrate.MOV  field_stand.MOV  pit_calibrate.MOV
    A/  measurements.yaml  sprint_*.MOV  approach_*.MOV  jump_*.MOV
    B/  measurements.yaml  ...
models/
  pose_landmarker_heavy.task       ← not in git (see §7)
  kokoro/                          ← TTS model for the narrated videos (not in git)
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
      - Heel recovery (max knee flexion in swing), foot strike (foot angle at touchdown)
      - Arm action: shoulder range of motion, elbow angle front/back, hand height, hand behind hip, arm–leg timing
    - **Approach-run simulations (A):** zone speed as % of the best flying sprint, and the distance his speed equation predicts vs the goal (`report.goal_table`).
    - **Takeoffs (A):** approach speed over the last two steps, last-three step lengths, contact times, CM lowering, takeoff contact time, touchdown (plant) angle, takeoff knee, trunk lean, free-leg knee drive, CM velocity at touchdown/toe-off, takeoff angle, horizontal velocity loss, toe-to-board distance, official vs effective distance, equation prediction (`takeoff.py`, references in 02).
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
- **Use standard sprint and jump terms only** (glossary in [04](04-analysis-method.md#terms)); never invent terms. Explain each term in plain words the first time it appears, and write so a non-specialist can follow.
- **Athlete A's goal** is 21'9" (6.63 m). Set speed goals with his equation in [02](02-reference-sprint-longjump.md) (≈ 19.6 mph approach speed), not with a generic estimate.
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
python3 -m venv .venv && .venv/bin/pip install --only-binary :all: -r requirements.txt
# pinned for macOS 12 x86_64 wheels; PyAV reads per-frame timestamps, so ffprobe is optional
.venv/bin/python -m pytest -q          # synthetic ground-truth tests
.venv/bin/python -m runform --help     # stages; run from repo root with PYTHONPATH=src
mkdir -p models
curl -L -o models/pose_landmarker_heavy.task \
  https://huggingface.co/spaces/AleNunezArroyo/pose-detection-mediapipe/resolve/main/models/pose_landmarker_heavy.task
# official copy: https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task

# PDF reports (reportlab; the macOS system python3 has it): figures + name map per report in results/<date>/pdf_build.json
python3 tools/build_pdfs.py results/2026-11-15/pdf_build.json

# narrated videos: local TTS (Kokoro-82M) in its own venv, because it needs numpy >= 2
python3 -m venv .venv-tts && .venv-tts/bin/pip install onnxruntime==1.19.2 "numpy>=2" colorlog espeakng-loader phonemizer-fork soundfile \
  && .venv-tts/bin/pip install --no-deps kokoro-onnx==0.4.9
mkdir -p models/kokoro && for f in kokoro-v1.0.onnx voices-v1.0.bin; do curl -L -o models/kokoro/$f \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f; done
cd src && ../.venv/bin/python -m runform.explainer ../results/2026-11-15/video/RC_shots.yaml
```

## 8. Status
- [x] Research and reference values
- [x] Session plan, field setup, agent brief
- [x] Baseline session filmed (2026-11-15): 30 fps renders of 240 fps slo-mo (timing inferred, see results/2026-11-15/qa/timebase.md); no landmark tape; no A photos
- [x] Baseline analysis: Athlete A (results/2026-11-15/report_A.md)
- [x] Baseline analysis: Athlete B (results/2026-11-15/report_B.md, incl. backflip; segments video-estimated)
- [x] Narrated analysis videos (results/2026-11-15/video/video_RC.mp4, video_Vinni.mp4; shot lists *_shots.yaml; render with `python -m runform.explainer`, TTS = Kokoro-82M in .venv-tts)
- [x] Goal set: 21'9" (6.63 m) ≈ 19.6 mph approach speed by Athlete A's equation; reports corrected (2026-11-15)
- [x] Arm action, heel recovery and foot strike added to the analysis and to the 2026-11-15 reports
- [x] Next-session setup ready: plan + field card (01), templates (`data/_template/` session, calib with `pit` setup), takeoff analysis (`takeoff.py`), speed-vs-goal table, reference values (02), terms (04)
- [ ] Retest + takeoff session (≈ mid-December 2026): copy the templates, file the clips, run `runform all`, then write the reports
- [ ] Ask other athletes whether they want analysis
