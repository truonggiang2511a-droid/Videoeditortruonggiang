#!/usr/bin/env python3
"""Flycam marking clips as HyperFrames projects: tracked red pin + ground ring + glass card / tag with leader line.

    python3 flymark/build.py            # builds every clip in CLIPS into flymark/<name>/index.html
Tracks come from work/track.py (per-frame [x, y] of a ground point on the 1080x1920 30fps proxy).
"""
import json, os, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(ROOT)
FPS = 30
HOOKV = f"{P}/hook"

# shots: (proxy, in, dur); marks: tracked markers with local start times
CLIPS = {
 "m0316": {"shots": [("DJI_0316_1080", 10.0, 7.0)],
           "marks": [{"kind": "pin", "track": "trk316", "shot": 0, "t": 0.35, "small": "LÔ ĐẤT", "big": "5M × 15M"},
                     {"kind": "card", "t": 0.9, "small": "TRỤC ĐƯỜNG D3", "big": "RỘNG 13M", "ribbon": "LÒNG ĐƯỜNG 6M • VỈA HÈ 3,5M"}]},
 "m0256": {"shots": [("DJI_0256_1080", 13.0, 4.2)],
           "marks": [{"kind": "pin", "track": "trk256", "shot": 0, "t": 0.3, "small": "LÔ ĐẤT", "big": "THE SOL CITY"},
                     {"kind": "card", "t": 0.7, "small": "CÁCH CHỢ HƯNG LONG", "big": "500M", "ribbon": "GIÁP RANH HƯNG LONG • BÌNH CHÁNH"}]},
 "m_tienich": {"shots": [("DJI_0242_1080", 0.2, 2.0), ("DJI_0245_1080", 0.5, 2.5), ("DJI_0241_1080", 3.0, 1.8)],
               "title": "TIỆN ÍCH NỘI KHU",
               "marks": [{"kind": "tag", "track": "trk242_pool", "shot": 0, "t": 0.9, "text": "HỒ BƠI", "dy": -330},
                         {"kind": "tag", "track": "trk245_pond", "shot": 1, "t": 0.15, "text": "CÔNG VIÊN", "dy": -260},
                         {"kind": "tag", "track": "trk245_pitch", "shot": 1, "t": 0.55, "text": "SÂN BÓNG", "dy": -330}]},
}

