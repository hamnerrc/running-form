# Vinni (Athlete B): mile-pace and kick analysis against the professional model, plus backflip (2026-11-15)

Miler · 176.0 cm · 68.9 kg (151.8 lb) · raced a meet the day before, so **everything here is fatigued data**. 3 runs at about mile pace and 1 at kick pace through the 10-yard zone, 240 fps, side-on, plus one standing backflip. Segment lengths were **estimated from video**, not tape-measured (thigh 47.9, shank 41.7, leg 97.9 cm, each ± 2.5–3 cm; `qa/anthropometrics_video.md`).

**How this was analysed.** Each stride was judged at the key positions professional coaches use (touchdown, full support, toe-off, swing) and compared with published professionals measured the same way: the **2017 World Championships men's 1500 m final** (Hanley et al. 2023) for mile pace, and **sprint data** (2017 World Championships 100 m finalists, Bissas 2022; college track and team-sport athletes, Clark 2025) for the kick, where sprint mechanics decide races. The research on what separates elite distance runners (Folland 2017, Preece 2019, Bushnell & Hunter 2007, Moore 2016) is summarised in `03-reference-miler.md`. Numbers come from `positions_B.csv/.md` and `metrics_B.csv`.

This version replaces the first report, which only flagged vertical oscillation and called the rest "tidy". It missed the swing-leg and push-off positions. See "Corrections" below.

## Summary

- **Pace:** the mile-pace runs were **5.67, 5.46 and 5.40 m/s** (± 0.03), i.e. 4:44, 4:55 and 4:58 per mile. The kick run was **7.58 ± 0.05 m/s** (about 26.4 s per 200 m).
- **Main finding: strong back-side mechanics, at mile pace and in the kick.** At touchdown his swing leg is still far behind. The swing knee is **39 ± 5 cm behind** the stance knee, the swing heel **0.51 ± 0.06 m behind his hips**, and the thigh separation is **−55 ± 5°** (every one of 20 touchdowns between −42° and −66°). Even at **full support**, when the CM is over the foot, the swing knee is still **11 cm behind** the stance knee. Most of his thigh motion happens behind the body: **knee lift 50°**, thigh **41° behind** at its furthest, a **front-side share of 55%**. This is the pattern Bushnell & Hunter found separates distance runners from sprinters at the same speed.
- **It doesn't change in the kick, and that limits his top-end speed.** At 7.6 m/s thigh separation is still **−57 ± 10°** (world-class 100 m: −10°). The swing thigh at touchdown is **−18°** (slowest published sprint group, 8.2 m/s: −10°; college track: +11 to +15°), knee lift is **55°** (team sport 64°, track 76°), and thigh angular velocity is **341 °/s** (slowest published group 409 °/s). Distance runners in Bushnell & Hunter kept this pattern when they sprinted, and the authors recommend technique work for the end of races. **This is the biggest opportunity**, because championship miles are decided in the last 200–300 m.
- **He pushes off to a straight leg.** At toe-off his knee is **172 ± 4°** at mile pace and 167° in the kick, and the hip 203–207° (world-class sprinters: 154° and 196°). For economy, "less leg extension at toe-off" is one of the features most linked to a lower energy cost (Moore 2016). It also starts the recovery from further back.
- **More forward lean than elite milers:** trunk lean **13 ± 4°** at mile pace (9° in the kick), and his stance hip angle at touchdown is **133°** vs **152°** for the world 1500 m final. Elite distance runners keep a more upright trunk that doesn't tip forward as they speed up (Preece 2019), and a more upright trunk went with better performance in Folland 2017.
- **What already matches world-class milers:** stance knee at touchdown (**153°** vs 154°), touchdown distance (middle of the foot **0.31 m** ahead of the CM vs 0.35 m at their faster 7–7.5 m/s), overstride (ankle 5 cm ahead of the knee vs 4.3 cm), shin close to vertical (**+6°**), and a kick that adds speed mostly through cadence (+25% step rate), as elite 1500 m runners do.
- **Vertical oscillation** (10 ± 2 cm per step at mile pace, 7 cm in the kick) is still higher than in his kick, but the evidence is mixed. Folland links less vertical oscillation with economy, while Preece found elite runners have *longer* flights. It is now a "watch", not the main item.

## Key positions vs professionals

