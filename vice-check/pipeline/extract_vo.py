"""Step 1: turn a script markdown into chapters of voiceover-only text.

Usage: python extract_vo.py <script.md> [--out work/<slug>/chapters.json]

Rules (from the handoff):
- drop [VISUAL: ...] lines, headings and any other bracketed cue
- keep [PAUSE] as a marker; voice.py turns it into 1.5 s of silence
- chapters come from `## Chapter: <name>` headings; the `## Packaging` block
  is parsed separately into meta (title, description, tags, thumbnail).
"""
import re, sys
from pathlib import Path
from common import WORK, save_json

CUE = re.compile(r"^\s*\[(?!PAUSE\])[^\]]*\]\s*$")   # a line that is only a [cue]
BOLD_CUE = re.compile(r"^\s*\*\*\[.*\]\*\*\s*$")

def parse(md: str):
    lines = md.splitlines()
    meta = {}
    chapters = []
    cur = None
    mode = "head"
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("## Chapter:"):
            cur = {"title": line.split(":", 1)[1].strip(), "paragraphs": []}
            chapters.append(cur); mode = "chapter"; continue
        if line.startswith("## Packaging"):
            mode = "packaging"; cur = None; continue
        if line.startswith("#"):
            continue
        if mode == "head":
            m = re.match(r"^(\w+):\s*(.+)$", line)
            if m: meta[m.group(1)] = m.group(2).strip()
            continue
        if mode == "packaging":
            m = re.match(r"^(\w+):\s*(.*)$", line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if val == "|":
                    meta[key] = ""; meta["_block"] = key
                else:
                    meta[key] = val; meta.pop("_block", None)
            elif meta.get("_block"):
                meta[meta["_block"]] += line.strip() + "\n" if line.strip() else "\n"
            continue
        # chapter body
        if not line.strip():
            continue
        if CUE.match(line) or BOLD_CUE.match(line):
            continue
        if line.strip() == "[PAUSE]":
            cur["paragraphs"].append("[PAUSE]"); continue
        if line.startswith("**") and line.endswith("**"):   # bold sub-labels like **Stop 1**
            continue
        # strip any inline bracketed cue and markdown emphasis
        text = re.sub(r"\[(?!PAUSE\])[^\]]*\]", "", line).strip()
        text = text.replace("**", "").replace("*", "")
        if text:
            cur["paragraphs"].append(text)
    meta.pop("_block", None)
    for c in chapters:
        c["chars"] = sum(len(p) for p in c["paragraphs"] if p != "[PAUSE]")
        c["words"] = sum(len(p.split()) for p in c["paragraphs"] if p != "[PAUSE]")
    return meta, chapters

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    meta, chapters = parse(src.read_text())
    slug = meta.get("slug") or src.stem
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else WORK / slug / "chapters.json"
    total_words = sum(c["words"] for c in chapters)
    total_chars = sum(c["chars"] for c in chapters)
    data = {"slug": slug, "meta": meta, "chapters": chapters,
            "total_words": total_words, "total_chars": total_chars,
            "est_runtime_sec_at_150wpm": round(total_words / 150 * 60)}
    save_json(out, data)
    print(f"{slug}: {len(chapters)} chapters, {total_words} words, {total_chars} chars "
          f"(~{data['est_runtime_sec_at_150wpm']//60}:{data['est_runtime_sec_at_150wpm']%60:02d} at 150 wpm)")
    for i, c in enumerate(chapters, 1):
        print(f"  {i:02d} {c['title']:<28} {c['words']:>4} words")
    print(f"-> {out}")

if __name__ == "__main__":
    main()
