# Reference: sprint mechanics for an elastic long jumper (Athlete A)

## Target
**Goal: 21'9" (6.63 m).** Use Athlete A's own conversion from **approach** speed (mph during the run-up, not at takeoff) to distance:

distance (ft) = 1.57 × speed (mph) − 8.87 + 0.18 × (height (in) − 70)

It assumes human-optimal form, so with real form a given distance needs a slightly higher speed than it predicts (treat the output as a ceiling). At 175.3 cm (69.0 in), 21'9" needs **≈ 19.6 mph (8.77 m/s)** of approach speed. Approaches usually run at about 92–97% of flat-out top speed (Lewis 1991: 11.06 m/s approach vs ≈ 12.0 m/s top speed), so top sprint speed needs to be about **20.2–21.3 mph (9.0–9.5 m/s)**. Speed raises the ceiling; the approach determines how much of it reaches the board.

(This replaces an earlier rough projectile estimate of 8.5–9 m/s for 22 ft, which was more optimistic than the equation.)

## Why Carl Lewis, and why published data instead of a clip
Lewis is the classic sprinter-style ("elastic") long jumper. Old broadcast footage pans, has no calibrated markers, and runs at 25–30 fps (a 0.09 s contact is ~3 frames), so measuring a clip would be mostly guesswork. The studies below used high-speed cameras (250 Hz in Tokyo 1991).

