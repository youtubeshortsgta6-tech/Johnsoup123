"""One-command build for a VICE Check long-form video.

  python vice-check/pipeline/run.py vice-check/scripts/longform-florida-locations-2026-09-26.md \\
         --shotlist vice-check/shotlists/florida-locations.json --date 2026-09-28 \\
         [--dry-voice] [--revoice] [--engine piper|elevenlabs] [--pause 1.5] [--gap 1.0] [--allow-placeholders] [--music x.mp3] [--tail 8]

Steps: extract VO -> voice (Piper, local) -> cards -> assemble -> thumbnail -> upload txt.
"""
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def step(*cmd):
    print("\n$", " ".join(map(str, cmd)))
    subprocess.run([sys.executable, *map(str, cmd)], check=True, cwd=ROOT)

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    script = Path(a[0])
    shotlist = a[a.index("--shotlist") + 1]
    date = a[a.index("--date") + 1]
    step(HERE / "extract_vo.py", script)
    slug = None                                   # the script's `slug:` line
    for line in script.read_text().splitlines():
        if line.startswith("slug:"): slug = line.split(":", 1)[1].strip(); break
    if not slug: sys.exit("script has no `slug:` line")
    chapters = ROOT / "work" / slug / "chapters.json"
    voice_args = [HERE / "voice.py", chapters]
    if "--dry-voice" in a: voice_args.append("--dry-run")
    if "--revoice" in a:
        for f in (ROOT / "vo" / slug).glob("*.mp3"): f.unlink()
    for flag in ("--pause", "--gap", "--engine"):
        if flag in a: voice_args += [flag, a[a.index(flag) + 1]]
    step(*voice_args)
    step(HERE / "cards.py", ROOT / "work" / "cards")
    timing = ROOT / "vo" / slug / "timing.json"
    out_mp4 = ROOT / "out" / f"{date}-{slug}.mp4"
    asm = [HERE / "assemble.py", shotlist, timing, out_mp4]
    if "--allow-placeholders" in a: asm.append("--allow-placeholders")
    if "--music" in a: asm += ["--music", a[a.index("--music") + 1]]
    if "--tail" in a: asm += ["--tail", a[a.index("--tail") + 1]]
    step(*asm)
    step(HERE / "thumbnail.py", ROOT / "out" / f"{date}-{slug}-thumb.png")
    up = [HERE / "upload_txt.py", chapters, timing, ROOT / "out" / f"{date}-{slug}-upload.txt", "--video", out_mp4]
    credits = ROOT / "footage" / "credits.txt"
    if credits.exists(): up += ["--credits", credits]
    step(*up)
    print("\nDONE. Review:", out_mp4, "+ thumb + upload.txt")

if __name__ == "__main__":
    main()
