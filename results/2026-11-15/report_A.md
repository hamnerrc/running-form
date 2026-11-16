# RC (Athlete A): sprint analysis against the professional model (2026-11-15)

Long jumper, right-foot takeoff · 175.3 cm · 61.7 kg (136.0 lb) · long-jump spikes · goal **21'9" (6.63 m)** · 4 runs through the 10-yard zone, filmed side-on at 240 fps: 2 **flying sprints** (top speed after a running start) and 2 **approach-run simulations** (full speed with long-jump approach control, no jump).

**How this was analysed.** Every stride was judged at the five **key positions** professional coaches use (toe-off, top of flight, strike, touchdown, full support; ALTIS kinogram method) and measured the same way as two published datasets: the **2017 World Championships 100 m finalists** (Bissas et al. 2022, 11.6 m/s) and **US college track athletes and team-sport athletes filmed exactly like us** (Clark et al. 2025: 240 fps iPhone, 10 m away; track group at 10.0 m/s, team-sport group at 8.2–9.3 m/s, which is RC's speed). The full model and sources are in `02-reference-sprint-longjump.md`; the definitions are in `04-analysis-method.md`. Numbers come from `positions_A.csv/.md` (key positions) and `metrics_A.csv` (timing, forces, arms).

This version replaces the first report. The first report missed the swing-leg positions completely and wrongly concluded that his form was close to elite apart from strength. See "Corrections" at the end.

## Summary

- **The main gap is the swing leg at touchdown: no "figure 4".** At touchdown professionals have already brought the swing knee through to about level with the stance knee, with the heel folded high under the hips (from the side, the legs make a "4"). RC's swing knee is still **21 ± 8 cm behind** his stance knee, and the swing heel is **30 ± 6 cm behind his hips**. The angle between his thighs (**thigh separation**) is **−34 ± 12°**, against **−10 ± 11°** for world-class 100 m finalists. That is about 2 SD outside their range, and every run averages behind them (run means −16° to −45°; 13 of the 14 measurable touchdowns are further behind than −10°). His swing thigh at touchdown (+1°) sits between the **team-sport group** in Clark 2025 (−9°) and the track groups (+11 to +15°). This is **back-side mechanics**.
- **Why it happens: the push-off finishes too far behind, then the thigh comes forward too slowly.** At toe-off his push-off leg is almost straight: **knee 169 ± 4°** vs world-class **154 ± 4°**, **hip 211 ± 4°** vs **196 ± 3°**, thigh **−33° behind** vs **−25°**. Professionals leave the ground before the leg is straight. RC pushes to full extension, so his leg starts its recovery about 8° further back. During the flight that follows it then comes forward about 34°, where the professionals' swing leg comes forward about 42°. The two gaps add up to the ≈ 16° he is short at touchdown.
- **Knee lift and thigh speed are below the track group.** Knee lift (max thigh angle in front) is **67 ± 4°** vs **76 ± 6°** for the 10 m/s track group. The **front-side share** of thigh motion is **67%** vs 73%. **Thigh angular velocity** (how fast the thighs scissor) is **447 ± 36 °/s** vs **483 ± 29** (track) and **428** (team sport). Within trained groups, thigh angular velocity is the variable that predicts top speed (Clark 2025). It takes hip flexor and hip extensor strength and speed, which is where strength training connects to the positions.
- **What is already at a professional level:** stance knee at touchdown (**154°** vs 156°), stance hip (**140°** vs 140°), shin angle (5° vs 9°), **touchdown distance** (toe tip **0.37 m** ahead of the CM vs 0.38 m), foot speed at touchdown (+2.5 vs +2.4 m/s), heel fold in swing (swing knee **53°** vs 49°), ground contact time (**107 ms**, short and stiff, with only ~4° of knee bend after touchdown), and thigh separation at toe-off (98° vs 93°). **The landing itself is fine; the leg that is not landing is the problem.**
- **Speed vs the goal: about 1 mph short in the approach.** His equation needs **19.6 mph (8.77 m/s)** of approach speed for 21'9". His approach runs averaged **18.7 mph** (8.21 and 8.54 ± 0.07 m/s, about 20'4" by the equation). His flying sprints were 19.0 and 19.8 mph, and each approach run was 96.7% of the flying sprint in the same direction, which is already high. The extra mph has to come from a higher top speed. At his near-elite step rate (4.5 per second) that means a longer step (1.93 m = 2.0 leg lengths vs elite 2.4), and the swing-leg and thigh-speed gaps above are the form part of that.
- **Possible right/left difference in the swing leg:** with the **left** leg swinging (i.e. at right-foot touchdowns, the takeoff foot), thigh separation is −44 ± 11° vs −29 ± 10° with the right leg swinging. At the board the left leg is the free leg. With n = 3–5 and left/right mixed up with wind direction, this needs the next session to confirm.

## Key positions vs professionals (flying sprints; approach runs in brackets)

| when | measure | RC | world-class 100 m | college track (10 m/s) / team sport (8.2–9.3 m/s) | verdict |
|---|---|---|---|---|---|
| touchdown | **thigh separation** (− = swing knee behind) | **−34 ± 12°** (−25) | −10 ± 11° | — | **behind** |
| | **swing thigh** vs vertical (+ = in front) | **+1 ± 11°** (+7) | ≈ +17° | +15 ± 14° / −9 ± 8° | **behind** (between team sport and track) |
| | swing knee vs stance knee | **21 ± 8 cm behind** (13) | ≈ level ("knees together") | — | **behind** |
| | swing heel behind the hips | **0.30 ± 0.06 m** (0.24) | — (heel under the hips) | — | behind |
| | swing knee angle (heel fold) | 53 ± 11° (44) | — | 49 ± 7° / 65 ± 7° | good |
| | stance knee / hip angle | 154 / 140° | 156 / 140° | — | good |
| | shin angle (+ = ankle ahead) | 5 ± 6° | 9 ± 4° | — | good |
| | leg angle (CM → foot) | 16 ± 3° | — | 13 ± 2° / 17 ± 2° | ok (team-sport level) |
| | touchdown distance (toe tip ahead of CM) | 0.37 ± 0.05 m | 0.38 ± 0.04 m | — | good |
| | foot speed over the ground | +2.5 ± 0.7 m/s | +2.4 ± 0.5 m/s | — | good |
| | trunk lean | 8 ± 4° | 14.5 ± 3° | — | more upright (low confidence) |
| toe-off | **push-off knee angle** | **169 ± 4°** (166) | **154 ± 4°** | — | **too straight** |
| | **push-off hip angle** | **211 ± 4°** (204) | **196 ± 3°** | — | **too far behind** |
| | trailing thigh | −33 ± 4° (−31) | −25 ± 3° | — | too far behind |
| | thigh separation | 98 ± 5° | 93 ± 7° | — | good |
| full support | swing knee ahead of stance knee | 9 ± 3 cm | — | — | ok (caught up) |
| | swing heel above stance knee | 28 ± 3 cm | — | — | ok |
| swing | knee lift (max thigh in front) | **67 ± 4°** | — | **76 ± 6°** / 64 ± 5° | low |
| | max thigh behind | −33 ± 5° | — | −28 ± 7° / −35 ± 5° | team-sport level |
| | thigh range of motion | 100 ± 6° | — | 105 ± 7° / 99 ± 6° | ok |
| | front-side share | 67 ± 4% | — | 73% / 65% | team-sport level |
| | **thigh angular velocity** | **447 ± 36 °/s** | — | **483 ± 29** / 428 ± 30 | between |
| | peak thigh angular acceleration | 9.9 ± 1.0 k°/s² | — | 11.0 ± 0.9 / 9.2 ± 1.0 | between |
| contact | leg excursion (CM → foot angle swept) | 49 ± 5° | — | 56 ± 4° / 61 ± 4° | short (fits his short contact) |

Angles ± 5° per touchdown (± 8° for the far leg), distances ± 3 cm. n = 5–8 touchdowns per value; each value uses only touchdowns where the leg it depends on faced the camera. Approach-run swing values are noisier (two tracking glitches removed).

**How to see it:** `figures/kinogram_A_sprint_1_right.jpg` shows all five positions for a right and a left touchdown. `figures/model_td_A_*.jpg` and `figures/model_to_A_*.jpg` show his touchdown and toe-off with the world-class average drawn over him in white (the published mean angles, sized to his own segment lengths, anchored at his foot). In the touchdown frames his swing shin points straight back at hip height while the white swing knee is forward and the white heel is tucked under. In the toe-off frames his push-off leg is straight while the white leg is still bent.

## Speed and the goal

| run | zone speed | mph | % of flying sprint, same direction | distance by his equation |
|---|---|---|---|---|
| flying sprint → (slight headwind) | 8.49 ± 0.07 m/s | 19.0 | — | 20'9" |
| flying sprint ← (slight tailwind) | 8.83 ± 0.07 m/s | 19.8 | — | 22'0" |
| approach-run simulation → | 8.21 ± 0.06 m/s | 18.4 | 96.7% | 19'10" |
| approach-run simulation ← | 8.54 ± 0.07 m/s | 19.1 | 96.7% | 21'0" |
| **needed for 21'9"** | **8.77 m/s** | **19.6** | — | 21'9" |

The equation applies to approach speed, so the approach-run rows are the ones to compare with the goal; the flying-sprint rows show his ceiling. Each distance is ± 3 in from the speed uncertainty, and the equation assumes optimal form, so it is a ceiling. Professionals approach at about 92–97% of top speed, so keeping 97% means a top speed of about **20.2 mph (9.0 m/s)**. The wind was slight and not measured.

## Timing and stride (near-side leg, mean ± SD across steps)

| metric | flying sprint | approach-run simulation | elite men, max velocity |
|---|---|---|---|
| Ground contact time (ms) | 107 ± 10 (n=7) | 109 ± 15 (n=6) | 93 (world-class 100 m); 80–100 |
| Flight time (ms) | 115 ± 17 (n=6) | 137 ± 11 (n=6) | 116–124 |
| Step rate (steps/s) | 4.51 ± 0.35 | 4.07 ± 0.23 | 4.7–4.8 |
| Step length (m) | 1.93 ± 0.05 | 1.95 ± 0.10 | 2.42 (world-class 100 m) |
| Step length ÷ leg length | 1.98 ± 0.05 | 1.99 ± 0.10 | ≈ 2.39 |
| Knee flexion at touchdown / max during contact (°) | 26 / 30 | 27 / 35 | little knee bend during contact |
| Heel recovery: max knee flexion in swing (°) | 150 ± 1 (n=5) | 150 ± 1 (n=4) | — |
| Foot strike | midfoot (6 of 7) | midfoot (5 of 6) | forefoot/midfoot at top speed |
| Peak vertical force (× body weight, model) | 3.3 ± 0.3 | 3.6 ± 0.4 | — |
| Vertical stiffness (kN/m, model) | 87 ± 14 | 82 ± 20 | — |

Force and stiffness come from the spring-mass model (Morin 2005), not force plates. Foot strike is low confidence (MediaPipe's heel and toe points are rough).

**In the approach runs** the step length stays the same (1.95 vs 1.93 m), but flight time is 22 ms longer, so step rate drops from 4.5 to 4.1 per second. The swing leg is slightly less far behind at touchdown (separation −25° vs −34°), which fits the longer flight: the leg simply has more time to come through. The pattern is the same, just slower.

## Arm action (near-side arm, flying sprints, n = 5 strides)

| measure | RC | reference |
|---|---|---|
| Arm swing forward: shoulder flexion, upper arm in front of the trunk (°) | 8 ± 5 | — |
| Arm swing back: shoulder extension, upper arm behind the trunk (°) | 68 ± 5 | — |
| Shoulder range of motion (°) | 76 ± 8 | ≈ 118 (slower) – 135 (faster) Olympic 200 m finalists* |
| Elbow angle at the front / back of the swing (°) | 62 ± 7 / 128 ± 13 (opens to 152 ± 8) | ≈ 85–90 / 95–100 (coaching guidance) |
| Hand height at the front, relative to the shoulder (m) | −0.13 ± 0.04 (mid-chest) | — |
| Hand behind the hips at the back (m) | 0.33 ± 0.11 | — |
| Arm–leg timing (ms) | −11 ± 5 (in time) | ≈ 0 |

*Mann's data, second-hand; angle definitions may differ. **Reading:** the arms mirror the legs. Like his legs, the swing is back-side: the arm goes well behind the body with the elbow opening almost straight, and forward it stops at the side of the trunk with the hand at mid-chest. Fixing the leg recovery and letting the arms come forward together are the same change seen from two places.

## Right vs left

| | R (seen on → runs) | L (seen on ← runs) |
|---|---|---|
| Ground contact time (ms) | 108 ± 11 | 108 ± 14 |
| Step length (m) | 1.96 ± 0.09 | 1.92 ± 0.04 |
| Thigh separation at touchdown, by **swing** leg (°), flying sprints | −29 ± 10 (R swinging, n=5) | **−44 ± 11** (L swinging, n=3) |
| Push-off knee / hip at toe-off (°), flying sprints | 168 / 209 | 172 / 218 |
| Heel recovery (°) | 150 | 150 |
| Shoulder range of motion (°) | 74 | 78 |

**Reading:** timing is symmetrical. The left leg may recover later and push off further behind than the right, which would matter at the board because the left is his free leg. Side is mixed up with wind (all left-leg data come from tailwind runs), so this is a "check next session", not a finding.

## What this means for the long jump

- **The free leg at the board.** In the takeoff the free (left) leg has to be driven forward and up during a ~0.12 s contact. One elite case study measured the free thigh at ≈ 790 °/s at toe-off and called its speed a key factor. A free leg that arrives at the board still behind the hips has further to go in that time. The pit session will measure free-thigh angle at board touchdown and toe-off directly.
- **Speed.** Better recovery and faster thigh scissoring are part of how the step lengthens without losing step rate, which is where the missing ~1 mph comes from.
- **Last steps.** The same push-off habit (driving to a straight leg behind) on the penultimate step would make the CM lowering and the quick last step harder. Measured next session.

## Recommendations (ranked)

### 1. Recover the swing leg earlier: "figure 4" at touchdown (confidence: medium-high)
**What we see:** at touchdown his swing knee is 21 cm behind the stance knee and his heel 30 cm behind the hips (world-class: knees about together, heel under the hips). Thigh separation is −34° vs −10°.
**Why it matters:** a swing leg that is still behind at touchdown can't help drive the next step down and back, and needs a bigger, later swing. Faster groups are more front-side, and coaches at every level use "knees together at touchdown" as the check (Mann; Seagrave; ALTIS).
- **Cues:** "Toe up, knee up, heel forward." "Step over the opposite knee." "Snap the knees together as you land."
- **Drills:** dribbles (ankle → calf → knee height: the foot steps over the opposite ankle/shin/knee and lands under the hips), 3 × 20 m each height. A-skips with a "figure 4" check at each landing, 2 × 20 m. Wall drill "figure 4" switches (stance leg straight, swing thigh up, heel under the hip; switch on a clap), 3 × 5. Wicket runs (mini-hurdles about 1.9–2.0 m apart at ~90% speed, 3–4 runs): the wickets force the knee to come forward and up.
- **Retest target:** thigh separation at touchdown from −34° toward −15°, and the swing knee within ~10 cm of the stance knee, with ground contact time not longer.

### 2. Leave the ground before the leg is straight (confidence: medium)
**What we see:** push-off knee 169° and hip 211° at toe-off (world-class 154° and 196°).
**Why it matters:** pushing to full extension behind the body adds time and starts the recovery from further back. It is the main reason the swing leg is late (#1). World-class sprinters leave the ground with the knee still bent.
- **Cues:** "Push down, not back." "Pop off the ground." "Hips tall, get off the track fast."
- **Drills:** fast-leg drill (single-leg cycling in a run: the leg pulls straight up off the ground under the hip, 3 × 20 m per leg). Straight-leg bounds (grabbing the ground under the hips), 2 × 20 m. Wicket runs (as #1).
- **Retest target:** push-off knee ≤ 160° and hip ≤ 200° at toe-off.

### 3. Strength that makes the positions possible: hip flexors, hamstrings and hip extensors (confidence: medium)
**What we see:** knee lift 67° vs 76° (track group) and thigh angular velocity 447 vs 483 °/s. These are exactly what fast hip flexion (pulling the thigh through) and fast hip extension (driving it back down) produce. You can't hold a figure-4 touchdown at 9 m/s without the hip flexor strength to pull the thigh through in ~0.12 s of flight.
- **Hip flexors:** banded or cable knee drives (fast, 3 × 6 per leg); hanging knee raises (3 × 8); A-march with an ankle weight or band (2 × 20 m).
- **Hamstrings and hip extensors:** Romanian deadlifts (already in his plan) and Nordic hamstring curls (2–3 × 4–6, also protects the hamstrings when the swing gets more aggressive); hip thrusts or single-leg hip thrusts.
- **Elastic power:** keep broad jumps and bounding. His short contacts are a strength to protect.
- **Retest target:** knee lift toward 72–75° and thigh angular velocity toward 470+ °/s; step length ÷ leg length rising from 1.98.

### 4. Approach runs: keep the quick rhythm (confidence: low-medium)
In the approach runs his flight time is 22 ms longer, so step rate drops from 4.5 to 4.1 per second. Cue: "quick and relaxed, same rhythm." Drill: approach runs to a clap or metronome at about 4.5 steps per second.

### 5. Arms: forward as well as back (confidence: low)
Shoulder range of motion is 76° (Olympic finalists ≈ 118–135°, second-hand), almost all of it behind. Cue: "hip to lip": the hand passes the hip pocket and comes up to chin height, elbow staying about 90°. The arms balance the legs, so expect this to come together with #1. Drop it if it costs relaxation.

### 6. Trunk (observation only, low confidence)
His trunk is more upright than the world-class finalists (8° vs 14.5° at touchdown, 4° vs 9° at toe-off). MediaPipe's trunk line (shoulders to hips) is rough, and Bissas measured trunk vs the ground from 3-D, so this isn't a cue yet. If it shows again next session, "lean from the ankles, hips tall" becomes a candidate.

**Not recommended:** cues that lengthen ground contact or reach the foot out. His landing (touchdown distance, shin, stance knee) already matches world-class values.

## Corrections to the first version of this report

- **"Touchdown distance is the one leg-action item to work on" was wrong.** Measured the same way as the world-class data (toe tip vs CM), his touchdown distance is 0.37 m vs 0.38 m, and his foot's forward speed at touchdown (+2.5 m/s) matches theirs (+2.4 m/s). Professionals' feet are also still moving forward when they land. The first report compared a hip-based distance with a vague "close under the body", and wrongly said elite sprinters' feet sweep backward over the ground at touchdown.
- **"Heel recovery and knee drive are in a normal range" missed the point.** The heel folds tightly enough (53° vs 49°). What it missed is where the leg is at touchdown and how far behind the push-off finishes.
- **"His form is basically elite; the gap is strength" was wrong.** The positions in #1–2 are clear, measurable form gaps. Strength (#3) is needed partly to hit those positions.

## Confidence and data quality

- **Timing.** Every frame of the slo-mo renders is 1/240 s (verified with gravity in Vinni's backflip, `qa/timebase.md`). Contact and flight times are ± 4 ms per edge.
- **Distances.** Homography from the 20/25/30 yard lines, the painted cone line and the 3 m far markers. Fit RMSE 0.8 px; independent 1-yard tick check 0.915 m (true 0.914). Zone speed ± 0.07 m/s.
- **Events.** Spot-checked to ±1 frame on close-ups. Three contacts over white paint were corrected by hand (`data/2026-11-15/events_override.yaml`).
- **Joint angles.** MediaPipe Heavy, no landmark tape. Leg angles ± 5° per touchdown (± 8° far leg), arm angles ± 5–10°. Where the knee landmark jumps (legs crossing) or the legs swap at toe-off, values are left blank. Every swing-leg finding was checked by eye on the frames (`figures/kinogram_A_*.jpg`).
- **References.** Bissas is 3-D hand-digitised world-class data; Clark uses the same 2-D side view as us. Both use joint centres, while MediaPipe's hip point sits slightly differently, so treat differences under ~5° as zero. The thigh-separation gap (24°) and the push-off gaps (15°) are well beyond that.
- **Small n.** 2 runs per condition, 5–8 touchdowns per value.

## Next session (≈ mid-December; plan in `01-plan-and-setup.md`)
Same field and setup, plus a ribbon on the far marker to show the wind. **2 flying sprints and 2 approach-run simulations each way**, then **2 full jumps into the pit**. Send the **original** slo-mo files ("All Photos Data" on), and wear a fitted short-sleeve shirt.
- **Key positions:** thigh separation and swing-knee position at touchdown; push-off knee and hip at toe-off; knee lift; thigh angular velocity; right vs left swing leg with wind balanced.
- **Speed and goal:** approach-run speed against **19.6 mph (8.77 m/s)**; step length ÷ leg length; step rate in the approach runs.
- **Pit:** approach speed over the last two steps, penultimate vs last step, CM lowering, takeoff contact time (pros 0.12–0.13 s), plant angle (≈ 58–62°), takeoff angle (≈ 18–24°), **free-leg thigh at board touchdown and toe-off**, speed lost in the takeoff, and how far behind the board he takes off.
