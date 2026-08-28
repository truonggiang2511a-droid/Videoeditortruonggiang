import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Bot, CheckCircle2, Clapperboard, Cloud, Download, Film, FolderKanban,
  LogIn, LogOut, Plus, RefreshCw, Sparkles, Upload, WandSparkles, Zap,
} from 'lucide-react';
import { sampleVideoFrames, buildSmartCuts } from './lib/scene-intelligence';
import { makeClip } from './lib/editor-engine';
import { renderTimelineToMp4 } from './lib/local-render';
import {
  createAgentPlan, createProject, createRenderJob, getUser, listProjectAssets,
  listProjects, signIn, signOut, subscribeRenderJob, uploadAsset,
} from './lib/os-api';
import { hasSupabase } from './lib/supabase';

const DEFAULT_PROMPT = 'Dựng video bán nhà phố 45 giây, hook mạnh 3 giây đầu, chọn cảnh đẹp, cắt khoảng lặng, caption rõ, nhấn giá + pháp lý + vị trí và CTA gọi/Zalo.';
const BUSINESS_RULES = {
  domain: 'real-estate',
  language: 'vi-VN',
  do_not_invent_property_facts: true,
  priority: ['hook', 'property_visuals', 'price', 'legal', 'location', 'cta'],
};
const fmt = (v = 0) => `${String(Math.floor(v / 60)).padStart(2, '0')}:${String(Math.floor(v % 60)).padStart(2, '0')}`;
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));

function starterClips(duration = 45) {
  return [makeClip({ trackId: 'video', label: 'Video Gốc', start: 0, end: duration, sourceStart: 0, sourceEnd: duration })];
}

