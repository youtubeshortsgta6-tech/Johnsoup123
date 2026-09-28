# VICE Check long-form pipeline

Produces everything up to the YouTube upload for one script: voiceover, cards, cut, thumbnail, upload text.

## Setup once

```
pip install pillow imageio-ffmpeg piper-tts        # ffmpeg is bundled by imageio-ffmpeg if none is installed
mkdir -p voices && cd voices && curl -sSL -o v.tgz https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-high.tar.gz && tar xzf v.tgz && rm v.tgz
```

Voice: Piper `en-us-ryan-high`, a local neural male voice, no API and no credits. Pace is set by `PIPER_LENGTH` (default 1.2, about 145 wpm; higher = slower).
ElevenLabs Liam is still available with `--engine elevenlabs` in `voice.py` when `ELEVENLABS_API_KEY` is set and `api.elevenlabs.io` is reachable.

Footage lives in `footage/` (never committed):

```
footage/trailer1.mp4   footage/trailer2.mp4   footage/extended-look-2026-08.mp4     official Rockstar trailers, your download
footage/screens/*.jpg                                                            official Rockstar screenshots / site postcards
footage/photos/*.jpg                                                             your own, licensed, or CC photos
footage/credits.txt                                                              one credit line per CC photo (goes in the description)
```

The shot list for each video (`vice-check/shotlists/<slug>.json`) names every file it expects and the trailer timecodes to fill in.

## Build a video

```
python vice-check/pipeline/run.py vice-check/scripts/longform-florida-locations-2026-09-26.md \
       --shotlist vice-check/shotlists/florida-locations.json --date 2026-09-28
```

Outputs: `out/<date>-<slug>.mp4` (1920x1080, 30 fps, VO at -14 LUFS), `out/<date>-<slug>-thumb.png` (1280x720), `out/<date>-<slug>-upload.txt` (title, description with real chapter timestamps, tags, post time).

Flags: `--allow-placeholders` renders a red MISSING card wherever a footage file is absent (preview cut only, never upload it). `--dry-voice` uses silence instead of TTS. `--revoice` discards cached chapter audio and re-records. `--music path.mp3` mixes a licensed bed at -20 dB under the VO. `--tail 8` holds the end screen for 8 s after the narration (YouTube end screens need 5 to 20 s).

## Per-video steps (what run.py does)

1. `extract_vo.py` drops `[VISUAL]` cues and headings, keeps `[PAUSE]`, splits on `## Chapter:` headings.
2. `voice.py` voices each chapter, turns `[PAUSE]` into 1.5 s of silence (`--pause`), joins chapters with a 1.0 s gap (`--gap`), writes `vo/<slug>/timing.json`.
3. `cards.py` renders the original graphic cards (dark background, pink/teal, VI badge). No logos, no game art, no faces.
4. `assemble.py` scales each chapter's shots to fit that chapter's VO exactly, then concatenates and normalises.
5. `thumbnail.py` draws the thumbnail from primitives (no real faces or characters).
6. `upload_txt.py` writes the upload sheet from the script's Packaging block and the measured chapter times.

## Guardrails checked by the pipeline

- Missing footage stops the build unless you ask for a placeholder preview.
- Only files you put in `footage/` and cards drawn from primitives reach the cut. Nothing is downloaded.
- Chapter timestamps come from the measured voiceover, never from estimates.
- Runtime is printed; the upload sheet says whether the video clears the 8:00 mid-roll line.

Manual checks that stay with you: no graphic violence in the first 7 s or the thumbnail (the Florida cold open is a statue and a photo), every spoken fact matches the corrected script, and the altered-content toggle stays off for an AI voice alone.

## Script format

```
# Title
slug: florida-locations
post: 2026-09-28 12:00 PT
## Chapter: <name>        one per YouTube chapter
[VISUAL: ...]             cue lines are dropped from the VO
[PAUSE]                   1.5 s silence
## Packaging              title, title_alt_1, title_alt_2, description: | ..., tags, thumbnail
```

Scripts from the GTA 6 yt clips Project need their `## Chapter:` headings added and their open corrections applied before they go here.

## Getting footage to the pipeline

This build environment cannot reach YouTube, Google Drive links, Dropbox or WeTransfer, but it can download GitHub release assets from this repo. So:

1. Download the official trailers (Trailer 1, Trailer 2, the Aug 2026 Extended Look) from Rockstar's own channels on your machine.
2. Collect the official screenshots / site postcards you want to use in a folder named `screens/`, and any licensed or Creative Commons photos in `photos/` with a `credits.txt` beside them. Zip those two folders as `stills.zip`.
3. On GitHub, open this repo, go to Releases, create a release with the tag `footage` (any title), and attach `trailer1.mp4`, `trailer2.mp4`, `extended-look-2026-08.mp4` and `stills.zip` as release assets. Each asset can be up to 2 GB.
4. Tell the session the release is up. `vice-check/pipeline/fetch_footage.py` pulls the assets into `footage/` and unzips the stills.

Screenshots alone can also be dropped in a Google Drive folder shared with the connected account; the pipeline can pull those (they are small), but not the trailers.
