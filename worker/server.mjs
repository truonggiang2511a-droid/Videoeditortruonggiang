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
const MAX_CONCURRENCY = Math.max(1, Math.min(8, Number(process.env.MAX_CONCURRENCY || 1)));
const POLL_MS = Math.max(1000, Number(process.env.POLL_MS || 3000));
const STALE_MINUTES = Math.max(10, Number(process.env.STALE_MINUTES || 30));

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY || !SECRET) {
  console.error('Missing SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or RENDER_WORKER_SECRET');
  process.exit(1);
}

const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, { auth: { autoRefreshToken: false, persistSession: false } });
const running = new Set();

function json(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(body));
}

async function parseBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
}

async function setJob(jobId, patch) {
  const { error } = await admin.from('render_jobs').update({ ...patch, updated_at: new Date().toISOString() }).eq('id', jobId);
  if (error) throw error;
}

async function download(pathname, target) {
  const { data, error } = await admin.storage.from(BUCKET).download(pathname);
  if (error) throw error;
  await fs.writeFile(target, Buffer.from(await data.arrayBuffer()));
}

async function upload(pathname, source) {
  const buffer = await fs.readFile(source);
  const { error } = await admin.storage.from(BUCKET).upload(pathname, buffer, { upsert: true, contentType: 'video/mp4', cacheControl: '3600' });
  if (error) throw error;
}

function safeName(value) { return String(value || 'clip').replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 100); }

function runFfmpeg(args, onProgress = () => {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(ffmpegPath, args, { stdio: ['ignore', 'pipe', 'pipe'] });
    let stderr = '';
    let total = 0;
    child.stderr.on('data', (buf) => {
      const text = buf.toString(); stderr += text;
      const dm = text.match(/Duration: (\d+):(\d+):(\d+\.\d+)/);
      if (dm) total = ((Number(dm[1]) * 3600) + (Number(dm[2]) * 60) + Number(dm[3])) * 1e6;
      const tm = text.match(/time=(\d+):(\d+):(\d+\.\d+)/);
      if (tm && total) {
        const now = ((Number(tm[1]) * 3600) + (Number(tm[2]) * 60) + Number(tm[3])) * 1e6;
        onProgress(Math.max(1, Math.min(99, Math.round(now / total * 100))));
      }
    });
    child.on('error', reject);
    child.on('close', (code) => code === 0 ? resolve() : reject(new Error(`ffmpeg exited ${code}: ${stderr.slice(-2500)}`)));
  });
}

function textFileArgs(text, filePath) { return fs.writeFile(filePath, String(text || '')); }
function aspectScale(aspect) {
  if (aspect === '16:9') return 'scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080';
  if (aspect === '1:1') return 'scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080';
  return 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920';
}