export default function SaaSApp() {
  const inputRef = useRef(null);
  const videoRef = useRef(null);
  const unsubscribeRef = useRef(null);
  const [user, setUser] = useState(null);
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState(null);
  const [workspaceId, setWorkspaceId] = useState(null);
  const [projectName, setProjectName] = useState('AI Real Estate Project');
  const [files, setFiles] = useState([]);
  const [assets, setAssets] = useState([]);
  const [file, setFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [duration, setDuration] = useState(45);
  const [current, setCurrent] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [clips, setClips] = useState(starterClips());
  const [plan, setPlan] = useState(null);
  const [status, setStatus] = useState('ready');
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [outputUrl, setOutputUrl] = useState('');
  const [localOutputUrl, setLocalOutputUrl] = useState('');
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let alive = true;
    getUser().then((u) => alive && setUser(u)).catch(() => {});
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (!user) return;
    listProjects().then(({ data }) => setProjects(data || [])).catch((e) => setNotice(e.message));
  }, [user]);

  useEffect(() => () => {
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    if (localOutputUrl) URL.revokeObjectURL(localOutputUrl);
    if (unsubscribeRef.current) unsubscribeRef.current();
  }, [videoUrl, localOutputUrl]);

  const pct = useMemo(() => duration ? (current / duration) * 100 : 0, [current, duration]);

  const createWorkspaceProject = async () => {
    const result = await createProject({ name: projectName, settings: { aspect: '9:16', targetDuration: duration, product: 'GQ AI Editor OS' } });
    const p = result?.data?.id ? result.data : Array.isArray(result?.data) ? result.data[0] : result?.data;
    if (!p?.id) throw new Error('Không tạo được project.');
    setProjectId(p.id);
    setWorkspaceId(p.workspace_id || null);
    const listing = await listProjects();
    setProjects(listing.data || []);
    return p;
  };

  const ensureProject = async () => {
    if (projectId) return { id: projectId, workspace_id: workspaceId };
    return createWorkspaceProject();
  };

  const refreshAssets = async (id) => {
    const result = await listProjectAssets(id);
    if (!result.error) setAssets(result.data || []);
    return result.data || [];
  };

  const setVideos = async (incoming) => {
    const list = Array.from(incoming || []).filter((f) => f?.type?.startsWith('video/')).slice(0, 30);
    if (!list.length) return setNotice('Hãy chọn tối đa 30 video MP4/MOV/WebM.');
    if (!hasSupabase || !user) {
      const first = list[0];
      setFiles(list); setFile(first);
      if (videoUrl) URL.revokeObjectURL(videoUrl);
      setVideoUrl(URL.createObjectURL(first));
      setPlan(null);
      setClips(starterClips(45));
      setLocalOutputUrl('');
      setNotice(`Đang ở Demo/Guest mode. Đã nhận ${list.length} clip; có thể xuất MP4 ngay trên máy.`);
      return;
    }
    setBusy(true);
    try {
      const project = await ensureProject();
      const uploaded = [];
      for (let i = 0; i < list.length; i += 1) {
        const r = await uploadAsset(project.id, list[i], 'video');
        if (r.error) throw r.error;
        uploaded.push(r.data);
        setUploadProgress(Math.round(((i + 1) / list.length) * 100));
      }
      setFiles(list);
      setFile(list[0]);
      if (videoUrl) URL.revokeObjectURL(videoUrl);
      setVideoUrl(URL.createObjectURL(list[0]));
      setAssets(uploaded);
      setPlan(null);
      setClips(starterClips(45));
      setCurrent(0);
      setDuration(45);
      setLocalOutputUrl('');
      setStatus('ready');
      setNotice(`Đã upload ${uploaded.length} clip lên Cloud Storage. Có thể AI dựng rồi Xuất MP4 trực tiếp trên máy.`);
    } catch (error) {
      console.error(error);
      setNotice(error.message || 'Upload cloud thất bại.');
    } finally {
      setBusy(false);
      setUploadProgress(0);
    }
  };

  const analyzeAndPlan = async () => {
    if (!file || busy) return setNotice('Upload footage trước.');
    if (!user && hasSupabase) return setAuthOpen(true);
    setBusy(true);
    setStatus('analyzing');
    try {
      const project = await ensureProject();
      const cloudAssets = assets.length ? assets : await refreshAssets(project.id);
      const meta = await sampleVideoFrames(file, { sampleCount: 48, width: 480 });
      const requested = clamp(Number((prompt.match(/(\d+)\s*(?:giây|s)/i) || [])[1]) || 45, 5, Math.max(5, meta.duration || 45));
      const localCuts = buildSmartCuts(meta.frames, requested, meta.duration);
      const response = await createAgentPlan({
        projectId: project.id,
        prompt,
        videoMeta: { ...meta, clipCount: files.length || 1 },
        assets: cloudAssets.map((a) => ({ id: a.id, name: a.original_name, storage_path: a.storage_path, kind: a.kind, size_bytes: a.size_bytes })),
        skill: 'real-estate-pro',
        businessRules: BUSINESS_RULES,
      });
      const aiPlan = response?.plan || {};
      const available = cloudAssets.length ? cloudAssets : [{ original_name: file.name, storage_path: null }];
      const sceneSource = aiPlan.scenes?.length ? aiPlan.scenes : localCuts.map((c) => ({ start: c.sourceStart, end: c.sourceEnd, role: c.type, score: c.quality }));
      const plannedCuts = sceneSource.map((s, i) => {
        const sourceAsset = available.find((a) => a.id === s.assetId || a.original_name === s.assetName) || available[i % available.length];
        const start = Number(s.start ?? s.sourceStart ?? 0);
        const end = Number(s.end ?? s.sourceEnd ?? start + 3);
        return makeClip({
          trackId: 'video', id: `scene-${i}-${crypto.randomUUID()}`, label: s.role || `Scene ${i + 1}`,
          start, end, sourceStart: start, sourceEnd: end, sceneType: s.role, score: s.score,
          storage_path: s.storage_path || sourceAsset?.storage_path || null, assetId: sourceAsset?.id,
        });
      });
      const clipsSafe = plannedCuts.length ? plannedCuts : localCuts.map((c, i) => makeClip({ ...c, trackId: 'video', storage_path: available[i % available.length]?.storage_path || null }));
      let cursor = 0;
      const finalCuts = clipsSafe.map((c) => {
        const len = Math.max(0.5, Number(c.sourceEnd) - Number(c.sourceStart));
        const out = { ...c, start: cursor, end: cursor + len };
        cursor += len;
        return out;
      });
      const finalDuration = Math.min(requested, cursor || requested);
      const enriched = { ...aiPlan, scenes: finalCuts.map((c) => ({ assetId: c.assetId, storage_path: c.storage_path, start: c.sourceStart, end: c.sourceEnd, role: c.sceneType, score: c.score })) };
      setClips(finalCuts.slice(0, 30));
      setDuration(finalDuration);
      setPlan(enriched);
      setStatus('ready');
      setLocalOutputUrl('');
      setNotice(`AI hoàn tất: ${finalCuts.length} cảnh • ${fmt(finalDuration)} • timeline sẵn sàng để preview / xuất MP4.`);
    } catch (error) {
      console.error(error);
      setStatus('failed');
      setNotice(error.message || 'AI Agent chưa chạy được.');
    } finally { setBusy(false); }
  };

  const exportLocal = async () => {
    if (!files.length || busy) return setNotice('Upload footage trước.');
    const scenes = plan?.scenes?.length
      ? plan.scenes
      : clips.map((c) => ({ assetId: c.assetId, start: c.sourceStart, end: c.sourceEnd, role: c.sceneType }));
    if (!scenes.length) return setNotice('Chưa có scene để xuất. Hãy chạy AI Tự Dựng trước.');

    setBusy(true);
    setStatus('exporting');
    setProgress(0);
    try {
      const blob = await renderTimelineToMp4({
        files,
        scenes,
        assets,
        width: 1080,
        height: 1920,
        crf: 22,
        onProgress: setProgress,
        onStage: setNotice,
      });
      const url = URL.createObjectURL(blob);
      setLocalOutputUrl((previous) => {
        if (previous) URL.revokeObjectURL(previous);
        return url;
      });
      setStatus('completed');
      setProgress(100);
      setNotice('Xuất MP4 hoàn tất. Video 9:16 1080×1920 đã sẵn sàng để tải xuống.');
    } catch (error) {
      console.error(error);
      setStatus('failed');
      setNotice(error.message || 'Xuất MP4 trên trình duyệt thất bại. Hãy thử clip ngắn hơn hoặc ít scene hơn.');
    } finally {
      setBusy(false);
    }
  };

  const render = async () => {
    if (!projectId) return setNotice('Tạo project và upload footage trước.');
    const scenes = plan?.scenes?.length ? plan.scenes : clips.map((c) => ({ assetId: c.assetId, storage_path: c.storage_path, start: c.sourceStart, end: c.sourceEnd, role: c.sceneType }));
    if (!scenes.length || scenes.some((s) => !s.storage_path)) return setNotice('Edit Plan chưa có storage_path. Hãy chạy AI Tự Dựng lại sau khi upload cloud.');
    setStatus('rendering'); setProgress(1); setOutputUrl('');
    try {
      const response = await createRenderJob({ projectId, editPlan: { version: 3, scenes, captions: plan?.captions || { enabled: true }, businessRules: BUSINESS_RULES }, output: { width: 1080, height: 1920, codec: 'h264', format: 'mp4', crf: 20, audioBitrate: '192k' } });
      if (unsubscribeRef.current) unsubscribeRef.current();
      if (response.jobId) {
        unsubscribeRef.current = subscribeRenderJob(response.jobId, (job) => {
          setProgress(job?.progress || 0);
          setStatus(job?.status || 'rendering');
          if (job?.status === 'completed') {
            const url = job?.output?.signed_url || job?.output?.signedUrl || '';
            setOutputUrl(url);
            setNotice('Render Cloud hoàn tất. File MP4 đã được lưu vào Storage.');
            unsubscribeRef.current?.();
          }
          if (job?.status === 'failed') {
            setNotice(job?.error || 'Render thất bại.');
            unsubscribeRef.current?.();
          }
        });
      }
    } catch (error) {
      setStatus('failed'); setNotice(error.message || 'Không tạo được render job.');
    }
  };

  const signInOrUp = async (e) => {
    e.preventDefault();
    try {
      if (authMode === 'login') await signIn(email, password);
      else {
        const { error } = await (await import('./lib/os-api')).signUp(email, password);
        if (error) throw error;
      }
      const u = await getUser();
      setUser(u); setAuthOpen(false); setNotice('Đăng nhập thành công.');
    } catch (error) { setNotice(error.message || 'Auth error.'); }
  };

  return <div className="os-app">
    <header className="os-topbar">
      <div className="os-brand"><div className="os-logo"><Clapperboard size={18}/></div><div><b>GQ AI EDITOR OS</b><span>AGENT • SKILL • VIDEO UNDERSTANDING • LOCAL + CLOUD RENDER</span></div></div>
      <div className="os-top-actions"><div className="workspace-pill"><Cloud size={14}/><span>{hasSupabase ? 'SaaS Cloud' : 'Demo Mode'}</span><i/></div>{user ? <><span className="user-pill">{user.email}</span><button className="os-btn ghost" onClick={async () => { await signOut(); setUser(null); }}><LogOut size={15}/></button></> : <button className="os-btn primary" onClick={() => setAuthOpen(true)}><LogIn size={15}/> Đăng nhập</button>}</div>
    </header>

    <div className="os-layout">
      <aside className="os-sidebar">
        <div className="side-caption">WORKSPACE</div>
        <button className="os-nav active"><FolderKanban size={17}/> Projects</button>
        <button className="os-nav"><Bot size={17}/> AI Agent <span>β</span></button>
        <button className="os-nav"><LayersIconFallback/> Skills</button>
        <button className="os-nav"><Film size={17}/> Media Library</button>
        <div className="side-divider"/>
        <button className="create-project" onClick={createWorkspaceProject}><Plus size={16}/> New Project</button>
        <div className="project-list">{projects.slice(0, 8).map((p) => <button key={p.id} onClick={async () => { setProjectId(p.id); setWorkspaceId(p.workspace_id); setProjectName(p.name); await refreshAssets(p.id); }} className={projectId === p.id ? 'project active' : 'project'}><span>{p.name}</span><small>{p.status}</small></button>)}</div>
      </aside>

      <main className="os-main">
        <section className="os-head"><div><div className="eyebrow">AI VIDEO PRODUCTION OS</div><h1>AI Real Estate Video Studio</h1><p>Upload 10–30 clips → AI Understanding → Edit Plan → Timeline → Preview → <b>Xuất MP4 ngay trên máy</b> hoặc Render Cloud.</p></div><div className="head-actions"><button className="os-btn ghost" onClick={() => inputRef.current?.click()}><Upload size={15}/> Upload 10–30 Clips</button><button className="os-btn primary" disabled={busy || !files.length} onClick={exportLocal}><Download size={15}/> {status === 'exporting' ? `Xuất ${progress}%` : 'Xuất MP4'}</button><button className="os-btn render" disabled={busy} onClick={render}><Zap size={15}/> {status === 'rendering' ? `Cloud ${progress}%` : 'Render Cloud'}</button></div></section>

        <section className="os-grid">
          <div className="preview-card">
            <div className="card-head"><span>PREVIEW</span><span>{files.length || assets.length} clips • {fmt(current)} / {fmt(duration)}</span></div>
            <div className="video-frame" onClick={() => inputRef.current?.click()}>
              {file ? <video ref={videoRef} src={videoUrl} playsInline onTimeUpdate={(e) => setCurrent(e.currentTarget.currentTime)} onLoadedMetadata={(e) => setDuration(Math.min(duration || 45, e.currentTarget.duration || 45))}/> : <div className="empty-video"><Upload size={32}/><b>Upload 10–30 clip</b><span>AI sẽ tự chọn cảnh và lập Edit Plan</span><button className="os-btn primary" onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}><Upload size={15}/> Chọn Footage</button></div>}
              {file && <button className="big-play" onClick={(e) => { e.stopPropagation(); if (!videoRef.current) return; if (videoRef.current.paused) { videoRef.current.play(); setPlaying(true); } else { videoRef.current.pause(); setPlaying(false); } }}>{playing ? '❚❚' : '▶'}</button>}
            </div>
            <div className="player-controls"><button onClick={() => setCurrent(clamp(current - 3, 0, duration))}>−3s</button><button onClick={() => { if (videoRef.current) videoRef.current.play(); setPlaying(true); }}><RefreshCw size={14}/></button><button onClick={() => setCurrent(clamp(current + 3, 0, duration))}>+3s</button><div className="scrub-line"><div style={{ width: `${pct}%` }}/><input aria-label="timeline" type="range" min="0" max={duration || 1} value={current} step="0.01" onChange={(e) => { const t = Number(e.target.value); setCurrent(t); if (videoRef.current) videoRef.current.currentTime = t; }}/></div></div>
          </div>

          <div className="agent-card">
            <div className="card-head"><span>AI AGENT</span><span className={`status ${status}`}>{status.toUpperCase()}</span></div>
            <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Ra lệnh cho AI Editor…"/>
            <div className="skill-row"><span><Sparkles size={14}/> Skill</span><b>Real Estate Pro v1</b><span className="rule-chip">FACT SAFE</span></div>
            <div className="upload-meter">{busy && uploadProgress > 0 && <><span>Cloud Upload {uploadProgress}%</span><div><i style={{ width: `${uploadProgress}%` }}/></div></>}</div>
            <button className="agent-run" disabled={busy || !file} onClick={analyzeAndPlan}><WandSparkles size={18}/>{busy ? 'ĐANG XỬ LÝ…' : 'AI TỰ DỰNG EDIT PLAN'}</button>
            <div className="agent-metrics"><div><b>{assets.length || files.length}</b><span>Assets</span></div><div><b>{clips.length}</b><span>Scenes</span></div><div><b>{status === 'completed' ? 'DONE' : status.toUpperCase()}</b><span>Pipeline</span></div></div>
            <div className="output-actions">
              <button className="download-output" disabled={busy || !files.length} onClick={exportLocal}><Download size={16}/> Xuất MP4 Trên Máy</button>
              {localOutputUrl && <a className="download-output success" href={localOutputUrl} download="gq-ai-real-estate.mp4"><Download size={16}/> Tải MP4</a>}
            </div>
            {outputUrl && <a className="download-output" href={outputUrl} target="_blank" rel="noreferrer"><Cloud size={16}/> Mở / tải MP4 Cloud</a>}
          </div>
        </section>

        <section className="timeline-card">
          <div className="card-head"><span>AI EDIT TIMELINE</span><span>{clips.length} scenes • {fmt(duration)}</span></div>
          <div className="timeline-wrap"><div className="track-labels"><span>VIDEO</span><span>AI PLAN</span><span>ASSETS</span></div><div className="tracks">
            <div className="track-row"><div className="track-line">{clips.map((c, i) => <div key={c.id} className="clip video" style={{ left: `${c.start / Math.max(duration, .1) * 100}%`, width: `${Math.max(4, (c.end - c.start) / Math.max(duration, .1) * 100)}%` }} onClick={() => { setCurrent(c.start); if (videoRef.current) videoRef.current.currentTime = c.sourceStart || 0; }}><b>{i + 1}</b><span>{c.label}</span></div>)}</div></div>
            <div className="track-row"><div className="track-line muted"><div className="clip text" style={{ left: '0%', width: '24%' }}>HOOK</div><div className="clip text" style={{ left: '28%', width: '30%' }}>PRICE • LEGAL • LOCATION</div><div className="clip text" style={{ right: '0%', width: '18%' }}>CTA</div></div></div>
            <div className="track-row"><div className="track-line muted">{assets.slice(0, 12).map((a, i) => <div key={a.id} className="clip asset" style={{ left: `${Math.min(94, i * 8)}%`, width: '7%' }} title={a.original_name}>{i + 1}</div>)}</div></div>
          </div></div>
        </section>

        <div className="pipeline-strip"><span><CheckCircle2/> Upload</span><span>→</span><span><Sparkles/> Understanding</span><span>→</span><span><Bot/> Agent</span><span>→</span><span><Film/> Edit Plan</span><span>→</span><span><Clapperboard/> Local / Cloud Render</span><span>→</span><span><Download/> MP4</span></div>
      </main>
    </div>

    <input ref={inputRef} type="file" accept="video/*" multiple hidden onChange={(e) => setVideos(e.target.files)} />
    {notice && <div className="toast"><Sparkles size={15}/>{notice}<button onClick={() => setNotice('')}>×</button></div>}
    {authOpen && <div className="modal-backdrop"><div className="auth-modal"><div className="card-head"><span>{authMode === 'login' ? 'ĐĂNG NHẬP' : 'TẠO TÀI KHOẢN'}</span><button onClick={() => setAuthOpen(false)}>×</button></div><form onSubmit={signInOrUp}><label>Email</label><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required/><label>Mật khẩu</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required/><button className="os-btn primary" type="submit"><LogIn size={15}/> {authMode === 'login' ? 'Đăng nhập' : 'Đăng ký'}</button></form><button className="auth-switch" onClick={() => setAuthMode((v) => v === 'login' ? 'signup' : 'login')}>{authMode === 'login' ? 'Chưa có tài khoản? Đăng ký' : 'Đã có tài khoản? Đăng nhập'}</button></div></div>}
  </div>;
}

function LayersIconFallback() { return <span style={{ fontSize: 15 }}>◈</span>; }
