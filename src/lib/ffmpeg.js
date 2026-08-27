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

async function createOverlayPng(text) {
  const canvas = document.createElement('canvas');
  canvas.width = 1080; canvas.height = 260;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = 'rgba(7,17,31,.88)';
  ctx.beginPath(); ctx.roundRect(36, 36, 1008, 188, 28); ctx.fill();
  ctx.font = '700 54px Arial, sans-serif'; ctx.fillStyle = '#ffffff';
  const safe = String(text).slice(0, 38); ctx.fillText(safe, 72, 116);
  ctx.font = '700 30px Arial, sans-serif'; ctx.fillStyle = '#ffc857'; ctx.fillText('BẤT ĐỘNG SẢN • GIANG QUANT', 72, 176);
  const blob = await new Promise((resolve, reject) => canvas.toBlob(b => b ? resolve(b) : reject(new Error('Không tạo được overlay')), 'image/png'));
  return new Uint8Array(await blob.arrayBuffer());
}

export async function exportMp4({ file, start = 0, duration, filter, overlayText, onProgress }) {
  const ffmpeg = await getFFmpeg(onProgress);
  const id = Date.now();
  const inputName = `input-${id}.mp4`;
  const outputName = `gq-realestate-${id}.mp4`;
  await ffmpeg.writeFile(inputName, await fetchFile(file));
  const vf = filter || 'eq=contrast=1.04:brightness=0.02:saturation=1.08:gamma=1.02';

  if (overlayText) {
    await ffmpeg.writeFile('overlay.png', await createOverlayPng(overlayText));
    await ffmpeg.exec([
      '-ss', String(start), '-i', inputName,
      '-loop', '1', '-i', 'overlay.png',
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
  await Promise.all([
    ffmpeg.deleteFile(inputName).catch(() => {}),
    ffmpeg.deleteFile(outputName).catch(() => {}),
    ffmpeg.deleteFile('overlay.png').catch(() => {}),
  ]);
  return new Blob([data.buffer], { type: 'video/mp4' });
}
