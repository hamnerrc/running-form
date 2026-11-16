"""Build the PDF reports listed in results/<date>/pdf_build.json (needs reportlab: system python3 has it).

    python3 tools/build_pdfs.py results/2026-11-15/pdf_build.json
"""
import json, subprocess, sys
from pathlib import Path

here = Path(__file__).resolve().parent
cfg = json.loads(Path(sys.argv[1]).read_text())
for name, c in cfg.items():
    subprocess.run([sys.executable, str(here / "md2pdf.py"), c["md"], c["pdf"], json.dumps(c["names"]),
                    json.dumps(c["figures"])], check=True)
