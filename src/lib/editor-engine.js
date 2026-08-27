const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value));

export const TRACKS = [
  { id: 'video', name: 'Video', type: 'video' },
  { id: 'broll', name: 'B-Roll', type: 'video' },
  { id: 'text', name: 'Text', type: 'text' },
  { id: 'caption', name: 'Caption', type: 'caption' },
  { id: 'audio', name: 'Audio', type: 'audio' },
  { id: 'voice', name: 'Voice', type: 'audio' },
];

export function createKeyframe(time, value) { return { id: crypto.randomUUID(), time, value }; }

export function interpolateKeyframes(keyframes = [], time, fallback) {
  if (!keyframes.length) return fallback;
  const ordered = [...keyframes].sort((a, b) => a.time - b.time);
  if (time <= ordered[0].time) return ordered[0].value;
  if (time >= ordered[ordered.length - 1].time) return ordered[ordered.length - 1].value;
  const rightIndex = ordered.findIndex((item) => item.time >= time);
  const left = ordered[rightIndex - 1];
  const right = ordered[rightIndex];
  const t = (time - left.time) / Math.max(0.0001, right.time - left.time);
  if (typeof left.value === 'number' && typeof right.value === 'number') return left.value + (right.value - left.value) * t;
  return t < 0.5 ? left.value : right.value;
}

export function makeClip({ id = crypto.randomUUID(), trackId = 'video', label = 'Clip', start = 0, end = 4, sourceStart = 0, sourceEnd = 4, ...rest } = {}) {
  return {
    id, trackId, label, start, end, sourceStart, sourceEnd,
    opacity: 1, volume: 1,
    transform: { x: 0, y: 0, scale: 1, rotate: 0, keyframes: [] },
    ...rest,
  };
}

export function splitClip(clip, at) {
  if (at <= clip.start || at >= clip.end) return [clip];
  const ratio = (at - clip.start) / Math.max(0.001, clip.end - clip.start);
  const sourceAt = clip.sourceStart + (clip.sourceEnd - clip.sourceStart) * ratio;
  return [
    { ...clip, id: crypto.randomUUID(), end: at, sourceEnd: sourceAt },
    { ...clip, id: crypto.randomUUID(), start: at, sourceStart: sourceAt },
  ];
}

export function moveClip(clips, clipId, delta, minStart = 0) {
  return clips.map((clip) => clip.id === clipId
    ? { ...clip, start: Math.max(minStart, clip.start + delta), end: Math.max(minStart + 0.1, clip.end + delta) }
    : clip);
}

export function resizeClip(clip, edge, delta, minLength = 0.15) {
  if (edge === 'start') {
    const start = Math.min(clip.end - minLength, Math.max(0, clip.start + delta));
    return { ...clip, start, sourceStart: clip.sourceStart + (start - clip.start) };
  }
  const end = Math.max(clip.start + minLength, clip.end + delta);
  return { ...clip, end, sourceEnd: clip.sourceEnd + (end - clip.end) };
}

export function normalizeTimeline(clips = []) {
  return [...clips].sort((a, b) => a.start - b.start).map((clip) => ({
    ...clip,
    start: Number(Math.max(0, clip.start).toFixed(3)),
    end: Number(Math.max(clip.start + 0.01, clip.end).toFixed(3)),
  }));
}

export function createRealEstateTracks({ smartCuts = [], duration = 45, title = '', price = '', caption = '', music = null } = {}) {
  const main = smartCuts.length
    ? smartCuts.map((item, index) => makeClip({
      id: item.id,
      trackId: 'video',
      label: item.label || `Cảnh ${index + 1}`,
      start: index * 3.6,
      end: Math.min(duration, index * 3.6 + 3.6),
      sourceStart: item.sourceStart,
      sourceEnd: item.sourceEnd,
      score: item.quality,
      sceneType: item.type,
    }))
    : [makeClip({ trackId: 'video', label: 'Video Gốc', start: 0, end: duration, sourceStart: 0, sourceEnd: duration })];
  const text = makeClip({ trackId: 'text', label: 'Headline + Giá', start: 0, end: Math.min(5, duration), text: title, secondary: price, preset: 'premium' });
  const legal = makeClip({ trackId: 'text', label: 'Pháp Lý / USP', start: Math.min(5, Math.max(1, duration * 0.55)), end: Math.min(duration, Math.max(7, duration * 0.7)), text: caption || 'Sổ Hồng Riêng • Vị Trí Đẹp' });
  const cta = makeClip({ trackId: 'text', label: 'CTA', start: Math.max(0, duration - 5), end: duration, text: 'GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ', preset: 'cta' });
  return {
    video: main,
    broll: [],
    text: [text, legal, cta],
    caption: [],
    audio: music ? [makeClip({ trackId: 'audio', label: music.name, start: 0, end: duration, volume: 0.18, sourceStart: 0, sourceEnd: music.duration || duration })] : [],
    voice: [],
  };
}

export function estimateBeatGrid(duration, bpm = 100) {
  const interval = 60 / Math.max(40, Math.min(220, bpm));
  return Array.from({ length: Math.ceil(duration / interval) }, (_, index) => Number((index * interval).toFixed(3)));
}

export function snapToBeat(time, beatGrid = [], threshold = 0.12) {
  if (!beatGrid.length) return time;
  let closest = beatGrid[0];
  let distance = Math.abs(time - closest);
  for (const beat of beatGrid) {
    const nextDistance = Math.abs(time - beat);
    if (nextDistance < distance) { closest = beat; distance = nextDistance; }
  }
  return distance <= threshold ? closest : time;
}

export function deriveTransform(clip, time) {
  const keyframes = clip?.transform?.keyframes || [];
  return {
    x: interpolateKeyframes(keyframes.filter((frame) => frame.property === 'x').map((frame) => ({ time: frame.time, value: frame.value })), time, clip?.transform?.x || 0),
    y: interpolateKeyframes(keyframes.filter((frame) => frame.property === 'y').map((frame) => ({ time: frame.time, value: frame.value })), time, clip?.transform?.y || 0),
    scale: clamp(interpolateKeyframes(keyframes.filter((frame) => frame.property === 'scale').map((frame) => ({ time: frame.time, value: frame.value })), time, clip?.transform?.scale || 1), 0.3, 4),
    rotate: interpolateKeyframes(keyframes.filter((frame) => frame.property === 'rotate').map((frame) => ({ time: frame.time, value: frame.value })), time, clip?.transform?.rotate || 0),
  };
}
