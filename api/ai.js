const SYSTEM = `You are GQ Video Editor AI, a Vietnamese real-estate video editing planner. Return ONLY JSON with keys: duration, aspect, style, hook, cta, scenes, captions, color, audio, export. scenes is an array of objects with type, priority, reason. Optimize for short property-sales videos, factual claims, strong first 3 seconds, clear CTA, and professional typography. Never invent property facts; use placeholders when data is missing.`;

function fallback(prompt = '', duration = 45) {
  const text = prompt.toLowerCase();
  const seconds = Number((text.match(/(\d+)\s*(?:giây|s)/i) || [])[1]) || Math.min(60, Math.max(20, Math.round(duration)));
  return {
    duration: seconds,
    aspect: text.includes('16:9') || text.includes('ngang') ? '16:9' : text.includes('1:1') ? '1:1' : '9:16',
    style: text.includes('sang') || text.includes('cao cấp') ? 'luxury' : text.includes('ấm') ? 'family' : 'fast',
    hook: 'CĂN NHÀ ĐÁNG XEM NHẤT KHU VỰC',
    cta: 'GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ',
    scenes: [
      { type: 'hook', priority: 10, reason: 'Mặt tiền/toàn cảnh cho ấn tượng đầu tiên' },
      { type: 'road', priority: 8, reason: 'Tạo ngữ cảnh vị trí và khả năng tiếp cận' },
      { type: 'living', priority: 9, reason: 'Thể hiện không gian sống chính' },
      { type: 'bedroom', priority: 7, reason: 'Bổ sung công năng' },
      { type: 'cta', priority: 10, reason: 'Kết thúc bằng giá trị và hành động' },
    ],
    captions: { enabled: true, style: 'premium', keywordHighlight: true },
    color: { auto: true, exposure: 0.02, contrast: 1.05, saturation: 1.08, gamma: 1.02 },
    audio: { voiceEnhance: true, ducking: true, targetLufs: -16 },
    export: { format: 'mp4', codec: 'h264', crf: 18, fps: 30 },
  };
}

function extractJson(text) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const candidate = fenced?.[1] || text;
  const first = candidate.indexOf('{');
  const last = candidate.lastIndexOf('}');
  if (first < 0 || last < first) throw new Error('AI did not return JSON');
  return JSON.parse(candidate.slice(first, last + 1));
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { prompt = '', videoMeta = {} } = req.body || {};
  const apiKey = process.env.AI_API_KEY || process.env.OPENAI_API_KEY;
  const baseUrl = (process.env.AI_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, '');
  const model = process.env.AI_MODEL || 'gpt-4.1-mini';

  if (!apiKey) return res.status(200).json({ provider: 'fallback', plan: fallback(prompt, videoMeta.duration || 45) });

  try {
    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        temperature: 0.2,
        response_format: { type: 'json_object' },
        messages: [
          { role: 'system', content: SYSTEM },
          { role: 'user', content: JSON.stringify({ prompt, videoMeta }) },
        ],
      }),
    });
    if (!response.ok) throw new Error(`AI provider ${response.status}: ${await response.text()}`);
    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || '{}';
    return res.status(200).json({ provider: 'remote', plan: extractJson(content) });
  } catch (error) {
    console.error(error);
    return res.status(200).json({ provider: 'fallback', warning: 'AI provider unavailable', plan: fallback(prompt, videoMeta.duration || 45) });
  }
}
