"""Step 4: cut the video from a shotlist + voiceover, 1920x1080 30fps, VO at -14 LUFS.

Usage: python assemble.py <shotlist.json> <vo/<slug>/timing.json> <out.mp4> [--allow-placeholders] [--music path.mp3] [--tail 8]

Shotlist format: {"chapters":[{"title":..., "segments":[seg,...]}]} where seg is one of
  {"type":"footage","file":"footage/trailer1.mp4","in":12.5,"out":18.0,"dur":6,"note":"..."}
  {"type":"image","file":"footage/screens/keys-whale.jpg","dur":5,"note":"..."}          (official screenshot / licensed photo)
  {"type":"card","card":"work/cards/map.png","dur":6}
  {"type":"compare","left":"...jpg","right":"...jpg","left_text":"..","right_text":"..","dur":3}
Segment durations are scaled so each chapter's visuals exactly fill that chapter's VO time.
A missing file stops the build unless --allow-placeholders, which renders a red MISSING card instead (preview only).
"""
import sys
from pathlib import Path
from common import ffmpeg_bin, run, media_duration, load_json, WORK, ROOT
from cards import Card

FPS = 30
VF_FIT = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b0c14,setsar=1,fps=30,format=yuv420p"
# screen recordings: per-file crop (letterbox bars + the recorder's FPS/GPU overlay in the top band), then fill 1080p
CROPS = {"trailer1.mp4": "crop=1904:1032:8:32", "trailer2.mp4": "crop=1902:936:8:34", "extended-look-2026-08.mp4": "crop=1902:1040:8:34"}
FILL = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30,format=yuv420p"
def vf_footage(src):
    return CROPS.get(Path(src).name, "crop=iw-48:ih-64:24:32") + "," + FILL
VF_ZOOM = "scale=2400:-2,zoompan=z='min(zoom+0.0006,1.08)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,format=yuv420p"

def render_segment(seg, dur, idx, tmp, allow_ph):
    ff = ffmpeg_bin()
    out = tmp / f"seg{idx:03d}.mp4"
    frames = max(int(dur * FPS), 1)
    kind = seg["type"]
    src = None
    if kind in ("footage", "image"):
        src = ROOT / seg["file"]
        if not src.exists() and seg.get("fallback") and (ROOT / seg["fallback"]).exists():
            src = ROOT / seg["fallback"]
        if not src.exists():
            if not allow_ph:
                raise SystemExit(f"missing {src}  ({seg.get('note','')})\nAdd the file or run with --allow-placeholders for a preview cut.")
            src = None
    if kind == "compare":
        card = tmp / f"compare{idx:03d}.png"
        Card().compare(seg.get("left_label", "GTA 6"), seg["left_text"], seg.get("right_label", "Real"), seg["right_text"],
                       ROOT / seg["left"] if seg.get("left") else None, ROOT / seg["right"] if seg.get("right") else None).save(card)
        src, kind = card, "image"
    if kind == "card":
        src, kind = ROOT / seg["card"], "image"
    if src is None:
        card = tmp / f"missing{idx:03d}.png"
        Card().placeholder(seg.get("note", seg.get("type")), seg.get("file")).save(card)
        src, kind = card, "image"
    if kind == "footage":
        src_len = media_duration(src)
        if float(seg.get("in", 0)) + 0.5 >= src_len:
            raise SystemExit(f"in-point {seg.get('in')} is past the end of {src} ({src_len:.0f}s)  ({seg.get('note','')})")
        clip = min(dur, float(seg["out"]) - float(seg.get("in", 0))) if seg.get("out") is not None else dur   # never run past the out-point; tpad holds the last frame
        cmd = [ff, "-y", "-ss", str(seg.get("in", 0)), "-t", f"{clip:.3f}", "-i", str(src), "-an",
               "-vf", vf_footage(src) + f",tpad=stop_mode=clone:stop_duration={dur:.3f}", "-t", f"{dur:.3f}",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS), str(out)]
    else:
        vf = VF_ZOOM.format(frames=frames) if seg.get("zoom", True) and "missing" not in src.name else VF_FIT
        cmd = [ff, "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(src), "-t", f"{dur:.3f}",
               "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(FPS), str(out)]
    run(cmd)
    if out.stat().st_size < 2000:
        raise SystemExit(f"segment {out.name} rendered empty: {seg}")
    return out

def main():
    a = sys.argv[1:]
    if len(a) < 3: sys.exit(__doc__)
    shot, timing, dest = load_json(a[0]), load_json(a[1]), Path(a[2])
    allow_ph = "--allow-placeholders" in a
    music = Path(a[a.index("--music") + 1]) if "--music" in a else None
    tail = float(a[a.index("--tail") + 1]) if "--tail" in a else 8.0
    tmp = WORK / shot.get("slug", dest.stem) / "segments"; tmp.mkdir(parents=True, exist_ok=True)
    for old in list(tmp.glob("missing*.png")) + list(tmp.glob("compare*.png")): old.unlink()   # counts must reflect this run
    if len(shot["chapters"]) != len(timing["chapters"]):
        raise SystemExit(f"shotlist has {len(shot['chapters'])} chapters, VO timing has {len(timing['chapters'])}")
    segs, idx = [], 0
    total = timing["runtime_sec"]
    for ci, (sc, tc) in enumerate(zip(shot["chapters"], timing["chapters"])):
        # chapter visual span = VO start of this chapter -> VO start of next (last chapter runs to the end + tail)
        start = tc["start"]
        end = timing["chapters"][ci + 1]["start"] if ci + 1 < len(timing["chapters"]) else total + tail
        span = end - start
        nominal = sum(s.get("dur", 5) for s in sc["segments"])
        scale = span / nominal
        acc = 0.0
        for si, seg in enumerate(sc["segments"]):
            dur = seg.get("dur", 5) * scale
            if si == len(sc["segments"]) - 1: dur = span - acc      # absorb rounding
            acc += dur
            segs.append(render_segment(seg, dur, idx, tmp, allow_ph)); idx += 1
        print(f"  chapter {ci+1:02d} {tc['title']:<26} {span:6.1f}s  {len(sc['segments'])} shots")
    lst = tmp / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
    silent = tmp / "video-silent.mp4"
    run([ffmpeg_bin(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])
    vo = Path(timing.get("vo_path") or (ROOT / "vo" / timing["slug"] / "full.wav"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg_bin(), "-y", "-i", str(silent), "-i", str(vo)]
    if music and music.exists():
        cmd += ["-stream_loop", "-1", "-i", str(music),
                "-filter_complex", "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[vo];[2:a]volume=0.10[m];[vo][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-filter_complex", "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]", "-map", "0:v", "-map", "[a]"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-movflags", "+faststart", str(dest)]   # video is longer than VO by `tail`; keep it
    run(cmd)
    n_missing = len(list(tmp.glob("missing*.png")))
    print(f"-> {dest}  {media_duration(dest):.1f}s" + (f"  ({n_missing} placeholder shots, preview only)" if n_missing else ""))

if __name__ == "__main__":
    main()
