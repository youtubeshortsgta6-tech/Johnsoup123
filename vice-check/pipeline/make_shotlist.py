"""Build a default shot list for a script that has no [VISUAL] cues.

Usage: python make_shotlist.py work/<slug>/chapters.json vice-check/shotlists/<slug>.json

Per chapter: chapter card, official-trailer b-roll placeholder, pull-quote card (the chapter's first sentence),
more b-roll. The owner replaces the b-roll placeholders with real trailer timecodes / official screenshots.
Cards are rendered by `cards.py <outdir> --from work/<slug>/chapters.json`.
"""
import re, sys
from common import load_json, save_json

def first_sentence(paragraphs, limit=150):
    text = " ".join(p for p in paragraphs if p != "[PAUSE]")
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    s = (m.group(1) if m else text).strip()
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "\u2026"
    return s

def main():
    src, dest = sys.argv[1], sys.argv[2]
    data = load_json(src)
    slug = data["slug"]
    chapters = []
    for i, ch in enumerate(data["chapters"], 1):
        n = f"{i:02d}"
        long = ch["words"] > 120
        segs = [
            {"type": "card", "card": f"work/cards/{slug}/chapter-{n}.png", "dur": 5},
            {"type": "footage", "file": "footage/trailer2.mp4", "in": 0, "out": 10, "dur": 10,
             "note": f"official trailer b-roll for: {ch['title']}"},
            {"type": "card", "card": f"work/cards/{slug}/quote-{n}.png", "dur": 8},
            {"type": "footage", "file": "footage/trailer1.mp4", "in": 0, "out": 10, "dur": 10,
             "note": f"official trailer / screenshot b-roll for: {ch['title']}"},
        ]
        if long:
            segs += [{"type": "card", "card": f"work/cards/{slug}/quote-{n}.png", "dur": 6, "zoom": False},
                     {"type": "footage", "file": "footage/trailer2.mp4", "in": 0, "out": 10, "dur": 10,
                      "note": f"more official b-roll for: {ch['title']}"}]
        if i == 1:
            segs.insert(0, {"type": "card", "card": f"work/cards/{slug}/title.png", "dur": 4})
        if i == len(data["chapters"]):
            segs.append({"type": "card", "card": f"work/cards/{slug}/endscreen.png", "dur": 12})
        chapters.append({"title": ch["title"], "segments": segs})
    save_json(dest, {"slug": slug, "notes": "Auto-generated default shot list. Replace footage placeholders with real trailer timecodes or official screenshots; cards come from cards.py --from.", "chapters": chapters})
    print("->", dest)

if __name__ == "__main__":
    main()
