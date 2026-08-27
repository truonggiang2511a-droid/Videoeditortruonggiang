import { FFmpeg } from '@ffmpeg/ffmpeg';
import { fetchFile, toBlobURL } from '@ffmpeg/util';

let ffmpegInstance;
let loaded = false;

export async function getFFmpeg(onProgress) {
  if (!ffmpegInstance) {
    ffmpegInstance = new FFmpeg();
    ffmpegInstance.on('progress', ({ progress }) => onProgress?.(Math.round(progress * 100)));
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

export async function exportMp4({ file, start = 0, duration, filter, overlayText, onProgress }) {
  const ffmpeg = await getFFmpeg(onProgress);
  const inputName = `input-${Date.now()}.mp4`;
  const outputName = `gq-realestate-${Date.now()}.mp4`;
  await ffmpeg.writeFile(inputName, await fetchFile(file));

  let vf = filter || 'eq=contrast=1.04:brightness=0.02:saturation=1.08:gamma=1.02';
  if (overlayText) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="260"><rect x="36" y="36" width="1008" height="188" rx="28" fill="rgba(7,17,31,0.86)"/><text x="72" y="116" fill="#fff" font-family="Arial, sans-serif" font-size="54" font-weight="700">${String(overlayText).replace(/[<>&"']/g, (c) => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&apos;'}[c]))}</text><text x="72" y="175" fill="#ffc857" font-family="Arial, sans-serif" font-size="30">BẤT ĐỘNG SẢN • GIANG QUANT</text></svg>`;
    await ffmpeg.writeFile('overlay.svg', new TextEncoder().encode(svg));
    vf = `${vf},format=yuv420p`;
    await ffmpeg.exec([
      '-ss', String(start), '-i', inputName,
      '-loop', '1', '-i', 'overlay.svg',
      '-filter_complex', `[0:v]${vf}[v0];[1:v]format=rgba[ov];[v0][ov]overlay=0:0:enable='between(t,0,5)'[v]`,
      '-map', '[v]', '-map', '0:a?', '-t', String(duration || 60),
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
      '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', outputName,
    ]);
  } else {
    await ffmpeg.exec([
      '-ss', String(start), '-i', inputName, '-t', String(duration || 60),
      '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
      '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', outputName,
    ]);
  }

  const data = await ffmpeg.readFile(outputName);
  await ffmpeg.deleteFile(inputName).catch(() => {});
  await ffmpeg.deleteFile(outputName).catch(() => {});
  await ffmpeg.deleteFile('overlay.svg').catch(() => {});
  return new Blob([data.buffer], { type: 'video/mp4' });
}
