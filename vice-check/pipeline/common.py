"""Shared helpers for the VICE Check pipeline."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repo root
VC = ROOT / "vice-check"
FOOTAGE = ROOT / "footage"
VO = ROOT / "vo"
OUT = ROOT / "out"
WORK = ROOT / "work"

def ffmpeg_bin() -> str:
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("ffmpeg not found. Install ffmpeg or `pip install imageio-ffmpeg`.")

def run(cmd, quiet=True):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(" ".join(map(str, cmd)), file=sys.stderr)
        print(p.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"command failed: {cmd[0]}")
    return p

def media_duration(path) -> float:
    """Seconds, from ffprobe if present, else parsed from ffmpeg -i."""
    if shutil.which("ffprobe"):
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
        return float(p.stdout.strip())
    p = subprocess.run([ffmpeg_bin(), "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", p.stderr)      # container duration = longest stream
    if not m:
        raise SystemExit(f"could not measure {path}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)

def fmt_ts(sec: float) -> str:
    sec = int(round(sec))
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def load_json(p):
    return json.loads(Path(p).read_text())

def save_json(p, data):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(data, indent=2))
