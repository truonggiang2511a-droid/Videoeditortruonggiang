const STYLE_RULES = [
  { id: 'luxury', words: ['sang', 'cao cấp', 'premium', 'luxury', 'đẳng cấp'] },
  { id: 'family', words: ['gia đình', 'ấm', 'ấm áp', 'hạnh phúc'] },
  { id: 'fast', words: ['nhanh', 'hook mạnh', 'chốt', 'viral', 'cuốn'] },
];

const SCENE_RULES = [
  ['hook', ['mặt tiền', 'mặt trước', 'toàn cảnh', 'căn nhà']],
  ['road', ['đường vào', 'đường', 'hẻm', 'giao thông', 'khu phố']],
  ['living', ['phòng khách', 'phòng khách lớn', 'sofa']],
  ['kitchen', ['bếp', 'phòng ăn', 'tủ bếp']],
  ['bedroom', ['phòng ngủ', 'master', 'phòng con']],
  ['bathroom', ['wc', 'toilet', 'phòng tắm']],
  ['yard', ['sân', 'vườn', 'ban công', 'terrace']],
  ['legal', ['sổ hồng', 'pháp lý', 'thổ cư']],
  ['cta', ['giá', 'liên hệ', 'gọi', 'inbox', 'zalo', 'xem nhà']],
];

function findNumber(text, patterns) {
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return Number(match[1]);
  }
  return null;
}

export function parseVietnameseEditCommand(text = '', sourceDuration = 45) {
  const lower = text.toLowerCase();
  const duration = findNumber(lower, [
    /(\d+(?:\.\d+)?)\s*(?:giây|s)/i,
    /(?:dài|thời lượng)\s*(\d+(?:\.\d+)?)\s*(?:giây|s)/i,
  ]) || Math.min(60, Math.max(20, Math.round(sourceDuration || 45)));

  let style = 'fast';
  for (const rule of STYLE_RULES) {
    if (rule.words.some(word => lower.includes(word))) {
      style = rule.id;
      break;
    }
  }

  const scenes = [];
  for (const [type, words] of SCENE_RULES) {
    if (words.some(word => lower.includes(word))) scenes.push(type);
  }

  const aspect = lower.includes('16:9') || lower.includes('ngang')
    ? '16:9'
    : lower.includes('1:1') || lower.includes('vuông')
      ? '1:1'
      : '9:16';

  const hasPrice = /(giá|tỷ|triệu|triệu\/m2|m2)/i.test(text);
  const wantsCaption = /(caption|phụ đề|sub|phụ de)/i.test(text);
  const wantsMusic = /(nhạc|music|beat|nhịp)/i.test(text);
  const wantsColor = /(màu|sáng|tươi|cinematic|cinema|color)/i.test(text);
  const wantsLogo = /(logo|watermark|thương hiệu)/i.test(text);

  const hook = lower.includes('hook')
    ? 'Đừng Bỏ Lỡ Căn Nhà Này!'
    : 'Căn Nhà Đáng Xem Nhất Khu Vực';

  const cta = hasPrice
    ? 'GỌI NGAY • HẸN XEM NHÀ HÔM NAY'
    : 'INBOX / ZALO ĐỂ NHẬN THÔNG TIN & LỊCH XEM NHÀ';

  return {
    duration,
    style,
    aspect,
    scenes: scenes.length ? scenes : ['hook', 'road', 'living', 'bedroom', 'cta'],
    hook,
    cta,
    features: {
      caption: wantsCaption,
      music: wantsMusic,
      autoColor: wantsColor || true,
      logo: wantsLogo,
      price: hasPrice,
    },
  };
}

export function buildRealEstateTimeline({ duration = 45, sourceDuration = duration, sceneTypes = [] } = {}) {
  const types = sceneTypes.length ? sceneTypes : ['hook', 'road', 'living', 'kitchen', 'bedroom', 'yard', 'cta'];
  const weights = {
    hook: 0.10,
    road: 0.10,
    living: 0.18,
    kitchen: 0.12,
    bedroom: 0.15,
    yard: 0.10,
    legal: 0.08,
    bathroom: 0.08,
    cta: 0.09,
  };
  const fallback = 1 / types.length;
  let cursor = 0;
  return types.map((type, index) => {
    const seconds = duration * (weights[type] || fallback);
    const end = index === types.length - 1 ? duration : Math.min(duration, cursor + seconds);
    const sourceStart = sourceDuration ? Math.min(sourceDuration, (cursor / duration) * sourceDuration) : cursor;
    const sourceEnd = sourceDuration ? Math.min(sourceDuration, (end / duration) * sourceDuration) : end;
    const clip = {
      id: `${type}-${index}-${Math.round(cursor * 100)}`,
      type,
      label: {
        hook: 'Hook / Mặt Tiền', road: 'Đường Vào', living: 'Phòng Khách',
        kitchen: 'Bếp', bedroom: 'Phòng Ngủ', bathroom: 'WC', yard: 'Sân / Vườn',
        legal: 'Pháp Lý', cta: 'Giá + CTA',
      }[type] || 'B-Roll',
      start: Number(sourceStart.toFixed(2)),
      end: Number(sourceEnd.toFixed(2)),
      timelineStart: Number(cursor.toFixed(2)),
      timelineEnd: Number(end.toFixed(2)),
      volume: type === 'cta' ? 1 : 0.92,
    };
    cursor = end;
    return clip;
  });
}

export function generateSalesCopy({ title = 'CĂN NHÀ ĐÁNG XEM', price = '', area = '', location = '' } = {}) {
  return {
    hook: `${title.toUpperCase()}`,
    value: [area && `Diện tích ${area}`, location && `Vị trí ${location}`].filter(Boolean).join(' • '),
    price: price || 'GIÁ ĐANG TỐT',
    cta: 'GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ',
  };
}

export async function requestAiPlan({ prompt, videoMeta, endpoint } = {}) {
  if (endpoint) {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, videoMeta }),
    });
    if (!response.ok) throw new Error(`AI endpoint failed: ${response.status}`);
    return response.json();
  }
  return parseVietnameseEditCommand(prompt, videoMeta?.duration || 45);
}
