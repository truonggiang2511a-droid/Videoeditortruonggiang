import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AudioLines, Captions, Check, Clapperboard, Download, Film, Layers3,
  Mic2, Music2, Plus, Scissors, Settings2, Sparkles, Split, SunMedium,
  Trash2, Type, Upload, Video, WandSparkles, X, Zap,
} from 'lucide-react';
import { exportTimeline, EXPORT_PROFILES } from './lib/ffmpeg';
import { parseVietnameseEditCommand, requestAiPlan } from './lib/ai';
import { sampleVideoFrames, buildSmartCuts, requestVisionPlan } from './lib/scene-intelligence';
import { TRACKS, makeClip, splitClip, moveClip, snapToBeat, createKeyframe, deriveTransform } from './lib/editor-engine';
import { LUT_PRESETS, buildColorFilter, buildPreviewFilter, analyzeFrameForAutoColor } from './lib/color-lab';
import { MUSIC_LIBRARY, autoDuckVolume, buildBeatCuts, createVoiceScript, requestVoice, decodeAudioPeaks } from './lib/audio-engine';
import { createSpeechRecognizer, captionLinesFromTranscript, CAPTION_STYLES } from './lib/captions';
import { saveProject, exportProjectJson, importProjectJson, DEFAULT_EXPORT } from './lib/project';

const DEFAULT_PROMPT = 'Làm video 45 giây bán căn nhà này, hook thật mạnh 3 giây đầu, phong cách sang, nhấn giá + pháp lý + vị trí, text chuyên nghiệp, tự chọn cảnh đẹp, tự chỉnh màu, nhạc nền nhẹ, CTA gọi/Zalo xem nhà.';
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
const fmt = (v) => `${String(Math.floor((v || 0) / 60)).padStart(2, '0')}:${String(Math.floor((v || 0) % 60)).padStart(2, '0')}`;
const resolutionLabel = (value, aspect) => {
  const width = Number(value);
  const height = aspect === '9:16' ? Math.round(width * 16 / 9) : aspect === '1:1' ? width : Math.round(width * 9 / 16);
  return `${width}×${height}`;
};

function blankTracks(duration = 45) {
  return {
    video: [makeClip({ trackId: 'video', label: 'Video Gốc', start: 0, end: duration, sourceStart: 0, sourceEnd: duration })],
    broll: [], text: [], caption: [], audio: [], voice: [],
  };
}

function clipAtTime(clips, time) {
  return [...clips].sort((a, b) => a.start - b.start).find((clip) => time >= clip.start && time < clip.end) || null;
}

