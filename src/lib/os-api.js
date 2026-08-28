import { supabase } from './supabase';

async function authHeaders(extra = {}) {
  if (!supabase) return { 'Content-Type': 'application/json', ...extra };
  const { data } = await supabase.auth.getSession();
  const token = data?.session?.access_token;
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...extra };
}

export async function getUser() {
  if (!supabase) return null;
  const { data } = await supabase.auth.getUser();
  return data?.user || null;
}

export async function signIn(email, password) {
  if (!supabase) throw new Error('Chưa cấu hình Supabase.');
  return supabase.auth.signInWithPassword({ email, password });
}

export async function signUp(email, password) {
  if (!supabase) throw new Error('Chưa cấu hình Supabase.');
  return supabase.auth.signUp({ email, password });
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut();
}

export async function createProject({ name, settings = {} }) {
  if (!supabase) return { data: { id: crypto.randomUUID(), name, settings }, error: null };
  return supabase.rpc('create_ai_editor_project', { p_name: name, p_settings: settings });
}

export async function listProjects() {
  if (!supabase) return { data: [], error: null };
  return supabase.from('projects').select('id,name,status,settings,created_at,updated_at').order('updated_at', { ascending: false });
}

export async function uploadAsset(projectId, file, kind = 'video') {
  if (!supabase) return { data: null, error: new Error('Supabase chưa cấu hình.') };
  const { data: project, error: projectError } = await supabase.from('projects').select('id,workspace_id').eq('id', projectId).single();
  if (projectError) return { data: null, error: projectError };
  const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, '-');
  const path = `${project.workspace_id}/${project.id}/${crypto.randomUUID()}-${safeName}`;
  const upload = await supabase.storage.from('ai-editor-assets').upload(path, file, { upsert: false, contentType: file.type });
  if (upload.error) return upload;
  const metadata = { original_name: file.name, kind, last_modified: file.lastModified };
  const inserted = await supabase.from('assets').insert({ project_id: project.id, workspace_id: project.workspace_id, kind, storage_path: upload.data.path, original_name: file.name, mime_type: file.type, size_bytes: file.size, metadata }).select().single();
  return inserted;
}

export async function createRenderJob({ projectId, editPlan, output = {} }) {
  const response = await fetch('/api/render', { method: 'POST', headers: await authHeaders(), body: JSON.stringify({ projectId, editPlan, output }) });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || 'Không tạo được render job.');
  return payload;
}

export async function createAgentPlan({ projectId, prompt, videoMeta, assets = [], skill = 'real-estate-pro' }) {
  const response = await fetch('/api/agent', { method: 'POST', headers: await authHeaders(), body: JSON.stringify({ projectId, prompt, videoMeta, assets, skill }) });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || 'AI Agent lỗi.');
  return payload;
}

export function subscribeRenderJob(jobId, onChange) {
  if (!supabase || !jobId) return () => {};
  const channel = supabase.channel(`render-job-${jobId}`)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'render_jobs', filter: `id=eq.${jobId}` }, (payload) => onChange(payload.new || payload.old))
    .subscribe();
  return () => { supabase.removeChannel(channel); };
}
