# Time base: these clips are 30 fps renders of 240 fps slo-mo

Every clip plays back at 30.0 fps (from the PTS). The originals were 240 fps slo-mo on an iPhone 11, which reports `capture_fps: 240`. The files we received are the rendered slow-motion versions, not the original 240 fps files.

**Assumption used:** every rendered frame is one captured frame, so real time = frame index / 240 s. That only holds if the render has no speed ramp and no interpolated or duplicated frames. Checks:

1. **No ramps.** The runner's displacement per frame is constant across each run. Medians in 40-frame windows are A 4.5–5.5 px/frame, B mile 2.9–3.6 and B kick 4.1–4.7. A ramp from 1/8 to normal speed would show up as an 8× jump.
2. **No duplicated frames.** The frame-to-frame image difference in the runner's box never drops to zero.
3. **Physics.** B's backflip flight lasts 156 ± 3 frames, from toe-off at frame 935 ± 1 to touchdown at 1091 ± 1. At 240 fps that is 0.650 ± 0.013 s, a centre-of-mass rise of about 0.5 m (g·t²/8), which is normal for a standing backflip. At 120 fps it would be 1.3 s and a 2.1 m rise, which is impossible. A gravity fit to the flight trajectory is in `qa/backflip.md`.
4. **Speeds.** At 240 fps the zone speeds come out in the expected ranges: A's sprints about 7–8 m/s and B's mile pace about 5 m/s.

**Effect:** the timing resolution is the same as for an original 240 fps file (±1 frame = ±4.2 ms). The render is more compressed than the original, so landmark noise is a little higher.

**For next time:** AirDrop the originals with "All Photos Data" on. The real 240 fps file then carries its own timing, and none of this inference is needed.