async function renderJob(job) {
  const { id: jobId, project_id: projectId, payload = {} } = job;
  const editPlan = payload.editPlan || {};
  const output = payload.output || {};
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'gq-render-'));
  const sourceFiles = [];
  try {
    const { data: project, error: projectError } = await admin.from('projects').select('id,workspace_id').eq('id', projectId).single();
    if (projectError || !project) throw new Error('Project not found');
    await setJob(jobId, { engine: 'ffmpeg-worker', progress: 2, error: null, started_at: new Date().toISOString(), status: 'processing' });
    await admin.from('projects').update({ status: 'rendering', updated_at: new Date().toISOString() }).eq('id', projectId);

    const scenes = Array.isArray(editPlan.scenes) ? editPlan.scenes.slice(0, 30) : [];
    if (!scenes.length) throw new Error('Edit Plan has no scenes');
    for (const [i, scene] of scenes.entries()) {
      const sp = scene.storage_path || scene.storagePath;
      const allowedPrefix = `${project.workspace_id}/${project.id}/`;
      if (!sp || !String(sp).startsWith(allowedPrefix)) throw new Error(`Scene ${i + 1} storage_path is outside project workspace`);
      const local = path.join(tmp, `${String(i).padStart(3, '0')}-${safeName(path.basename(sp))}`);
      await download(sp, local);
      sourceFiles.push({ local, scene });
      await setJob(jobId, { progress: Math.max(3, Math.round((i + 1) / scenes.length * 15)) });
    }

    const segments = [];
    for (const [i, item] of sourceFiles.entries()) {
      const seg = path.join(tmp, `seg-${String(i).padStart(3, '0')}.mp4`);
      const start = Math.max(0, Number(item.scene.sourceStart ?? item.scene.start ?? 0));
      const end = Number(item.scene.sourceEnd ?? item.scene.end ?? 0);
      const duration = Math.max(0.25, end > start ? end - start : Number(item.scene.duration || 3));
      await runFfmpeg(['-y','-ss',String(start),'-i',item.local,'-t',String(duration),'-an','-vf',aspectScale(editPlan.project?.aspect || output.aspect || '9:16'),'-r',String(output.fps || editPlan.export?.fps || 30),'-c:v','libx264','-preset',process.env.FFMPEG_PRESET || 'veryfast','-crf',String(output.crf ?? 20),'-pix_fmt','yuv420p',seg],
        (p) => setJob(jobId, { progress: Math.min(78, 15 + Math.round((i / Math.max(1, sourceFiles.length)) * 55) + Math.round(p * 0.12)) }));
      segments.push(seg);
    }

    const concatList = path.join(tmp, 'concat.txt');
    await fs.writeFile(concatList, segments.map((p) => `file '${p.replaceAll("'", "'\\''")}'`).join('\n'));
    let base = path.join(tmp, 'concat.mp4');
    await runFfmpeg(['-y','-f','concat','-safe','0','-i',concatList,'-c:v','libx264','-preset',process.env.FFMPEG_PRESET || 'veryfast','-crf',String(output.crf ?? 20),'-pix_fmt','yuv420p','-an',base],
      (p) => setJob(jobId, { progress: Math.min(86, 70 + Math.round(p * 0.16)) }));

    const overlays = Array.isArray(editPlan.overlays) ? editPlan.overlays.slice(0, 8) : [];
    const overlayInputs = [];
    let filters = [];
    for (let i = 0; i < overlays.length; i++) {
      const o = overlays[i];
      if (!o?.text) continue;
      const tf = path.join(tmp, `overlay-${i}.txt`);
      await textFileArgs(o.text, tf);
      const start = Math.max(0, Number(o.start || 0));
      const end = Math.max(start + 0.1, Number(o.end || start + 3));
      filters.push(`drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=${tf}:fontcolor=white:bordercolor=black:borderw=3:fontsize=58:x=(w-text_w)/2:y=h*0.10:enable='between(t,${start},${end})'`);
    }

    const audioPath = editPlan.audio?.storage_path || editPlan.audio?.storagePath;
    if (filters.length) {
      const withText = path.join(tmp, 'with-text.mp4');
      await runFfmpeg(['-y','-i',base,'-vf',filters.join(','),'-c:v','libx264','-preset',process.env.FFMPEG_PRESET || 'veryfast','-crf',String(output.crf ?? 20),'-pix_fmt','yuv420p','-an',withText],
        (p) => setJob(jobId, { progress: Math.min(93, 86 + Math.round(p * 0.07)) }));
      base = withText;
    }

    let finalPath = path.join(tmp, 'output.mp4');
    if (audioPath && String(audioPath).startsWith(`${project.workspace_id}/${project.id}/`)) {
      const audioLocal = path.join(tmp, `audio-${safeName(path.basename(audioPath))}`);
      await download(audioPath, audioLocal);
      await runFfmpeg(['-y','-i',base,'-stream_loop','-1','-i',audioLocal,'-filter_complex','[1:a]volume=0.16[a1];[a1]apad[a2]','-map','0:v:0','-map','[a2]','-shortest','-c:v','copy','-c:a','aac','-b:a',String(output.audioBitrate || '192k'),'-movflags','+faststart',finalPath]);
    } else {
      await fs.copyFile(base, finalPath);
    }

    const outputStoragePath = `${project.workspace_id}/${project.id}/render/${jobId}.mp4`;
    await upload(outputStoragePath, finalPath);
    const { data: signed, error: signError } = await admin.storage.from(BUCKET).createSignedUrl(outputStoragePath, 7 * 24 * 60 * 60);
    if (signError) throw signError;
    await setJob(jobId, { status: 'completed', progress: 100, output: { storage_path: outputStoragePath, signed_url: signed.signedUrl, content_type: 'video/mp4', engine: 'ffmpeg-worker', remotion_ready: true }, finished_at: new Date().toISOString() });
    await admin.from('projects').update({ status: 'completed', updated_at: new Date().toISOString() }).eq('id', projectId);
  } catch (error) {
    console.error('render failed', jobId, error);
    await setJob(jobId, { status: 'failed', error: error?.message || String(error), finished_at: new Date().toISOString() }).catch(() => {});
    await admin.from('projects').update({ status: 'failed', updated_at: new Date().toISOString() }).eq('id', projectId).catch(() => {});
  } finally {
    await fs.rm(tmp, { recursive: true, force: true }).catch(() => {});
    running.delete(jobId);
  }
}

async function resetStaleJobs() {
  const cutoff = new Date(Date.now() - STALE_MINUTES * 60 * 1000).toISOString();
  const { error } = await admin.from('render_jobs').update({ status: 'queued', progress: 0, error: `Requeued stale worker job`, updated_at: new Date().toISOString() }).eq('status', 'processing').lt('updated_at', cutoff);
  if (error) console.warn('stale recovery:', error.message);
}

async function pollQueue() {
  if (running.size >= MAX_CONCURRENCY) return;
  const slots = MAX_CONCURRENCY - running.size;
  const { data, error } = await admin.rpc('claim_render_jobs', { p_limit: slots });
  if (error) { console.error('claim queue:', error.message); return; }
  for (const job of data || []) {
    running.add(job.id);
    void renderJob(job);
  }
}

async function dispatchHint(payload) {
  if (!payload?.jobId) return;
  await pollQueue();
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/health') return json(res, 200, { ok: true, service: 'gq-render-worker', concurrency: MAX_CONCURRENCY, running: running.size });
  if (req.method !== 'POST' || req.url !== '/render') return json(res, 404, { error: 'Not found' });
  if (req.headers['x-render-secret'] !== SECRET) return json(res, 401, { error: 'Unauthorized' });
  try {
    const payload = await parseBody(req);
    if (!payload.jobId || !payload.projectId) return json(res, 400, { error: 'jobId and projectId required' });
    await dispatchHint(payload);
    return json(res, 202, { accepted: true, jobId: payload.jobId, queue: true });
  } catch (error) {
    return json(res, 400, { error: error?.message || 'Invalid request' });
  }
});

server.listen(PORT, async () => {
  console.log(`GQ Render Worker listening on :${PORT}`);
  await resetStaleJobs();
  await pollQueue();
  setInterval(async () => { await resetStaleJobs(); await pollQueue(); }, POLL_MS);
});