TPL = r"""<!doctype html>
<html lang="vi">
<head>
<meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<script src="assets/vendor/gsap.min.js"></script>
<style>
@font-face { font-family: "BVP"; src: url("assets/fonts/BeVietnamPro-ExtraBold.ttf"); font-weight: 800; }
@font-face { font-family: "BVP"; src: url("assets/fonts/BeVietnamPro-Black.ttf"); font-weight: 900; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: #000; }
#root { position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: "BVP", sans-serif; }
.full { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
video.full { object-fit: cover; }
#fx { pointer-events: none; }
.mk { position: absolute; left: 0; top: 0; width: 0; height: 0; will-change: transform; }
.ring { position: absolute; left: -95px; top: -32px; width: 190px; height: 64px; border-radius: 50%; border: 5px solid #FFD400; box-shadow: 0 0 22px rgba(255,212,0,0.9), inset 0 0 18px rgba(255,212,0,0.6); opacity: 0; }
.ring.r2 { border-color: #fff; box-shadow: 0 0 18px rgba(255,255,255,0.8); }
.pin { position: absolute; left: -48px; top: -132px; width: 96px; height: 132px; opacity: 0; filter: drop-shadow(0 12px 14px rgba(0,0,0,0.55)); }
.ptag { position: absolute; left: 0; top: -158px; white-space: nowrap; text-align: center; opacity: 0;
  background: rgba(10,14,24,0.86); border: 3px solid #FFD400; border-radius: 16px; padding: 10px 22px 12px; }
.ptag b { display: block; font-size: 26px; font-weight: 800; letter-spacing: 0.14em; color: #FFD400; }
.ptag i { display: block; font-style: normal; font-size: 46px; font-weight: 900; color: #fff; line-height: 1.05; }
.card { position: absolute; left: 70px; right: 70px; top: 330px; padding: 26px 30px 0; border-radius: 26px; text-align: center; opacity: 0;
  background: linear-gradient(180deg, rgba(14,18,34,0.9), rgba(10,12,24,0.92));
  border: 3px solid transparent; background-clip: padding-box; box-shadow: 0 0 0 3px #3DE2FF, 0 0 34px rgba(61,226,255,0.55), 0 0 60px rgba(139,92,255,0.45), 0 24px 50px rgba(0,0,0,0.55); overflow: hidden; }
.card .s { font-size: 34px; font-weight: 800; letter-spacing: 0.16em; color: #9fe9ff; }
.card .b { margin-top: 2px; font-size: 118px; font-weight: 900; line-height: 1.02; color: #fff; letter-spacing: -0.01em; text-shadow: 0 6px 24px rgba(0,0,0,0.5); }
.card .rb { margin: 18px -30px 0; padding: 14px 20px 16px; background: #FFD400; color: #14110a; font-size: 32px; font-weight: 900; letter-spacing: 0.04em; }
.tag { position: absolute; left: 0; top: 0; white-space: nowrap; opacity: 0;
  background: rgba(10,14,24,0.88); border: 3px solid #3DE2FF; box-shadow: 0 0 24px rgba(61,226,255,0.6); border-radius: 18px; padding: 12px 30px 14px;
  font-size: 58px; font-weight: 900; color: #fff; }
.lead { position: absolute; left: 0; top: 0; width: 4px; background: linear-gradient(#3DE2FF, #FFD400); transform-origin: 50% 0; opacity: 0; }
.dot { position: absolute; left: -14px; top: -14px; width: 28px; height: 28px; border-radius: 50%; background: #FFD400; border: 4px solid #fff; box-shadow: 0 0 18px #FFD400; opacity: 0; }
#title { position: absolute; left: 0; right: 0; top: 300px; text-align: center; opacity: 0; }
#title span { display: inline-block; font-size: 64px; font-weight: 900; color: #fff; background: rgba(10,14,24,0.82); border-bottom: 8px solid #FFD400; padding: 16px 40px 18px; border-radius: 14px; letter-spacing: 0.04em; }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="%DUR%" data-width="1080" data-height="1920">
%VIDEOS%
<div id="fx" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="5">
%MARKS%
%TITLE%
</div>
%AUDIO%
</div>
<script>
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
const FPS = 30, SHOTS = %SHOTS%, TR = %TRACKS%, MARKS = %MARKJS%;
const els = MARKS.map((m, i) => document.getElementById("m" + i));
const lead = MARKS.map((m, i) => document.getElementById("l" + i));
const tags = MARKS.map((m, i) => document.getElementById("g" + i));
const clock = { t: 0 };
gsap.set(".tag, .ptag", { xPercent: -50, yPercent: -100 });
function place() {
  const t = clock.t;
  MARKS.forEach((m, i) => {
    if (m.kind === "card") return;
    const sh = SHOTS[m.shot], lt = t - sh.at;
    const vis = lt >= 0 && lt < sh.dur;
    els[i].style.display = vis ? "block" : "none";
    if (lead[i]) { lead[i].style.display = els[i].style.display; tags[i].style.display = els[i].style.display; }
    if (!vis) return;
    const tr = TR[m.track], f = Math.min(tr.length - 1, Math.max(0, Math.round((sh.in + lt) * FPS)));
    const [x, y] = tr[f];
    els[i].style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
    if (m.kind === "tag") {
      const ty = Math.max(470, Math.min(1480, y + m.dy)), tx = Math.max(230, Math.min(850, x));
      tags[i].style.left = tx + "px"; tags[i].style.top = ty + "px";
      lead[i].style.left = (x - 2) + "px"; lead[i].style.top = ty + "px"; lead[i].style.height = Math.max(0, y - ty - 14) + "px";
    }
  });
}
tl.to(clock, { t: %DUR%, duration: %DUR%, ease: "none", onUpdate: place }, 0);
MARKS.forEach((m, i) => {
  const t0 = m.t + SHOTS[m.shot || 0].at;
  if (m.kind === "pin") {
    tl.fromTo(`#m${i} .pin`, { y: -260, opacity: 0 }, { y: 0, opacity: 1, duration: 0.7, ease: "bounce.out" }, t0);
    [0, 1.1, 2.2, 3.3, 4.4, 5.5].forEach((d) => { if (t0 + 0.55 + d < %DUR% - 0.3) tl.fromTo(`#m${i} .ring`, { scale: 0.3, opacity: 0.95 }, { scale: 1.9, opacity: 0, duration: 1.4, ease: "power2.out", stagger: 0.35, immediateRender: false }, t0 + 0.55 + d); });
    tl.fromTo(`#m${i} .ptag`, { opacity: 0, y: 24, scale: 0.85 }, { opacity: 1, y: 0, scale: 1, duration: 0.45, ease: "back.out(1.8)" }, t0 + 0.45);
  } else if (m.kind === "card") {
    tl.fromTo(`#m${i}`, { opacity: 0, y: -40, scale: 0.92 }, { opacity: 1, y: 0, scale: 1, duration: 0.55, ease: "power3.out" }, t0);
    tl.fromTo(`#m${i} .rb`, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.5, ease: "power2.out" }, t0 + 0.35);
    tl.to(`#m${i}`, { opacity: 0, y: -30, duration: 0.35, ease: "power2.in" }, %DUR% - 0.4);
  } else {
    const end = SHOTS[m.shot].at + SHOTS[m.shot].dur;
    tl.fromTo(`#m${i} .dot`, { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.5)" }, t0);
    tl.fromTo(`#l${i}`, { scaleY: 0, opacity: 0 }, { scaleY: 1, opacity: 1, duration: 0.3, ease: "power2.out" }, t0 + 0.1);
    tl.fromTo(`#g${i}`, { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }, t0 + 0.25);
    tl.to([`#g${i}`, `#l${i}`, `#m${i} .dot`], { opacity: 0, duration: 0.2 }, end - 0.2);
  }
});
if (document.getElementById("title")) {
  tl.fromTo("#title", { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.45, ease: "power3.out" }, 0.1);
  tl.to("#title", { opacity: 0, duration: 0.3 }, %DUR% - 0.35);
}
place();
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""

PIN = ('<svg class="pin" viewBox="0 0 96 132"><defs><linearGradient id="pg%d" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff4146"/><stop offset="1" stop-color="#c50d12"/></linearGradient></defs>'
       '<path d="M48 129 C48 129 6 76 6 47 A42 42 0 0 1 90 47 C90 76 48 129 48 129 Z" fill="url(#pg%d)" stroke="#fff" stroke-width="5"/>'
       '<circle cx="48" cy="46" r="16" fill="#fff"/></svg>')


def build(name, c):
    d = f"{ROOT}/{name}"; os.makedirs(f"{d}/assets/vendor", exist_ok=True); os.makedirs(f"{d}/assets/fonts", exist_ok=True); os.makedirs(f"{d}/assets/sfx", exist_ok=True)
    for f in ("hyperframes.json", "package.json", "CLAUDE.md", "AGENTS.md"): shutil.copy(f"{HOOKV}/{f}", d)
    json.dump({"id": f"fly-{name}", "name": f"fly-{name}"}, open(f"{d}/meta.json", "w"))
    shutil.copy(f"{HOOKV}/assets/vendor/gsap.min.js", f"{d}/assets/vendor/")
    for f in ("ExtraBold", "Black"): shutil.copy(f"{P}/../../ea_video/kit/fonts/BeVietnamPro-{f}.ttf", f"{d}/assets/fonts/")
    for s in ("pop", "whoosh", "chime"):
        src = f"{P}/../vi-tri-nha-vuon-phuoc-ly/assets/sfx/{s}.wav"
        if os.path.exists(src): shutil.copy(src, f"{d}/assets/sfx/")
    shots, at, vids = [], 0.0, []
    for k, (prox, tin, dur) in enumerate(c["shots"]):
        out = f"{d}/assets/shot{k}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(tin), "-i", f"{P}/work/fly/{prox}.mp4", "-t", str(dur), "-c:v", "libx264", "-crf", "14", "-preset", "veryfast", "-an", out], check=True)
        vids.append(f'<video id="v{k}" class="full clip" src="assets/shot{k}.mp4" data-start="{at:.2f}" data-media-start="0" data-duration="{dur}" data-track-index="0" muted playsinline></video>')
        shots.append({"at": at, "in": 0.0, "dur": dur, "src_in": tin}); at += dur
    DUR = round(at, 2)
    tracks = {}
    for m in c["marks"]:
        if "track" in m:
            tr = json.load(open(f"{P}/work/{m['track']}.json"))["pts"]
            sh = shots[m["shot"]]; f0 = round(sh["src_in"] * FPS)
            tracks[m["track"]] = tr[f0: f0 + round(sh["dur"] * FPS) + 2]
    marks_html, mj = [], []
    for i, m in enumerate(c["marks"]):
        mm = {"kind": m["kind"], "t": m["t"], "shot": m.get("shot", 0), "track": m.get("track"), "dy": m.get("dy", -300)}
        if m["kind"] == "pin":
            marks_html.append(f'<div class="mk" id="m{i}"><div class="ring"></div><div class="ring r2"></div>{PIN % (i, i)}<div class="ptag"><b>{m["small"]}</b><i>{m["big"]}</i></div></div>')
        elif m["kind"] == "card":
            marks_html.append(f'<div class="card" id="m{i}"><div class="s">{m["small"]}</div><div class="b">{m["big"]}</div><div class="rb">{m["ribbon"]}</div></div>')
        else:
            marks_html.append(f'<div class="mk" id="m{i}"><div class="dot"></div></div><div class="lead" id="l{i}"></div><div class="tag" id="g{i}">{m["text"]}</div>')
        mj.append(mm)
    audio = []
    for i, m in enumerate(c["marks"]):
        t0 = m["t"] + shots[m.get("shot", 0)]["at"]
        audio.append(f'<audio id="a{i}" class="clip" src="assets/sfx/{"chime" if m["kind"] == "card" else "pop"}.wav" data-start="{t0 + (0.45 if m["kind"] == "pin" else 0):.2f}" data-duration="1.2" data-track-index="{8 + i}" data-volume="0.55"></audio>')
    html = TPL
    rep = {"%DUR%": str(DUR), "%VIDEOS%": "\n".join(vids), "%MARKS%": "\n".join(marks_html),
           "%TITLE%": f'<div id="title"><span>{c["title"]}</span></div>' if c.get("title") else "",
           "%AUDIO%": "\n".join(audio), "%SHOTS%": json.dumps(shots), "%TRACKS%": json.dumps(tracks), "%MARKJS%": json.dumps(mj)}
    for k, v in rep.items(): html = html.replace(k, v)
    open(f"{d}/index.html", "w", encoding="utf-8").write(html)
    print(name, DUR, "s")


if __name__ == "__main__":
    import sys
    for n in (sys.argv[1:] or CLIPS):
        build(n, CLIPS[n])
