import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AudioLines, Captions, Check, Clapperboard, Download, Film, Layers3,
  WandSparkles, Mic2, Music2, Play, Plus, Scissors, Settings2, Sparkles,
  Split, SunMedium, Trash2, Type, Upload, Video, X, Zap,
} from 'lucide-react';
import { exportTimeline, EXPORT_PROFILES } from './lib/ffmpeg';
import { parseVietnameseEditCommand, buildRealEstateTimeline, requestAiPlan } from './lib/ai';
import { sampleVideoFrames, buildSmartCuts, requestVisionPlan } from './lib/scene-intelligence';
import { TRACKS, makeClip, splitClip, moveClip, snapToBeat, createKeyframe, deriveTransform } from './lib/editor-engine';
import { LUT_PRESETS, buildColorFilter } from './lib/color-lab';
import { MUSIC_LIBRARY, autoDuckVolume, buildBeatCuts, createVoiceScript, requestVoice, decodeAudioPeaks } from './lib/audio-engine';
import { saveProject, exportProjectJson, importProjectJson, DEFAULT_EXPORT } from './lib/project';

const DEFAULT_PROMPT = 'Làm video 45 giây bán căn nhà này, hook thật mạnh, màu sáng sang, text chuyên nghiệp, nhấn giá và pháp lý, cuối video có CTA gọi/Zalo xem nhà.';
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
const fmt = (v) => `${String(Math.floor((v || 0) / 60)).padStart(2, '0')}:${String(Math.floor((v || 0) % 60)).padStart(2, '0')}`;

function initialTracks() {
  const clips = buildRealEstateTimeline({ duration: 45 });
  return {
    video: clips.map((clip) => makeClip({ ...clip, trackId: 'video', sourceStart: clip.start, sourceEnd: clip.end, start: clip.timelineStart ?? clip.start, end: clip.timelineEnd ?? clip.end })),
    broll: [],
    text: [
      makeClip({ trackId: 'text', label: 'Hook + Giá', start: 0, end: 5, text: 'CĂN NHÀ ĐÁNG XEM NHẤT KHU VỰC', secondary: '3,2 TỶ', preset: 'premium' }),
      makeClip({ trackId: 'text', label: 'USP', start: 5, end: 30, text: 'Sổ Hồng Riêng • Vị Trí Đẹp' }),
      makeClip({ trackId: 'text', label: 'CTA', start: 40, end: 45, text: 'GỌI / ZALO NGAY ĐỂ HẸN XEM NHÀ', preset: 'cta' }),
    ],
    caption: [],
    audio: [],
    voice: [],
  };
}