| when | measure | mile pace (3 runs) | kick (1 run) | professional reference | verdict |
|---|---|---|---|---|---|
| touchdown | **thigh separation** (− = swing knee behind) | **−55 ± 5°** (n=20) | **−57 ± 10°** (n=5) | sprint world-class −10 ± 11° | **far behind** (kick) |
| | **swing thigh** vs vertical (+ = in front) | **−22 ± 4°** | **−18 ± 7°** | sprint 8.2–9.3 m/s −9 ± 8°; track +11 to +15° | **behind** |
| | swing knee vs stance knee | **39 ± 5 cm behind** | 40 cm behind | ≈ level (sprint) | behind |
| | swing heel behind the hips | **0.51 ± 0.06 m** | 0.44 m | — | far behind |
| | swing knee angle (heel fold) | 78 ± 8° | 66 ± 4° | sprint 8.2–9.3 m/s 65 ± 7° | ok in the kick |
| | stance knee angle | 153 ± 4° | 154° | world 1500 m final 154° | **good** |
| | stance hip angle (trunk–thigh) | **133 ± 5°** | 132° | world 1500 m final 152° | **more flexed** (trunk lean) |
| | shin angle (+ = ankle ahead) | 6 ± 3° | 11° | elite closer to vertical than recreational | good |
| | trunk lean | **13 ± 4°** | 9 ± 3° | elite distance runners stay upright | leaning |
| | touchdown distance (middle of foot ahead of CM) | 0.31 ± 0.03 m | 0.35 m | world 1500 m final 0.35 m (at 7–7.5 m/s) | good |
| | overstride (ankle ahead of knee) | 0.05 ± 0.02 m | 0.06 m | world 1500 m final 0.043 m | good |
| full support | swing knee ahead of stance knee | **−11 ± 10 cm (behind)** | −6 cm | knee passing the stance knee (coaching model) | behind |
| toe-off | **push-off knee angle** | **172 ± 4°** | 167 ± 9° | sprint world-class 154°; economy: less extension | **too straight** |
| | push-off hip angle | 203 ± 5° | 207° | sprint world-class 196° | far behind |
| | trailing thigh | −34 ± 4° | −31° | sprint world-class −25° | behind |
| swing | **knee lift** (max thigh in front) | **50 ± 4°** | **55°** | sprint 8.2–9.3 m/s 64°; track 76° | **low** (kick) |
| | max thigh behind | −41 ± 2° | −43° | sprint −28 to −35° | far behind |
| | front-side share | 55 ± 3% | 56% | sprint 65–73% | back-side |
| | **thigh angular velocity** | 268 ± 16 °/s | **341 °/s** | slowest sprint group (8.2 m/s) 409 °/s | low (kick) |
| | time from toe-off until the thigh passes vertical | 173 ± 49 ms | 169 ms | — (RC: 87 ms) | slow recovery |

Sprint references are at 8.2–11.6 m/s, so at mile pace (5.5 m/s) they show direction only, not a target. There is no published swing-leg value for elite milers at mile pace. Angles ± 5° per touchdown (± 8° far leg), distances ± 3 cm. Figures: `figures/kinogram_B_normal_1_right.mov.jpg`, `figures/model_td_B_*.jpg` (touchdown with the world-class sprint average in white), `figures/model_to_B_*.jpg`.

## Timing and stride (near-side leg, mean ± SD across steps)

