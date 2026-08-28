const SYSTEM = `You are GQ AI Editor OS, a production-grade Vietnamese video editing agent for real-estate sales.
Return ONLY valid JSON.
Never invent property facts. Use only facts supplied by the user or asset metadata; missing claims must be omitted or marked as placeholders.
Create an executable edit plan, not prose.
Schema: {project:{duration,aspect,style},story:{hook,cta},scenes:[{assetId,start,end,role,score,reason}],overlays:[{start,end,text,kind}],captions:{enabled,style},audio:{musicMood,voice,ducking},color:{preset,exposure,contrast,saturation},export:{format,codec,fps,width}}.
Optimize the first 3 seconds, pacing, semantic B-roll matching, readability, factuality and CTA.`;

const fallback = ({ prompt = '', videoMeta = {}, assets = [] } = {}) => {
  const text = prompt.toLowerCase();
  const requested = Number((text.match(/(\d+)\s*(?:giây|s)/i) || [])[1]) || 45;
  const duration = Math.min(Math.max(5, requested), Number(videoMeta.duration || requested || 45));
  const aspect = text.includes('16:9') || text.includes('ngang') ? '16:9' : text.includes('1:1') ? '1:1' : '9:16';
  const ordered = assets.slice(0, 8).map((a, i) => ({ assetId: a.id || a.name || String(i), start: 0, end: 0, role: i === 0 ? 'hook' : 'broll', score: 100 - i * 8, reason: 'Fallback semantic selection' }));
  return {
    project: { duration, aspect, style: text.includes('sang') || text.includes('cao cấp') ? 'luxury' : 'real-estate-fast' },
    story: { hook: 'CĂN NHÀ ĐÁNG XEM NHẤT KHU VỰC', cta: 'GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ' },
    scenes: ordered,
    overlays: [{ start: 0, end: Math.min(3, duration), text: 'CĂN NHÀ ĐÁNG XEM NHẤT KHU VỰC', kind: 'hook' }, { start: Math.max(0, duration - 4), end: duration, text: 'GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ', kind: 'cta' }],
    captions: { enabled: true, style: 'premium' },
    audio: { musicMood: 'clean-real-estate', voice: true, ducking: true },
    color: { preset: 'luxury', exposure: 0.02, contrast: 1.05, saturation: 1.08 },
    export: { format: 'mp4', codec: 'h264', fps: 30, width: aspect === '9:16' ? 1080 : 1920 },
  };
};

async function authenticate(req) {
  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  const supabaseUrl = process.env.SUPABASE_URL;
  const publishableKey = process.env.SUPABASE_PUBLISHABLE_KEY || process.env.SUPABASE_ANON_KEY;
  if (!token || !supabaseUrl || !publishableKey) return null;
  const response = await fetch(`${supabaseUrl.replace(/\/$/, '')}/auth/v1/user`, { headers: { apikey: publishableKey, Authorization: `Bearer ${token}` } });
  if (!response.ok) return null;
  return response.json();
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  const body = req.body || {};
  const user = await authenticate(req);
  const requireAuth = String(process.env.REQUIRE_AUTH || 'true') !== 'false';
  if (requireAuth && !user) return res.status(401).json({ error: 'Unauthorized' });

  const apiKey = process.env.AI_API_KEY || process.env.OPENAI_API_KEY;
  const baseUrl = (process.env.AI_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, '');
  const model = process.env.AI_MODEL || 'gpt-4.1-mini';
  const payload = { prompt: body.prompt || '', videoMeta: body.videoMeta || {}, assets: body.assets || [], skill: body.skill || 'real-estate-pro' };

  if (!apiKey) return res.status(200).json({ provider: 'fallback', userId: user?.id || null, plan: fallback(payload) });

  try {
    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, temperature: 0.15, response_format: { type: 'json_object' }, messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: JSON.stringify(payload) }] }),
    });
    if (!response.ok) throw new Error(`AI provider ${response.status}: ${await response.text()}`);
    const data = await response.json();
    const plan = JSON.parse(data.choices?.[0]?.message?.content || '{}');
    return res.status(200).json({ provider: 'remote', userId: user?.id || null, plan });
  } catch (error) {
    console.error(error);
    return res.status(200).json({ provider: 'fallback', userId: user?.id || null, warning: 'AI provider unavailable', plan: fallback(payload) });
  }
}
