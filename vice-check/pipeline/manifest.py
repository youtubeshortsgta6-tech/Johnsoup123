"""Write vice-check/DELIVERABLES.md from out/*-upload.txt (runtime, post time, files)."""
import re, sys
from pathlib import Path
from common import ROOT, OUT
rows = []
for up in sorted(OUT.glob("*-upload.txt")):
    t = up.read_text()
    title = t.split("\n")[1].strip()
    post = re.search(r"POST TIME\n(.*)", t).group(1).strip()
    rt = re.search(r"RUNTIME\n(.*)", t).group(1).strip()
    base = up.name.replace("-upload.txt", "")
    mp4 = OUT / f"{base}.mp4"; thumb = OUT / f"{base}-thumb.png"
    rows.append((base, title, post, rt, mp4.exists(), thumb.exists()))
md = ["# VICE Check deliverables", "", "Files live in `out/` on the build box (not committed). Each row: `out/<name>.mp4` (1920x1080, 30 fps, VO at -14 LUFS), `out/<name>-thumb.png` (1280x720), `out/<name>-upload.txt` (title, description with chapter timestamps, tags, post time).", "",
      "| # | name | title | post | runtime | mp4 | thumb |", "|---|---|---|---|---|---|---|"]
for i, (b, ti, po, rt, m, th) in enumerate(rows, 1):
    md.append(f"| {i} | {b} | {ti} | {po} | {rt} | {'yes' if m else 'MISSING'} | {'yes' if th else 'MISSING'} |")
md += ["", "Not built: 09 controller-scalping (voice after the week-of-Oct-19 re-check), 13 countdown (HOLD, no script).", ""]
Path(ROOT / "vice-check" / "DELIVERABLES.md").write_text("\n".join(md))
print("\n".join(md))
