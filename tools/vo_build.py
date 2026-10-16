#!/usr/bin/env python
"""Build a voice-over track from a timed script via the local VieNeu Studio server.

  python tools/vo_build.py vo/script.json --voice "Mai Anh" --out out/vo.wav [--tail 1.5]

script.json = [{"t": 0.5, "text": "Xin chào"}, {"t": 4.0, "text": "...", "voice": "Thiện Minh"}]
  t     = start second on the film timeline (snap to a beat start where you can)
  text  = Vietnamese text; emotion tags [cười] [thở dài] [hắng giọng] allowed
Writes out/vo.wav (48 kHz mono) and out/vo.json = [{t0, t1, text}] for the beat map.
Each line keeps its exact rendered length, so timings need no speech-to-text pass.
Set VIENEU_URL to override the server (default http://127.0.0.1:8001).
"""
import argparse, io, json, os, urllib.request, urllib.error
import numpy as np, soundfile as sf, librosa

ap = argparse.ArgumentParser(); ap.add_argument('script'); ap.add_argument('--voice', default=None)
ap.add_argument('--out', default='out/vo.wav'); ap.add_argument('--tail', type=float, default=1.5)
ap.add_argument('--temperature', type=float, default=0.8); ap.add_argument('--top-k', type=int, default=25)
a = ap.parse_args()
BASE = os.environ.get('VIENEU_URL', 'http://127.0.0.1:8001'); SR = 48000

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r: return json.load(r)

def tts(text, voice):
    body = {'text': text, 'temperature': a.temperature, 'top_k': a.top_k}
    if voice: body['voice'] = voice
    req = urllib.request.Request(BASE + '/api/tts', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r: raw = r.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f'TTS lỗi {e.code}: {e.read().decode(errors="ignore")[:200]}')
    y, sr = sf.read(io.BytesIO(raw), dtype='float32', always_2d=False)
    if y.ndim > 1: y = y.mean(axis=1)
    return librosa.resample(y, orig_sr=sr, target_sr=SR) if sr != SR else y

health = get('/api/health')
if not health.get('status', {}).get('loaded'): raise SystemExit('VieNeu đang tải model (loaded=false). Chờ rồi chạy lại.')
lines = json.load(open(a.script))
lines.sort(key=lambda l: l['t'])

clips, meta, end = [], [], 0.0
for l in lines:
    y = tts(l['text'], l.get('voice', a.voice))
    t0 = float(l['t'])
    if t0 < end - 1e-3: raise SystemExit(f'Lời thoại tại {t0:.2f}s chồng lên đoạn trước (kết thúc {end:.2f}s). Lùi t lại.')
    clips.append((t0, y)); meta.append({'t0': round(t0, 3), 't1': round(t0 + len(y) / SR, 3), 'text': l['text']})
    end = t0 + len(y) / SR
    print(f"  {t0:6.2f}s  {len(y)/SR:5.2f}s  {l['text'][:60]}")

total = end + a.tail
track = np.zeros(int(total * SR), dtype=np.float32)
for t0, y in clips:
    i = int(round(t0 * SR)); track[i:i + len(y)] += y
os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
sf.write(a.out, track, SR)
json.dump(meta, open(os.path.join(os.path.dirname(a.out) or '.', 'vo.json'), 'w'), ensure_ascii=False, indent=1)
print(f'✓ {a.out}  ({len(clips)} lines, {total:.2f} s) + vo.json')
