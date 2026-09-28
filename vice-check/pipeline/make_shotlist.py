"""Build a shot list for a script with no [VISUAL] cues, from the owner's footage.

Usage: python make_shotlist.py work/<slug>/chapters.json vice-check/shotlists/<slug>.json

Rotates through curated, weapon-free segments of the official trailers / Extended Look recording
and picks official stills by keyword per chapter. Cards come from `cards.py <outdir> --from`.
"""
import re, sys
from common import load_json, save_json

# (file, in, out, note)  - hand-picked from contact sheets; no weapon close-ups
BROLL = [
    ("footage/trailer2.mp4", 150, 158, "Trailer 2: Vice City skyline pull-back at sunset"),
    ("footage/trailer1.mp4", 1, 4, "Trailer 1: causeway aerial at sunset"),
    ("footage/trailer2.mp4", 30, 36, "Trailer 2: highway into the Vice City skyline"),
    ("footage/trailer1.mp4", 10, 13, "Trailer 1: turquoise water and beach aerial"),
    ("footage/trailer2.mp4", 36, 42, "Trailer 2: beach gym on Ocean Beach"),
    ("footage/trailer1.mp4", 18, 21, "Trailer 1: swamp at sunrise"),
    ("footage/trailer2.mp4", 42, 48, "Trailer 2: street murals"),
    ("footage/trailer1.mp4", 30, 33, "Trailer 1: night aerial and neon street"),
    ("footage/trailer2.mp4", 6, 12, "Trailer 2: Jason and the truck"),
    ("footage/extended-look-2026-08.mp4", 1200, 1210, "Extended Look: daytime skyline"),
    ("footage/trailer2.mp4", 18, 24, "Trailer 2: stilt house in the Keys"),
    ("footage/trailer2.mp4", 78, 84, "Trailer 2: dock at sunset"),
    ("footage/extended-look-2026-08.mp4", 1240, 1250, "Extended Look: driving toward the towers"),
    ("footage/trailer2.mp4", 24, 30, "Trailer 2: Jason driving"),
    ("footage/trailer1.mp4", 35, 39, "Trailer 1: Keys bridges and penthouse pool"),
    ("footage/trailer2.mp4", 84, 90, "Trailer 2: Lucia and Jason in the kitchen"),
    ("footage/extended-look-2026-08.mp4", 1543, 1549, "Extended Look: night skyline, rooftop pool"),
    ("footage/trailer2.mp4", 144, 150, "Trailer 2: Lucia in the convertible"),
    ("footage/extended-look-2026-08.mp4", 1567, 1573, "Extended Look: sunset skyline, boat"),
    ("footage/trailer2.mp4", 12, 18, "Trailer 2: Brian Heder"),
]
SCREENS = "footage/GTAVI_Screenshots"
STILLS = {   # keyword -> weapon-free official stills
    "lucia": [f"{SCREENS}/People/Lucia Caminos/Lucia_Caminos_0{i}.jpg" for i in (1, 2, 3, 6, 8)],
    "jason": [f"{SCREENS}/People/Jason Duval/Jason_Duval_0{i}.jpg" for i in (1, 2, 3, 4, 6)],
    "protagonist": [f"{SCREENS}/People/Jason and Lucia/Jason_and_Lucia_{i:02d}.jpg" for i in (3, 5, 7, 10, 13)],
    "bonnie": [f"{SCREENS}/People/Jason and Lucia/Jason_and_Lucia_{i:02d}.jpg" for i in (8, 13, 3)],
    "vice city": [f"{SCREENS}/Places/Vice City/Vice_City_{i:02d}.jpg" for i in (1, 3, 5, 8, 10, 11)],
    "leonida": [f"{SCREENS}/Places/Leonida Keys/Leonida_Keys_01.jpg", f"{SCREENS}/Places/Grassrivers/Grassrivers_05.jpg",
                f"{SCREENS}/Places/Mount Kalaga National Park/Mount_Kalaga_National_Park_04.jpg", f"{SCREENS}/Places/Port Gellhorn/Port_Gellhorn_06.jpg"],
    "map": [f"{SCREENS}/Places/Leonida Keys/Leonida_Keys_01.jpg", f"{SCREENS}/Places/Vice City/Vice_City_03.jpg", f"{SCREENS}/Places/Ambrosia/Ambrosia_02.jpg"],
    "ultimate": ["footage/GTAVI_Ultimate_Edition_Benefits/ULTIMATE_EDITION_01.jpg", "footage/GTAVI_Ultimate_Edition_Benefits/ULTIMATE_EDITION_02.jpg",
                 "footage/GTAVI_Ultimate_Edition_Benefits/ULTIMATE_EDITION_GROTTI_CHEETAH_02.jpg", "footage/GTAVI_Ultimate_Edition_Benefits/ULTIMATE_EDITION_SQUALO_01.jpg"],
    "vintage": ["footage/GTAVI_Vintage_Vice_City_Pack/VINTAGE_VICE_CITY_PACK_01.jpg", "footage/GTAVI_Vintage_Vice_City_Pack/VINTAGE_VICE_CITY_PACK_VAPID_STANIER_01.jpg"],
    "price": ["footage/GTAVI_Ultimate_Edition_Benefits/ULTIMATE_EDITION_01.jpg", "footage/GTAVI_Vintage_Vice_City_Pack/VINTAGE_VICE_CITY_PACK_02.jpg"],
    "trailer": [f"{SCREENS}/Places/Vice City/Vice_City_01.jpg", f"{SCREENS}/Places/Vice City/Vice_City_10.jpg"],
}
GENERIC = [f"{SCREENS}/Places/Vice City/Vice_City_{i:02d}.jpg" for i in (3, 5, 8, 10)] + \
          [f"{SCREENS}/Places/Leonida Keys/Leonida_Keys_0{i}.jpg" for i in (1, 5)] + \
          [f"{SCREENS}/Places/Grassrivers/Grassrivers_0{i}.jpg" for i in (3, 5)] + \
          [f"{SCREENS}/Places/Port Gellhorn/Port_Gellhorn_0{i}.jpg" for i in (1, 6)] + \
          [f"{SCREENS}/Places/Mount Kalaga National Park/Mount_Kalaga_National_Park_0{i}.jpg" for i in (2, 4)]

