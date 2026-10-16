#!/usr/bin/env node
/* Voice-over via VieNeu Studio (local TTS server, default http://127.0.0.1:8001).
 *   node tools/vo.mjs "Xin chào" --voice "Mai Anh" --out out/vo.wav [--temperature 0.8] [--top-k 25]
 *   node tools/vo.mjs --list                       # print voice ids
 * Text may contain emotion tags: [cười] [thở dài] [hắng giọng]. Voice ids come from /api/voices — never invented.
 */
import fs from 'node:fs'; import path from 'node:path';
const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const base = process.env.VIENEU_URL || 'http://127.0.0.1:8001';

const health = await fetch(`${base}/api/health`).then(r => r.json()).catch(() => null);
if (!health) { console.error(`VieNeu server không phản hồi tại ${base}. Hãy chạy VieNeu Studio trước.`); process.exit(1); }
if (!health.status?.loaded) { console.error('VieNeu đang tải model (loaded=false). Chờ rồi chạy lại.'); process.exit(1); }

if (argv.includes('--list')) {
  const { voices } = await fetch(`${base}/api/voices`).then(r => r.json());
  for (const v of voices) console.log(`${v.id}\t${v.label}`);
  process.exit(0);
}

const text = argv[0];
if (!text || text.startsWith('--')) { console.error('Usage: node tools/vo.mjs "<text>" [--voice <id>] [--out <file.wav>]'); process.exit(1); }
const body = { text, temperature: +arg('temperature', 0.8), top_k: +arg('top-k', 25) };
if (arg('voice')) body.voice = arg('voice');
const out = arg('out', 'out/vo.wav');

const res = await fetch(`${base}/api/tts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
if (!res.ok) { const err = await res.json().catch(() => ({})); console.error(`TTS lỗi ${res.status}: ${err.detail ?? 'không rõ'}`); process.exit(1); }
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, Buffer.from(await res.arrayBuffer()));
console.log(`✓ ${out}`);
