import { FFmpeg } from '@ffmpeg/ffmpeg';
import { fetchFile, toBlobURL } from '@ffmpeg/util';

let ffmpegInstance;
let loaded = false;

export const EXPORT_PROFILES = {
  'TikTok / Reels': { aspect: '9:16', width: 1080, crf: 18, fps: 30, audioBitrate: '192k' },
  Facebook: { aspect: '1:1', width: 1080, crf: 18, fps: 30, audioBitrate: '192k' },
  YouTube: { aspect: '16:9', width: 1920, crf: 18, fps: 30, audioBitrate: '256k' },
  'YouTube 4K': { aspect: '16:9', width: 3840, crf: 18, fps: 30, audioBitrate: '320k' },
  'Master 4K': { aspect: '9:16', width: 2160, crf: 17, fps: 30, audioBitrate: '320k' },
};

export async function getFFmpeg(onProgress) {
  if (!ffmpegInstance) {
    ffmpegInstance = new FFmpeg();
    ffmpegInstance.on('progress', ({ progress }) => onProgress?.(Math.min(100, Math.round(progress * 100))));
  }
  if (!loaded) {
    const baseURL = 'https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.12.10/dist/esm';
    await ffmpegInstance.load({
      coreURL: await toBlobURL(`${baseURL}/ffmpeg-core.js`, 'text/javascript'),
      wasmURL: await toBlobURL(`${baseURL}/ffmpeg-core.wasm`, 'application/wasm'),
    });
    loaded = true;
  }
  return ffmpegInstance;
}

