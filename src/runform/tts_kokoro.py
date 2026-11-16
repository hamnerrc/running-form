"""Local text-to-speech with Kokoro-82M (kokoro-onnx). Runs in the separate .venv-tts (it needs numpy ≥ 2,
which the MediaPipe venv can't take).

    .venv-tts/bin/python src/runform/tts_kokoro.py lines.json out_dir [voice] [speed]

lines.json: [{"id": "s1", "text": "..."}, ...]  →  out_dir/<id>.wav (24 kHz mono) and out_dir/durations.json.
Model files: models/kokoro/kokoro-v1.0.onnx and voices-v1.0.bin (from the kokoro-onnx GitHub releases)."""
import json
import sys
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parents[2]


def main():
    lines = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    voice = sys.argv[3] if len(sys.argv) > 3 else "am_michael"
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    k = Kokoro(str(ROOT / "models/kokoro/kokoro-v1.0.onnx"), str(ROOT / "models/kokoro/voices-v1.0.bin"))
    durs = {}
    for ln in lines:
        samples, sr = k.create(ln["text"], voice=voice, speed=speed, lang="en-us")
        sf.write(out / f"{ln['id']}.wav", samples, sr)
        durs[ln["id"]] = len(samples) / sr
        print(ln["id"], round(durs[ln["id"]], 2), flush=True)
    (out / "durations.json").write_text(json.dumps(durs, indent=2))


if __name__ == "__main__":
    main()
