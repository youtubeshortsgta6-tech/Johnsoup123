"""Step 2: voice each chapter, concatenate, report runtime.

Default engine is Piper (local, free, no API): voice en-us-ryan-high in voices/.
Pass --engine elevenlabs to use Liam via ElevenLabs instead (needs ELEVENLABS_API_KEY and network access to api.elevenlabs.io).

Usage: python voice.py work/<slug>/chapters.json [--engine piper|elevenlabs] [--pause 1.5] [--gap 1.0] [--dry-run]

Writes:
  vo/<slug>/<nn>.mp3       one file per chapter
  vo/<slug>/full.wav       all chapters joined, chapter gap = --gap seconds
  vo/<slug>/timing.json    chapter start/end seconds (used for YouTube chapters)
--dry-run synthesises silence of the estimated length instead of any TTS,
so the rest of the pipeline can be tested without a voice model or key.
"""
import glob, json, os, sys, urllib.request, wave
from pathlib import Path
from common import VO, ffmpeg_bin, run, media_duration, load_json, save_json

VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"     # Liam
MODEL = "eleven_multilingual_v2"
API = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128"

def tts(text: str, dest: Path, key: str):
    body = json.dumps({"text": text, "model_id": MODEL,
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.2}}).encode()
    req = urllib.request.Request(API, data=body, method="POST", headers={
        "xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())

PIPER_MODEL = os.environ.get("PIPER_MODEL") or (glob.glob(str(VO.parent / "voices" / "**" / "*.onnx"), recursive=True) or [None])[0]
_piper = None
def piper_tts(text: str, dest: Path):
    """Local neural TTS. length_scale > 1 slows delivery (1.0 = model default)."""
    global _piper
    from piper import PiperVoice, SynthesisConfig
    if _piper is None:
        if not PIPER_MODEL:
            sys.exit("no Piper model in voices/. See vice-check/README.md (voice setup).")
        _piper = PiperVoice.load(PIPER_MODEL)
    cfg = SynthesisConfig(length_scale=float(os.environ.get("PIPER_LENGTH", "1.2")), noise_scale=0.55, noise_w_scale=0.7)
    wav = dest.with_suffix(".wav")
    with wave.open(str(wav), "wb") as w:
        _piper.synthesize_wav(text, w, cfg)
    run([ffmpeg_bin(), "-y", "-i", str(wav), "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", str(dest)])
    wav.unlink()

def silence(dest: Path, seconds: float):
    run([ffmpeg_bin(), "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{seconds:.3f}",
         "-c:a", "libmp3lame", "-b:a", "128k", str(dest)])

def concat(parts, dest: Path):
    lst = dest.with_suffix(".txt")
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    codec = ["-c:a", "pcm_s16le"] if dest.suffix == ".wav" else ["-c:a", "libmp3lame", "-b:a", "128k"]
    run([ffmpeg_bin(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-ar", "44100", "-ac", "1", *codec, str(dest)])

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    args = sys.argv[1:]
    data = load_json(args[0])
    pause = float(args[args.index("--pause") + 1]) if "--pause" in args else 1.5
    gap = float(args[args.index("--gap") + 1]) if "--gap" in args else 1.0
    dry = "--dry-run" in args
    engine = args[args.index("--engine") + 1] if "--engine" in args else "piper"
    key = os.environ.get("ELEVENLABS_API_KEY")
    if engine == "elevenlabs-connector":
        # chapter mp3s were produced through the ElevenLabs connector and downloaded to vo/<slug>/NN.mp3 already
        missing = [i for i in range(1, len(data["chapters"]) + 1) if not (VO / data["slug"] / f"{i:02d}.mp3").exists()]
        if missing: sys.exit(f"elevenlabs-connector: chapter files missing for {missing}; download them first")
    if engine == "elevenlabs" and not key and not dry:
        sys.exit("ELEVENLABS_API_KEY is not set. Add it to the environment (never paste it in chat), "
                 "or run with --dry-run to test the pipeline with silent placeholder audio.")
    slug = data["slug"]
    vdir = VO / slug
    vdir.mkdir(parents=True, exist_ok=True)
    chapter_files = []
    total_chars = 0
    for i, ch in enumerate(data["chapters"], 1):
        dest = vdir / f"{i:02d}.mp3"
        if dest.exists() and not dry:
            print(f"  {i:02d} exists, skipping"); chapter_files.append(dest); continue
        # split on [PAUSE]; each run of paragraphs becomes one request
        takes, buf = [], []
        for p in ch["paragraphs"]:
            if p == "[PAUSE]":
                if buf: takes.append("\n\n".join(buf)); buf = []
                takes.append(None)
            else:
                buf.append(p)
        if buf: takes.append("\n\n".join(buf))
        parts = []
        for j, t in enumerate(takes):
            part = vdir / f"{i:02d}_{j}.mp3"
            if t is None:
                silence(part, pause)
            elif dry:
                silence(part, len(t.split()) / 150 * 60)
            elif engine == "elevenlabs":
                total_chars += len(t)
                tts(t, part, key)
            else:
                total_chars += len(t)
                piper_tts(t, part)
            parts.append(part)
        concat(parts, dest)
        for p in parts: p.unlink()
        print(f"  {i:02d} {ch['title']:<28} {media_duration(dest):6.1f}s")
        chapter_files.append(dest)
    # join with a gap between chapters, and record timing
    gapfile = vdir / "_gap.mp3"; silence(gapfile, gap)
    seq, timing, t = [], [], 0.0
    for ch, f in zip(data["chapters"], chapter_files):
        d = media_duration(f)
        timing.append({"title": ch["title"], "start": round(t, 3), "end": round(t + d, 3)})
        seq.append(f); t += d
        seq.append(gapfile); t += gap
    seq.pop(); t -= gap
    full = vdir / "full.wav"
    concat(seq, full)
    gapfile.unlink()
    runtime = media_duration(full)
    save_json(vdir / "timing.json", {"slug": slug, "runtime_sec": runtime, "chapters": timing,
                                     "dry_run": dry, "engine": "silence" if dry else engine,
                                     "voice": "silence" if dry else (VOICE_ID if engine.startswith("elevenlabs") else Path(PIPER_MODEL).name),
                                     "chars": total_chars})
    m, s = divmod(int(round(runtime)), 60)
    print(f"runtime {m}:{s:02d}  ({'DRY RUN, silent' if dry else f'{engine}, {total_chars} chars'})  -> {full}")

if __name__ == "__main__":
    main()