export default function App() {
  const videoRef = useRef(null);
  const inputRef = useRef(null);
  const audioRef = useRef(null);
  const importRef = useRef(null);
  const [file, setFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
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
  const [tracks, setTracks] = useState(initialTracks());
  const [selectedId, setSelectedId] = useState(null);
  const [sceneReport, setSceneReport] = useState(null);
  const [smartCuts, setSmartCuts] = useState([]);
  const [music, setMusic] = useState(MUSIC_LIBRARY[0]);
  const [musicFile, setMusicFile] = useState(null);
  const [audioInfo, setAudioInfo] = useState(null);
  const [voiceScript, setVoiceScript] = useState('');
  const [voiceBlobUrl, setVoiceBlobUrl] = useState('');
  const [beatSync, setBeatSync] = useState(true);
  const [fps, setFps] = useState(30);
  const [profileName, setProfileName] = useState('TikTok / Reels');
  const [rendering, setRendering] = useState(false);
  const [progress, setProgress] = useState(0);
  const [toast, setToast] = useState('');

  const profile = EXPORT_PROFILES[profileName] || EXPORT_PROFILES['TikTok / Reels'];
  const filter = useMemo(() => autoColor ? buildColorFilter({ exposure, contrast, saturation, temperature, tint, sharpen, lut }) : 'null', [autoColor, exposure, contrast, saturation, temperature, tint, sharpen, lut]);
  const flatVideoClips = Object.values(tracks).flat().filter((clip) => clip.trackId === 'video' || clip.trackId === 'broll');
  const selectedClip = flatVideoClips.find((clip) => clip.id === selectedId) || null;

  useEffect(() => () => {
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    if (voiceBlobUrl) URL.revokeObjectURL(voiceBlobUrl);
  }, [videoUrl, voiceBlobUrl]);

  const setVideo = (nextFile) => {
    if (!nextFile?.type?.startsWith('video/')) return setToast('Chọn video MP4, MOV hoặc WebM.');
    setFile(nextFile);
    setVideoUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(nextFile);
    });
    setTracks(initialTracks());
    setSceneReport(null);
    setSmartCuts([]);
    setCurrent(0);
    setToast('Đã nạp video. Có thể bắt đầu AI Auto Edit.');
  };

  const jump = (time) => {
    if (!videoRef.current) return;
    const next = clamp(time, 0, duration || 1);
    videoRef.current.currentTime = next;
    setCurrent(next);
  };

  const analyze = async () => {
    if (!file) return setToast('Hãy upload video trước.');
    try {
      setToast('AI đang quét footage + phân tích lệnh tiếng Việt…');
      const localMeta = await sampleVideoFrames(file, { sampleCount: 20, width: 320 });
      const command = parseVietnameseEditCommand(prompt, localMeta.duration);
      const localCuts = buildSmartCuts(localMeta.frames, command.duration);
      const timeline = buildRealEstateTimeline({ duration: command.duration, sourceDuration: localMeta.duration, sceneTypes: command.scenes });
      const vision = await requestVisionPlan({ endpoint: import.meta.env.VITE_VISION_ENDPOINT, prompt, videoMeta: localMeta, frames: localMeta.frames }).catch(() => null);
      const ai = await requestAiPlan({ prompt, videoMeta: localMeta, endpoint: import.meta.env.VITE_AI_ENDPOINT }).catch(() => command);
      const nextVideo = (localCuts.length ? localCuts : timeline).map((cut, index) => {
        const start = localCuts.length ? index * (command.duration / Math.max(1, localCuts.length)) : (cut.timelineStart ?? cut.start ?? 0);
        const end = localCuts.length ? Math.min(command.duration, (index + 1) * (command.duration / Math.max(1, localCuts.length))) : (cut.timelineEnd ?? cut.end ?? command.duration);
        return makeClip({ ...cut, trackId: 'video', label: vision?.clips?.[index]?.label || cut.label, start, end, sourceStart: cut.sourceStart ?? cut.start ?? 0, sourceEnd: cut.sourceEnd ?? cut.end ?? localMeta.duration });
      });
      setPreset(ai.style || command.style);
      setAspect(ai.aspect || command.aspect);
      setTitle(ai.hook || command.hook);
      setTracks((old) => ({ ...old, video: nextVideo, text: [
        makeClip({ trackId: 'text', label: 'Hook + Giá', start: 0, end: Math.min(5, command.duration), text: ai.hook || command.hook, secondary: price, preset: 'premium' }),
        makeClip({ trackId: 'text', label: 'USP', start: Math.min(5, command.duration * 0.5), end: Math.min(command.duration, command.duration * 0.72), text: captionBrand }),
        makeClip({ trackId: 'text', label: 'CTA', start: Math.max(0, command.duration - 5), end: command.duration, text: ai.cta || command.cta, preset: 'cta' }),
      ] }));
      setDuration(Math.min(command.duration, localMeta.duration || command.duration));
      setSmartCuts(localCuts);
      setSceneReport(localMeta);
      setToast(`AI hoàn tất: ${localCuts.length || 1} cảnh + kế hoạch ${command.duration}s.`);
    } catch (error) {
      console.error(error);
      setToast('AI phân tích gặp lỗi. App vẫn cho phép dựng thủ công.');
    }
  };

  const applySmartCut = () => {
    if (!smartCuts.length) return setToast('Hãy chạy AI Auto Edit trước.');
    setTracks((old) => ({ ...old, video: smartCuts.map((cut, index) => makeClip({ ...cut, trackId: 'video', label: cut.label, start: index * 3.5, end: Math.min(duration, index * 3.5 + 3.5), sourceStart: cut.sourceStart, sourceEnd: cut.sourceEnd })) }));
    setToast('Đã đưa Smart Cut vào timeline.');
  };

  const splitSelected = () => {
    if (!selectedClip) return setToast('Chọn một clip trong timeline.');
    if (current <= selectedClip.start || current >= selectedClip.end) return setToast('Đưa playhead vào trong clip rồi Split.');
    setTracks((old) => Object.fromEntries(Object.entries(old).map(([key, list]) => [key, list.flatMap((clip) => clip.id === selectedClip.id ? splitClip(clip, current) : [clip])] )));
    setToast('Đã Split clip.');
  };

  const deleteSelected = () => {
    if (!selectedId) return setToast('Chưa chọn clip.');
    setTracks((old) => Object.fromEntries(Object.entries(old).map(([key, list]) => [key, list.filter((clip) => clip.id !== selectedId)])));
    setSelectedId(null);
  };

  const addTextClip = () => {
    const clip = makeClip({ trackId: 'text', label: 'Text mới', start: current, end: Math.min(duration, current + 4), text: 'NHÀ ĐẸP • GIÁ TỐT • SỔ HỒNG RIÊNG' });
    setTracks((old) => ({ ...old, text: [...old.text, clip] }));
    setSelectedId(clip.id);
  };

  const addKeyframe = () => {
    if (!selectedClip) return setToast('Chọn clip video trước.');
    const relativeTime = clamp(current - selectedClip.start, 0, selectedClip.end - selectedClip.start);
    const updated = { ...selectedClip, transform: { ...selectedClip.transform, keyframes: [...(selectedClip.transform?.keyframes || []), { ...createKeyframe(relativeTime, 1.18), property: 'scale' }] } };
    setTracks((old) => Object.fromEntries(Object.entries(old).map(([key, list]) => [key, list.map((clip) => clip.id === selectedId ? updated : clip)])));
    setToast('Đã tạo keyframe Zoom.');
  };

  const onClipDrag = (e, clip) => e.dataTransfer.setData('application/x-gq-clip', clip.id);
  const onTrackDrop = (e, trackId) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('application/x-gq-clip');
    if (!id) return;
    const clip = Object.values(tracks).flat().find((item) => item.id === id);
    if (!clip) return;
    const rect = e.currentTarget.getBoundingClientRect();
    let nextStart = clamp(((e.clientX - rect.left) / rect.width) * duration, 0, Math.max(0, duration - (clip.end - clip.start)));
    if (beatSync && audioInfo?.bpm) nextStart = snapToBeat(nextStart, buildBeatCuts({ clipCount: 40, bpm: audioInfo.bpm, duration }), 0.18);
    const delta = nextStart - clip.start;
    setTracks((old) => Object.fromEntries(Object.entries(old).map(([key, list]) => [key, list.map((item) => item.id === id ? { ...moveClip([item], id, delta)[0], trackId } : item)])));
  };

  const onMusic = async (nextFile) => {
    if (!nextFile) return;
    setMusicFile(nextFile);
    try { setAudioInfo(await decodeAudioPeaks(nextFile)); } catch { setAudioInfo(null); }
    setToast(`Đã nạp nhạc: ${nextFile.name}`);
  };

  const makeVoice = async () => {
    const script = createVoiceScript({ title, price, cta: 'Gọi / Zalo ngay để hẹn xem nhà', seconds: Math.min(45, duration) });
    setVoiceScript(script.text);
    const blob = await requestVoice({ endpoint: import.meta.env.VITE_VOICE_ENDPOINT, text: script.text }).catch(() => null);
    if (blob) {
      const url = URL.createObjectURL(blob);
      setVoiceBlobUrl((old) => { if (old) URL.revokeObjectURL(old); return url; });
      setTracks((old) => ({ ...old, voice: [makeClip({ trackId: 'voice', label: 'AI Voice', start: 0, end: duration, volume: 1 })] }));
      setToast('Đã nhận voice AI và thêm vào timeline.');
    } else {
      setTracks((old) => ({ ...old, voice: [makeClip({ trackId: 'voice', label: 'AI Voice • Chờ API', start: 0, end: duration, volume: 1, text: script.text })] }));
      setToast('Script voice đã sẵn sàng.');
    }
  };

  const runAutoColor = () => {
    if (!file) return setToast('Upload video trước.');
    setAutoColor(true);
    setExposure(0.02);
    setContrast(1.05);
    setSaturation(1.08);
    setToast('Đã áp Auto Color + preset màu BĐS.');
  };

  const makeProject = () => ({ version: 1, name: `GQ-BDS-${Date.now()}`, duration, aspect, prompt, fileName: file?.name || '', title, price, captionBrand, lut, autoColor, tracks, export: { ...DEFAULT_EXPORT, ...profile } });
  const saveCurrentProject = () => { saveProject(makeProject()); setToast('Đã lưu project trên trình duyệt.'); };
  const downloadProject = () => exportProjectJson(makeProject());
  const loadProject = async (nextFile) => {
    try {
      const project = await importProjectJson(nextFile);
      setDuration(project.duration || 45); setAspect(project.aspect || '9:16'); setPrompt(project.prompt || DEFAULT_PROMPT); setTitle(project.title || title); setPrice(project.price || price); setCaptionBrand(project.captionBrand || captionBrand); setTracks(project.tracks || initialTracks()); setLut(project.lut || 'luxury'); setAutoColor(project.autoColor !== false); setToast('Đã import project JSON. Video nguồn cần upload lại nếu máy không còn file.');
    } catch { setToast('Project JSON không hợp lệ.'); }
  };

  const doExport = async () => {
    if (!file) return setToast('Hãy upload video.');
    try {
      setRendering(true); setProgress(0);
      const blob = await exportTimeline({ file, clips: flatVideoClips, filter, aspect: profile.aspect, width: profile.width, crf: profile.crf, fps, audioBitrate: profile.audioBitrate, overlayText: `${title} • ${price}`, enhanceVoice: tracks.voice.length > 0, onProgress: setProgress });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url; link.download = `GQ-BDS-${profileName.replace(/[^a-z0-9]+/gi, '-')}-${Date.now()}.mp4`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
      setToast('Xuất MP4 thành công.');
    } catch (error) {
      console.error(error);
      setToast('Render lỗi. Thử 1080p trước; 4K cần máy đủ RAM/CPU.');
    } finally { setRendering(false); }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><div className="brand-mark"><Clapperboard size={18}/></div><div><b>GQ VIDEO EDITOR</b><span>CAPCUT CHO MÔI GIỚI BĐS</span></div></div>
        <div className="top-actions"><button className="ghost" onClick={saveCurrentProject}><Layers3 size={15}/> Lưu</button><button className="ghost" onClick={downloadProject}><Download size={15}/> Project</button><button className="export-btn" onClick={doExport}><Video size={16}/> {rendering ? `Đang Xuất ${progress}%` : 'Xuất MP4'}</button></div>
      </header>
      <main className="workspace">
        <aside className="sidebar"><div className="sidebar-title">Studio BĐS</div>{[['ai',WandSparkles,'AI Auto Edit'],['media',Film,'Media'],['text',Type,'Text & Motion'],['captions',Captions,'Captions'],['audio',AudioLines,'Âm Thanh'],['color',SunMedium,'Color Lab'],['settings',Settings2,'Export']].map(([id,Icon,label]) => <button key={id} className={`side-item ${tool === id ? 'active' : ''}`} onClick={() => setTool(id)}><Icon size={18}/><span>{label}</span></button>)}<div className="sidebar-bottom"><label className="upload-mini"><Upload size={15}/> Upload Video<input ref={inputRef} type="file" accept="video/*" hidden onChange={(e) => setVideo(e.target.files?.[0])}/></label><label className="upload-mini"><Music2 size={15}/> Thêm Nhạc<input ref={audioRef} type="file" accept="audio/*" hidden onChange={(e) => onMusic(e.target.files?.[0])}/></label><label className="upload-mini"><Download size={15}/> Import Project<input ref={importRef} type="file" accept="application/json" hidden onChange={(e) => loadProject(e.target.files?.[0])}/></label></div></aside>
        <section className="center">
          <div className="editor-head"><div><h1>AI Real Estate Video Studio</h1><span>{file ? file.name : 'Upload footage để bắt đầu'}</span></div><div className="format-switch"><span>Tỷ lệ</span>{['9:16','1:1','16:9'].map((v) => <button key={v} onClick={() => setAspect(v)} className={aspect === v ? 'chosen' : ''}>{v}</button>)}</div></div>
          <div className={`preview-stage ratio-${aspect.replace(':','x')}`}>
            {!file && <div className="dropzone" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); setVideo(e.dataTransfer.files?.[0]); }} onClick={() => inputRef.current?.click()}><div className="upload-icon"><Upload size={28}/></div><h2>Thả Video Vào Đây</h2><p>MP4 • MOV • WebM • Full HD / 4K</p><button className="primary"><Upload size={16}/> Chọn Video</button></div>}
            {file && <><video ref={videoRef} src={videoUrl} className="preview-video" style={{ filter: autoColor ? 'contrast(1.05) brightness(1.025) saturate(1.08)' : 'none', transform: selectedClip ? `scale(${deriveTransform(selectedClip, current - selectedClip.start).scale || 1})` : 'scale(1)' }} onLoadedMetadata={(e) => setDuration(e.currentTarget.duration || 45)} onTimeUpdate={(e) => setCurrent(e.currentTarget.currentTime)} onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} playsInline /><div className="video-gradient"/><div className="overlay-copy top-copy"><small>{captionBrand}</small><strong>{title}</strong></div><div className="overlay-copy price-copy"><b>{price}</b><span>Gọi / Zalo ngay để hẹn xem nhà</span></div><button className="play-btn" onClick={() => { if (videoRef.current?.paused) videoRef.current.play(); else videoRef.current?.pause(); }}>{playing ? '❚❚' : '▶'}</button></>}
            <div className="timecode">{fmt(current)} <span>/</span> {fmt(duration)}</div>
          </div>
          <div className="transport"><button onClick={() => jump(current - 3)}>−3s</button><button className="transport-play" onClick={() => { if (!file) return; if (videoRef.current?.paused) videoRef.current.play(); else videoRef.current?.pause(); }}>{playing ? '❚❚' : '▶'}</button><button onClick={() => jump(current + 3)}>+3s</button><div className="scrub"><div className="scrub-fill" style={{ width: `${duration ? current / duration * 100 : 0}%` }}/><input aria-label="scrub" type="range" min="0" max={duration || 1} step="0.01" value={current} onChange={(e) => jump(Number(e.target.value))}/></div><span>{fps}fps</span></div>
          <div className="timeline-panel"><div className="timeline-head"><b>Multi-Track Timeline</b><span>{flatVideoClips.length} video clips • {Object.values(tracks).flat().length} total clips</span><div><button onClick={splitSelected}><Scissors size={14}/> Split</button><button onClick={addTextClip}><Plus size={14}/> Text</button><button onClick={deleteSelected}><Trash2 size={14}/></button></div></div><div className="timeline">{TRACKS.map((track) => <div className="track-row" key={track.id}><div className="track-name">{track.name}</div><div className="track" onDragOver={(e) => e.preventDefault()} onDrop={(e) => onTrackDrop(e, track.id)}>{(tracks[track.id] || []).map((clip) => <div draggable key={clip.id} onDragStart={(e) => onClipDrag(e, clip)} onClick={() => { setSelectedId(clip.id); jump(clip.start); }} className={`segment ${selectedId === clip.id ? 'selected' : ''}`} style={{ left: `${duration ? clip.start / duration * 100 : 0}%`, width: `${duration ? Math.max(2, (clip.end - clip.start) / duration * 100) : 8}%` }}><span>{clip.label}</span><small>{fmt(clip.end - clip.start)}</small></div>)}<div className="playhead" style={{ left: `${duration ? current / duration * 100 : 0}%` }}/></div></div>)}</div></div>
        </section>
        <aside className="inspector">
          {tool === 'ai' && <><div className="inspector-title"><div><b>AI Auto Edit</b><span>Điều khiển bằng tiếng Việt</span></div><div className="ai-dot"/></div><textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={6}/><button className="ai-button" onClick={analyze}><WandSparkles size={17}/> Phân Tích & Tự Dựng</button><div className="smart-grid"><button onClick={applySmartCut}><Zap size={15}/> Smart Cut</button><button onClick={runAutoColor}><SunMedium size={15}/> Auto Color</button></div>{sceneReport && <div className="ai-result"><div className="result-head"><Check size={15}/> Scene Intelligence</div><div className="result-row"><span>Cảnh đã quét</span><b>{sceneReport.frames.length}</b></div><div className="result-row"><span>Cảnh tốt</span><b>{sceneReport.frames.filter((f) => f.type === 'good').length}</b></div><div className="result-row"><span>Cảnh cần bỏ</span><b>{sceneReport.frames.filter((f) => f.type === 'bad').length}</b></div></div>}<label className="field-label">Preset</label><select value={preset} onChange={(e) => setPreset(e.target.value)}><option value="luxury">Luxury BĐS</option><option value="fast">Chốt Nhanh</option><option value="family">Gia Đình</option></select></>}
          {tool === 'text' && <><div className="inspector-title"><div><b>Text & Motion</b><span>Typography bán hàng chuyên nghiệp</span></div></div><label className="field-label">Headline</label><textarea value={title} onChange={(e) => setTitle(e.target.value)} rows={3}/><label className="field-label">Giá</label><input value={price} onChange={(e) => setPrice(e.target.value)}/><label className="field-label">USP / Pháp lý</label><input value={captionBrand} onChange={(e) => setCaptionBrand(e.target.value)}/><div className="style-card"><b>Premium Real Estate</b><div className="style-preview"><strong>{title}</strong><span>{price} • {captionBrand}</span></div></div><button className="secondary" onClick={addTextClip}><Plus size={16}/> Thêm Text Vào Timeline</button><button className="secondary" onClick={addKeyframe}><Split size={16}/> Tạo Keyframe Zoom</button></>}
          {tool === 'captions' && <><div className="inspector-title"><div><b>AI Captions</b><span>Sub chuyên nghiệp cho Reels/TikTok</span></div></div><div className="feature-list"><span><Captions/> Speech-to-Text tiếng Việt</span><span><Sparkles/> Keyword Highlight</span><span><Zap/> Karaoke Timing</span></div><button className="secondary" onClick={() => setToast('Caption Engine đã sẵn sàng; cần kết nối STT endpoint để tạo transcript tự động.')}>Tạo Caption Tự Động</button></>}
          {tool === 'audio' && <><div className="inspector-title"><div><b>Audio Studio</b><span>Nhạc • voice • beat</span></div></div><select value={music.id} onChange={(e) => setMusic(MUSIC_LIBRARY.find((item) => item.id === e.target.value) || MUSIC_LIBRARY[0])}>{MUSIC_LIBRARY.map((item) => <option key={item.id} value={item.id}>{item.name} • {item.bpm} BPM</option>)}</select><div className="smart-row"><div><b>Beat Sync</b><span>Snap clip vào nhịp</span></div><button className={`toggle ${beatSync ? 'on' : ''}`} onClick={() => setBeatSync((v) => !v)}><i/></button></div><div className="feature-list"><span><AudioLines/> Auto Ducking {audioInfo?.bpm ? `• ${audioInfo.bpm} BPM` : ''}</span><span><AudioLines/> Voice Enhance</span><span><Mic2/> AI Voice</span></div><textarea value={voiceScript} onChange={(e) => setVoiceScript(e.target.value)} placeholder="Script voice AI…" rows={5}/><button className="secondary" onClick={makeVoice}><Mic2 size={16}/> Tạo Voice Script / AI Voice</button>{voiceBlobUrl && <audio controls src={voiceBlobUrl} style={{ width: '100%', marginTop: 12 }}/>} {musicFile && <div className="help">Nhạc: {musicFile.name}. Auto Ducking đề xuất volume {Math.round(autoDuckVolume({ musicVolume: .18, voicePresent: tracks.voice.length > 0 }) * 100)}%.</div>}</>}
          {tool === 'color' && <><div className="inspector-title"><div><b>Color Lab</b><span>Auto Match • LUT • HSL</span></div></div><select value={lut} onChange={(e) => setLut(e.target.value)}>{LUT_PRESETS.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>{[['Exposure', exposure, setExposure, -1, 1, .01], ['Contrast', contrast, setContrast, .7, 1.5, .01], ['Saturation', saturation, setSaturation, .5, 1.5, .01], ['Temperature', temperature, setTemperature, -1, 1, .01], ['Tint', tint, setTint, -1, 1, .01], ['Sharpen', sharpen, setSharpen, 0, 1, .01]].map(([label, value, setter, min, max, step]) => <div className="knob-row" key={label}><span>{label}</span><input type="range" min={min} max={max} step={step} value={value} onChange={(e) => setter(Number(e.target.value))}/><b>{Number(value).toFixed(2)}</b></div>)}<button className={`secondary ${autoColor ? 'selected' : ''}`} onClick={() => setAutoColor((v) => !v)}><SunMedium size={16}/> {autoColor ? 'Auto Color: ON' : 'Auto Color: OFF'}</button></>}
          {tool === 'settings' && <><div className="inspector-title"><div><b>Export Master</b><span>Social • Full HD • 4K</span></div></div><label className="field-label">Profile</label><select value={profileName} onChange={(e) => setProfileName(e.target.value)}>{Object.keys(EXPORT_PROFILES).map((name) => <option key={name}>{name}</option>)}</select><div className="ai-result"><div className="result-row"><span>Resolution</span><b>{profile.width}×{Math.round(profile.width * (profile.aspect === '9:16' ? 16 / 9 : profile.aspect === '1:1' ? 1 : 9 / 16))}</b></div><div className="result-row"><span>Codec</span><b>H.264 + AAC</b></div><div className="result-row"><span>Quality</span><b>CRF {profile.crf}</b></div></div><label className="field-label">FPS</label><select value={fps} onChange={(e) => setFps(Number(e.target.value))}><option value="24">24 fps</option><option value="30">30 fps</option><option value="60">60 fps</option></select><button className="export-btn big" onClick={doExport}><Download size={17}/> Xuất {profileName}</button></>}
          <div className="inspector-bottom"><div className="quality"><span>Project</span><b>Local + JSON</b></div><div className="quality"><span>Engine</span><b>FFmpeg WASM</b></div></div>
        </aside>
      </main>
      {rendering && <div className="render-bar"><div style={{ width: `${progress}%` }}/><span>Đang render {progress}%</span></div>}
      {toast && <div className="toast"><Sparkles size={15}/>{toast}<button onClick={() => setToast('')}><X size={14}/></button></div>}
    </div>
  );
}
