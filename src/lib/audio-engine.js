export const MUSIC_LIBRARY = [
  { id: 'realestate-01', name: 'Luxury Walkthrough', bpm: 96, mood: 'Sang • Tin Cậy', url: '' },
  { id: 'realestate-02', name: 'Modern Listing', bpm: 110, mood: 'Hiện Đại • Năng Lượng', url: '' },
  { id: 'realestate-03', name: 'Family Home', bpm: 88, mood: 'Ấm Áp • Gia Đình', url: '' },
  { id: 'realestate-04', name: 'Fast Deal', bpm: 124, mood: 'Nhanh • Chốt Deal', url: '' },
];

export function autoDuckVolume({ musicVolume = 0.18, voicePresent = true } = {}) {
  return voicePresent ? Math.min(0.14, musicVolume) : musicVolume;
}

export function buildBeatCuts({ clipCount = 8, bpm = 110, duration = 30 } = {}) {
  const beat = 60 / Math.max(40, Math.min(220, bpm));
  const bar = beat * 4;
  const ideal = [];
  for (let time = 0; time < duration && ideal.length < clipCount - 1; time += bar) ideal.push(Number(time.toFixed(3)));
  return ideal;
}

export async function decodeAudioPeaks(file, { maxPeaks = 240 } = {}) {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return { peaks: [], bpm: 0 };
  const ctx = new AudioCtx();
  const data = await file.arrayBuffer();
  const buffer = await ctx.decodeAudioData(data.slice(0));
  const channel = buffer.getChannelData(0);
  const bucket = Math.max(1, Math.floor(channel.length / maxPeaks));
  const peaks = [];
  for (let i = 0; i < channel.length; i += bucket) {
    let max = 0;
    const end = Math.min(channel.length, i + bucket);
    for (let j = i; j < end; j += 1) max = Math.max(max, Math.abs(channel[j]));
    peaks.push(Number(max.toFixed(4)));
  }
  await ctx.close();
  const active = peaks.filter((value) => value > 0.28).length;
  const estimatedBpm = buffer.duration ? Math.max(70, Math.min(150, Math.round((active / buffer.duration) * 2 * 60))) : 0;
  return { duration: buffer.duration, peaks, bpm: estimatedBpm };
}

export function createVoiceScript({ title, area, location, price, cta, seconds = 35 } = {}) {
  const lines = [
    title || 'Căn nhà đáng xem trong khu vực',
    area && `Diện tích ${area}`,
    location && `Vị trí ${location}`,
    price && `Giá chỉ ${price}`,
    cta || 'Gọi hoặc Zalo để hẹn xem nhà hôm nay',
  ].filter(Boolean);
  return { text: lines.join('. '), targetSeconds: seconds };
}

export async function requestVoice({ endpoint, text, voice = 'vi-VN' } = {}) {
  if (!endpoint) return null;
  const response = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, voice }) });
  if (!response.ok) throw new Error(`Voice endpoint failed: ${response.status}`);
  return response.blob();
}