def pick_still(text, used):
    t = text.lower()
    pools = [STILLS[k] for k in STILLS if k in t] or [GENERIC]
    for pool in pools + [GENERIC]:
        for f in pool:
            if f not in used:
                used.add(f); return f
    return GENERIC[0]

def main():
    src, dest = sys.argv[1], sys.argv[2]
    data = load_json(src); slug = data["slug"]
    chapters, bi, used = [], 0, set()
    for i, ch in enumerate(data["chapters"], 1):
        n = f"{i:02d}"
        text = ch["title"] + " " + " ".join(p for p in ch["paragraphs"] if p != "[PAUSE]")
        def broll(d):
            nonlocal bi
            f, a, b, note = BROLL[bi % len(BROLL)]; bi += 1
            return {"type": "footage", "file": f, "in": a, "out": b, "dur": d, "note": note}
        segs = [{"type": "card", "card": f"work/cards/{slug}/chapter-{n}.png", "dur": 4},
                broll(8),
                {"type": "image", "file": pick_still(text, used), "dur": 7, "note": "official still"},
                {"type": "card", "card": f"work/cards/{slug}/quote-{n}.png", "dur": 7},
                broll(8)]
        if ch["words"] > 120:
            segs += [{"type": "image", "file": pick_still(text, used), "dur": 7, "note": "official still"}, broll(8)]
        if ch["words"] > 200:
            segs += [{"type": "image", "file": pick_still(text, used), "dur": 7, "note": "official still"}, broll(8)]
        if i == 1:
            segs.insert(0, {"type": "card", "card": f"work/cards/{slug}/title.png", "dur": 4})
        if i == len(data["chapters"]):
            segs.append({"type": "card", "card": f"work/cards/{slug}/endscreen.png", "dur": 12})
        chapters.append({"title": ch["title"], "segments": segs})
    save_json(dest, {"slug": slug, "notes": "Generated from the owner's footage: official trailer/Extended Look recordings and Rockstar press-pack stills, weapon-free segments only.", "chapters": chapters})
    print("->", dest)

if __name__ == "__main__":
    main()
