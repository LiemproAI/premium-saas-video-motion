# Pipeline, commands and measured timings

## Commands
Windows: `python3` may be the Microsoft Store stub. Use `python` instead, or the project venv `./.venv/Scripts/python.exe` if it exists (see `WINDOWS-SETUP.md`). Set `PYTHONUTF8=1` if the console fails on Vietnamese or ✓ characters.
```bash
npm i                                   # playwright (Chromium) — once
python3 -m pip install librosa soundfile numpy   # audio tools — once; ffmpeg must be on PATH

python3 tools/beatgrid.py song.mp3                              # BPM, grid, energy, drop guesses
python3 tools/beatgrid.py song.mp3 --plan "[[0,80,14],[14,94,26]]" --out out/edit.wav
python3 tools/vo_build.py vo/script.json --voice "<id>" --out out/vo.wav   # only with VO: VieNeu at 127.0.0.1:8001
node tools/sheet.mjs templates/kinetic-promo/index.html --every 0.5          # review sheet (≈20 s)
node tools/render.mjs templates/kinetic-promo/index.html --mode preview      # ≈45 s
node tools/cues.mjs templates/kinetic-promo/index.html > out/cues.json
python3 tools/mix.py out/cues.json --music out/edit.wav --sfx assets/audio/sfx.json --vo out/vo.wav --duck 10 --out out/mix.wav   # drop --vo for no-VO films
node tools/render.mjs templates/kinetic-promo/index.html --mode final --audio out/mix.wav --out out/film.mp4
python3 tools/popcheck.py out/film.mp4 --bpm 120
```
Renders are chunked and resumable: if a shell times out, re-run the same command.
Agents: start long renders in the background (`nohup … &`) and poll, don't block one shell call.

## Voice-over stage (when the film has VO)
Order: script → `vo/script.json` → VO audio → beat map → build → mix → final.
1. Write `vo/script.json`: `[{"t": <start s, snapped to a beat>, "text": "...", "voice": "<id>"}]`. Vietnamese keeps diacritics.
2. `python3 tools/vo_build.py vo/script.json --voice "<id>" --out out/vo.wav`. Needs VieNeu Studio at `VIENEU_URL`
   (default `http://127.0.0.1:8001`) with `/api/health` → `loaded: true`. Writes `out/vo.wav` (48 kHz mono) and
   `out/vo.json` `[{t0, t1, text}]`; `t1` is exact because each line keeps its rendered length.
3. Lines may not overlap: the builder stops and asks you to move `t` later if they do.
4. Check the VO in the mix: `--duck 10` (8–12 dB). Music returns after the voice stops; no ducking outside speech.
5. Quick single-line test or voice check: `node tools/vo.mjs "<text>" --voice "<id>" --out out/test.wav`; `--list` shows ids.
Tested: 3 lines (15 s of VO) mixed with music and SFX gave −13.5 LUFS, 1.5 dBFS peak.

## Where the time went — "Converse — The Pink Edit" (28 s, 1440², 60 fps)
| Stage | Wall time | Share |
|---|---|---|
| Author film.html from scratch (one pass) | 5.4 min | 17% |
| Contact-sheet review + 3 bug fixes | 2.0 min | 6% |
| Render: 4 sub-frames × 60 fps = 6 762 screenshots, 2 cores | 21 min (10 lost to a shell timeout) | 65% |
| Blend + encode (tmix, preset slow) | 2.2 min | 7% |
| Mux, package, deliver | 1 min | 3% |

## What we changed and what it measured
| Change | Before | After |
|---|---|---|
| Drop double-rAF wait in `seek()` | 51 ms/seek | 9 ms (pixel-identical frames) |
| CDP `captureScreenshot {optimizeForSpeed}` vs page.screenshot | 104 ms | 92 ms |
| 2 sub-frames instead of 4 | 6 762 samples | 3 380 |
| `radial-gradient` instead of `filter: blur(140px)` (glow shot) | 1 605 ms/frame | 88 ms |
| Chunked, resumable workers (1 per core) | lost 10 min to a timeout | resume in place |
| Preview mode (½ size, 30 fps, no blur) | — | 20 s film in 44 s |
| **Final 20 s 1080p60 with blur + audio (kinetic-promo)** | — | **2 min 40 s** |
Estimated same-machine time for the Converse film with the new pipeline: ≈4 min instead of 23.

## Where the remaining time goes
Screenshot capture ≈ 85% of render time and scales with pixel count. More cores = linear speed-up
(`--workers`). On an 8-core Mac, the 20 s final render takes well under a minute.
The biggest remaining lever is authoring: templates cut the 5-min from-scratch build and most bug loops.