## Lewis as a sprinter — Seoul 1988 100 m (9.92)
- Fastest 10 m segment: **12.04 m/s** (50–60 m).
- 30–60 m: 12.5 steps, **4.84 steps/s, 2.40 m** per step. 60–90 m: 11.3 steps, **4.41 steps/s, 2.65 m**.
- Compared with Ben Johnson, Lewis took fewer, longer steps at a lower rate. A long-stride, late-accelerating profile.
- Source: IAAF Seoul 1988 scientific project, via [Charlie Francis forum](https://forum.charliefrancis.com/t/100m-final-1988-olympics-seoul-split-times/21715)

## Lewis as a long jumper — Tokyo 1991 World Championships (8.91)
- Approach speed **11.06 m/s** (Powell 11.00; other finalists 10.20–10.58). [ISBS 2008](https://lida.sport-iat.de/twm/Record/4016739?lng=en)
- **Second-to-last stride 47 cm longer** than the one before. CM lowered 3 cm during that ground contact, then ~10 cm more during the long stride; lowest point at the last-step contact.
- Takeoff: horizontal velocity 10.5 → 9.1 m/s (−1.4), vertical +3.4 m/s, **takeoff angle 20.3°** (Powell: +4.2 m/s, 24.6°).
- The authors' reading: Lewis started converting horizontal into vertical velocity earlier, **spreading it across two strides**, essentially sprint technique adapted to jumping. Powell used a more force-based, single big takeoff. [Ariel Dynamics](https://www.arielnet.com/articles/show/adi-pub-01140/long-jump-technique-power-or-speed)
- Plant leg at touchdown: both jumpers used a leg angle just over 60°, and faster runs went with a straighter knee at touchdown. [ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/777/700)

## Key positions at top speed: the professional model (what Athlete A gets compared against)

Professional sprint analysis (the ALTIS kinogram method used by elite coaches, McMillan & Pfaff 2018; Mann's
front-side model; Seagrave 2009) judges a stride at five **key positions**: **toe-off**, **top of flight**
(ALTIS: "MVP", maximal vertical projection), **strike** (just before touchdown), **touchdown** and **full support**
(CM over the foot). The two measured datasets below give numbers for each position. They are what every metric
in `positions_A.md` is compared with.

- **Bissas et al. 2022**: the 2017 World Championships men's 100 m finalists (~11.6 m/s, 3-D, hand digitised).
  [eprints.glos.ac.uk/10241](https://eprints.glos.ac.uk/10241/)
- **Clark et al. 2025**: 98 US intercollegiate men filmed exactly like us (240 fps iPhone, 10 m away, 1 m high):
  track & field sprinters/jumpers at 10.0 and 9.3 m/s, and team-sport athletes at 8.2–9.3 m/s (RC's speed range).
  [Front. Sports Act. Living 7:1535798](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1535798/full)

| position | measure | world-class 100 m (Bissas) | track 10.0 m/s / team sport 8.2–9.3 m/s (Clark) |
|---|---|---|---|
| **touchdown** | **thigh separation** (swing thigh − stance thigh; − = swing knee behind) | **−10 ± 11°** (range −27 to −2) | — |
| | **swing thigh** vs vertical (+ = knee in front of the hip) | ≈ +17° (27.4 − 9.9) | **+15 ± 14°** / −9 ± 8° |
| | swing knee angle (included; small = heel folded tight) | — | 49 ± 7° / 65 ± 7° |
| | stance thigh / knee / hip angle | 27 ± 5° / 156 ± 6° / 140 ± 5° | — |
| | shin angle (+ = ankle ahead of knee) | 9 ± 4° | — |
| | trunk lean (forward) | 14.5 ± 3° | — |
| | leg angle (CM → foot vs vertical) | — | 12.7 ± 2.4° / 17.0 ± 1.9° |
| | touchdown distance (toe tip ahead of CM) | 0.38 ± 0.04 m | — |
| | foot speed over the ground (+ = still moving forward) | +2.4 ± 0.5 m/s (3.3 just before) | — |
| **toe-off** | trailing thigh (− = behind) | −25 ± 3° | — |
| | thigh separation | 93 ± 7° | — |
| | push-off knee / hip angle | **154 ± 4° / 196 ± 3°** (leave **before** the leg is straight) | — |
| | trunk lean | 9 ± 3° | — |
| **swing (whole stride)** | knee lift: max thigh angle in front | — | **76 ± 6°** / 64 ± 5° |
| | max thigh angle behind | — | −28 ± 7° / −35 ± 5° |
| | thigh range of motion | — | 105 ± 7° / 99 ± 6° |
| | front-side share (front ÷ total thigh motion) | — | 73% / 65% |
| | average thigh angular velocity | — | **483 ± 29 °/s** / 409–445 °/s |
| | peak thigh angular acceleration | — | 11.0 ± 0.9 / 8.4–9.9 k°/s² |
| **contact** | leg excursion (angle the CM → foot line sweeps) | — | 56 ± 4° / 61 ± 4° |
| | ground contact / flight time | 0.093 / 0.116 s | — |
| | step length / rate | 2.42 m / 4.80 per s | — |

**What the professionals' positions mean in plain words**
- **Touchdown, the "figure 4":** when the foot lands, the swing knee has already come through to about level with
  the stance knee ("knees together", Seagrave/Mann), with the swing heel folded high under the hips and the foot
  near the stance knee. From the side the two legs look like a "4". Behind this is fast **recovery**: the thigh is
  pulled forward right after toe-off ("toe up, knee up, heel forward", "step over the opposite knee").
- **Toe-off before full extension:** world-class sprinters leave the ground with the knee still bent ~26° and the
  hip only ~16° past straight. A leg pushed to full extension behind the body has further to travel back, so it
  arrives late at the next touchdown. This is the opposite of "push longer".
- **Front-side mechanics:** most of the thigh's motion happens in front of the body (big knee lift, little trailing
  behind). Faster groups are more front-side than slower groups (Clark 2025; Mann). Inside one homogeneous group
  of trained sprinters the positions alone don't predict speed (Haugen 2018; Clark 2025), but **thigh angular
  velocity and acceleration do**: how fast the thighs scissor, which needs hip flexor and hip extensor strength.
- **Correction to the baseline:** professionals' feet are also still moving forward over the ground at touchdown
  (+2.4 m/s) and land ~0.38 m (toe tip) ahead of the CM. The "backward sweep" coaches teach is relative to the hip,
  not the ground. Touchdown distance by itself is therefore not a fault when compared on the same definition.
- Team-sport athletes at the same speed use a "less front-side, more ground-based" pattern (swing thigh behind at
  touchdown, more extended swing knee, more thigh extension behind). Clark 2025 sees that as a style difference at
  team-sport level; for a sprinter or long jumper the track pattern is the model.

**Other elite max-velocity values:** contact 0.08–0.10 s, step length ≈ 2.39 × leg length, step rate ≈ 4.7 /s,
thigh range of motion ≈ 100° ([PMC8580521](https://pmc.ncbi.nlm.nih.gov/articles/PMC8580521)); little knee bend
during contact ([J Hum Kinet](https://jhk.termedia.pl/Kinematic-Stride-Characteristics-of-Maximal-Sprint-Running-of-Elite-Sprinters-Verification,158511,0,2.html)).

## Arm action (what the arms do, and what the research says)
- **Role:** the arms mainly balance the legs' rotation (they cancel the trunk twist the legs create) and add a little lift; they are not a main source of forward speed. The 2018 review of arm mechanics in sprinting calls the evidence "ambiguous and under-investigated" compared with the legs. [Macadam et al. 2018, Strength Cond J 40(5)](https://ro.ecu.edu.au/ecuworkspost2013/6770)
- **Range of motion:** in Mann's analysis of Olympic 200 m finalists, faster sprinters had a larger arm swing at the shoulder (**≈ 135° vs 118°** total) and elbow (**≈ 84° vs 67°** of range). Quoted second-hand; the original tables were not available to us. [SimpliFaster](https://simplifaster.com/?p=34351)
- **Elbow angle:** coaches commonly teach ≈ 90°; practitioner guidance is ≈ 85° at the front of the swing, opening to ≈ 95–100° on the way down and back. This is coaching guidance, not a measured norm. [Speed Endurance](https://speedendurance.com/2016/06/16/how-to-hold-your-hands-when-sprinting/)
- **What we compare:** shoulder range of motion, elbow angle at the front and back of the swing, hand height at the front, how far the hands pass behind the hips, and arm–leg timing (each arm should be furthest back when the same-side knee is furthest forward). Arm range of motion scales with leg range of motion, so arm cues are only worth giving when the arm action is clearly smaller than or out of time with the legs. "Pump your arms harder" alone is not supported as a speed fix.

## Takeoff reference values (for the pit session)
| measure | skilled / elite value | source |
|---|---|---|
| Approach speed (11–6 m before the board) | elite men 10.2–11.1 m/s; sub-elite women ≈ 8.7 m/s horizontal at takeoff | [ISBS 2008](https://lida.sport-iat.de/twm/Record/4016739?lng=en), [sub-elite women](https://worldathletics.org/news/news/biomechanical-analysis-of-sub-elite-performer) |
| Distance gained per extra run-up speed | ≈ 8 cm per +0.1 m/s (≈ 1.2 ft per +1 mph) in one training study; Athlete A's equation uses 1.57 ft per mph | [ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/4832/4472) |
| Takeoff contact time | 0.120–0.130 s (World Champs 2017 men); 0.122 s men / 0.117 s women (World Indoors 2008) | [IAAF 2017 report](https://lida.sport-iat.de/twm/Record/4049026?lng=en), [Athletics Weekly](https://athleticsweekly.com/?p=86703) |
| Last two steps | penultimate step longer, last step shorter; CM lowered over the last two steps, mostly on the penultimate (Lewis: +47 cm longer penultimate step, ≈ 13 cm total lowering) | IAAF 2017 report; Tokyo 1991 above |
| Touchdown (plant) angle, CM/hip to ankle vs ground | ≈ 58–60° (men 57.7 ± 3.0°, women 59.6 ± 2.8°); "just over 60°" in Bridgett & Linthorne | [Redalyc](https://www.redalyc.org/pdf/3010/301050352005.pdf), [ISBS 2005](https://ojs.ub.uni-konstanz.de/cpa/article/view/777/700) |
| Takeoff knee at toe-off | ≈ 171° included (≈ 9° of flexion) | [indoor women's study](https://ojs.ub.uni-konstanz.de/cpa/article/view/4041/3741) |
| Takeoff angle | ≈ 18–24° (elite ≈ 20–21°; Lewis 20.3°, Powell 24.6°; sub-elite women 18.1°) | Redalyc; ISBS 2008; sub-elite women |
| Vertical velocity at toe-off | elite ≈ 3.4–4.2 m/s; sub-elite women ≈ 2.45 m/s | Tokyo 1991; sub-elite women |
| Horizontal velocity loss during takeoff | ≈ 1–1.5 m/s (Lewis −1.4) | Tokyo 1991 |
| Toe-to-board distance | as small as possible without fouling; every cm behind the board is lost from the official distance | — |

**Free (swing) leg at the takeoff:** the same recovery matters on the board. The free leg is driven forward and up
through the takeoff contact; one elite case study measured the free thigh at **≈ 790 °/s** at toe-off and called its
speed "a very important factor" for takeoff efficiency ([ISBS](https://ojs.ub.uni-konstanz.de/cpa/article/view/4748/4389)).
A free leg that is still trailing behind at board touchdown has to be swung through in ~0.12 s. The pit analysis
reports free-thigh angle at board touchdown and toe-off, plus the same key positions on the last approach steps.

The camera at the pit sees roughly the last 7 m, so our approach speed is measured over the last two steps, a little later than the professionals' 11–6 m window, where speed is usually slightly lower.

## What this means for Athlete A
1. **Lewis is the right model for his style, but only with Lewis's speed.** At 11 m/s Lewis could take off at a flat 20°. At about 8.4–8.8 m/s Athlete A probably needs a somewhat higher angle; one analysis estimates **~0.3 m per extra degree**. [NBC / Lees](https://www.nbcnews.com/id/wbna48246625). That's for the approach session.
2. **Sprint markers:** every key position in the table above (touchdown, toe-off, swing, contact), plus contact time, step length ÷ leg length (Lewis ~6'2" vs A's 5'9"), arm action and **right vs left asymmetry** (limited right dorsiflexion).
3. **Pit session:** the longer penultimate step, CM lowering across the last two steps, and the ~60° touchdown (plant) angle (table above). With a right-foot takeoff, the lowering step is on the **left** leg (the shin-splint side), so its loading matters.
4. **Prioritizing:** no cues that trade short contacts for "push longer". Positions and strength go together: the swing-leg positions need fast, strong hip flexion and extension (thigh angular velocity), so each position gap gets both a drill and the strength work that makes the position possible.
