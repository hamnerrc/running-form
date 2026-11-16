"""Minimal Markdown → PDF (reportlab) for the athlete reports. Usage: md2pdf.py in.md out.pdf name_map.json figures.json"""
import json, re, sys
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

SUP = "/System/Library/Fonts/Supplemental/"
for n, f in (("AU", "Arial.ttf"), ("AU-B", "Arial Bold.ttf"), ("AU-I", "Arial Italic.ttf"), ("AU-BI", "Arial Bold Italic.ttf")):
    pdfmetrics.registerFont(TTFont(n, SUP + f))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("AU", normal="AU", bold="AU-B", italic="AU-I", boldItalic="AU-BI")

src, out, names, figs = sys.argv[1], sys.argv[2], json.loads(sys.argv[3]), json.loads(sys.argv[4])
text = Path(src).read_text()
for k, v in names.items():
    text = text.replace(k, v)

INK, MUTED, ACCENT, RULE = colors.HexColor("#1f2933"), colors.HexColor("#52606d"), colors.HexColor("#0b6e4f"), colors.HexColor("#d9e2ec")
base = dict(fontName="AU", textColor=INK)
S = {
    "title": ParagraphStyle("t", fontSize=20, leading=25, spaceAfter=4, textColor=ACCENT, fontName="AU-B"),
    "h2": ParagraphStyle("h2", fontSize=14, leading=18, spaceBefore=14, spaceAfter=5, textColor=ACCENT, fontName="AU-B"),
    "h3": ParagraphStyle("h3", fontSize=11.5, leading=15, spaceBefore=10, spaceAfter=3, textColor=INK, fontName="AU-B"),
    "p": ParagraphStyle("p", fontSize=9.6, leading=13.4, spaceAfter=5, **base),
    "meta": ParagraphStyle("m", fontSize=9, leading=12.5, spaceAfter=8, textColor=MUTED, fontName="AU"),
    "li": ParagraphStyle("li", fontSize=9.6, leading=13.2, **base),
    "cell": ParagraphStyle("c", fontSize=8.2, leading=10.4, **base),
    "cellh": ParagraphStyle("ch", fontSize=8.2, leading=10.4, textColor=colors.white, fontName="AU-B"),
    "cap": ParagraphStyle("cap", fontSize=8.5, leading=11, textColor=MUTED, fontName="AU", spaceAfter=8),
}

def inline(s):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"`([^`]+)`", r'<font color="#52606d">\1</font>', s)
    return s

story, lines, i = [], text.splitlines(), 0
section = [None]

def fig_block(path, cap, w=1.0, max_h=4.3 * inch):
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(path).getSize()
    width = W * w; height = width * ih / iw
    if height > max_h:
        height = max_h; width = height * iw / ih
    im = Image(path, width=width, height=height); im.hAlign = "LEFT"
    return KeepTogether([Spacer(1, 4), im, Paragraph(inline(cap), S["cap"])])

def flush_figs():
    for path, cap, w in figs.get(section[0] or "", []):
        story.append(fig_block(path, cap, w))
W = letter[0] - 1.5 * inch

def flush_list(items):
    # items: list of (level, text)
    def build(start, level):
        out, k = [], start
        while k < len(items) and items[k][0] >= level:
            if items[k][0] == level:
                out.append([Paragraph(inline(items[k][1]), S["li"])]); k += 1
            else:
                sub, k = build(k, items[k][0])
                out[-1].append(ListFlowable([ListItem(x, leftIndent=12) for x in sub], bulletType="bullet",
                                            start="–", leftIndent=12, bulletFontName="AU", bulletFontSize=8))
        return out, k
    tops, _ = build(0, items[0][0])
    return ListFlowable([ListItem(x, leftIndent=12, value="•") for x in tops], bulletType="bullet", start="•",
                        leftIndent=12, bulletFontName="AU", bulletFontSize=8, spaceAfter=5)

while i < len(lines):
    ln = lines[i]
    if ln.startswith("# "):
        story.append(Paragraph(inline(ln[2:]), S["title"]))
        story.append(Spacer(1, 2)); i += 1; first_meta = True
        continue
    if ln.startswith("## "):
        flush_figs(); section[0] = ln[3:].strip()
        h = ln[3:]
        story.append(Paragraph(inline(h), S["h2"]))
        for f in figs.get(h, []):
            pass
        i += 1; continue
    if ln.startswith("### "):
        flush_figs(); section[0] = ln[4:].strip()
        story.append(Paragraph(inline(ln[4:]), S["h3"])); i += 1; continue
    if ln.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                rows.append(cells)
            i += 1
        n = len(rows[0])
        data = [[Paragraph(inline(c), S["cellh"] if r == 0 else S["cell"]) for c in row] for r, row in enumerate(rows)]
        # column widths follow the text: average cell length per column, clamped so short columns stay readable
        avg = [sum(len(re.sub(r"[*`]", "", row[k])) for row in rows[1:]) / max(1, len(rows) - 1) for k in range(n)]
        hdr = [len(rows[0][k]) for k in range(n)]
        wts = [min(40.0, max(11.0, a, h * 0.6)) for a, h in zip(avg, hdr)]
        cw = [W * w / sum(wts) for w in wts]
        t = Table(data, colWidths=cw, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ACCENT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
                               ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE), ("TOPPADDING", (0, 0), (-1, -1), 3),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        story += [t, Spacer(1, 8)]
        continue
    m = re.match(r"^(\s*)[-*] (.*)", ln)
    if m:
        items = []
        while i < len(lines):
            m = re.match(r"^(\s*)[-*] (.*)", lines[i])
            if not m:
                break
            items.append((len(m.group(1)) // 2, m.group(2))); i += 1
        story.append(flush_list(items)); continue
    if ln.startswith("!["):
        i += 1; continue
    if not ln.strip():
        i += 1; continue
    para = [ln]; i += 1
    while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||\s*[-*] |!\[|\d+\. )", lines[i]):
        para.append(lines[i]); i += 1
    style = S["meta"] if len(story) <= 2 else S["p"]
    story.append(Paragraph(inline(" ".join(para)), style))

flush_figs()

def footer(c, d):
    c.saveState(); c.setFont("AU", 7.5); c.setFillColor(MUTED)
    c.drawString(0.75 * inch, 0.5 * inch, names.get("__footer", ""))
    c.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"page {d.page}")
    c.restoreState()

doc = SimpleDocTemplate(out, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                        topMargin=0.7 * inch, bottomMargin=0.75 * inch, title=names.get("__title", ""), author="")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote", out)
