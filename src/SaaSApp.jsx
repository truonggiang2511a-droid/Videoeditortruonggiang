import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Bot, CheckCircle2, Clapperboard, Cloud, Film, FolderKanban, Layers3,
  LogIn, LogOut, Menu, Play, Plus, RefreshCw, Sparkles, Upload, UserPlus,
  WandSparkles, X, Zap,
} from 'lucide-react';
import { sampleVideoFrames, buildSmartCuts } from './lib/scene-intelligence';
import { makeClip } from './lib/editor-engine';
import { createAgentPlan, createProject, createRenderJob, getUser, listProjects, signIn, signOut, subscribeRenderJob } from './lib/os-api';
import { hasSupabase } from './lib/supabase';

const DEFAULT_PROMPT = 'Dựng video bán nhà phố 45 giây, hook mạnh 3 giây đầu, tự chọn cảnh đẹp, cắt khoảng lặng, caption nổi bật, nhấn giá + pháp lý + vị trí, CTA gọi/Zalo.';
const fmt = (v = 0) => `${String(Math.floor(v / 60)).padStart(2, '0')}:${String(Math.floor(v % 60)).padStart(2, '0')}`;
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));

function starterClips(duration = 45) {
  return [makeClip({ trackId: 'video', label: 'Video Gốc', start: 0, end: duration, sourceStart: 0, sourceEnd: duration })];
}

