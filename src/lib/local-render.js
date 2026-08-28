import { FFmpeg } from '@ffmpeg/ffmpeg';
import { fetchFile, toBlobURL } from '@ffmpeg/util';

const CORE_BASE = 'https://unpkg.com/@ffmpeg/core@0.12.6/dist/umd';
let ffmpegInstance = null;
let ffmpegLoading = null;
let progressListenerBound = false;
let activeProgress = () => {};

async function getFFmpeg() {
  if (ffmpegInstance) return ffmpegInstance;
  if (ffmpegLoading) return ffmpegLoading;

  ffmpegLoading = (async () => {
    const ffmpeg = new FFmpeg();
    if (!progressListenerBound) {
      ffmpeg.on('progress', ({ progress }) => {
        activeProgress(Math.max(0, Math.min(100, Math.round((progress || 0) * 100))));
      });
      progressListenerBound = true;
    }

    await ffmpeg.load({
      coreURL: await toBlobURL(`${CORE_BASE}/ffmpeg-core.js`, 'text/javascript'),
      wasmURL: await toBlobURL(`${CORE_BASE}/ffmpeg-core.wasm`, 'application/wasm'),
    });
    ffmpegInstance = ffmpeg;
    return ffmpeg;
  })();

  try {
    return await ffmpegLoading;
  } finally {
    ffmpegLoading = null;
  }
}

const safeName = (name, fallback = 'source') => String(name || fallback)
  .replace(/[^a-zA-Z0-9._-]/g, '-')
  .slice(-96);

const sceneDuration = (scene) => Math.max(
  0.25,
  Number(scene?.end ?? scene?.sourceEnd ?? 0) - Number(scene?.start ?? scene?.sourceStart ?? 0),
);

function findFileIndex(scene, sceneIndex, files = [], assets = []) {
  if (!files.length) return -1;

  if (scene?.fileIndex != null) {
    const index = Number(scene.fileIndex);
    if (Number.isInteger(index) && index >= 0 && index < files.length) return index;
  }

  if (scene?.assetId) {
    const assetIndex = assets.findIndex((asset) => asset?.id === scene.assetId);
    if (assetIndex >= 0 && assetIndex < files.length) return assetIndex;
  }

  // When the AI plan has no asset identity (guest/local analysis), prefer the
  // first source file instead of silently switching to unrelated footage.
  if (!scene?.assetId && sceneIndex === 0) return 0;
  return 0;
}

async function removeIfExists(ffmpeg, path) {
  try { await ffmpeg.deleteFile(path); } catch (_) { /* ignore */ }
}

export async function renderTimelineToMp4({
  files = [],
  scenes = [],
  assets = [],
  width = 1080,
  height = 1920,
  crf = 22,
  onProgress = () => {},
  onStage = () => {},
}) {
  if (!files.length) throw new Error('Chưa có footage để xuất video.');

  const usableScenes = scenes.length
    ? scenes.slice(0, 30)
    : [{ start: 0, end: Math.min(45, 60), fileIndex: 0 }];

  const ffmpeg = await getFFmpeg();
  activeProgress = (value) => onProgress(value);
  onStage('Đang khởi động bộ máy xuất MP4 trên trình duyệt…');
  await ffmpeg.createDir('sources').catch(() => {});
  await ffmpeg.createDir('parts').catch(() => {});

  const inputNames = new Map();
  const createdPartNames = [];

  const getInputName = async (index) => {
    if (inputNames.has(index)) return inputNames.get(index);
    const source = files[index];
    if (!source) throw new Error(`Không tìm thấy footage #${index + 1}.`);
    const name = `sources/${index}-${safeName(source.name, `clip-${index + 1}.mp4`)}`;
    await ffmpeg.writeFile(name, await fetchFile(source));
    inputNames.set(index, name);
    return name;
  };

  try {
    for (let i = 0; i < usableScenes.length; i += 1) {
      const scene = usableScenes[i];
      const fileIndex = findFileIndex(scene, i, files, assets);
      const input = await getInputName(fileIndex);
      const start = Math.max(0, Number(scene?.start ?? scene?.sourceStart ?? 0));
      const duration = sceneDuration(scene);
      const part = `parts/scene-${i}.mp4`;
      createdPartNames.push(part);

      onStage(`Đang dựng cảnh ${i + 1}/${usableScenes.length}…`);
      onProgress(Math.round((i / Math.max(1, usableScenes.length)) * 75));

      await ffmpeg.exec([
        '-y',
        '-ss', String(start),
        '-i', input,
        '-t', String(duration),
        '-vf', `scale=${width}:${height}:force_original_aspect_ratio=increase,crop=${width}:${height},fps=30,format=yuv420p`,
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', String(crf),
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '48000',
        '-movflags', '+faststart',
        part,
      ]);
    }

    const concatFile = 'concat.txt';
    const concatText = `${createdPartNames.map((name) => `file '${name}'`).join('\n')}\n`;
    await ffmpeg.writeFile(concatFile, new TextEncoder().encode(concatText));

    onStage('Đang ghép timeline và tối ưu MP4…');
    onProgress(82);
    await ffmpeg.exec([
      '-y',
      '-f', 'concat',
      '-safe', '0',
      '-i', concatFile,
      '-c', 'copy',
      '-movflags', '+faststart',
      'final.mp4',
    ]);

    onProgress(96);
    const data = await ffmpeg.readFile('final.mp4');
    onStage('Hoàn tất xuất MP4.');
    onProgress(100);

    const bytes = data instanceof Uint8Array ? data : new Uint8Array(data);
    return new Blob([bytes], { type: 'video/mp4' });
  } finally {
    activeProgress = () => {};
    await removeIfExists(ffmpeg, 'concat.txt');
    await removeIfExists(ffmpeg, 'final.mp4');
    for (const path of createdPartNames) await removeIfExists(ffmpeg, path);
    for (const path of inputNames.values()) await removeIfExists(ffmpeg, path);
  }
}
