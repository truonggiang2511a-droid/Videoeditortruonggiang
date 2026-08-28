async function authenticate(req) {
  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  const supabaseUrl = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY || process.env.SUPABASE_ANON_KEY;
  if (!token || !supabaseUrl || !key) return null;
  const r = await fetch(`${supabaseUrl.replace(/\/$/, '')}/auth/v1/user`, { headers: { apikey: key, Authorization: `Bearer ${token}` } });
  return r.ok ? r.json() : null;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  const user = await authenticate(req);
  if (String(process.env.REQUIRE_AUTH || 'true') !== 'false' && !user) return res.status(401).json({ error: 'Unauthorized' });

  const { projectId, editPlan = {}, output = {} } = req.body || {};
  if (!projectId) return res.status(400).json({ error: 'projectId is required' });

  const supabaseUrl = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY || process.env.SUPABASE_ANON_KEY;
  if (!supabaseUrl || !key || !user) {
    return res.status(200).json({ provider: 'local', status: 'queued-local', jobId: crypto.randomUUID(), message: 'Supabase chưa cấu hình; render worker chưa được kết nối.' });
  }

  const headers = { apikey: key, Authorization: `Bearer ${req.headers.authorization?.replace(/^Bearer\s+/i, '')}`, 'Content-Type': 'application/json', Prefer: 'return=representation' };
  const projectResponse = await fetch(`${supabaseUrl}/rest/v1/projects?id=eq.${encodeURIComponent(projectId)}&select=id,workspace_id`, { headers });
  if (!projectResponse.ok) return res.status(403).json({ error: 'Project access denied' });
  const projects = await projectResponse.json();
  const project = projects?.[0];
  if (!project) return res.status(404).json({ error: 'Project not found' });

  const row = { workspace_id: project.workspace_id, project_id: project.id, created_by: user.id, status: 'queued', progress: 0, engine: process.env.RENDER_ENGINE || 'render-adapter', payload: { editPlan, output } };
  const insert = await fetch(`${supabaseUrl}/rest/v1/render_jobs`, { method: 'POST', headers, body: JSON.stringify(row) });
  if (!insert.ok) return res.status(500).json({ error: await insert.text() });
  const job = (await insert.json())?.[0];

  const workerUrl = process.env.RENDER_WORKER_URL;
  const workerSecret = process.env.RENDER_WORKER_SECRET;
  if (workerUrl) {
    try {
      await fetch(workerUrl, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(workerSecret ? { 'X-Render-Secret': workerSecret } : {}) }, body: JSON.stringify({ jobId: job.id, projectId: project.id, editPlan, output }) });
    } catch (error) {
      console.error('Render worker dispatch failed', error);
    }
  }

  return res.status(202).json({ provider: 'queue', status: job.status, jobId: job.id });
}