function escapeXml(value) {
  return String(value).replace(/[<>&"']/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' }[c]));
}

function overlaySvg(text, width = 1080, height = 320) {
  const first = escapeXml(text).slice(0, 90);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><defs><filter id="shadow"><feDropShadow dx="0" dy="4" stdDeviation="7" flood-opacity=".45"/></filter></defs><rect x="28" y="28" width="${width - 56}" height="${height - 56}" rx="28" fill="#08121fee" filter="url(#shadow)"/><text x="64" y="128" fill="#ffffff" font-family="Arial, sans-serif" font-size="52" font-weight="700">${first}</text><text x="64" y="195" fill="#f7c85a" font-family="Arial, sans-serif" font-size="30" font-weight="700">BẤT ĐỘNG SẢN • GIANG QUANT</text></svg>`;
}

function videoGeometry(aspect = '9:16', width = 1080) {
  if (aspect === '16:9') {
    const height = Math.round(width * 9 / 16);
    return `scale=${width}:${height}:force_original_aspect_ratio=decrease,pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2,setsar=1`;
  }
  if (aspect === '1:1') return `scale=${width}:${width}:force_original_aspect_ratio=decrease,pad=${width}:${width}:(ow-iw)/2:(oh-ih)/2,setsar=1`;
  const height = Math.round(width * 16 / 9);
  return `scale=${width}:${height}:force_original_aspect_ratio=decrease,crop=${width}:${height},setsar=1`;
}

async function cleanup(ffmpeg, names = []) {
  await Promise.all(names.map((name) => ffmpeg.deleteFile(name).catch(() => {})));
}

export async function exportMp4({ file, start = 0, duration = 60, filter, overlayText, aspect = '9:16', width = 1080, crf = 18, fps = 30, audioBitrate = '192k', enhanceVoice = false, onProgress }) {
  if (!file) throw new Error('Missing source video');
  const ffmpeg = await getFFmpeg(onProgress);
  const stamp = Date.now();
  const inputName = `input-${stamp}.mp4`;
  const outputName = `gq-realestate-${stamp}.mp4`;
  const overlayName = `overlay-${stamp}.svg`;
  await ffmpeg.writeFile(inputName, await fetchFile(file));
  const effects = filter || 'eq=contrast=1.04:brightness=0.02:saturation=1.08:gamma=1.02';
  const geometry = videoGeometry(aspect, width);
  const vf = `${effects},${geometry},fps=${fps},format=yuv420p`;
  try {
    if (overlayText) {
      await ffmpeg.writeFile(overlayName, new TextEncoder().encode(overlaySvg(overlayText, width, Math.max(240, Math.round(width * 0.28)))));
      const audio = enhanceVoice ? '[0:a]highpass=f=80,lowpass=f=12000,loudnorm=I=-16:LRA=11:TP=-1.5[a]' : '[0:a]aresample=async=1:first_pts=0[a]';
      await ffmpeg.exec(['-ss', String(Math.max(0, start)), '-i', inputName, '-loop', '1', '-i', overlayName, '-filter_complex', `[0:v]${vf}[base];[1:v]format=rgba[ov];[base][ov]overlay=0:0:enable='between(t,0,5)'[v];${audio}`, '-map', '[v]', '-map', '[a]', '-t', String(Math.max(1, duration)), '-c:v', 'libx264', '-preset', 'medium', '-crf', String(crf), '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:a', 'aac', '-b:a', audioBitrate, '-movflags', '+faststart', outputName]);
    } else {
      const audioFilter = enhanceVoice ? 'highpass=f=80,lowpass=f=12000,loudnorm=I=-16:LRA=11:TP=-1.5' : 'aresample=async=1:first_pts=0';
      await ffmpeg.exec(['-ss', String(Math.max(0, start)), '-i', inputName, '-t', String(Math.max(1, duration)), '-vf', vf, '-af', audioFilter, '-c:v', 'libx264', '-preset', 'medium', '-crf', String(crf), '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:a', 'aac', '-b:a', audioBitrate, '-movflags', '+faststart', outputName]);
    }
    const data = await ffmpeg.readFile(outputName);
    return new Blob([data.buffer], { type: 'video/mp4' });
  } finally {
    await cleanup(ffmpeg, [inputName, outputName, overlayName]);
  }
}

export async function exportTimeline({ file, clips = [], filter, aspect = '9:16', width = 1080, crf = 18, fps = 30, audioBitrate = '192k', overlayText, enhanceVoice = false, onProgress }) {
  if (!file) throw new Error('Missing source video');
  const ordered = clips.filter((clip) => clip.trackId === 'video' || clip.trackId === 'broll').sort((a, b) => a.start - b.start);
  if (!ordered.length) return exportMp4({ file, filter, aspect, width, crf, fps, audioBitrate, overlayText, enhanceVoice, duration: 30, onProgress });
  const ffmpeg = await getFFmpeg(onProgress);
  const stamp = Date.now();
  const inputName = `timeline-input-${stamp}.mp4`;
  const outputName = `timeline-output-${stamp}.mp4`;
  const overlayName = `timeline-overlay-${stamp}.svg`;
  await ffmpeg.writeFile(inputName, await fetchFile(file));
  const effects = filter || 'eq=contrast=1.04:brightness=0.02:saturation=1.08:gamma=1.02';
  const geometry = videoGeometry(aspect, width);
  const inputs = ordered.map((clip, index) => `[0:v]trim=start=${Math.max(0, clip.sourceStart || 0)}:end=${Math.max((clip.sourceEnd || 1), (clip.sourceStart || 0) + 0.05)},setpts=PTS-STARTPTS,${effects},${geometry},fps=${fps},format=yuv420p[v${index}]`).join(';');
  const concat = `${ordered.map((_, index) => `[v${index}]`).join('')}concat=n=${ordered.length}:v=1:a=0[vout]`;
  const duration = ordered.reduce((total, clip) => total + Math.max(0.05, clip.end - clip.start), 0);
  try {
    let graph = `${inputs};${concat}`;
    let command = ['-i', inputName];
    let mapVideo = '[vout]';
    if (overlayText) {
      await ffmpeg.writeFile(overlayName, new TextEncoder().encode(overlaySvg(overlayText, width, Math.max(240, Math.round(width * 0.28)))));
      command.push('-loop', '1', '-i', overlayName);
      graph += `;[1:v]format=rgba[ov];[vout][ov]overlay=0:0:enable='between(t,0,5)'[final]`;
      mapVideo = '[final]';
    }
    const audio = enhanceVoice ? '[0:a]highpass=f=80,lowpass=f=12000,loudnorm=I=-16:LRA=11:TP=-1.5[a]' : '[0:a]aresample=async=1:first_pts=0[a]';
    graph += `;${audio}`;
    await ffmpeg.exec([...command, '-filter_complex', graph, '-map', mapVideo, '-map', '[a]', '-t', String(Math.max(1, duration)), '-c:v', 'libx264', '-preset', 'medium', '-crf', String(crf), '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:a', 'aac', '-b:a', audioBitrate, '-movflags', '+faststart', outputName]);
    const data = await ffmpeg.readFile(outputName);
    return new Blob([data.buffer], { type: 'video/mp4' });
  } finally {
    await cleanup(ffmpeg, [inputName, outputName, overlayName]);
  }
}
