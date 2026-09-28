"""Step 6: write out/<date>-<slug>-upload.txt with title, description (real chapter timestamps), tags, post time.
Usage: python upload_txt.py work/<slug>/chapters.json vo/<slug>/timing.json out/<date>-<slug>-upload.txt [--video out/<date>-<slug>.mp4] [--credits credits.txt]
"""
import sys
from pathlib import Path
from common import load_json, fmt_ts, media_duration

def main():
    a = sys.argv[1:]
    if len(a) < 3: sys.exit(__doc__)
    ch, tm, dest = load_json(a[0]), load_json(a[1]), Path(a[2])
    meta = ch["meta"]
    credits = Path(a[a.index("--credits") + 1]).read_text().strip() if "--credits" in a else ""
    chapters = " · ".join(f"{fmt_ts(c['start'])} {c['title']}" for c in tm["chapters"])
    desc = meta.get("description", "").strip().split("\n\n")
    desc.insert(1, "Chapters: " + chapters)
    if credits: desc.append("Photo credits:\n" + credits)
    body = "\n\n".join(desc)
    video_sec = media_duration(a[a.index("--video") + 1]) if "--video" in a else tm["runtime_sec"]
    runtime = fmt_ts(video_sec)
    txt = f"""TITLE
{meta.get('title','')}

ALT TITLES (A/B)
{meta.get('title_alt_1','')}
{meta.get('title_alt_2','')}

POST TIME
{meta.get('post','')}

RUNTIME
{runtime} video, {fmt_ts(tm['runtime_sec'])} narration{'  (mid-roll eligible: 8:00 or longer)' if video_sec >= 480 else '  (under 8:00, no mid-roll)'}

DESCRIPTION
{body}

TAGS
{meta.get('tags','')}

SETTINGS
Altered or synthetic content: OFF (AI voice only; no realistic AI-generated scenes)
Thumbnail: out/{dest.stem.replace('-upload','')}-thumb.png
"""
    dest.write_text(txt)
    print(f"-> {dest}")

if __name__ == "__main__":
    main()
