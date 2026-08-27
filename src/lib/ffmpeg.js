import { FFmpeg } from '@ffmpeg/ffmpeg';
import { fetchFile, toBlobURL } from '@ffmpeg/util';

let ffmpegInstance;
let loaded = false;

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
  return String(value).replace(/[<>&"']/g, c => ({
    '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;',
  }[c]));
}

function overlaySvg(text, width = 1080, height = 300) {
  const first = escapeXml(text).slice(0, 80);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
  <defs><filter id="shadow"><feDropShadow dx="0" dy="4" stdDeviation="7" flood-opacity=".45"/></filter></defs>
  <rect x="28" y="28" width="${width - 56}" height="${height - 56}" rx="28" fill="#08121fee" filter="url(#shadow)"/>
  <text x="64" y="128" fill="#ffffff" font-family="Arial, sans-serif" font-size="52" font-weight="700">${first}</text>
  <text x="64" y="195" fill="#f7c85a" font-family="Arial, sans-serif" font-size="30" font-weight="700">BẤT ĐỘNG SẢN • GIANG QUANT</text>
  </svg>`;
}

function videoGeometry(aspect = '9:16', width = 1080) {
  if (aspect === '16:9') return `scale=${width}:-2:force_original_aspect_ratio=decrease,pad=${width}:608:(ow-iw)/2:(oh-ih)/2,setsar=1`;
  if (aspect === '1:1') return `scale=${width}:${width}:force_original_aspect_ratio=decrease,pad=${width}:${width}:(ow-iw)/2:(oh-ih)/2,setsar=1`;
  return `scale=${width}:1920:force_original_aspect_ratio=decrease,crop=${width}:1920,setsar=1`;
}

export async function exportMp4({
  file,
  start = 0,
  duration = 60,
  filter,
  overlayText,
  aspect = '9:16',
  width = 1080,
  crf = 18,
  fps = 30,
  audioBitrate = '192k',
  enhanceVoice = false,
  onProgress,
}) {
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
      await ffmpeg.writeFile(overlayName, new TextEncoder().encode(overlaySvg(overlayText, width, 320)));
      const audio = enhanceVoice
        ? '[0:a]highpass=f=80,lowpass=f=12000,loudnorm=I=-16:LRA=11:TP=-1.5[a]'
        : '[0:a]aresample=async=1:first_pts=0[a]';
      await ffmpeg.exec([
        '-ss', String(Math.max(0, start)), '-i', inputName,
        '-loop', '1', '-i', overlayName,
        '-filter_complex', `[0:v]${vf}[base];[1:v]format=rgba[ov];[base][ov]overlay=0:0:enable='between(t,0,5)'[v];${audio}`,
        '-map', '[v]', '-map', '[a]', '-t', String(Math.max(1, duration)),
        '-c:v', 'libx264', '-preset', 'medium', '-crf', String(crf),
        '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
        '-c:a', 'aac', '-b:a', audioBitrate, '-movflags', '+faststart', outputName,
      ]);
    } else {
      const audioFilter = enhanceVoice ? 'highpass=f=80,lowpass=f=12000,loudnorm=I=-16:LRA=11:TP=-1.5' : 'aresample=async=1:first_pts=0';
      await ffmpeg.exec([
        '-ss', String(Math.max(0, start)), '-i', inputName, '-t', String(Math.max(1, duration)),
        '-vf', vf, '-af', audioFilter,
        '-c:v', 'libx264', '-preset', 'medium', '-crf', String(crf),
        '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
        '-c:a', 'aac', '-b:a', audioBitrate, '-movflags', '+faststart', outputName,
      ]);
    }

    const data = await ffmpeg.readFile(outputName);
    return new Blob([data.buffer], { type: 'video/mp4' });
  } finally {
    await ffmpeg.deleteFile(inputName).catch(() => {});
    await ffmpeg.deleteFile(outputName).catch(() => {});
    await ffmpeg.deleteFile(overlayName).catch(() => {});
  }
}