export default function SaaSApp() {
  const inputRef = useRef(null);
  const videoRef = useRef(null);
  const [user, setUser] = useState(null);
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState(null);
  const [projectName, setProjectName] = useState('AI Real Estate Project');
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
    listProjects().then(({ data }) => setProjects(data || [])).catch(() => {});
  }, [user]);

  useEffect(() => () => { if (videoUrl) URL.revokeObjectURL(videoUrl); }, [videoUrl]);

  const pct = useMemo(() => duration ? (current / duration) * 100 : 0, [current, duration]);

  const setVideo = (next) => {
    if (!next?.type?.startsWith('video/')) return setNotice('Hãy chọn video MP4, MOV hoặc WebM.');
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    setFile(next);
    setVideoUrl(URL.createObjectURL(next));
    setPlan(null);
    setClips(starterClips(45));
    setCurrent(0);
    setDuration(45);
    setStatus('ready');
    setNotice(`Đã nạp ${next.name}. AI có thể phân tích và lập Edit Plan.`);
  };

  const analyzeAndPlan = async () => {
    if (!file || busy) return setNotice('Upload video trước.');
    setBusy(true);
    setStatus('analyzing');
    try {
      const meta = await sampleVideoFrames(file, { sampleCount: 48, width: 480 });
      const requested = clamp(Number((prompt.match(/(\d+)\s*(?:giây|s)/i) || [])[1]) || 45, 5, Math.max(5, meta.duration || 45));
      const localCuts = buildSmartCuts(meta.frames, requested, meta.duration);
      const response = await createAgentPlan({ projectId, prompt, videoMeta: meta, assets: [{ id: file.name, name: file.name, duration: meta.duration, kind: 'video' }] });
      const aiPlan = response?.plan || {};
      const plannedCuts = (aiPlan.scenes?.length ? aiPlan.scenes : localCuts.map((c) => ({ assetId: file.name, start: c.sourceStart, end: c.sourceEnd, role: c.type, score: c.quality })))
        .map((s, i) => makeClip({ trackId: 'video', label: s.role || `Scene ${i + 1}`, start: Math.min(meta.duration || requested, s.start || 0), end: Math.min(meta.duration || requested, s.end || Math.min(meta.duration || requested, (s.start || 0) + 3)), sourceStart: s.start || 0, sourceEnd: s.end || Math.min(meta.duration || requested, (s.start || 0) + 3), sceneType: s.role, score: s.score }));
      const usable = plannedCuts.length ? plannedCuts : localCuts.map((c) => makeClip({ ...c, trackId: 'video', sourceStart: c.sourceStart, sourceEnd: c.sourceEnd }));
      const normalized = usable.map((c, i) => ({ ...c, start: i === 0 ? 0 : usable.slice(0, i).reduce((n, x) => n + Math.max(.5, x.end - x.start), 0), end: 0 }));
      let cursor = 0;
      const finalCuts = normalized.map((c) => { const len = Math.max(0.5, c.sourceEnd - c.sourceStart); const out = { ...c, start: cursor, end: cursor + len }; cursor += len; return out; });
      setClips(finalCuts.slice(0, 12));
      setDuration(Math.min(requested, cursor || requested));
      setPlan(aiPlan);
      setStatus('ready');
      setNotice(`AI đã tạo Edit Plan: ${finalCuts.length} cảnh • ${fmt(Math.min(requested, cursor || requested))}.`);
    } catch (error) {
      console.error(error);
      setStatus('failed');
      setNotice(error.message || 'AI Agent chưa chạy được. Kiểm tra API và video.');
    } finally { setBusy(false); }
  };

  const saveNewProject = async () => {
    try {
      const result = await createProject({ name: projectName, settings: { aspect: '9:16', targetDuration: duration } });
      const p = result?.data;
      setProjectId(p?.id || p?.[0]?.id || null);
      setNotice('Project đã được tạo và gắn với workspace.');
      const listing = await listProjects();
      setProjects(listing.data || []);
    } catch (error) { setNotice(error.message || 'Không tạo project.'); }
  };

  const render = async () => {
    if (!projectId) {
      if (hasSupabase) return setNotice('Tạo project trước khi render cloud.');
      return setNotice('Demo mode: render cloud cần Supabase + worker.');
    }
    setStatus('rendering'); setProgress(8);
    try {
      const response = await createRenderJob({ projectId, editPlan: plan || { scenes: clips.map(({ sourceStart, sourceEnd, ...c }) => ({ ...c, start: sourceStart, end: sourceEnd })) }, output: { width: 1080, height: 1920, codec: 'h264', format: 'mp4' } });
      if (response.jobId) {
        const unsubscribe = subscribeRenderJob(response.jobId, (job) => {
          setProgress(job?.progress || 0);
          setStatus(job?.status || 'rendering');
          if (job?.status === 'completed') { setNotice('Render hoàn tất.'); unsubscribe(); }
          if (job?.status === 'failed') { setNotice(job?.error || 'Render thất bại.'); unsubscribe(); }
        });
      }
      if (response.status === 'queued-local') setNotice('Job đã được ghi nhận ở chế độ local. Kết nối Render Worker để xuất MP4 server-side.');
    } catch (error) {
      setStatus('failed');
      setNotice(error.message || 'Không tạo được render job.');
    }
  };

  const toggle = async () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) { await videoRef.current.play(); setPlaying(true); }
    else { videoRef.current.pause(); setPlaying(false); }
  };

  const doAuth = async (e) => {
    e.preventDefault();
    try {
      if (authMode === 'login') await signIn(email, password);
      else {
        const { error } = await (await import('./lib/os-api')).signUp(email, password);
        if (error) throw error;
      }
      const u = await getUser(); setUser(u); setAuthOpen(false); setNotice('Đăng nhập thành công.');
    } catch (error) { setNotice(error.message || 'Auth error.'); }
  };

  return <div className="os-app">
    <header className="os-topbar">
      <div className="os-brand"><div className="os-logo"><Clapperboard size={18}/></div><div><b>GQ AI EDITOR OS</b><span>AGENT • SKILL • VIDEO INTELLIGENCE • RENDER</span></div></div>
      <div className="os-top-actions"><div className="workspace-pill"><Cloud size={14}/><span>{hasSupabase ? 'SaaS Cloud' : 'Demo Mode'}</span><i/></div>{user ? <><span className="user-pill">{user.email}</span><button className="os-btn ghost" onClick={async () => { await signOut(); setUser(null); setNotice('Đã đăng xuất.'); }}><LogOut size={15}/></button></> : <button className="os-btn primary" onClick={() => setAuthOpen(true)}><LogIn size={15}/> Đăng nhập</button>}</div>
    </header>

    <div className="os-layout">
      <aside className="os-sidebar">
        <div className="side-caption">WORKSPACE</div>
        <button className="os-nav active"><FolderKanban size={17}/> Projects</button>
        <button className="os-nav"><Bot size={17}/> AI Agent <span>β</span></button>
        <button className="os-nav"><Layers3 size={17}/> Skills</button>
        <button className="os-nav"><Film size={17}/> Media Library</button>
        <div className="side-divider"/>
        <button className="create-project" onClick={saveNewProject}><Plus size={16}/> New Project</button>
        <div className="project-list">{projects.slice(0, 8).map((p) => <button key={p.id} onClick={() => { setProjectId(p.id); setProjectName(p.name); }} className={projectId === p.id ? 'project active' : 'project'}><span>{p.name}</span><small>{p.status}</small></button>)}</div>
      </aside>

      <main className="os-main">
        <section className="os-head"><div><div className="eyebrow">AI VIDEO PRODUCTION</div><h1>AI Real Estate Video Studio</h1><p>Upload footage → AI hiểu nội dung → Edit Plan → Timeline → Cloud Render.</p></div><div className="head-actions"><button className="os-btn ghost" onClick={saveNewProject}><Plus size={15}/> Tạo Project</button><button className="os-btn render" onClick={render}><Zap size={15}/> {status === 'rendering' ? `Render ${progress}%` : 'Render Cloud'}</button></div></section>

        <section className="os-grid">
          <div className="preview-card">
            <div className="card-head"><span>PREVIEW</span><span>{fmt(current)} / {fmt(duration)}</span></div>
            <div className="video-frame" onClick={() => inputRef.current?.click()}>
              {file ? <video ref={videoRef} src={videoUrl} playsInline onTimeUpdate={(e) => setCurrent(e.currentTarget.currentTime)} onLoadedMetadata={(e) => setDuration(Math.min(duration || 45, e.currentTarget.duration || 45))}/> : <div className="empty-video"><Upload size={32}/><b>Drop video vào đây</b><span>MP4 / MOV / WebM</span><button className="os-btn primary" onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}><Upload size={15}/> Upload Footage</button></div>}
              {file && <button className="big-play" onClick={(e) => { e.stopPropagation(); toggle(); }}>{playing ? '❚❚' : '▶'}</button>}
            </div>
            <div className="player-controls"><button onClick={() => setCurrent(clamp(current - 3, 0, duration))}>−3s</button><button onClick={toggle}><Play size={15}/></button><button onClick={() => setCurrent(clamp(current + 3, 0, duration))}>+3s</button><div className="scrub-line"><div style={{ width: `${pct}%` }}/><input aria-label="timeline" type="range" min="0" max={duration || 1} value={current} step="0.01" onChange={(e) => { const t = Number(e.target.value); setCurrent(t); if (videoRef.current) videoRef.current.currentTime = t; }}/></div></div>
          </div>

          <div className="agent-card">
            <div className="card-head"><span>AI AGENT</span><span className={`status ${status}`}>{status.toUpperCase()}</span></div>
            <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Ra lệnh cho AI Editor…"/>
            <div className="skill-row"><span><Sparkles size={14}/> Skill</span><b>Real Estate Pro</b><button title="skill">⚙</button></div>
            <button className="agent-run" disabled={busy || !file} onClick={analyzeAndPlan}><WandSparkles size={18}/>{busy ? 'AI ĐANG PHÂN TÍCH…' : 'AI TỰ DỰNG EDIT PLAN'}</button>
            <div className="agent-metrics"><div><b>{plan?.scenes?.length || clips.length}</b><span>Scenes</span></div><div><b>{plan?.captions?.enabled ? 'ON' : 'AUTO'}</b><span>Captions</span></div><div><b>{plan?.project?.aspect || '9:16'}</b><span>Format</span></div></div>
          </div>
        </section>

        <section className="timeline-card">
          <div className="card-head"><span>AI EDIT TIMELINE</span><span>{clips.length} clips • {fmt(duration)}</span></div>
          <div className="timeline-wrap"><div className="track-labels"><span>VIDEO</span><span>TEXT</span><span>CAPTION</span><span>AUDIO</span></div><div className="tracks">
            <div className="track-row"><div className="track-line">{clips.map((c, i) => <div key={c.id} className="clip video" style={{ left: `${c.start / Math.max(duration, .1) * 100}%`, width: `${Math.max(5, (c.end - c.start) / Math.max(duration, .1) * 100)}%` }} onClick={() => { setCurrent(c.start); if (videoRef.current) videoRef.current.currentTime = c.sourceStart || 0; }}><b>{i + 1}</b><span>{c.label}</span></div>)}</div></div>
            <div className="track-row"><div className="track-line muted"><div className="clip text" style={{ left: '0%', width: '22%' }}>HOOK</div><div className="clip text" style={{ left: '26%', width: '30%' }}>USP / GIÁ / PHÁP LÝ</div><div className="clip text" style={{ right: '0%', width: '18%' }}>CTA</div></div></div>
            <div className="track-row"><div className="track-line muted"><div className="clip caption" style={{ left: '5%', width: '24%' }}>AUTO CAPTION</div><div className="clip caption" style={{ left: '34%', width: '36%' }}>HIGHLIGHT KEYWORDS</div></div></div>
            <div className="track-row"><div className="track-line muted"><div className="clip audio" style={{ left: '0%', width: '92%' }}>MUSIC + VOICE + DUCKING</div></div></div>
            <div className="playhead" style={{ left: `${pct}%` }}/>
          </div></div>
        </section>

        <section className="os-bottom-grid">
          <div className="plan-card"><div className="card-head"><span>EDIT PLAN</span><button className="os-btn tiny ghost" onClick={() => setPlan(null)}><RefreshCw size={13}/> Reset</button></div><pre>{JSON.stringify(plan || { status: 'Chưa có plan — hãy upload + chạy AI Agent.' }, null, 2)}</pre></div>
          <div className="scale-card"><div className="card-head"><span>SCALE / MULTI-TENANT</span><CheckCircle2 size={16}/></div><div className="scale-items"><div><b>Workspace isolation</b><span>RLS theo workspace/user</span></div><div><b>Async render queue</b><span>Job status + progress realtime</span></div><div><b>Reusable Skills</b><span>Style riêng cho từng khách hàng</span></div><div><b>Usage metering</b><span>Ghi nhận phút render / AI cost</span></div></div></div>
        </section>
      </main>
    </div>

    <input ref={inputRef} hidden type="file" accept="video/*" onChange={(e) => setVideo(e.target.files?.[0])}/>
    {notice && <div className="os-toast"><Sparkles size={15}/><span>{notice}</span><button onClick={() => setNotice('')}><X size={14}/></button></div>}
    {status === 'rendering' && <div className="render-progress"><div style={{ width: `${progress}%` }}/></div>}

    {authOpen && <div className="modal-backdrop"><form className="auth-modal" onSubmit={doAuth}><button type="button" className="modal-close" onClick={() => setAuthOpen(false)}><X/></button><div className="modal-icon"><UserPlus size={20}/></div><h2>{authMode === 'login' ? 'Đăng nhập GQ AI Editor OS' : 'Tạo tài khoản'}</h2><p>{hasSupabase ? 'Workspace và project sẽ được lưu trên Cloud.' : 'Demo UI: cấu hình Supabase để bật SaaS thật.'}</p><input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="Email" required/><input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="Mật khẩu" minLength={6} required/><button className="agent-run" type="submit">{authMode === 'login' ? 'Đăng nhập' : 'Đăng ký'}</button><button type="button" className="switch-auth" onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}>{authMode === 'login' ? 'Chưa có tài khoản? Đăng ký' : 'Đã có tài khoản? Đăng nhập'}</button></form></div>}
  </div>;
}
