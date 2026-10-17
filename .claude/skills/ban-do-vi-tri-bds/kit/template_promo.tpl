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
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: "BVP", sans-serif; --zi: 1; --tilt: 0deg; --rot: 0deg; background: #04070c; }
      .full { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
      #stage { perspective: 1800px; perspective-origin: 540px 800px; overflow: hidden; }
      #tilt { transform-style: preserve-3d; transform-origin: 540px 900px; }
      #world { position: absolute; left: 0; top: 0; width: %W%px; height: %H%px; transform-origin: 0 0; transform-style: preserve-3d; }
      #world img { position: absolute; display: block; }
      #outer { left: %OX%px; top: %OY%px; width: %OWN%px; height: %OHN%px; transform-origin: 0 0; transform: scale(%OS%); filter: saturate(1.1) brightness(0.85) contrast(1.05); }
      #far { left: %FX%px; top: %FY%px; width: %FW%px; height: %FH%px; filter: saturate(1.08) brightness(0.86) contrast(1.05); }
      #wide { left: 0; top: 0; width: %W%px; height: %H%px; opacity: 0; filter: saturate(1.15) contrast(1.08) brightness(0.9); }
      #detail { left: %DX%px; top: %DY%px; width: %DW%px; height: %DH%px; opacity: 0; filter: saturate(1.12) contrast(1.06) brightness(0.94); }
      svg#lines { position: absolute; left: 0; top: 0; width: %W%px; height: %H%px; overflow: visible; }
      /* administrative areas: tinted fill, inner glow, bright outline */
      .reg { opacity: 0; }
      .rfill { stroke: none; }
      .redge { fill: none; stroke: var(--edge); stroke-width: calc(40px * var(--zi)); opacity: 0.7; filter: blur(calc(9px * var(--zi))); }
      .rline { fill: none; stroke: #ffffff; stroke-width: calc(4px * var(--zi)); stroke-dasharray: 1; stroke-dashoffset: 1; filter: drop-shadow(0 0 calc(6px * var(--zi)) var(--edge)); }
      /* the city boundary: hot glow + white core + running dashes */
      .bu, .bg, .bc, .bf { fill: none; stroke-linecap: round; stroke-linejoin: round; }
      .bu, .bg, .bc { stroke-dasharray: 1; stroke-dashoffset: 1; }
      .bu { stroke: rgba(0,0,0,0.6); stroke-width: calc(16px * var(--zi)); }
      .bg { stroke: #FF2E63; stroke-width: calc(30px * var(--zi)); opacity: 0.6; filter: blur(calc(6px * var(--zi))); }
      .bc { stroke: #FFE3EA; stroke-width: calc(7px * var(--zi)); }
      .bf { stroke: #FF2E63; stroke-width: calc(7px * var(--zi)); stroke-dasharray: 0.004 0.008; opacity: 0; }
      /* main axes: glow + bright core + moving dashes */
      .road path { fill: none; stroke-linecap: round; stroke-linejoin: round; }
      .rgl { stroke: var(--rc); stroke-width: calc(26px * var(--zi)); opacity: 0.5; filter: blur(calc(6px * var(--zi))); stroke-dasharray: 1; stroke-dashoffset: 1; }
      .rco { stroke: var(--rc); stroke-width: calc(8px * var(--zi)); stroke-dasharray: 1; stroke-dashoffset: 1; filter: drop-shadow(0 0 calc(5px * var(--zi)) var(--rc)); }
      .rda { stroke: #ffffff; stroke-width: calc(4px * var(--zi)); stroke-dasharray: calc(26px * var(--zi)) calc(22px * var(--zi)); opacity: 0; }
      /* access line from the house */
      #acc path { fill: none; stroke-linecap: round; stroke-dasharray: 1; stroke-dashoffset: 1; }
      .ag { stroke: #FFC23A; stroke-width: calc(28px * var(--zi)); opacity: 0.6; filter: blur(calc(6px * var(--zi))); }
      .ac { stroke: #FFE58A; stroke-width: calc(9px * var(--zi)); filter: drop-shadow(0 0 calc(6px * var(--zi)) #FFC23A); }
      .comet { position: absolute; left: 0; top: 0; width: 0; height: 0; opacity: 0; }
      .comet .cc { position: absolute; left: -24px; top: -24px; width: 48px; height: 48px; border-radius: 50%; transform: scale(var(--zi)); background: radial-gradient(circle, #ffffff 0 22%, #FF8FAE 36%, rgba(255,46,99,0.55) 55%, rgba(255,46,99,0) 72%); }
      /* flat 3D names lying on the ground (kept from the v3 style) */
      .flat { position: absolute; transform: translate(-50%, -50%) rotate(var(--a)); white-space: nowrap; font-weight: 900; letter-spacing: 0.03em; line-height: 1; text-align: center; }
      .rti { position: relative; display: inline-block; opacity: 0; }
      .rti small { display: inline-block; font-size: 0.42em; letter-spacing: 0.12em; margin-top: 0.12em; }
      .rti .ex { position: absolute; left: 0; top: 0; color: #5b6673; text-shadow: 0 0.012em 0 #56606c, 0 0.024em 0 #4f5965, 0 0.036em 0 #48525d, 0 0.048em 0 #414a55, 0 0.06em 0 #3a424c, 0 0.072em 0 #333b44, 0 0.084em 0 #2c333b, 0 0.14em 0.2em rgba(0,0,0,0.85); }
      .rti .fc { position: relative; display: inline-block; background: linear-gradient(180deg, #ffffff 0%, #ffffff 42%, #d5dde6 58%, #ffffff 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
      .flat.c .rti .fc { background-image: linear-gradient(180deg, #ffffff 0%, #E6FCFF 40%, #7EEBFF 60%, #ffffff 100%); }
      .flat.g .rti .fc { background-image: linear-gradient(180deg, #ffffff 0%, #EFFFF4 40%, #8DF5B4 60%, #ffffff 100%); }
      .flat.y .rti .fc { background-image: linear-gradient(180deg, #FFFBE6 0%, #FFE58A 45%, #FFC23A 60%, #FFF4C8 100%); }
      .flat.c .rti { filter: drop-shadow(0 0 0.08em rgba(46,230,255,0.95)); }
      .flat.g .rti { filter: drop-shadow(0 0 0.08em rgba(59,240,138,0.9)); }
      .flat.y .rti { filter: drop-shadow(0 0 0.1em rgba(255,194,58,0.95)); }
      .flat.q .rti { filter: drop-shadow(0 0 0.1em rgba(255,176,32,0.95)); }
      .flat.t .rti { filter: drop-shadow(0 0 0.1em rgba(46,230,255,0.95)); }
      .flat.w .rti { filter: drop-shadow(0 0 0.1em rgba(255,79,216,0.9)); }
      /* upright screen-space markers */
      .poi, #home { position: absolute; left: 0; top: 0; width: 0; height: 0; will-change: transform; }
      .stem { position: absolute; left: -2px; top: 0; width: 4px; transform-origin: 2px 0; }
      .stem i { display: block; width: 4px; height: 100%; transform-origin: 50% 0; background: linear-gradient(180deg, #ffffff, rgba(255,255,255,0.65)); box-shadow: 0 0 8px rgba(255,255,255,0.8); }
      .badge { position: absolute; left: -28px; top: -28px; width: 56px; height: 56px; border-radius: 14px; background: rgba(10,14,24,0.92); border: 3px solid var(--c); box-shadow: 0 0 16px var(--c), 0 8px 16px rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; transform: scale(0); }
      .badge svg { width: 32px; height: 32px; }
      .badge.flagb { border-radius: 50% 50% 50% 8px; left: -32px; top: -78px; width: 64px; height: 64px; background: var(--c); border-color: #fff; }
      .badge.flagb svg { transform: rotate(45deg); }
      .card { position: absolute; width: 270px; background: rgba(8,12,22,0.95); border: 3px solid #ffffff; border-radius: 16px; overflow: hidden; opacity: 0; box-shadow: 0 0 22px rgba(46,230,255,0.55), 0 16px 30px rgba(0,0,0,0.6); }
      .card .ph { position: relative; height: 160px; overflow: hidden; }
      .card .ph img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .card .ph i { position: absolute; right: 8px; bottom: 6px; font-style: normal; font-size: 15px; font-weight: 800; letter-spacing: 0.08em; color: rgba(255,255,255,0.85); text-shadow: 0 1px 3px #000; }
      .card b { display: block; padding: 10px 12px 0; font-size: 27px; font-weight: 900; color: #fff; line-height: 1.12; text-align: center; }
      .card span { display: block; padding: 4px 10px 12px; font-size: 26px; font-weight: 800; color: #FFD23F; text-align: center; }
      .chipx { position: absolute; left: 0; top: -110px; transform: translate(-50%, -100%); white-space: nowrap; text-align: center; background: rgba(8,13,22,0.94); border: 3px solid #FF2E63; border-radius: 16px; padding: 12px 24px 14px; opacity: 0; box-shadow: 0 0 22px rgba(255,46,99,0.55), 0 12px 26px rgba(0,0,0,0.55); }
      .chipx b { display: block; font-size: 34px; font-weight: 900; color: #fff; }
      .chipx span { display: block; font-size: 30px; font-weight: 800; color: #FFD23F; }
      /* the house: drop pin, label box, ripples */
      #home .rip { position: absolute; left: -140px; top: -140px; width: 280px; height: 280px; border-radius: 50%; border: 7px solid #2EE6FF; box-shadow: 0 0 22px rgba(46,230,255,0.9), inset 0 0 18px rgba(46,230,255,0.6); opacity: 0; }
      #home .rip.r2 { border-color: #FFD23F; box-shadow: 0 0 22px rgba(255,210,63,0.9); }
      #homemk { position: absolute; left: 0; top: 0; }
      #homemk .drop { position: absolute; left: -40px; top: -108px; width: 80px; height: 108px; filter: drop-shadow(0 10px 14px rgba(0,0,0,0.6)); }
      #hlabel { position: absolute; left: 0; top: -124px; transform: translate(-50%, -100%); white-space: nowrap; padding: 10px 22px 12px; border-radius: 10px; background: linear-gradient(180deg, rgba(10,20,36,0.95), rgba(6,12,24,0.95)); border: 3px solid #2EE6FF; box-shadow: 0 0 0 0 #2EE6FF, 0 0 18px rgba(46,230,255,0.6); font-size: 34px; font-weight: 900; font-style: italic; letter-spacing: 0.04em; color: #FFE24A; text-align: center; opacity: 0; }
      #hlabel small { display: block; font-style: normal; font-size: 22px; font-weight: 700; color: #cfe9ff; letter-spacing: 0.02em; }
      /* screen text */
      #title { position: absolute; left: 0; right: 0; top: 330px; text-align: center; }
      #title .k { display: inline-block; font-size: 32px; font-weight: 800; letter-spacing: 0.22em; color: #1b1300; background: #FFD23F; padding: 10px 26px 12px; border-radius: 999px; }
      #title .t { margin-top: 24px; font-size: 104px; font-weight: 900; line-height: 1.06; color: #fff; text-shadow: 0 4px 0 rgba(0,0,0,0.25), 0 10px 40px rgba(0,0,0,0.85); }
      #title .t em { font-style: normal; color: #2EE6FF; }
      #title .s { margin-top: 22px; display: inline-block; font-size: 38px; font-weight: 800; color: #fff; background: rgba(8,13,22,0.78); padding: 12px 30px 14px; border-radius: 14px; border: 2px solid rgba(255,255,255,0.25); }
      #tplate { background: radial-gradient(ellipse at 50% 28%, rgba(0,0,0,0.62) 0%, rgba(0,0,0,0) 62%); }
      #slogan { position: absolute; left: 40px; right: 40px; top: 330px; text-align: center; font-style: italic; font-weight: 900; color: #FFE24A; text-shadow: 0 3px 0 #6b3a00, 0 0 24px rgba(0,0,0,0.9), 0 6px 22px rgba(0,0,0,0.9); }
      #slogan .l1, #slogan .l2 { display: block; font-size: 46px; line-height: 1.22; white-space: nowrap; letter-spacing: -0.01em; }
      #splate { background: linear-gradient(180deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.45) 24%, rgba(0,0,0,0) 40%); opacity: 0; }
      #cta { position: absolute; left: 0; right: 0; top: 1180px; text-align: center; }
      #cta .c1 { display: inline-block; font-size: 76px; font-weight: 900; font-style: italic; color: #FFE24A; -webkit-text-stroke: 3px #7a1a00; paint-order: stroke fill; text-shadow: 0 6px 0 #7a1a00, 0 0 30px rgba(0,0,0,0.9); }
      #cta .c2 { display: inline-block; margin-top: 16px; padding: 12px 30px 14px; background: linear-gradient(180deg, #E8202A, #A80D14); border-radius: 14px; font-size: 50px; font-weight: 900; font-style: italic; color: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.6); border: 3px solid rgba(255,255,255,0.85); }
      #note { position: absolute; left: 0; right: 0; bottom: 104px; text-align: center; font-size: 21px; font-weight: 700; color: rgba(255,255,255,0.8); text-shadow: 0 2px 6px rgba(0,0,0,0.9); }
      #credit { position: absolute; left: 0; right: 0; bottom: 74px; text-align: center; font-size: 19px; font-weight: 700; color: rgba(255,255,255,0.7); text-shadow: 0 2px 6px rgba(0,0,0,0.9); }
      #vig { pointer-events: none; background: radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 54%, rgba(0,0,0,0.58) 100%), linear-gradient(180deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 76%, rgba(0,0,0,0.5) 100%); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="%DUR%" data-width="1080" data-height="1920">
      <div id="stage" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="0">
        <div id="tilt" class="full">
          <div id="world">
            <img id="outer" src="assets/outer_z12.jpg" alt="" />
            <img id="far" src="assets/far_z14.jpg" alt="" />
            <img id="wide" src="assets/wide_z16.jpg" alt="" />
            <img id="detail" src="assets/detail_z18.jpg" alt="" />
            <svg id="lines" viewBox="0 0 %W% %H%">%SVG%</svg>
            %LABELS%
            <div class="comet" id="cm_nA"><div class="cc"></div></div>
            <div class="comet" id="cm_nB"><div class="cc"></div></div>
          </div>
        </div>
      </div>
      <div id="vig" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="1"></div>
      <div id="marks" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="3">
        %CARDS%
        <div id="home" data-w="%HX%,%HY%">
          <div class="rip"></div><div class="rip r2"></div><div class="rip"></div>
          <div id="homemk">
            <svg class="drop" viewBox="0 0 92 124"><defs><linearGradient id="dg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff3a3f"/><stop offset="1" stop-color="#b80c11"/></linearGradient></defs><path d="M46 121 C46 121 5 70 5 44 A41 41 0 0 1 87 44 C87 70 46 121 46 121 Z" fill="url(#dg)" stroke="#fff" stroke-width="5"/><path d="M28 50 L46 34 L64 50 V64 H28 Z" fill="#fff"/><rect x="41" y="52" width="10" height="12" fill="#c80f14"/></svg>
            <div id="hlabel">%HTAG%</div>
          </div>
        </div>
      </div>
      <div id="hudlayer" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="2">
        <div id="tplate" class="full"></div>
        <div id="title"><div class="k">%TK%</div><div class="t">%T1%<br /><em>%T2%</em></div><div class="s">%TSUB%</div></div>
        <div id="splate" class="full"></div>
        <div id="slogan"><span class="l1">“%SL1%</span><span class="l2">%SL2%”</span></div>
        <div id="cta"><div class="c1">%CTA1%</div><br /><div class="c2">%CTA2%</div></div>
        <div id="note">%NOTE%</div>
        <div id="credit">Ảnh vệ tinh: Esri, Maxar · Dữ liệu: © OpenStreetMap</div>
      </div>
      %AUDIO%
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      const root = document.getElementById("root"), world = document.getElementById("world"), tiltEl = document.getElementById("tilt");
      const CAM = %CAM%, SAMP = %SAMP%, DUR = %DUR%;
      const MARKS = Array.from(document.querySelectorAll("[data-w]"));
      MARKS.forEach((el) => { const [x, y] = el.dataset.w.split(",").map(Number); el._wx = x; el._wy = y; });
      const cam = { x: CAM[0][2], y: CAM[0][3], lz: Math.log2(CAM[0][4]), t: CAM[0][5], r: CAM[0][6] };
      // camera: pan (x, y), zoom (lz), tilt (t) and orbit (r) around the screen centre
      function apply() {
        const z = Math.pow(2, cam.lz);
        world.style.transform = `translate(540px, 900px) rotate(${cam.r}deg) scale(${z}) translate(${-cam.x}px, ${-cam.y}px)`;
        tiltEl.style.transform = `rotateX(${cam.t}deg)`;
        root.style.setProperty("--zi", (1 / z).toFixed(5));
        const a = cam.t * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a), PD = 1800;
        const rr = cam.r * Math.PI / 180, cr = Math.cos(rr), sr = Math.sin(rr);
        for (const el of MARKS) {
          const dx = (el._wx - cam.x) * z, dy = (el._wy - cam.y) * z;
          const sx = 540 + dx * cr - dy * sr, sy = 900 + dx * sr + dy * cr;
          const yr = (sy - 900) * ca + 900, zr = (sy - 900) * sa, k = PD - zr > 50 ? PD / (PD - zr) : 36;
          el.style.transform = `translate(${(540 + (sx - 540) * k).toFixed(1)}px, ${(800 + (yr - 800) * k).toFixed(1)}px)`;
        }
      }
      apply();
      tl.set(cam, { x: CAM[0][2], y: CAM[0][3], lz: Math.log2(CAM[0][4]), t: CAM[0][5], r: CAM[0][6], onComplete: apply }, 0);
      CAM.slice(1).forEach(([t0, d, x, y, z, t, r]) => tl.to(cam, { x, y, lz: Math.log2(z), t, r, duration: d, ease: "sine.inOut", onUpdate: apply }, t0));
      document.querySelectorAll(".card").forEach((c) => gsap.set(c, { xPercent: -50, yPercent: c.classList.contains("up") ? -100 : 0 }));
      gsap.set("#chipX", { xPercent: -50, yPercent: -100 });
      // a path that draws itself with a glowing comet on its tip
      function drawWithComet(key, sel, t0, d) {
        const P = SAMP[key]; if (!P || P.length < 3) return;
        const n = P.length - 1, prog = { p: 0 }, els = document.querySelectorAll(sel), cm = document.getElementById("cm_" + key);
        const draw = () => {
          const f = prog.p * n, k = Math.min(n - 1, Math.floor(f)), r = f - k;
          cm.style.transform = `translate(${P[k][0] + (P[k + 1][0] - P[k][0]) * r}px, ${P[k][1] + (P[k + 1][1] - P[k][1]) * r}px)`;
          els.forEach((el) => (el.style.strokeDashoffset = (1 - prog.p).toFixed(5)));
        };
        tl.set(cm, { opacity: 1 }, t0);
        tl.to(prog, { p: 1, duration: d, ease: "sine.inOut", onUpdate: draw }, t0);
        tl.to(cm, { opacity: 0, duration: 0.4 }, t0 + d);
      }
      tl.fromTo("#slogan", { opacity: 1 }, { opacity: 1, duration: 0.01 }, 0);
      gsap.set(["#slogan .l1", "#slogan .l2", "#cta .c1", "#cta .c2"], { opacity: 0 });
      %JS%
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
