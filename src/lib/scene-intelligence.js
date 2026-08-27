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
  return { brightness: mean, contrast: Math.sqrt(variance), sharpness: clamp(edges / Math.max(1, pixels) * 5) };
}

function classifyVisual(stats) {
  if (stats.brightness < 0.10) return { label: 'Thiếu Sáng', type: 'bad', confidence: 0.91 };
  if (stats.brightness > 0.93) return { label: 'Quá Sáng', type: 'bad', confidence: 0.86 };
  if (stats.sharpness < 0.09) return { label: 'Có Thể Bị Mờ/Rung', type: 'bad', confidence: 0.72 };
  if (stats.sharpness > 0.22 && stats.contrast > 0.15) return { label: 'Cảnh Nổi Bật', type: 'good', confidence: 0.78 };
  return { label: 'Cảnh Bình Thường', type: 'neutral', confidence: 0.64 };
}

export async function sampleVideoFrames(file, options = {}) {
  const sampleCount = Math.max(12, Math.min(60, options.sampleCount || 32));
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
    const time = duration ? Math.min(Math.max(0, duration - 0.02), (index / Math.max(1, sampleCount - 1)) * duration) : 0;
    video.currentTime = time;
    await new Promise((resolve, reject) => {
      const done = () => { cleanup(); resolve(); };
      const fail = () => { cleanup(); reject(new Error('Không seek được frame video')); };
      const cleanup = () => { video.removeEventListener('seeked', done); video.removeEventListener('error', fail); };
      video.addEventListener('seeked', done, { once: true });
      video.addEventListener('error', fail, { once: true });
    });
    ctx.drawImage(video, 0, 0, width, height);
    const stats = frameStats(ctx, width, height);
    const motion = previous ? Math.abs(stats.brightness - previous.brightness) + Math.abs(stats.contrast - previous.contrast) : 0;
    const quality = clamp(0.62 * stats.sharpness + 0.38 * (1 - Math.abs(stats.brightness - 0.55) * 1.4));
    frames.push({ index, time, ...stats, motion: clamp(motion * 6), quality: clamp(quality), ...classifyVisual(stats) });
    previous = stats;
  }
  URL.revokeObjectURL(video.src);
  return { duration, width: video.videoWidth, height: video.videoHeight, frames };
}

function chooseAnchors(frames, count) {
  const usable = frames.filter((frame) => frame.type !== 'bad');
  const source = usable.length ? usable : frames;
  const selected = [];
  const sorted = [...source].sort((a, b) => b.quality - a.quality || a.time - b.time);
  const minGap = Math.max(0.7, frames.length ? (frames[frames.length - 1].time / Math.max(1, count)) * 0.55 : 1);
  for (const frame of sorted) {
    if (selected.every((item) => Math.abs(item.time - frame.time) >= minGap)) selected.push(frame);
    if (selected.length >= count) break;
  }
  return selected.length ? selected.sort((a, b) => a.time - b.time) : [{ ...frames[0] }];
}

export function buildSmartCuts(frames = [], targetDuration = 45, sourceDuration = null) {
  if (!frames.length) return [];
  const source = Number(sourceDuration || frames[frames.length - 1]?.time || 0);
  const effectiveDuration = Math.max(0.5, Math.min(Number(targetDuration) || 45, source || Number(targetDuration) || 45));
  const count = Math.max(4, Math.min(12, Math.round(effectiveDuration / 4.5)));
  const anchors = chooseAnchors(frames, count);
  const clipLength = effectiveDuration / anchors.length;
  return anchors.map((anchor, index) => {
    const safeHalf = Math.max(0.35, Math.min(clipLength * 0.45, 2));
    let sourceStart = Math.max(0, anchor.time - safeHalf);
    let sourceEnd = sourceStart + clipLength;
    if (source) {
      if (sourceEnd > source) {
        sourceEnd = source;
        sourceStart = Math.max(0, sourceEnd - clipLength);
      }
      if (sourceEnd - sourceStart < clipLength) {
        sourceStart = 0;
        sourceEnd = Math.min(source, clipLength);
      }
    }
    const timelineStart = Number((index * clipLength).toFixed(3));
    const timelineEnd = index === anchors.length - 1 ? Number(effectiveDuration.toFixed(3)) : Number(((index + 1) * clipLength).toFixed(3));
    return {
      id: `smart-${index}-${Math.round(anchor.time * 100)}`,
      type: index === 0 ? 'hook' : index === anchors.length - 1 ? 'cta' : 'broll',
      label: index === 0 ? 'Hook / Cảnh Đẹp' : index === anchors.length - 1 ? 'CTA / Chốt' : `B-Roll ${index}`,
      start: timelineStart,
      end: timelineEnd,
      timelineStart,
      timelineEnd,
      sourceStart: Number(sourceStart.toFixed(3)),
      sourceEnd: Number(sourceEnd.toFixed(3)),
      quality: Number(anchor.quality.toFixed(2)),
      note: anchor.label,
    };
  });
}

export function buildAutoEditPlan(frames = [], targetDuration = 45, sourceDuration = null) {
  const effective = Math.max(0.5, Math.min(Number(targetDuration) || 45, Number(sourceDuration || targetDuration) || targetDuration));
  const clips = buildSmartCuts(frames, effective, sourceDuration);
  const total = clips.reduce((sum, clip) => sum + (clip.end - clip.start), 0);
  return { duration: Number(total.toFixed(3)), requestedDuration: Number(targetDuration), clips };
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