| metric | mile pace (3 runs) | kick (1 run) | direction linked to better results |
|---|---|---|---|
| Ground contact time (ms) | 185 ± 8 (n=9) | 143 ± 9 (n=3) | shorter (world 1500 m final: 147 ms at 7–7.5 m/s) |
| Flight time (ms) | 161 ± 17 | 140 ± 27 | longer flights in elite runners (Preece) |
| Step rate (steps/s) | 2.89 ± 0.13 (173 /min) | 3.61 ± 0.46 | higher cadence → economy (small effect) |
| Step length (m) | 1.92 ± 0.09 | 2.18 ± 0.06 | self-optimised; don't force it |
| Duty factor, per stride (Folland's definition) | ≈ 0.27 | ≈ 0.25 | lower (world 1500 m final 0.245) |
| Knee flexion: touchdown / max during contact / toe-off (°) | 27.5 / 49 ± 3 / 8 ± 2 | 27 / 55 / 13 | mixed evidence |
| Heel recovery: max knee flexion in swing (°) | 141 ± 2 (n=6) | 144 ± 1 (n=2) | more fold in elite runners |
| Foot strike (foot angle at touchdown) | rearfoot 5 / midfoot 4 (+4 ± 3°) | mixed | no cue unless it causes braking |
| Vertical oscillation of the CM per step | 10 ± 2 cm (5.8% of height) | 7 ± 2 cm (4.0%) | mixed evidence |
| Braking: CM speed lost after touchdown | 13 ± 7% | 11 ± 12% | smaller (low confidence) |
| Vertical / leg stiffness (kN/m, model) | 34 ± 2 / 9.9 ± 0.9 | 58 ± 10 / 11 ± 1 | higher → economy |

Left vs right at mile pace: ground contact time R 185 ± 10 vs L 186 ± 2 ms; step length R 1.94 vs L 1.89 m; thigh separation at touchdown R swinging −54 ± 4° vs L swinging −56 ± 7°. **No asymmetry to act on.**

### Arm action (near-side arm; low confidence)

| measure | mile pace (n=5 strides) | kick (n=1) |
|---|---|---|
| Shoulder flexion forward / extension back (°) | 12 ± 26 / 58 ± 7 | 20 / 66 |
| Shoulder range of motion (°) | 69 ± 27 | 86 |
| Elbow angle, min / max during the swing (°) | 56 ± 11 / 132 ± 24 | 38 / 101 |
| Arm–leg timing (ms, ≈ 0 = in time) | −8 ± 29 | −29 |

At touchdown, world 1500 m finalists have the arm 47° behind the trunk and the elbow at 72° (Hanley 2023). His arm tracking is noisy (step-to-step SD up to 27°), so these are descriptive only. In the frames his arms, like his legs, work mostly behind the body, with the hands low by the hips.

## Recommendations (ranked)

### 1. Sprint mechanics for the kick: bring the knee through (confidence: medium)
**What we see:** in the kick his swing leg is as far behind at touchdown as at mile pace (thigh separation −57°), knee lift is 55° and thigh angular velocity 341 °/s, all below the slowest published sprint group.
**Why it matters:** the last 200–300 m of a championship mile are run at 7–8 m/s, where sprint mechanics decide places. Distance runners don't switch to sprint mechanics on their own when they speed up (Bushnell & Hunter 2007), so it has to be trained.
- **Cues (kick only):** "Knees up and through." "Step over the opposite knee." "Quick off the ground."
- **Drills (2 × per week, before or after easy runs):** A-skips, 2 × 20 m; dribbles to knee height, 2 × 20 m; wicket runs (mini-hurdles about 2.0–2.2 m apart at kick speed, 4 runs); fast-leg drill, 2 × 20 m per leg; then 3–4 × 60–80 m strides at kick speed carrying the same knee lift.
- **Strength:** hip flexors (banded knee drives 3 × 6 per leg, hanging knee raises 3 × 8) and calves (single-leg calf raises, pogo hops; stop if the shins complain).
- **Retest target:** in the kick, thigh separation from −57° toward −35°, knee lift from 55° toward 62°+, thigh angular velocity up, at the same or higher speed.

### 2. At mile pace: quicker recovery, lighter toe-off (confidence: low-medium)
**What we see:** he pushes off to a straight knee (172°) and the thigh takes 173 ms after toe-off to swing back to vertical. Even at full support the swing knee is behind the stance knee.
**Why it matters:** less leg extension at toe-off is one of the features most linked to economy (Moore 2016), and a leg that trails behind has to be brought further forward on every step. **Caveat:** in the 2017 world 1500 m final the best finishers actually used *more* hip extension late in stance (Hanley 2023), so this is a nudge to test, not a rebuild. Trained runners self-optimise, and he was tired.
- **Cue:** "Pick the foot up under you, don't push it back."
- **Drill:** strides at mile pace with a cadence nudge of about 3–5% (173 → about 180 steps/min, metronome), 4–6 × 100 m. A slightly higher step rate shortens the back-side naturally.
- **Retest target:** push-off knee ≤ 165°, swing knee level with the stance knee at full support, ground contact time not longer.

### 3. Run tall (confidence: low-medium)
**What we see:** 13° of forward trunk lean at mile pace and a stance hip angle of 133° vs 152° in the world 1500 m final.
**Why it matters:** elite distance runners keep the trunk upright and don't tip forward as they speed up (Preece), and a more upright trunk went with better performance (Folland). MediaPipe's trunk line is rough, so this is low confidence.
- **Cue:** "Run tall, hips under you." Check on the next video.

### 4. Watch vertical oscillation; don't chase it (confidence: low)
10 cm per step at mile pace and 7 cm in the kick. Recommendations #2 and #3 tend to reduce it anyway. The research disagrees on whether lower is better (Folland vs Preece), so it gets no separate cue.

**Not cued:** foot strike, knee bend during contact (mixed evidence; his matches the world 1500 m final), touchdown distance and overstride (both match elite milers), and arms (tracking too noisy).

## Corrections to the first version of this report

- **"His mile-pace mechanics are tidy; the one number that stands out is vertical oscillation" was wrong.** The first report didn't measure the swing leg at all. His back-side pattern (swing leg far behind at touchdown and at full support, low knee lift, straight-leg push-off) is the biggest difference from professionals, especially in the kick.
- **Vertical oscillation** is downgraded from the top recommendation to a watch item, because the elite-runner evidence is mixed (Preece 2019).

## Backflip critique (extra)

Measured from the clip (`qa/backflip.md`, figures `B_backflip_keyframes.jpg` and `B_backflip_traces.png`). Flight time is **0.650 ± 0.013 s** and the CM rises **0.35 m** after toe-off.

**What's good**
- **Height and direction.** He jumps up, not back. The CM lands within 2 cm horizontally of where it took off, and the vertical take-off speed is about 2.6 m/s. That is a strong, safe set.
- **Arm swing.** The arms are fully overhead at toe-off, with the countermovement-to-swing timing done before he leaves the ground.
- **Tuck quality.** Once he tucks it is tight (hips about 145°, knees about 135°) and the rotation rate jumps to about 830°/s.

**What to fix (ranked)**
1. **Tuck earlier.** From 0.10 to 0.27 s after toe-off his trunk angle stays flat at about 52° back. He is arched open, and the trunk barely rotates while he rises. The tuck only starts at the top of the jump (≈ +0.27 s). That leaves about 0.38 s to rotate the remaining roughly 315°. He gets about 220° of it done before his feet land.
   - **Cue:** "Jump up, then pull your knees to your chest straight away. Don't throw your head back."
   - **Drills:** tuck jumps (straight up, knees to chest at the top, land in a soft squat), 3 × 5; backward rolls / back tucks onto a crash mat or with a spotter, focusing on the knees arriving before the head goes back.
2. **Land upright with bent knees.** At touchdown his trunk has rotated 266° of the 360° needed, so his chest is about 90° short of upright, nearly horizontal. His knees are almost straight (about 20°) at contact and then fold to about 75°. A piked, stiff-legged landing loads the low back and hamstrings and leaves no margin if a rep comes up shorter. Fix #1 gives the time to finish the rotation.
   - **Cue:** "Spot the ground, open out, land in a quarter squat with your chest up."
   - **Drill:** stick-landing practice. Drop or jump from a low box into a quiet quarter-squat with the chest up, 3 × 5.
3. **Minor, low confidence:** the leg may leave the ground before it is fully straight (knee about 30° at toe-off). Inverted-body pose is ± 10°, so this is a maybe.

**Safety:** practise the changes on a mat or with a spotter first. This is technique feedback, not medical advice.

## Confidence and data quality

- **Timing.** These are 240 fps slo-mo renders with 1 frame = 1/240 s, verified by the backflip gravity fit (9.3 m/s² measured, `qa/timebase.md`). Event timing is ± 4 ms per edge. In close-up checks, auto toe-offs for him tended to be 0–4 frames late, so contact may read up to about 15 ms long. Contacts that tracking had split in two, or that sat at the frame edge, were corrected or dropped by hand (`events_override.yaml`).
- **Joint angles.** Where the swing knee passes the stance knee, MediaPipe's knee jumps. Those angles are blanked rather than reported. Leg angles ± 5° per touchdown (± 8° far leg). Every swing-leg finding was checked by eye on the frames (`figures/kinogram_B_*.jpg`); the pattern is obvious there.
- **References.** The world 1500 m data are 3-D hand-digitised, faster (7.0–7.5 m/s) and fresh; sprint references are at much higher speeds and only show direction at mile pace.
- **Braking.** This comes from differentiating the CM velocity, the noisiest metric here. SDs are about as large as the means, so don't act on it.
- **Forces and stiffness.** Spring-mass model estimates, with mass 68.9 ± 0.5 kg (the 151.8 assumed to be lb).
- **Fatigue.** He raced the day before, so these are not his fresh mechanics.

## Retest plan (3–4 weeks)
Same setup: 3 mile-pace runs each way (fresh if possible) and **2 kicks each way** (the kick is where the main recommendation applies), original slo-mo files. Compare: thigh separation and swing-knee position at touchdown, knee lift, thigh angular velocity and push-off knee angle in the kick; push-off knee, swing knee at full support, trunk lean, step rate and ground contact time at a matched mile pace. Backflip: film one after a few weeks of tuck drills and compare tuck timing and trunk angle at landing.
