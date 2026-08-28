const SYSTEM = `You are GQ AI Editor OS, a production-grade Vietnamese video editing agent for real-estate sales.
Return ONLY valid JSON.
Never invent property facts. Use only facts supplied by the user or asset metadata; missing claims must be omitted or marked as placeholders.
Create an executable edit plan, not prose.
Schema: {project:{duration,aspect,style},story:{hook,cta},scenes:[{assetId,assetName,storage_path,start,end,role,score,reason}],overlays:[{start,end,text,kind}],captions:{enabled,style},audio:{musicMood,voice,ducking},color:{preset,exposure,contrast,saturation},export:{format,codec,fps,width}}.
Optimize the first 3 seconds, pacing, semantic B-roll matching, readability, factuality and CTA.`;

const fallback = ({ prompt = '', videoMeta = {}, assets = [], businessRules = {}, skillRules = {} } = {}) => {
  const text = prompt.toLowerCase();
  const requested = Number((text.match(/(\d+)\s*(?:giây|s)/i) || [])[1]) || Number(videoMeta.targetDuration) || 45;
  const duration = Math.min(Math.max(5, requested), Number(videoMeta.duration || requested || 45));
  const aspect = text.includes('16:9') || text.includes('ngang') ? '16:9' : text.includes('1:1') ? '1:1' : '9:16';
  const ordered = assets.slice(0, 30).map((a, i) => ({ assetId: a.id || a.name || String(i), assetName: a.name, storage_path: a.storage_path, start: 0, end: Math.min(4, Number(a.duration_seconds || 4)), role: i === 0 ? 'hook' : 'broll', score: Math.max(40, 100 - i * 2), reason: 'Fallback asset ranking' }));
  return {
    project: { duration, aspect, style: text.includes('sang') || text.includes('cao cấp') ? 'luxury' : 'real-estate-fast' },
    story: { hook: 'CĂN NHÀ ĐÁNG XEM NHẤT KHU VỰC', cta: skillRules.cta || 'GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ' },
    scenes: ordered,
    overlays: [{ start: 0, end: Math.min(3, duration), text: 'CĂN NHÀ ĐÁNG XEM NHẤT KHU VỰC', kind: 'hook' }, { start: Math.max(0, duration - 4), end: duration, text: skillRules.cta || 'GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ', kind: 'cta' }],
    captions: { enabled: true, style: skillRules.captions?.styles?.[0] || 'premium' },
    audio: { musicMood: 'clean-real-estate', voice: true, ducking: true },
    color: { preset: skillRules.color?.preset || 'luxury', exposure: 0.02, contrast: 1.05, saturation: 1.08 },
    export: { format: 'mp4', codec: 'h264', fps: 30, width: aspect === '9:16' ? 1080 : 1920 },
    businessRules,
    skillRules,
  };
};

async function authenticate(req) {
  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  const supabaseUrl = process.env.SUPABASE_URL;
  const publishableKey = process.env.SUPABASE_PUBLISHABLE_KEY || process.env.SUPABASE_ANON_KEY;
  if (!token || !supabaseUrl || !publishableKey) return null;
  const response = await fetch(`${supabaseUrl.replace(/\/$/, '')}/auth/v1/user`, { headers: { apikey: publishableKey, Authorization: `Bearer ${token}` } });
  return response.ok ? response.json() : null;
}

async function restJson(url, headers, options = {}) {
  const response = await fetch(url, { ...options, headers: { ...headers, ...(options.headers || {}) } });
  if (!response.ok) throw new Error(`Supabase ${response.status}: ${await response.text()}`);
  return response.status === 204 ? null : response.json();
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  const body = req.body || {};
  const user = await authenticate(req);
  if (String(process.env.REQUIRE_AUTH || 'true') !== 'false' && !user) return res.status(401).json({ error: 'Unauthorized' });

  const supabaseUrl = process.env.SUPABASE_URL;
  const publishableKey = process.env.SUPABASE_PUBLISHABLE_KEY || process.env.SUPABASE_ANON_KEY;
  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  const headers = { apikey: publishableKey || '', Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', Prefer: 'return=representation' };
  const projectId = body.projectId;
  const payload = { prompt: body.prompt || '', videoMeta: body.videoMeta || {}, assets: Array.isArray(body.assets) ? body.assets.slice(0, 30) : [], skill: body.skill || 'real-estate-pro', businessRules: body.businessRules || {} };
  let skillRules = {};

  if (supabaseUrl && token && projectId) {
    try {
      const skills = await restJson(`${supabaseUrl}/rest/v1/skills?slug=eq.${encodeURIComponent(payload.skill)}&select=rules,version,workspace_id,is_public&order=workspace_id.desc.nullslast`, headers);
      skillRules = skills?.[0]?.rules || {};
    } catch (error) { console.warn('Skill lookup failed:', error.message); }
  }
  payload.businessRules = { ...skillRules, ...payload.businessRules };

  const apiKey = process.env.AI_API_KEY || process.env.OPENAI_API_KEY;
  const baseUrl = (process.env.AI_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, '');
  const model = process.env.AI_MODEL || 'gpt-4.1-mini';
  let plan;
  let provider = 'fallback';

  if (!apiKey) {
    plan = fallback(payload);
  } else {
    try {
      const response = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, temperature: 0.15, response_format: { type: 'json_object' }, messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: JSON.stringify(payload) }] }),
      });
      if (!response.ok) throw new Error(`AI provider ${response.status}: ${await response.text()}`);
      const data = await response.json();
      plan = JSON.parse(data.choices?.[0]?.message?.content || '{}');
      provider = 'remote';
    } catch (error) {
      console.error(error);
      plan = fallback(payload);
    }
  }

  if (supabaseUrl && token && user?.id && projectId) {
    try {
      const project = await restJson(`${supabaseUrl}/rest/v1/projects?id=eq.${encodeURIComponent(projectId)}&select=id,workspace_id`, headers);
      if (project?.[0]) {
        const normalized = { ...plan, businessRules: payload.businessRules, generated_by: provider, generated_at: new Date().toISOString() };
        await restJson(`${supabaseUrl}/rest/v1/projects?id=eq.${encodeURIComponent(projectId)}`, headers, { method: 'PATCH', body: JSON.stringify({ status: 'ready', edit_plan: normalized, updated_at: new Date().toISOString() }) });
        await restJson(`${supabaseUrl}/rest/v1/analyses`, headers, { method: 'POST', body: JSON.stringify({ project_id: projectId, asset_id: null, transcript: payload.videoMeta?.transcript || {}, scenes: normalized.scenes || [], vision: payload.videoMeta?.vision || payload.videoMeta?.clips || {}, scores: { provider, skill: payload.skill } }) });
      }
    } catch (error) { console.warn('Plan persistence warning:', error.message); }
  }

  return res.status(200).json({ provider, userId: user?.id || null, skill: payload.skill, plan });
}
