import http from 'node:http';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import ffmpegPath from 'ffmpeg-static';
import { createClient } from '@supabase/supabase-js';

const PORT = Number(process.env.PORT || 8080);
const SECRET = process.env.RENDER_WORKER_SECRET || '';
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const BUCKET = process.env.STORAGE_BUCKET || 'ai-editor-assets';

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}
if (!SECRET) {
  console.error('Missing RENDER_WORKER_SECRET');
  process.exit(1);
}

const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false },
});

function json(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(body));
}

async function body(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
}

async function setJob(jobId, patch) {
  const { error } = await admin.from('render_jobs').update({ ...patch, updated_at: new Date().toISOString() }).eq('id', jobId);
  if (error) throw error;
}

async function storageDownload(storagePath, dest) {
  const { data, error } = await admin.storage.from(BUCKET).download(storagePath);
  if (error) throw error;
  const arrayBuffer = await data.arrayBuffer();
  await fs.writeFile(dest, Buffer.from(arrayBuffer));
}

async function storageUpload(storagePath, filePath, contentType) {
  const buffer = await fs.readFile(filePath);
  const { error } = await admin.storage.from(BUCKET).upload(storagePath, buffer, {
    contentType,
    upsert: true,
    cacheControl: '3600',
  });
  if (error) throw error;
  return storagePath;
}

function runFfmpeg(args, onProgress) {
  return new Promise((resolve, reject) => {
    const child = spawn(ffmpegPath, args, { stdio: ['ignore', 'pipe', 'pipe'] });
    let stderr = '';
    let durationUs = 0;
    child.stderr.on('data', (buf) => {
      const text = buf.toString();
      stderr += text;
      const dm = text.match(/Duration: (\d+):(\d+):(\d+\.\d+)/);
      if (dm) durationUs = ((Number(dm[1]) * 3600) + (Number(dm[2]) * 60) + Number(dm[3])) * 1e6;
      const tm = text.match(/time=(\d+):(\d+):(\d+\.\d+)/);
      if (tm && durationUs > 0) {
        const currentUs = ((Number(tm[1]) * 3600) + (Number(tm[2]) * 60) + Number(tm[3])) * 1e6;
        onProgress(Math.max(1, Math.min(98, Math.round((currentUs / durationUs) * 100))));
      }
    });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) return resolve();
      reject(new Error(`ffmpeg exited ${code}: ${stderr.slice(-3000)}`));
    });
  });
}

function safeName(value) {
  return String(value || 'clip').replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 100);
}

async function processJob(payload) {
  const { jobId, projectId, editPlan = {}, output = {} } = payload;
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'gq-render-'));
  const inputPaths = [];
  try {
    await setJob(jobId, { status: 'processing', progress: 3, engine: 'ffmpeg-worker', started_at: new Date().toISOString(), error: null });
    const scenes = Array.isArray(editPlan.scenes) ? editPlan.scenes : [];
    if (!scenes.length) throw new Error('Edit Plan has no scenes');

    for (let i = 0; i < scenes.length; i++) {
      const scene = scenes[i];
      const storagePath = scene.storage_path || scene.storagePath || scene.path;
      if (!storagePath) throw new Error(`Scene ${i + 1} missing storage_path`);
      const ext = path.extname(storagePath) || '.mp4';
      const local = path.join(tmp, `${String(i).padStart(4, '0')}-${safeName(path.basename(storagePath))}${ext === '.mp4' ? '' : ext}`);
      await storageDownload(storagePath, local);
      inputPaths.push({ local, scene });
      await setJob(jobId, { progress: Math.min(20, 5 + Math.round(((i + 1) / scenes.length) * 15)) });
    }

    const concatList = path.join(tmp, 'concat.txt');
    const segmentPaths = [];
    for (let i = 0; i < inputPaths.length; i++) {
      const { local, scene } = inputPaths[i];
      const seg = path.join(tmp, `seg-${String(i).padStart(4, '0')}.mp4`);
      const start = Number(scene.start ?? scene.sourceStart ?? 0);
      const end = Number(scene.end ?? scene.sourceEnd ?? 0);
      const duration = Math.max(0.2, end > start ? end - start : Number(scene.duration || 3));
      const args = ['-y', '-ss', String(Math.max(0, start)), '-i', local, '-t', String(duration), '-an', '-c:v', 'libx264', '-preset', process.env.FFMPEG_PRESET || 'veryfast', '-crf', String(output.crf ?? 20), '-pix_fmt', 'yuv420p', seg];
      await runFfmpeg(args, (p) => setJob(jobId, { progress: Math.min(75, 20 + Math.round((i / Math.max(1, inputPaths.length)) * 45) + Math.round(p * 0.15)) }));
      segmentPaths.push(seg);
    }

    await fs.writeFile(concatList, segmentPaths.map((p) => `file '${p.replaceAll("'", "'\\''")}'`).join('\n'));
    const outputPath = path.join(tmp, 'output.mp4');
    await runFfmpeg(['-y', '-f', 'concat', '-safe', '0', '-i', concatList, '-c:v', 'libx264', '-preset', process.env.FFMPEG_PRESET || 'veryfast', '-crf', String(output.crf ?? 20), '-c:a', 'aac', '-b:a', String(output.audioBitrate || '192k'), '-movflags', '+faststart', outputPath], (p) => setJob(jobId, { progress: Math.min(96, 68 + Math.round(p * 0.28)) }));

    const outputStoragePath = `${projectId}/render/${jobId}.mp4`;
    await storageUpload(outputStoragePath, outputPath, 'video/mp4');
    const { data: signed, error: signError } = await admin.storage.from(BUCKET).createSignedUrl(outputStoragePath, 60 * 60 * 24 * 7);
    if (signError) throw signError;
    await setJob(jobId, { status: 'completed', progress: 100, output: { storage_path: outputStoragePath, signed_url: signed?.signedUrl, content_type: 'video/mp4' }, finished_at: new Date().toISOString() });
    return { jobId, status: 'completed', outputStoragePath, signedUrl: signed?.signedUrl };
  } catch (error) {
    console.error('render job failed', jobId, error);
    await setJob(jobId, { status: 'failed', error: error?.message || String(error), finished_at: new Date().toISOString() }).catch(() => {});
    throw error;
  } finally {
    await fs.rm(tmp, { recursive: true, force: true }).catch(() => {});
  }
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/health') return json(res, 200, { ok: true, service: 'gq-render-worker' });
  if (req.method !== 'POST' || req.url !== '/render') return json(res, 404, { error: 'Not found' });
  if (req.headers['x-render-secret'] !== SECRET) return json(res, 401, { error: 'Unauthorized' });
  try {
    const payload = await body(req);
    if (!payload.jobId || !payload.projectId) return json(res, 400, { error: 'jobId and projectId required' });
    res.writeHead(202, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ accepted: true, jobId: payload.jobId }));
    setImmediate(() => processJob(payload).catch((error) => console.error(error)));
  } catch (error) {
    return json(res, 400, { error: error?.message || 'Invalid request' });
  }
});

server.listen(PORT, () => console.log(`GQ Render Worker listening on :${PORT}`));
