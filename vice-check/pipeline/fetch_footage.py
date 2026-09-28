"""Pull footage from a GitHub release on this repo into footage/.

Usage: python fetch_footage.py [--tag footage] [--repo owner/name]
Downloads every asset of the release, then unzips any .zip into footage/ (expects screens/ and photos/ inside).
"""
import json, subprocess, sys, urllib.request, zipfile
from pathlib import Path
from common import ROOT, FOOTAGE

def main():
    a = sys.argv[1:]
    tag = a[a.index("--tag") + 1] if "--tag" in a else "footage"
    repo = a[a.index("--repo") + 1] if "--repo" in a else "youtubeshortsgta6-tech/Johnsoup123"
    api = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    with urllib.request.urlopen(urllib.request.Request(api, headers={"Accept": "application/vnd.github+json", "User-Agent": "vice-check"})) as r:
        rel = json.loads(r.read())
    FOOTAGE.mkdir(exist_ok=True)
    for asset in rel.get("assets", []):
        dest = FOOTAGE / asset["name"]
        if dest.exists() and dest.stat().st_size == asset["size"]:
            print("have", dest.name); continue
        print("downloading", asset["name"], f"{asset['size']/1e6:.0f} MB")
        subprocess.run(["curl", "-sS", "-fL", "--retry", "3", "-o", str(dest), asset["browser_download_url"]], check=True)
    for z in FOOTAGE.glob("*.zip"):
        with zipfile.ZipFile(z) as zf:
            zf.extractall(FOOTAGE)
        print("unzipped", z.name)
    print(sorted(p.relative_to(ROOT).as_posix() for p in FOOTAGE.rglob("*") if p.is_file())[:50])

if __name__ == "__main__":
    main()
