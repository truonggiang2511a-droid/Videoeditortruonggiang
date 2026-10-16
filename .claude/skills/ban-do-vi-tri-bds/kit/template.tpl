<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face { font-family: "BVP"; src: url("assets/fonts/BeVietnamPro-Bold.ttf") format("truetype"); font-weight: 700; }
      @font-face { font-family: "BVP"; src: url("assets/fonts/BeVietnamPro-ExtraBold.ttf") format("truetype"); font-weight: 800; }
      @font-face { font-family: "BVP"; src: url("assets/fonts/BeVietnamPro-Black.ttf") format("truetype"); font-weight: 900; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #04070c; }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: "BVP", Inter, sans-serif; --zi: 1; --tilt: 0deg; background: #04070c; }
      .full { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
      #stage { perspective: 1800px; perspective-origin: 540px 800px; overflow: hidden; }
      #tilt { transform-style: preserve-3d; transform-origin: 540px 900px; }
      #world { position: absolute; left: 0; top: 0; width: %W%px; height: %H%px; transform-origin: 0 0; transform-style: preserve-3d; }
      #world img { position: absolute; display: block; }
      #far { left: %FX%px; top: %FY%px; width: %FW%px; height: %FH%px; filter: saturate(1.05) brightness(0.85); }
      #wide { left: 0; top: 0; width: %W%px; height: %H%px; filter: saturate(1.1) contrast(1.06) brightness(0.88); }
      #detail { left: %DX%px; top: %DY%px; width: %DW%px; height: %DH%px; opacity: 0; filter: saturate(1.1) contrast(1.06) brightness(0.92); }
      svg#lines { position: absolute; left: 0; top: 0; width: %W%px; height: %H%px; overflow: visible; }
      .road { fill: none; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1; stroke-dashoffset: 1; }
      .road.ql1 { stroke: #FF9F1C; stroke-width: calc(10px * var(--zi)); filter: drop-shadow(0 0 calc(8px * var(--zi)) rgba(255,159,28,0.95)); }
      .road.tl { stroke: #2EE6FF; stroke-width: calc(10px * var(--zi)); filter: drop-shadow(0 0 calc(8px * var(--zi)) rgba(46,230,255,0.95)); }
      .road.ct { stroke: #F4F7FB; stroke-width: calc(8px * var(--zi)); filter: drop-shadow(0 0 calc(6px * var(--zi)) rgba(255,255,255,0.85)); }
      .ru, .rg, .rc, .rf { fill: none; stroke-linecap: round; stroke-linejoin: round; }
      .ru, .rg, .rc { stroke-dasharray: 1; stroke-dashoffset: 1; }
      .ru { stroke: rgba(0,0,0,0.6); stroke-width: calc(16px * var(--zi)); }
      .rg { stroke: #FFC23A; stroke-width: calc(30px * var(--zi)); opacity: 0.55; filter: blur(calc(6px * var(--zi))); }
      .rc { stroke: #FFF4C8; stroke-width: calc(8px * var(--zi)); }
      .rf { stroke: #ffffff; stroke-width: calc(5px * var(--zi)); stroke-dasharray: 0.006 0.024; opacity: 0; filter: drop-shadow(0 0 calc(4px * var(--zi)) #fff); }
      .comet { position: absolute; left: 0; top: 0; width: 0; height: 0; opacity: 0; }
      .comet .cc { position: absolute; left: -22px; top: -22px; width: 44px; height: 44px; border-radius: 50%; background: radial-gradient(circle, #ffffff 0 22%, #FFE58A 34%, rgba(255,194,58,0.55) 55%, rgba(255,194,58,0) 72%); transform: scale(var(--zi)) rotateX(calc(-1 * var(--tilt))); }
      /* flat 3D road names: glossy white face over a deep extrusion */
      .roadtxt { position: absolute; transform: translate(-50%, -50%) rotate(var(--a)); white-space: nowrap; font-weight: 900; letter-spacing: 0.03em; line-height: 1; }
      .rti { position: relative; display: inline-block; opacity: 0; }
      .rti .ex { position: absolute; left: 0; top: 0; color: #5b6673; text-shadow: 0 1px 0 #56606c, 0 2px 0 #4f5965, 0 3px 0 #48525d, 0 4px 0 #414a55, 0 5px 0 #3a424c, 0 6px 0 #333b44, 0 7px 0 #2c333b, 0 12px 18px rgba(0,0,0,0.85); }
      .rti .fc { position: relative; display: inline-block; background: linear-gradient(180deg, #ffffff 0%, #ffffff 42%, #d5dde6 58%, #ffffff 100%); -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-stroke: 1.5px rgba(255,255,255,0.6); }
      .roadtxt.q .rti { filter: drop-shadow(0 0 10px rgba(255,159,28,0.9)); }
      .roadtxt.t .rti { filter: drop-shadow(0 0 10px rgba(46,230,255,0.9)); }
      .roadtxt.w .rti { filter: drop-shadow(0 0 8px rgba(255,255,255,0.6)); }
      /* upright, zoom-proof markers */
      .poi, #home { position: absolute; left: 0; top: 0; width: 0; height: 0; will-change: transform; }
      .poi .cs { position: absolute; left: 0; top: 0; }
      .badge { position: absolute; left: -32px; top: -78px; width: 64px; height: 64px; border-radius: 50% 50% 50% 8px; transform: rotate(-45deg) scale(0); border: 4px solid #fff; box-shadow: 0 8px 18px rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; }
      .badge svg { width: 34px; height: 34px; transform: rotate(45deg); }
      .chip { position: absolute; left: 0; top: -96px; background: rgba(8,13,22,0.9); border: 2px solid rgba(255,210,63,0.85); border-radius: 14px; padding: 10px 18px 12px; white-space: nowrap; text-align: center; opacity: 0; }
      .poi.d .chip { top: 22px; }
      .poi.l .chip { top: -46px; left: -44px; }
      .poi.r .chip { top: -46px; left: 44px; }
      .chip b { display: block; color: #fff; font-size: 28px; font-weight: 900; }
      .chip span { display: block; margin-top: 2px; color: #FFD23F; font-size: 24px; font-weight: 800; font-variant-numeric: tabular-nums; }
      
      #home .ringwrap { position: absolute; left: 0; top: 0; }
      #home .ring { position: absolute; left: -100px; top: -100px; width: 200px; height: 200px; border-radius: 50%; border: 6px solid #FFD23F; box-shadow: 0 0 24px rgba(255,210,63,0.8); opacity: 0; }
      #home .mk { position: absolute; left: 0; top: 0; }
      #homemk { position: absolute; left: 0; top: 0; }
      #homemk .drop { position: absolute; left: -46px; top: -124px; width: 92px; height: 124px; filter: drop-shadow(0 10px 14px rgba(0,0,0,0.6)); }
      #hometag { position: absolute; left: 0; top: -150px; transform: translate(-50%, -100%); background: linear-gradient(180deg, #ff2a2f, #c80f14); color: #fff; font-weight: 900; font-size: 42px; padding: 12px 28px 16px; border-radius: 14px; white-space: nowrap; text-align: center; line-height: 1.1; box-shadow: 0 12px 30px rgba(0,0,0,0.55); border: 3px solid rgba(255,255,255,0.85); }
      #hometag small { display: block; margin-top: 4px; font-size: 26px; font-weight: 700; color: #FFE7A6; }
      /* screen-space HUD */
      #title { position: absolute; left: 0; right: 0; top: 330px; text-align: center; }
      #title .k { display: inline-flex; align-items: center; gap: 12px; font-size: 32px; font-weight: 800; letter-spacing: 0.22em; color: #1b1300; background: #FFD23F; padding: 10px 26px 12px; border-radius: 999px; }
      #title .t { margin-top: 26px; font-size: 118px; font-weight: 900; line-height: 1.04; color: #fff; letter-spacing: -0.01em; text-shadow: 0 4px 0 rgba(0,0,0,0.25), 0 10px 40px rgba(0,0,0,0.85); }
      #title .t em { font-style: normal; color: #FFD23F; }
      #title .s { margin-top: 22px; display: inline-block; font-size: 38px; font-weight: 800; color: #fff; background: rgba(8,13,22,0.75); padding: 12px 30px 14px; border-radius: 14px; border: 2px solid rgba(255,255,255,0.25); }
      #tplate { background: radial-gradient(ellipse at 50% 30%, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 60%); }
      .hud { position: absolute; left: 60px; right: 60px; top: 1210px; display: flex; gap: 26px; align-items: center; padding: 26px 30px; background: rgba(8,13,22,0.9); border-radius: 24px; border: 2px solid rgba(255,210,63,0.8); box-shadow: 0 22px 50px rgba(0,0,0,0.6); opacity: 0; }
      .hud .hi { flex: none; width: 120px; height: 120px; border-radius: 22px; display: flex; align-items: center; justify-content: center; border: 3px solid rgba(255,255,255,0.85); }
      .hud .hi svg { width: 72px; height: 72px; }
      .hud .hb { min-width: 0; }
      .hud .hk { font-size: 24px; font-weight: 800; letter-spacing: 0.16em; color: #9fb0c4; }
      .hud .ht { margin-top: 4px; font-size: 54px; font-weight: 900; color: #fff; line-height: 1.08; }
      .hud .hr { margin-top: 8px; display: flex; gap: 22px; align-items: baseline; }
      .hud .hd { font-size: 70px; font-weight: 900; color: #FFD23F; font-variant-numeric: tabular-nums; line-height: 1; }
      .hud .hm { font-size: 36px; font-weight: 800; color: #e9eef5; }
      #summary { position: absolute; left: 50px; right: 50px; top: 980px; padding: 28px 32px 22px; background: rgba(8,13,22,0.92); border-radius: 26px; border: 2px solid rgba(255,210,63,0.85); opacity: 0; box-shadow: 0 22px 50px rgba(0,0,0,0.6); }
      #summary .st { font-size: 46px; font-weight: 900; color: #fff; margin-bottom: 10px; }
      .srow { display: grid; grid-template-columns: 58px 1fr auto auto; gap: 18px; align-items: center; padding: 12px 0; border-top: 1px solid rgba(255,255,255,0.14); }
      .srow i { width: 58px; height: 58px; border-radius: 14px; display: flex; align-items: center; justify-content: center; }
      .srow i svg { width: 34px; height: 34px; }
      .srow span { font-size: 36px; font-weight: 800; color: #eef2f7; }
      .srow b { font-size: 40px; font-weight: 900; color: #FFD23F; font-variant-numeric: tabular-nums; }
      .srow em { font-style: normal; font-size: 30px; font-weight: 700; color: #9fb0c4; min-width: 140px; text-align: right; }
      #note { position: absolute; left: 0; right: 0; bottom: 104px; text-align: center; font-size: 22px; font-weight: 700; color: rgba(255,255,255,0.82); text-shadow: 0 2px 6px rgba(0,0,0,0.9); }
      #credit { position: absolute; left: 0; right: 0; bottom: 72px; text-align: center; font-size: 20px; font-weight: 700; color: rgba(255,255,255,0.72); text-shadow: 0 2px 6px rgba(0,0,0,0.9); }
      #vig { pointer-events: none; background: radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 52%, rgba(0,0,0,0.6) 100%), linear-gradient(180deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 20%, rgba(0,0,0,0) 74%, rgba(0,0,0,0.55) 100%); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="%DUR%" data-width="1080" data-height="1920">
      <div id="stage" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="0">
        <div id="tilt" class="full">
          <div id="world">
            <img id="far" src="assets/far_z14.jpg" alt="" />
            <img id="wide" src="assets/wide_z16.jpg" alt="" />
            <img id="detail" src="assets/detail_z18.jpg" alt="" />
            <svg id="lines" viewBox="0 0 %W% %H%">%ROADS%%ROUTES%</svg>
            %ROADTXT%
            %COMET%
          </div>
        </div>
      </div>
      <div id="vig" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="1"></div>
      <div id="marks" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="3">
            %POIS%
            <div id="home" data-w="%HX%,%HY%">
              <div class="ringwrap"><div class="ring" id="ring1"></div><div class="ring" id="ring2"></div></div>
              <div class="mk"><div id="homemk">
                <svg class="drop" viewBox="0 0 92 124"><defs><linearGradient id="dg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff3a3f"/><stop offset="1" stop-color="#b80c11"/></linearGradient></defs><path d="M46 121 C46 121 5 70 5 44 A41 41 0 0 1 87 44 C87 70 46 121 46 121 Z" fill="url(#dg)" stroke="#fff" stroke-width="5"/><path d="M28 50 L46 34 L64 50 V64 H28 Z" fill="#fff"/><rect x="41" y="52" width="10" height="12" fill="#c80f14"/></svg>
                <div id="hometag">%TAG1%<small>%TAG2%</small></div>
              </div></div>
            </div>
      </div>
      <div id="hudlayer" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="2">
        <div id="tplate" class="full"></div>
        <div id="title"><div class="k">%TK%</div><div class="t">%T1%<br /><em>%T2%</em></div><div class="s">%TSUB%</div></div>
        %HUD%
        <div id="summary"><div class="st">Từ căn nhà đi</div>%SUMMARY%</div>
        <div id="note">Quãng đường theo bản đồ OpenStreetMap · thời gian ô tô ước tính</div>
        <div id="credit">Ảnh vệ tinh: Esri, Maxar · Dữ liệu đường: © OpenStreetMap</div>
      </div>
      %BGM%
      %AUDIO%
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      const root = document.getElementById("root");
      const world = document.getElementById("world");
      const tiltEl = document.getElementById("tilt");
      const CAM = %CAM%;
      const MARKS = Array.from(document.querySelectorAll("[data-w]"));
      MARKS.forEach((el) => { const [x, y] = el.dataset.w.split(",").map(Number); el._wx = x; el._wy = y; });
      const cam = { x: CAM[0][2], y: CAM[0][3], lz: Math.log2(CAM[0][4] * 0.8), t: 18 };
      function apply() {
        const z = Math.pow(2, cam.lz);
        world.style.transform = `translate(${540 - cam.x * z}px, ${900 - cam.y * z}px) scale(${z})`;
        tiltEl.style.transform = `rotateX(${cam.t}deg)`;
        root.style.setProperty("--zi", (1 / z).toFixed(5));
        root.style.setProperty("--tilt", cam.t.toFixed(3) + "deg");
        // project world anchors to the screen with the same math as the CSS camera
        const a = cam.t * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a), PD = 1800;
        for (const el of MARKS) {
          const sx = 540 + (el._wx - cam.x) * z, sy = 900 + (el._wy - cam.y) * z;
          const yr = (sy - 900) * ca + 900, zr = (sy - 900) * sa;
          const k = PD / (PD - zr);
          el.style.transform = `translate(${(540 + (sx - 540) * k).toFixed(1)}px, ${(800 + (yr - 800) * k).toFixed(1)}px)`;
        }
      }
      apply();
      tl.set(cam, { x: CAM[0][2], y: CAM[0][3], lz: Math.log2(CAM[0][4] * 0.8), t: 18, onComplete: apply }, 0);
      CAM.forEach(([t0, d, x, y, z, t]) => {
        tl.to(cam, { x, y, lz: Math.log2(z), t, duration: d, ease: "sine.inOut", onUpdate: apply }, t0);
      });
      // imagery layers
      %LAYERJS%
      // title
      tl.fromTo("#tplate", { opacity: 0 }, { opacity: 1, duration: 0.6 }, 0.2);
      tl.fromTo("#title .k", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, 0.4);
      tl.fromTo("#title .t", { opacity: 0, scale: 1.25, filter: "blur(10px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.7, ease: "power4.out" }, 0.8);
      tl.fromTo("#title .s", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, 1.4);
      tl.to(["#title", "#tplate"], { opacity: 0, y: -40, duration: 0.6, ease: "power2.in" }, 4.6);
      // home
      tl.fromTo("#homemk", { y: -300, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: "bounce.out" }, %HOMEIN%);
      const ringPulse = (t) => tl.fromTo(["#ring1", "#ring2"], { opacity: 0.95, scale: 0.15 }, { opacity: 0, scale: 1.7, duration: 1.8, ease: "power2.out", stagger: 0.6, immediateRender: false }, t);
      ringPulse(%HOMEIN% + 0.7); ringPulse(%BACK% + 1.2);
      tl.to("#hometag", { opacity: 0, duration: 0.5 }, %TAGOUT%);
      // routes: slow draw with a glowing comet riding the tip
      // chip offsets live in GSAP (xPercent/yPercent) so the slide-in tween never wipes them
      const SIDEP = { u: [-50, -100], d: [-50, 0], l: [-100, -50], r: [0, -50] };
      document.querySelectorAll(".poi").forEach((p) => {
        const sd = ["u", "d", "l", "r"].find((k) => p.classList.contains(k)) || "u";
        gsap.set(p.querySelector(".chip"), { xPercent: SIDEP[sd][0], yPercent: SIDEP[sd][1] });
      });
      const STOPS = %STOPS%;
      const SAMP = %SAMPLES%;
      STOPS.forEach(([t0, d, h0, h1], i) => {
        const P = SAMP[i], n = P.length - 1, prog = { p: 0 };
        const segs = ["#ru" + i, "#rg" + i, "#rc" + i].map((s) => document.querySelector(s));
        const cm = document.getElementById("cm" + i);
        const draw = () => {
          const f = prog.p * n, k = Math.min(n - 1, Math.floor(f)), r = f - k;
          const x = P[k][0] + (P[k + 1][0] - P[k][0]) * r, y = P[k][1] + (P[k + 1][1] - P[k][1]) * r;
          cm.style.transform = `translate(${x}px, ${y}px)`;
          segs.forEach((el) => (el.style.strokeDashoffset = (1 - prog.p).toFixed(5)));
        };
        tl.set(cm, { opacity: 1 }, t0);
        tl.to(prog, { p: 1, duration: d, ease: "sine.inOut", onUpdate: draw }, t0);
        tl.to(cm, { opacity: 0, duration: 0.4 }, t0 + d);
        // energy flow along the active route
        const flowEnd = i + 1 < STOPS.length ? STOPS[i + 1][0] : %DUR%;
        tl.set("#rf" + i, { opacity: 0.9 }, t0 + d);
        tl.fromTo("#rf" + i, { strokeDashoffset: 0 }, { strokeDashoffset: -(flowEnd - t0 - d) * 0.08, duration: flowEnd - t0 - d, ease: "none" }, t0 + d);
        if (i + 1 < STOPS.length) {
          tl.to("#rf" + i, { opacity: 0, duration: 0.5 }, flowEnd);
          tl.to(["#rg" + i, "#rc" + i], { opacity: 0.4, duration: 0.8 }, flowEnd);
        }
        // marker
        tl.fromTo("#b" + i, { scale: 0, rotation: -45 }, { scale: 1, rotation: -45, duration: 0.6, ease: "back.out(2.2)" }, t0 + d);
        tl.fromTo("#c" + i, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.45, ease: "power3.out" }, t0 + d + 0.2);
        const cardOut = h1 != null ? h1 : t0 + d + 3.2;
        tl.to("#c" + i, { opacity: 0, duration: 0.4 }, cardOut);
        if (h0 != null) {
          tl.fromTo("#h" + i, { opacity: 0, y: 70 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, h0);
          tl.to("#h" + i, { opacity: 0, y: 30, duration: 0.45, ease: "power2.in" }, h1 - 0.45);
        }
      });
      // road highlights + glossy flat road names
      %ROADJS%
      // summary
      tl.fromTo("#summary", { opacity: 0, y: 70 }, { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" }, %SUMT%);
      tl.to({}, { duration: 0.01 }, %DUR% - 0.01);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
