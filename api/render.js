async function authenticate(req) {
  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  const supabaseUrl = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY || process.env.SUPABASE_ANON_KEY;
  if (!token || !supabaseUrl || !key) return null;
  const r = await fetch(`${supabaseUrl.replace(/\/$/, '')}/auth/v1/user`, { headers: { apikey: key, Authorization: `Bearer ${token}` } });
  return r.ok ? r.json() : null;
}

async function supaFetch(url, headers, options = {}) {
  const r = await fetch(url, { ...options, headers: { ...headers, ...(options.headers || {}) } });
  const text = await r.text();
  if (!r.ok) throw new Error(`Supabase ${r.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  const user = await authenticate(req);
  if (String(process.env.REQUIRE_AUTH || 'true') !== 'false' && !user) return res.status(401).json({ error: 'Unauthorized' });

  const { projectId, editPlan = {}, output = {} } = req.body || {};
  if (!projectId) return res.status(400).json({ error: 'projectId is required' });
  const supabaseUrl = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY || process.env.SUPABASE_ANON_KEY;
  if (!supabaseUrl || !key || !user) return res.status(503).json({ error: 'Cloud render requires Supabase authentication.' });

  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  const headers = { apikey: key, Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', Prefer: 'return=representation' };
  let project;
  try {
    const projects = await supaFetch(`${supabaseUrl}/rest/v1/projects?id=eq.${encodeURIComponent(projectId)}&select=id,workspace_id,name`, headers);
    project = projects?.[0];
  } catch (error) { return res.status(403).json({ error: 'Project access denied' }); }
  if (!project) return res.status(404).json({ error: 'Project not found' });

  const scenes = Array.isArray(editPlan.scenes) ? editPlan.scenes : [];
  if (!scenes.length) return res.status(400).json({ error: 'Edit Plan has no scenes.' });
  if (scenes.some((s) => !s?.storage_path)) return res.status(400).json({ error: 'Every scene must include storage_path.' });

  const row = {
    workspace_id: project.workspace_id,
    project_id: project.id,
    created_by: user.id,
    status: 'queued',
    progress: 0,
    engine: process.env.RENDER_ENGINE || 'ffmpeg-worker',
    payload: { editPlan, output },
  };
  let job;
  try {
    const inserted = await supaFetch(`${supabaseUrl}/rest/v1/render_jobs`, headers, { method: 'POST', body: JSON.stringify(row) });
    job = inserted?.[0];
    if (!job?.id) throw new Error('Render job not created');
    await supaFetch(`${supabaseUrl}/rest/v1/projects?id=eq.${encodeURIComponent(project.id)}`, headers, { method: 'PATCH', body: JSON.stringify({ status: 'rendering', updated_at: new Date().toISOString() }) });
    await supaFetch(`${supabaseUrl}/rest/v1/usage_events`, headers, { method: 'POST', body: JSON.stringify({ workspace_id: project.workspace_id, user_id: user.id, event_type: 'render_queued', quantity: Number(editPlan?.project?.duration || output?.duration || 1), metadata: { project_id: project.id, job_id: job.id } }) });
  } catch (error) {
    return res.status(500).json({ error: error.message || 'Could not create render job.' });
  }

  const workerUrl = process.env.RENDER_WORKER_URL;
  const workerSecret = process.env.RENDER_WORKER_SECRET;
  if (!workerUrl) {
    return res.status(202).json({ provider: 'queue', status: 'queued', jobId: job.id, warning: 'Render Worker chưa được deploy. Job đã nằm trong queue và sẽ tự chạy khi worker kết nối.' });
  }

  try {
    const workerResponse = await fetch(workerUrl.replace(/\/$/, '') + '/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(workerSecret ? { 'X-Render-Secret': workerSecret } : {}) },
      body: JSON.stringify({ jobId: job.id, projectId: project.id, editPlan, output }),
    });
    if (!workerResponse.ok) {
      const text = await workerResponse.text();
      console.error('Render worker dispatch failed', workerResponse.status, text);
      return res.status(202).json({ provider: 'queue', status: 'queued', jobId: job.id, warning: 'Worker chưa nhận trực tiếp; queue vẫn giữ job để worker polling.' });
    }
  } catch (error) {
    console.error('Render worker dispatch error', error);
  }

  return res.status(202).json({ provider: 'queue', status: job.status, jobId: job.id });
}
