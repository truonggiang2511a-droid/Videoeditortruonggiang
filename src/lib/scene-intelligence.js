const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value));

function frameStats(ctx, width, height) {
  const { data } = ctx.getImageData(0, 0, width, height);
  let sum = 0;
  let sq = 0;
  let edges = 0;
  let pixels = 0;
  for (let y = 1; y < height; y += 2) {
    for (let x = 1; x < width; x += 2) {
      const i = (y * width + x) * 4;
      const g = (0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2]) / 255;
      const il = (y * width + x - 1) * 4;
      const iu = ((y - 1) * width + x) * 4;
      const gl = (0.2126 * data[il] + 0.7152 * data[il + 1] + 0.0722 * data[il + 2]) / 255;
      const gu = (0.2126 * data[iu] + 0.7152 * data[iu + 1] + 0.0722 * data[iu + 2]) / 255;
      sum += g;
      sq += g * g;
      edges += Math.min(1, Math.abs(g - gl) + Math.abs(g - gu));
      pixels += 1;
    }
  }
  const mean = sum / Math.max(1, pixels);
  const variance = Math.max(0, sq / Math.max(1, pixels) - mean * mean);
  return {
    brightness: mean,
    contrast: Math.sqrt(variance),
    sharpness: clamp(edges / Math.max(1, pixels) * 5),
  };
}

function classifyVisual(stats) {
  if (stats.brightness < 0.10) return { label: 'Thiếu Sáng', type: 'bad', confidence: 0.91 };
  if (stats.brightness > 0.93) return { label: 'Quá Sáng', type: 'bad', confidence: 0.86 };
  if (stats.sharpness < 0.09) return { label: 'Có Thể Bị Mờ/Rung', type: 'bad', confidence: 0.72 };
  if (stats.sharpness > 0.22 && stats.contrast > 0.15) return { label: 'Cảnh Nổi Bật', type: 'good', confidence: 0.78 };
  return { label: 'Cảnh Bình Thường', type: 'neutral', confidence: 0.64 };
}

export async function sampleVideoFrames(file, options = {}) {
  const sampleCount = Math.max(8, Math.min(48, options.sampleCount || 24));
  const maxWidth = options.width || 320;
  const video = document.createElement('video');
  video.muted = true;
  video.playsInline = true;
  video.preload = 'metadata';
  video.src = URL.createObjectURL(file);
  await new Promise((resolve, reject) => {
    video.onloadedmetadata = resolve;
    video.onerror = () => reject(new Error('Không đọc được metadata video'));
  });
  const duration = Number(video.duration) || 0;
  const scale = Math.min(1, maxWidth / Math.max(1, video.videoWidth || maxWidth));
  const width = Math.max(160, Math.round((video.videoWidth || maxWidth) * scale));
  const height = Math.max(90, Math.round((video.videoHeight || 180) * scale));
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const frames = [];
  let previous = null;
  for (let index = 0; index < sampleCount; index += 1) {
    const time = duration ? Math.min(duration - 0.02, (index / Math.max(1, sampleCount - 1)) * duration) : 0;
    video.currentTime = Math.max(0, time);
    await new Promise((resolve) => { video.onseeked = resolve; });
    ctx.drawImage(video, 0, 0, width, height);
    const stats = frameStats(ctx, width, height);
    let motion = 0;
    if (previous) motion = Math.abs(stats.brightness - previous.brightness) + Math.abs(stats.contrast - previous.contrast);
    const quality = clamp(0.62 * stats.sharpness + 0.38 * (1 - Math.abs(stats.brightness - 0.55) * 1.4));
    const visual = classifyVisual(stats);
    frames.push({ index, time, ...stats, motion: clamp(motion * 6), quality: clamp(quality), ...visual });
    previous = stats;
  }
  URL.revokeObjectURL(video.src);
  return { duration, width: video.videoWidth, height: video.videoHeight, frames };
}

export function buildSmartCuts(frames = [], targetDuration = 45) {
  if (!frames.length) return [];
  const usable = frames.filter((frame) => frame.type !== 'bad').sort((a, b) => b.quality - a.quality);
  const picks = [];
  const minGap = Math.max(1.2, targetDuration / 28);
  for (const frame of usable) {
    if (picks.every((picked) => Math.abs(picked.time - frame.time) >= minGap)) picks.push(frame);
    if (picks.length >= 12) break;
  }
  picks.sort((a, b) => a.time - b.time);
  return picks.map((pick, index) => ({
    id: `smart-${index}-${Math.round(pick.time * 100)}`,
    type: index === 0 ? 'hook' : 'broll',
    label: index === 0 ? 'Hook / Cảnh Đẹp' : `B-Roll ${index}`,
    sourceStart: Math.max(0, pick.time - Math.min(1.5, targetDuration / 20)),
    sourceEnd: pick.time + Math.min(2.8, targetDuration / 10),
    quality: Number(pick.quality.toFixed(2)),
    note: pick.label,
  }));
}

export async function requestVisionPlan({ endpoint, prompt, videoMeta, frames }) {
  if (!endpoint) return null;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, videoMeta, frames }),
  });
  if (!response.ok) throw new Error(`Vision endpoint failed: ${response.status}`);
  return response.json();
}
