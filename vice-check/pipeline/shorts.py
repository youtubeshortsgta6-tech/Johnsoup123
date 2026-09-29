"""Cut a vertical Short (1080x1920, <=60 s) from a built long-form video, one chapter at a time.

Usage: python shorts.py <slug> <chapter number> [--date YYYY-MM-DD] [--headline "TEXT"] [--start S --end S]
  Reads vo/<slug>/timing.json for the chapter's start/end on the video timeline and out/<date>-<slug>.mp4
  (the date defaults to the newest out/ file for that slug). Blurred, darkened fill behind the 16:9 picture,
  headline on top, "Full check on VICE Check" plus the VI badge at the bottom. Writes out/shorts/<slug>-chNN.mp4.
"""
import sys, json
from pathlib import Path
from PIL import Image, ImageDraw
from common import ROOT, OUT, VO, ffmpeg_bin, run, media_duration
from cards import font, PINK, TEAL, WHITE, BG2

def overlay(headline: str, dest: Path):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # headline block, top: wrap to ~3 lines
    words = headline.upper().split(); lines, cur = [], ""
    f = font(92)
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > 960 and cur: lines.append(cur); cur = w
        else: cur = t
    if cur: lines.append(cur)
    y = 150
    for i, line in enumerate(lines[:4]):
        for dx in (-5, 5):
            for dy in (-5, 5): d.text((540 + dx, y + dy), line, font=f, fill=(0, 0, 0, 255), anchor="ma")
        d.text((540, y), line, font=f, fill=WHITE if i % 2 == 0 else PINK, anchor="ma"); y += 104
    # bottom CTA
    d.rounded_rectangle([90, 1600, 990, 1720], radius=24, fill=(11, 12, 20, 230), outline=PINK, width=4)
    d.text((540, 1660), "FULL CHECK ON VICE CHECK", font=font(46), fill=WHITE, anchor="mm")
    d.text((540, 1770), "link in the comments", font=font(34, False), fill=TEAL, anchor="mm")
    # VI badge
    d.rounded_rectangle([880, 60, 1020, 150], radius=16, outline=PINK, width=5, fill=BG2 + (255,))
    d.text((950, 105), "VI", font=font(56), fill=WHITE, anchor="mm")
    im.save(dest)

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    slug, ch = a[0], int(a[1])
    timing = json.loads((VO / slug / "timing.json").read_text())
    c = timing["chapters"][ch - 1]
    start = float(a[a.index("--start") + 1]) if "--start" in a else c["start"]
    end = float(a[a.index("--end") + 1]) if "--end" in a else c["end"]
    if end - start > 60: sys.exit(f"chapter is {end-start:.0f}s; Shorts must be 60s or less. Pass --start/--end to trim.")
    headline = a[a.index("--headline") + 1] if "--headline" in a else c["title"]
    date = a[a.index("--date") + 1] if "--date" in a else None
    srcs = sorted(OUT.glob(f"{date or '*'}-{slug}.mp4"))
    srcs = [s for s in srcs if "preview" not in s.name and ".part" not in s.name]
    if not srcs: sys.exit(f"no built video for {slug} in out/")
    src = srcs[-1]
    dest = OUT / "shorts" / f"{slug}-ch{ch:02d}.mp4"; dest.parent.mkdir(parents=True, exist_ok=True)
    ov = dest.with_suffix(".overlay.png"); overlay(headline, ov)
    fc = ("[0:v]split=2[bg][fg];"
          "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5,eq=brightness=-0.25[bgb];"
          "[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2[v1];[v1][1:v]overlay=0:0,format=yuv420p[v]")
    run([ffmpeg_bin(), "-y", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(src), "-i", str(ov),
         "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-r", "30", "-movflags", "+faststart", str(dest)])
    ov.unlink()
    print(f"-> {dest}  {media_duration(dest):.1f}s  headline: {headline}")

if __name__ == "__main__":
    main()