export default function App() {
  const videoRef = useRef(null);
  const inputRef = useRef(null);
  const audioRef = useRef(null);
  const importRef = useRef(null);
  const speechRef = useRef(null);

  const [file, setFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [sourceDuration, setSourceDuration] = useState(0);
  const [duration, setDuration] = useState(45);
  const [current, setCurrent] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [tool, setTool] = useState('ai');
  const [aspect, setAspect] = useState('9:16');
  const [preset, setPreset] = useState('luxury');
  const [autoColor, setAutoColor] = useState(true);
  const [lut, setLut] = useState('luxury');
  const [exposure, setExposure] = useState(0);
  const [contrast, setContrast] = useState(1);
  const [saturation, setSaturation] = useState(1);
  const [temperature, setTemperature] = useState(0);
  const [tint, setTint] = useState(0);
  const [sharpen, setSharpen] = useState(0.2);
  const [title, setTitle] = useState('CĂN NHÀ ĐÁNG XEM NHẤT KHU VỰC');
  const [price, setPrice] = useState('3,2 TỶ');
  const [captionBrand, setCaptionBrand] = useState('Sổ Hồng Riêng • Vị Trí Đẹp');
  const [tracks, setTracks] = useState(blankTracks());
  const [selectedId, setSelectedId] = useState(null);
  const [sceneReport, setSceneReport] = useState(null);
  const [smartCuts, setSmartCuts] = useState([]);
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [music, setMusic] = useState(MUSIC_LIBRARY[0]);
  const [musicFile, setMusicFile] = useState(null);
  const [audioInfo, setAudioInfo] = useState(null);
  const [voiceScript, setVoiceScript] = useState('');
  const [voiceBlobUrl, setVoiceBlobUrl] = useState('');
  const [beatSync, setBeatSync] = useState(true);
  const [fps, setFps] = useState(30);
  const [resolution, setResolution] = useState(1080);
  const [crf, setCrf] = useState(18);
  const [audioBitrate, setAudioBitrate] = useState('192k');
  const [profileName, setProfileName] = useState('TikTok / Reels');
  const [captionText, setCaptionText] = useState('');
  const [captionStyle, setCaptionStyle] = useState('premium');
  const [speechListening, setSpeechListening] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [progress, setProgress] = useState(0);
  const [toast, setToast] = useState('');

  const profile = EXPORT_PROFILES[profileName] || EXPORT_PROFILES['TikTok / Reels'];
  const previewFilter = useMemo(() => autoColor ? buildPreviewFilter({ exposure, contrast, saturation, temperature, tint }) : 'none', [autoColor, exposure, contrast, saturation, temperature, tint]);
  const filter = useMemo(() => autoColor ? buildColorFilter({ exposure, contrast, saturation, temperature, tint, sharpen, lut }) : 'null', [autoColor, exposure, contrast, saturation, temperature, tint, sharpen, lut]);
  const videoClips = useMemo(() => Object.values(tracks).flat().filter((clip) => clip.trackId === 'video' || clip.trackId === 'broll').sort((a, b) => a.start - b.start), [tracks]);
  const selectedClip = videoClips.find((clip) => clip.id === selectedId) || null;
  const activeClip = clipAtTime(videoClips, current) || videoClips[0] || null;

  useEffect(() => () => {
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    if (voiceBlobUrl) URL.revokeObjectURL(voiceBlobUrl);
  }, [videoUrl, voiceBlobUrl]);

  useEffect(() => {
    if (!playing || !videoRef.current) return undefined;
    const timer = window.setInterval(() => {
      const video = videoRef.current;
      const clip = clipAtTime(videoClips, current) || videoClips[0];
      if (!video || !clip) return;
      if (video.currentTime >= (clip.sourceEnd || clip.end) - 0.08) {
        const next = videoClips.find((item) => item.start >= clip.end - 0.001);
        if (next) {
          video.currentTime = next.sourceStart || 0;
          setCurrent(next.start);
        } else {
          video.pause();
          setPlaying(false);
          setCurrent(duration);
        }
        return;
      }
      const srcStart = clip.sourceStart || 0;
      const srcDuration = Math.max(0.01, (clip.sourceEnd || srcStart + 1) - srcStart);
      const timelineDuration = Math.max(0.01, clip.end - clip.start);
      const timelineTime = clip.start + ((video.currentTime - srcStart) / srcDuration) * timelineDuration;
      setCurrent(clamp(timelineTime, clip.start, clip.end));
    }, 80);
    return () => window.clearInterval(timer);
  }, [playing, videoClips, current, duration]);

  const seekTimeline = (time) => {
    const nextTime = clamp(Number(time) || 0, 0, duration || 1);
    const clip = clipAtTime(videoClips, nextTime) || videoClips[videoClips.length - 1];
    setCurrent(nextTime);
    if (!videoRef.current || !clip) return;
    const ratio = clamp((nextTime - clip.start) / Math.max(0.01, clip.end - clip.start), 0, 1);
    videoRef.current.currentTime = (clip.sourceStart || 0) + ratio * Math.max(0.01, (clip.sourceEnd || clip.sourceStart + 1) - (clip.sourceStart || 0));
  };

  const togglePlay = async () => {
    if (!file || !videoRef.current || !videoClips.length) return;
    const clip = clipAtTime(videoClips, current) || videoClips[0];
    if (videoRef.current.paused) {
      const safeCurrent = current >= duration ? 0 : current;
      const selected = clipAtTime(videoClips, safeCurrent) || videoClips[0];
      const ratio = clamp((safeCurrent - selected.start) / Math.max(0.01, selected.end - selected.start), 0, 1);
      videoRef.current.currentTime = (selected.sourceStart || 0) + ratio * Math.max(0.01, (selected.sourceEnd || selected.sourceStart + 1) - (selected.sourceStart || 0));
      setCurrent(safeCurrent);
      await videoRef.current.play();
      setPlaying(true);
    } else {
      videoRef.current.pause();
      setPlaying(false);
    }
  };

  const setVideo = (nextFile) => {
    if (!nextFile?.type?.startsWith('video/')) return setToast('Chọn video MP4, MOV hoặc WebM.');
    setFile(nextFile);
    setVideoUrl((old) => { if (old) URL.revokeObjectURL(old); return URL.createObjectURL(nextFile); });
    setSourceDuration(0);
    setDuration(45);
    setCurrent(0);
    setPlaying(false);
    setTracks(blankTracks(45));
    setSceneReport(null);
    setSmartCuts([]);
    setToast('Đã nạp footage. Bấm “AI Tự Dựng” để dựng video hoàn chỉnh.');
  };

  const runAutoColor = () => {
    if (!file || !videoRef.current) return setToast('Upload video trước.');
    const canvas = document.createElement('canvas');
    canvas.width = 240; canvas.height = 135;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return setToast('Trình duyệt không hỗ trợ Color Analysis.');
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const result = analyzeFrameForAutoColor(ctx, canvas.width, canvas.height);
    setAutoColor(true);
    setExposure(result.exposure);
    setTemperature(result.temperature);
    setTint(result.tint);
    setContrast(1.05);
    setSaturation(1.08);
    setToast('Auto Color đã phân tích frame và cập nhật màu Preview.');
  };

  const analyze = async () => {
    if (!file) return setToast('Hãy upload video trước.');
    if (analysisBusy) return;
    setAnalysisBusy(true);
    try {
      setToast('AI đang xem footage, chấm điểm cảnh và dựng storyboard…');
      const localMeta = await sampleVideoFrames(file, { sampleCount: 36, width: 360 });
      const command = parseVietnameseEditCommand(prompt, localMeta.duration);
      const requested = clamp(command.duration || 45, 5, Math.max(5, localMeta.duration || 45));
      const cuts = buildSmartCuts(localMeta.frames, requested, localMeta.duration);
      if (!cuts.length) throw new Error('Không tạo được Smart Cut');
      const vision = await requestVisionPlan({ endpoint: import.meta.env.VITE_VISION_ENDPOINT, prompt, videoMeta: localMeta, frames: localMeta.frames }).catch(() => null);
      const ai = await requestAiPlan({ prompt, videoMeta: { ...localMeta, requestedDuration: requested }, endpoint: import.meta.env.VITE_AI_ENDPOINT }).catch(() => command);
      const nextVideo = cuts.map((cut, index) => makeClip({
        ...cut,
        trackId: 'video',
        id: cut.id,
        label: vision?.clips?.[index]?.label || cut.label,
        sourceStart: cut.sourceStart,
        sourceEnd: Math.min(localMeta.duration, cut.sourceEnd),
        start: cut.start,
        end: cut.end,
        sceneType: cut.type,
        score: cut.quality,
      }));
      const target = cuts[cuts.length - 1].end;
      const nextTitle = ai.hook || command.hook || title;
      const nextCta = ai.cta || command.cta || 'GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ';
      const text = [
        makeClip({ trackId: 'text', label: 'HOOK', start: 0, end: Math.min(3.5, target), text: nextTitle, secondary: price, preset: 'premium', animation: 'rise' }),
        makeClip({ trackId: 'text', label: 'USP', start: Math.min(3.5, target * 0.25), end: Math.min(target, target * 0.62), text: captionBrand, preset: 'minimal' }),
        makeClip({ trackId: 'text', label: 'CTA', start: Math.max(0, target - 4.5), end: target, text: nextCta, preset: 'cta', animation: 'pop' }),
      ];
      setTracks((old) => ({ ...old, video: nextVideo, text }));
      setSmartCuts(cuts);
      setSceneReport(localMeta);
      setDuration(target);
      setCurrent(0);
      setPreset(ai.style || command.style || preset);
      setAspect(ai.aspect || command.aspect || aspect);
      setTitle(nextTitle);
      if (requested < Number(command.duration || requested)) setToast(`Footage chỉ đủ ${fmt(target)} nên AI đã giới hạn video ở thời lượng khả dụng.`);
      else setToast(`AI đã tự dựng ${fmt(target)}: chọn cảnh + hook + text + CTA + màu.`);
    } catch (error) {
      console.error(error);
      setToast('AI chưa dựng được video từ footage này. Thử video MP4/MOV rõ nét hơn.');
    } finally {
      setAnalysisBusy(false);
    }
  };

  const splitSelected = () => {
    if (!selectedClip) return setToast('Chọn clip video trước.');
    if (current <= selectedClip.start || current >= selectedClip.end) return setToast('Đưa playhead vào trong clip rồi Split.');
    setTracks((old) => Object.fromEntries(Object.entries(old).map(([key, list]) => [key, list.flatMap((clip) => clip.id === selectedClip.id ? splitClip(clip, current) : [clip])] )));
    setToast('Đã Split clip.');
  };

  const deleteSelected = () => {
    if (!selectedId) return setToast('Chưa chọn clip.');
    setTracks((old) => Object.fromEntries(Object.entries(old).map(([key, list]) => [key, list.filter((clip) => clip.id !== selectedId)])));
    setSelectedId(null);
    setToast('Đã xóa clip.');
  };

  const addTextClip = () => {
    const clip = makeClip({ trackId: 'text', label: 'Text mới', start: current, end: Math.min(duration, current + 4), text: 'NHÀ ĐẸP • GIÁ TỐT • SỔ HỒNG RIÊNG', preset: 'premium' });
    setTracks((old) => ({ ...old, text: [...old.text, clip] }));
    setSelectedId(clip.id);
  };

  const addKeyframe = () => {
    if (!selectedClip) return setToast('Chọn clip video trước.');
    const relativeTime = clamp(current - selectedClip.start, 0, selectedClip.end - selectedClip.start);
    const updated = { ...selectedClip, transform: { ...selectedClip.transform, keyframes: [...(selectedClip.transform?.keyframes || []), { ...createKeyframe(relativeTime, 1.18), property: 'scale' }] } };
    setTracks((old) => Object.fromEntries(Object.entries(old).map(([key, list]) => [key, list.map((clip) => clip.id === selectedId ? updated : clip)])));
    setToast('Đã thêm keyframe Zoom.');
  };

  const onTrackDrop = (e, trackId) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('application/x-gq-clip');
    if (!id) return;
    const clip = Object.values(tracks).flat().find((item) => item.id === id);
    if (!clip) return;
    const rect = e.currentTarget.getBoundingClientRect();
    let nextStart = clamp(((e.clientX - rect.left) / rect.width) * duration, 0, Math.max(0, duration - (clip.end - clip.start)));
    if (beatSync && audioInfo?.bpm) nextStart = snapToBeat(nextStart, buildBeatCuts({ clipCount: 48, bpm: audioInfo.bpm, duration }), 0.14);
    const delta = nextStart - clip.start;
    setTracks((old) => Object.fromEntries(Object.entries(old).map(([key, list]) => [key, list.map((item) => item.id === id ? { ...moveClip([item], id, delta)[0], trackId } : item)])));
  };

  const onMusic = async (nextFile) => {
    if (!nextFile) return;
    setMusicFile(nextFile);
    try { setAudioInfo(await decodeAudioPeaks(nextFile)); } catch { setAudioInfo(null); }
    setToast(`Đã nạp nhạc: ${nextFile.name}`);
  };

  const buildVoice = async () => {
    const script = createVoiceScript({ title, price, cta: 'Gọi / Zalo ngay để hẹn xem nhà', seconds: Math.min(45, duration) });
    setVoiceScript(script.text);
    const blob = await requestVoice({ endpoint: import.meta.env.VITE_VOICE_ENDPOINT, text: script.text }).catch(() => null);
    if (blob) {
      const url = URL.createObjectURL(blob);
      setVoiceBlobUrl((old) => { if (old) URL.revokeObjectURL(old); return url; });
      setTracks((old) => ({ ...old, voice: [makeClip({ trackId: 'voice', label: 'AI Voice', start: 0, end: duration, volume: 1 })] }));
      setToast('Đã tạo Voice AI từ endpoint.');
    } else {
      setTracks((old) => ({ ...old, voice: [makeClip({ trackId: 'voice', label: 'TTS Script', start: 0, end: duration, volume: 1, text: script.text })] }));
      setToast('Đã tạo script TTS. Có thể Nghe Thử bằng giọng đọc của trình duyệt.');
    }
  };

  const previewTts = () => {
    if (!voiceScript) buildVoice();
    const Speech = window.speechSynthesis;
    if (!Speech) return setToast('Trình duyệt không hỗ trợ TTS.');
    Speech.cancel();
    const utterance = new SpeechSynthesisUtterance(voiceScript || createVoiceScript({ title, price, cta: 'Gọi hoặc Zalo để hẹn xem nhà hôm nay' }).text);
    utterance.lang = 'vi-VN';
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;
    Speech.speak(utterance);
    setToast('Đang nghe thử TTS tiếng Việt.');
  };

  const toggleCaptionSpeech = () => {
    if (speechListening) {
      speechRef.current?.stop();
      setSpeechListening(false);
      return;
    }
    try {
      const recognizer = createSpeechRecognizer({
        language: 'vi-VN',
        onStart: () => setSpeechListening(true),
        onEnd: () => setSpeechListening(false),
        onError: (message) => { setSpeechListening(false); setToast(`STT: ${message}`); },
        onFinal: (text) => {
          setCaptionText((old) => `${old} ${text}`.trim());
          setTracks((old) => ({ ...old, caption: [makeClip({ trackId: 'caption', label: 'Caption', start: current, end: Math.min(duration, current + 4), text })] }));
        },
      });
      speechRef.current = recognizer;
      recognizer.start();
    } catch (error) {
      setToast(error.message || 'Không mở được STT.');
    }
  };

  const makeCaptionsFromText = () => {
    const sourceText = captionText || voiceScript || `${title}. ${captionBrand}. ${price}. Gọi hoặc Zalo để hẹn xem nhà.`;
    const lines = captionLinesFromTranscript(sourceText, 34);
    const segmentDuration = Math.max(1.2, duration / Math.max(1, lines.length));
    const captionClips = lines.map((line, index) => makeClip({ trackId: 'caption', label: `SUB ${index + 1}`, start: index * segmentDuration, end: Math.min(duration, (index + 1) * segmentDuration), text: line, style: CAPTION_STYLES[captionStyle] }));
    setCaptionText(sourceText);
    setTracks((old) => ({ ...old, caption: captionClips }));
    setToast(`Đã tạo ${captionClips.length} caption theo timeline.`);
  };

  const makeProject = () => ({ version: 2, name: `GQ-BDS-${Date.now()}`, duration, aspect, prompt, fileName: file?.name || '', sourceDuration, title, price, captionBrand, lut, autoColor, tracks, export: { ...DEFAULT_EXPORT, profileName, resolution, crf, fps, audioBitrate } });
  const saveCurrentProject = () => { saveProject(makeProject()); setToast('Đã lưu project trên trình duyệt.'); };
  const downloadProject = () => exportProjectJson(makeProject());
  const loadProject = async (nextFile) => {
    try {
      const project = await importProjectJson(nextFile);
      setDuration(project.duration || 45); setAspect(project.aspect || '9:16'); setPrompt(project.prompt || DEFAULT_PROMPT); setTitle(project.title || title); setPrice(project.price || price); setCaptionBrand(project.captionBrand || captionBrand); setTracks(project.tracks || blankTracks(project.duration || 45)); setLut(project.lut || 'luxury'); setAutoColor(project.autoColor !== false); setToast('Đã import project JSON. Upload lại video nguồn để preview/render.');
    } catch { setToast('Project JSON không hợp lệ.'); }
  };

  const doExport = async () => {
    if (!file) return setToast('Hãy upload video.');
    if (!videoClips.length) return setToast('Timeline chưa có clip video.');
    try {
      setRendering(true); setProgress(0);
      const blob = await exportTimeline({ file, clips: videoClips, filter, aspect, width: Number(resolution), crf: Number(crf), fps: Number(fps), audioBitrate, overlayText: `${title} • ${price}`, enhanceVoice: tracks.voice.length > 0, onProgress: setProgress });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url; link.download = `GQ-BDS-${Date.now()}-${String(resolution)}p.mp4`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
      setToast(`Xuất ${resolutionLabel(resolution, aspect)} MP4 thành công.`);
    } catch (error) {
      console.error(error);
      setToast('Render lỗi. Giảm độ phân giải hoặc CRF và thử lại.');
    } finally { setRendering(false); }
  };

  const resetColor = () => { setExposure(0); setContrast(1); setSaturation(1); setTemperature(0); setTint(0); setSharpen(0.2); setLut('luxury'); setAutoColor(true); setToast('Đã reset màu.'); };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><div className="brand-mark"><Clapperboard size={18}/></div><div><b>GQ VIDEO EDITOR</b><span>AUTO EDIT STUDIO • DÀNH CHO MÔI GIỚI BĐS</span></div></div>
        <div className="top-actions"><button className="ghost" onClick={saveCurrentProject}><Layers3 size={15}/> Lưu</button><button className="ghost" onClick={downloadProject}><Download size={15}/> Project</button><button className="export-btn" onClick={doExport}><Video size={16}/> {rendering ? `Đang Xuất ${progress}%` : 'Xuất Video'}</button></div>
      </header>
      <main className="workspace">
        <aside className="sidebar"><div className="sidebar-title">AUTO EDIT</div>{[
          ['ai',WandSparkles,'AI Tự Dựng'],['media',Film,'Media'],['text',Type,'Text & Motion'],['captions',Captions,'Phụ Đề + STT'],['audio',AudioLines,'Âm Thanh + TTS'],['color',SunMedium,'Auto Color'],['settings',Settings2,'Xuất Video'],
        ].map(([id,Icon,label]) => <button key={id} className={`side-item ${tool === id ? 'active' : ''}`} onClick={() => setTool(id)}><Icon size={18}/><span>{label}</span></button>)}<div className="sidebar-bottom"><label className="upload-mini"><Upload size={15}/> Upload Video<input ref={inputRef} type="file" accept="video/*" hidden onChange={(e) => setVideo(e.target.files?.[0])}/></label><label className="upload-mini"><Music2 size={15}/> Thêm Nhạc<input ref={audioRef} type="file" accept="audio/*" hidden onChange={(e) => onMusic(e.target.files?.[0])}/></label><label className="upload-mini"><Download size={15}/> Import Project<input ref={importRef} type="file" accept="application/json" hidden onChange={(e) => loadProject(e.target.files?.[0])}/></label></div></aside>
        <section className="center">
          <div className="editor-head"><div><h1>AI Real Estate Video Studio</h1><span>{file ? `${file.name} • Nguồn ${fmt(sourceDuration)}` : 'Upload footage để bắt đầu'}</span></div><div className="format-switch"><span>Khung</span>{['9:16','1:1','16:9'].map((v) => <button key={v} onClick={() => setAspect(v)} className={aspect === v ? 'chosen' : ''}>{v}</button>)}</div></div>
          <div className={`preview-stage ratio-${aspect.replace(':','x')}`}>
            {!file && <div className="dropzone" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); setVideo(e.dataTransfer.files?.[0]); }} onClick={() => inputRef.current?.click()}><div className="upload-icon"><WandSparkles size={28}/></div><h2>Upload → AI Tự Dựng Video</h2><p>MP4 • MOV • WebM • Full HD / 4K • tối ưu video bán nhà</p><button className="primary"><Upload size={16}/> Chọn Video</button></div>}
            {file && <><video ref={videoRef} src={videoUrl} className="preview-video" style={{ filter: previewFilter, transform: selectedClip ? `scale(${deriveTransform(selectedClip, current - selectedClip.start).scale || 1})` : 'scale(1)' }} onLoadedMetadata={(e) => { setSourceDuration(e.currentTarget.duration || 0); if (!videoClips.length) setDuration(Math.min(45, e.currentTarget.duration || 45)); }} onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onError={() => setToast('Video này không giải mã được trong trình duyệt. Thử MP4 H.264.') } playsInline /><div className="video-gradient"/><div className="overlay-copy top-copy"><small>{captionBrand}</small><strong>{title}</strong></div><div className="overlay-copy price-copy"><b>{price}</b><span>Gọi / Zalo ngay để hẹn xem nhà</span></div>{activeClip && tracks.caption?.length > 0 && (() => { const cap = tracks.caption.find((item) => current >= item.start && current < item.end); return cap ? <div className="caption-preview">{cap.text}</div> : null; })()}<button className="play-btn" onClick={togglePlay}>{playing ? '❚❚' : '▶'}</button></>}
            <div className="timecode">{fmt(current)} <span>/</span> {fmt(duration)}</div>
          </div>
          <div className="transport"><button onClick={() => seekTimeline(current - 3)}>−3s</button><button className="transport-play" onClick={togglePlay}>{playing ? '❚❚' : '▶'}</button><button onClick={() => seekTimeline(current + 3)}>+3s</button><div className="scrub"><div className="scrub-fill" style={{ width: `${duration ? current / duration * 100 : 0}%` }}/><input aria-label="scrub" type="range" min="0" max={duration || 1} step="0.01" value={current} onChange={(e) => seekTimeline(e.target.value)}/></div><span>{fps}fps • {resolutionLabel(resolution, aspect)}</span></div>
          <div className="timeline-panel"><div className="timeline-head"><b>AI EDIT TIMELINE</b><span>{videoClips.length} cảnh • {fmt(duration)} • kéo-thả để tinh chỉnh</span><div><button onClick={splitSelected}><Scissors size={14}/> Split</button><button onClick={addTextClip}><Plus size={14}/> Text</button><button onClick={deleteSelected}><Trash2 size={14}/></button></div></div><div className="timeline">{TRACKS.map((track) => <div className="track-row" key={track.id}><div className="track-name">{track.name}</div><div className="track" onDragOver={(e) => e.preventDefault()} onDrop={(e) => onTrackDrop(e, track.id)}>{(tracks[track.id] || []).map((clip) => <div draggable key={clip.id} onDragStart={(e) => e.dataTransfer.setData('application/x-gq-clip', clip.id)} onClick={() => { setSelectedId(clip.id); seekTimeline(clip.start); }} className={`segment ${selectedId === clip.id ? 'selected' : ''}`} style={{ left: `${duration ? clip.start / duration * 100 : 0}%`, width: `${duration ? Math.max(2, (clip.end - clip.start) / duration * 100) : 8}%` }}><span>{clip.label}</span><small>{fmt(clip.end - clip.start)}</small></div>)}<div className="playhead" style={{ left: `${duration ? current / duration * 100 : 0}%` }}/></div></div>)}</div></div>
        </section>
        <aside className="inspector">
          {tool === 'ai' && <><div className="inspector-title"><div><b>AI TỰ DỰNG VIDEO</b><span>Đây là chức năng chính của GQ Video Editor</span></div><div className="ai-dot"/></div><textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={7}/><div className="smart-row"><div><b>Thời lượng mục tiêu</b><span>AI sẽ chọn/cắt cảnh để đạt đúng thời lượng</span></div><select value={Math.round(duration)} onChange={(e) => setDuration(clamp(Number(e.target.value), 5, 180))}><option value="15">15s</option><option value="30">30s</option><option value="45">45s</option><option value="60">60s</option><option value="90">90s</option></select></div><button className="ai-button" disabled={analysisBusy} onClick={analyze}><WandSparkles size={18}/> {analysisBusy ? 'AI ĐANG DỰNG…' : 'AI TỰ DỰNG 1 CHẠM'}</button><div className="smart-grid"><button onClick={runAutoColor}><SunMedium size={15}/> Auto Color</button><button onClick={makeCaptionsFromText}><Captions size={15}/> Auto Caption</button></div>{sceneReport && <div className="ai-result"><div className="result-head"><Check size={15}/> Phân tích đã hoàn tất</div><div className="result-row"><span>Frame đã quét</span><b>{sceneReport.frames.length}</b></div><div className="result-row"><span>Cảnh tốt</span><b>{sceneReport.frames.filter((f) => f.type === 'good').length}</b></div><div className="result-row"><span>Cảnh cần bỏ</span><b>{sceneReport.frames.filter((f) => f.type === 'bad').length}</b></div><div className="result-row"><span>Timeline</span><b>{fmt(duration)}</b></div></div>}</>}
          {tool === 'text' && <><div className="inspector-title"><div><b>TEXT & MOTION</b><span>Text bán hàng theo ngữ cảnh</span></div></div><label className="field-label">Headline</label><textarea value={title} onChange={(e) => setTitle(e.target.value)} rows={3}/><label className="field-label">Giá</label><input value={price} onChange={(e) => setPrice(e.target.value)}/><label className="field-label">USP / Pháp lý</label><input value={captionBrand} onChange={(e) => setCaptionBrand(e.target.value)}/><div className="style-card"><b>Premium Real Estate</b><div className="style-preview"><strong>{title}</strong><span>{price} • {captionBrand}</span></div></div><button className="secondary" onClick={addTextClip}><Plus size={16}/> Thêm Text</button><button className="secondary" onClick={addKeyframe}><Split size={16}/> Keyframe Zoom</button></>}
          {tool === 'captions' && <><div className="inspector-title"><div><b>PHỤ ĐỀ + STT</b><span>Tiếng Việt • chia câu • highlight</span></div></div><label className="field-label">Kiểu Caption</label><select value={captionStyle} onChange={(e) => setCaptionStyle(e.target.value)}><option value="premium">Premium</option><option value="bold">Bold</option><option value="minimal">Minimal</option></select><label className="field-label">Nội dung</label><textarea value={captionText} onChange={(e) => setCaptionText(e.target.value)} rows={6} placeholder="Nhập script hoặc nói trực tiếp bằng microphone…"/><div className="smart-grid"><button onClick={toggleCaptionSpeech}><Mic2 size={15}/> {speechListening ? 'Đang Nghe…' : 'Nói → STT'}</button><button onClick={makeCaptionsFromText}><Captions size={15}/> Dựng Caption</button></div><div className="feature-list"><span><Captions/> Caption chạy theo timeline</span><span><Sparkles/> Highlight từ khóa BĐS</span><span><Zap/> Karaoke-ready</span></div></>}
          {tool === 'audio' && <><div className="inspector-title"><div><b>ÂM THANH + TTS</b><span>Nhạc nền • voice • beat</span></div></div><label className="field-label">Nhạc mẫu</label><select value={music.id} onChange={(e) => setMusic(MUSIC_LIBRARY.find((item) => item.id === e.target.value) || MUSIC_LIBRARY[0])}>{MUSIC_LIBRARY.map((item) => <option key={item.id} value={item.id}>{item.name} • {item.bpm} BPM</option>)}</select><div className="smart-row"><div><b>Beat Sync</b><span>Tự bắt nhịp khi kéo clip</span></div><button className={`toggle ${beatSync ? 'on' : ''}`} onClick={() => setBeatSync((v) => !v)}><i/></button></div><div className="feature-list"><span><AudioLines/> Auto Ducking {audioInfo?.bpm ? `• ${audioInfo.bpm} BPM` : ''}</span><span><AudioLines/> Voice Enhance</span><span><Mic2/> AI Voice / TTS</span></div><textarea value={voiceScript} onChange={(e) => setVoiceScript(e.target.value)} rows={5} placeholder="Script đọc bán căn nhà…"/><div className="smart-grid"><button onClick={buildVoice}><Mic2 size={15}/> Tạo TTS / Voice</button><button onClick={previewTts}><PlayIconFallback/> Nghe Thử</button></div>{voiceBlobUrl && <audio controls src={voiceBlobUrl} style={{ width: '100%', marginTop: 12 }}/>} {musicFile && <div className="help">Nhạc: {musicFile.name}. Ducking đề xuất {Math.round(autoDuckVolume({ musicVolume: .18, voicePresent: tracks.voice.length > 0 }) * 100)}% volume.</div>}</>}
          {tool === 'color' && <><div className="inspector-title"><div><b>AUTO COLOR</b><span>Preview đổi ngay theo từng slider</span></div></div><select value={lut} onChange={(e) => setLut(e.target.value)}>{LUT_PRESETS.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>{[['Exposure', exposure, setExposure, -1, 1, .01], ['Contrast', contrast, setContrast, .6, 1.6, .01], ['Saturation', saturation, setSaturation, .5, 1.7, .01], ['Temperature', temperature, setTemperature, -1, 1, .01], ['Tint', tint, setTint, -1, 1, .01], ['Sharpen', sharpen, setSharpen, 0, 1, .01]].map(([label, value, setter, min, max, step]) => <div className="knob-row" key={label}><span>{label}</span><input type="range" min={min} max={max} step={step} value={value} onChange={(e) => setter(Number(e.target.value))}/><b>{Number(value).toFixed(2)}</b></div>)}<div className="smart-grid"><button className="secondary" onClick={runAutoColor}><SunMedium size={16}/> Phân Tích Auto</button><button className="secondary" onClick={resetColor}>Reset</button></div><div className="help">Sharpen áp dụng khi render; Exposure/Contrast/Saturation/Temperature/Tint đều phản ánh trực tiếp trên Preview.</div></>}
          {tool === 'settings' && <><div className="inspector-title"><div><b>EXPORT MASTER</b><span>Tùy chỉnh độ phân giải và chất lượng</span></div></div><label className="field-label">Profile gợi ý</label><select value={profileName} onChange={(e) => { const name = e.target.value; setProfileName(name); if (EXPORT_PROFILES[name]) { setAspect(EXPORT_PROFILES[name].aspect); setResolution(EXPORT_PROFILES[name].width); setCrf(EXPORT_PROFILES[name].crf); setFps(EXPORT_PROFILES[name].fps); setAudioBitrate(EXPORT_PROFILES[name].audioBitrate); } }}>{Object.keys(EXPORT_PROFILES).map((name) => <option key={name}>{name}</option>)}</select><label className="field-label">Độ phân giải</label><select value={resolution} onChange={(e) => setResolution(Number(e.target.value))}><option value="720">720p • {resolutionLabel(720, aspect)}</option><option value="1080">1080p • {resolutionLabel(1080, aspect)}</option><option value="1440">1440p • {resolutionLabel(1440, aspect)}</option><option value="1920">2K • {resolutionLabel(1920, aspect)}</option><option value="2160">4K/UHD • {resolutionLabel(2160, aspect)}</option><option value="3840">4K Landscape • {resolutionLabel(3840, aspect)}</option></select><label className="field-label">Quality (CRF)</label><select value={crf} onChange={(e) => setCrf(Number(e.target.value))}><option value="16">Rất Cao • CRF 16</option><option value="18">Cao • CRF 18</option><option value="20">Cân Bằng • CRF 20</option><option value="23">Nhanh/Nhẹ • CRF 23</option></select><label className="field-label">FPS</label><select value={fps} onChange={(e) => setFps(Number(e.target.value))}><option value="24">24 fps</option><option value="30">30 fps</option><option value="60">60 fps</option></select><label className="field-label">Audio</label><select value={audioBitrate} onChange={(e) => setAudioBitrate(e.target.value)}><option value="128k">128k</option><option value="192k">192k</option><option value="256k">256k</option><option value="320k">320k</option></select><div className="ai-result"><div className="result-row"><span>Xuất hiện tại</span><b>{resolutionLabel(resolution, aspect)}</b></div><div className="result-row"><span>Codec</span><b>H.264 + AAC</b></div><div className="result-row"><span>Màu</span><b>BT.709</b></div><div className="result-row"><span>4K</span><b>{resolution >= 2160 ? 'Bật' : 'Tắt'}</b></div></div><button className="export-btn big" onClick={doExport}><Download size={17}/> Xuất {resolutionLabel(resolution, aspect)}</button><div className="help">Không phóng đại chất lượng nguồn: footage 1080p xuất 4K sẽ không tạo thêm chi tiết thật.</div></>}
          <div className="inspector-bottom"><div className="quality"><span>Project</span><b>Local + JSON</b></div><div className="quality"><span>Preview</span><b>Native HTML5</b></div><div className="quality"><span>Render</span><b>FFmpeg WASM</b></div></div>
        </aside>
      </main>
      {rendering && <div className="render-bar"><div style={{ width: `${progress}%` }}/><span>Đang render {progress}%</span></div>}
      {toast && <div className="toast"><Sparkles size={15}/>{toast}<button onClick={() => setToast('')}><X size={14}/></button></div>}
    </div>
  );
}

function PlayIconFallback() {
  return <span style={{ fontSize: 14 }}>▶</span>;
}
