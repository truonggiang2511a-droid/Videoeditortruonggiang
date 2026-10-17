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
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: "BVP", sans-serif; --zi: 1; --tilt: 0deg; background: #04070c; }
      .full { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
      #stage { perspective: 1800px; perspective-origin: 540px 800px; overflow: hidden; }
      #tilt { transform-style: preserve-3d; transform-origin: 540px 900px; }
      #world { position: absolute; left: 0; top: 0; width: %W%px; height: %H%px; transform-origin: 0 0; transform-style: preserve-3d; }
      #world img { position: absolute; display: block; }
      #far { left: %FX%px; top: %FY%px; width: %FW%px; height: %FH%px; filter: saturate(1.05) brightness(0.85); }
      #wide { left: 0; top: 0; width: %W%px; height: %H%px; filter: saturate(1.1) contrast(1.06) brightness(0.88); }
      #detail { left: %DX%px; top: %DY%px; width: %DW%px; height: %DH%px; opacity: 0; filter: saturate(1.1) contrast(1.06) brightness(0.92); }
      svg#lines { position: absolute; left: 0; top: 0; width: %W%px; height: %H%px; overflow: visible; }
      /* regions: Tây Ninh side dimmed, TP.HCM lit */
      #dimTN { fill: rgba(2,6,14,0.5); opacity: 0; }
      #hcmFill { fill: rgba(46,214,255,0.2); opacity: 0; }
      #hcmEdge { fill: none; stroke: #2EE6FF; stroke-width: calc(46px * var(--zi)); opacity: 0; filter: blur(calc(10px * var(--zi))); }
      /* border line: dark under, hot glow, white core, running dashes */
      .bu, .bg, .bc, .bf, .ru, .rg, .rc, .rf { fill: none; stroke-linecap: round; stroke-linejoin: round; }
      .bu, .bg, .bc, .ru, .rg, .rc { stroke-dasharray: 1; stroke-dashoffset: 1; }
      .bu { stroke: rgba(0,0,0,0.65); stroke-width: calc(18px * var(--zi)); }
      .bg { stroke: #FF2E63; stroke-width: calc(34px * var(--zi)); opacity: 0.6; filter: blur(calc(7px * var(--zi))); }
      .bc { stroke: #FFE3EA; stroke-width: calc(8px * var(--zi)); }
      .bf { stroke: #FF2E63; stroke-width: calc(8px * var(--zi)); stroke-dasharray: 0.004 0.008; opacity: 0; }
      .ru { stroke: rgba(0,0,0,0.6); stroke-width: calc(16px * var(--zi)); }
      .rg { stroke: #FFC23A; stroke-width: calc(30px * var(--zi)); opacity: 0.55; filter: blur(calc(6px * var(--zi))); }
      .rc { stroke: #FFF4C8; stroke-width: calc(8px * var(--zi)); }
      .rf { stroke: #ffffff; stroke-width: calc(5px * var(--zi)); stroke-dasharray: 0.02 0.06; opacity: 0; filter: drop-shadow(0 0 calc(4px * var(--zi)) #fff); }
      .comet { position: absolute; left: 0; top: 0; width: 0; height: 0; opacity: 0; }
      .comet .cc { position: absolute; left: -24px; top: -24px; width: 48px; height: 48px; border-radius: 50%; transform: scale(var(--zi)) rotateX(calc(-1 * var(--tilt))); }
      .comet.y .cc { background: radial-gradient(circle, #ffffff 0 22%, #FFE58A 34%, rgba(255,194,58,0.55) 55%, rgba(255,194,58,0) 72%); }
      .comet.p .cc { background: radial-gradient(circle, #ffffff 0 22%, #FF8FAE 36%, rgba(255,46,99,0.55) 55%, rgba(255,46,99,0) 72%); }
      /* flat 3D names lying on the ground */
      .roadtxt { position: absolute; transform: translate(-50%, -50%) rotate(var(--a)); white-space: nowrap; font-weight: 900; letter-spacing: 0.03em; line-height: 1; text-align: center; }
      .rti { position: relative; display: inline-block; opacity: 0; }
      .rti small { display: inline-block; font-size: 0.36em; letter-spacing: 0.14em; margin-top: 0.14em; }
      .rti .ex { position: absolute; left: 0; top: 0; color: #5b6673; text-shadow: 0 0.012em 0 #56606c, 0 0.024em 0 #4f5965, 0 0.036em 0 #48525d, 0 0.048em 0 #414a55, 0 0.06em 0 #3a424c, 0 0.072em 0 #333b44, 0 0.084em 0 #2c333b, 0 0.14em 0.2em rgba(0,0,0,0.85); }
      .rti .fc { position: relative; display: inline-block; background: linear-gradient(180deg, #ffffff 0%, #ffffff 42%, #d5dde6 58%, #ffffff 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
      .roadtxt.c .rti .fc { background: linear-gradient(180deg, #ffffff 0%, #E6FCFF 40%, #7EEBFF 60%, #ffffff 100%); -webkit-background-clip: text; background-clip: text; }
      .roadtxt.c .rti { filter: drop-shadow(0 0 0.08em rgba(46,230,255,0.95)); }
      .roadtxt.w .rti { filter: drop-shadow(0 0 0.06em rgba(255,255,255,0.55)); }
      /* upright markers */
      .poi, #home { position: absolute; left: 0; top: 0; width: 0; height: 0; will-change: transform; }
      .badge { position: absolute; left: -34px; top: -82px; width: 68px; height: 68px; border-radius: 50% 50% 50% 8px; transform: rotate(-45deg) scale(0); border: 4px solid #fff; box-shadow: 0 8px 18px rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; background: #FF2E63; }
      .badge svg { width: 36px; height: 36px; transform: rotate(45deg); }
      .chip { position: absolute; left: 0; top: 0; background: rgba(8,13,22,0.92); border: 3px solid #FFD23F; border-radius: 16px; padding: 12px 22px 14px; white-space: nowrap; text-align: center; opacity: 0; box-shadow: 0 12px 26px rgba(0,0,0,0.55); }
      .chip b { display: block; color: #fff; font-size: 32px; font-weight: 900; }
      .chip span { display: block; margin-top: 2px; color: #FFD23F; font-size: 28px; font-weight: 800; }
      .chip.pk { border-color: #FF2E63; box-shadow: 0 0 22px rgba(255,46,99,0.55), 0 12px 26px rgba(0,0,0,0.55); }
      .chip.pk span { color: #FF9BB4; }
      #chipC { top: -96px; }
      #home .ring { position: absolute; left: -100px; top: -100px; width: 200px; height: 200px; border-radius: 50%; border: 6px solid #FFD23F; box-shadow: 0 0 24px rgba(255,210,63,0.8); opacity: 0; }
      #homemk { position: absolute; left: 0; top: 0; }
      #homemk .drop { position: absolute; left: -46px; top: -124px; width: 92px; height: 124px; filter: drop-shadow(0 10px 14px rgba(0,0,0,0.6)); }
      #hometag { position: absolute; left: 0; top: -150px; transform: translate(-50%, -100%); background: linear-gradient(180deg, #ff2a2f, #c80f14); color: #fff; font-weight: 900; font-size: 42px; padding: 12px 28px 16px; border-radius: 14px; white-space: nowrap; text-align: center; line-height: 1.1; box-shadow: 0 12px 30px rgba(0,0,0,0.55); border: 3px solid rgba(255,255,255,0.85); }
      #hometag small { display: block; margin-top: 4px; font-size: 26px; font-weight: 700; color: #FFE7A6; }
      /* screen HUD */
      #title { position: absolute; left: 0; right: 0; top: 330px; text-align: center; }
      #title .k { display: inline-block; font-size: 32px; font-weight: 800; letter-spacing: 0.22em; color: #1b1300; background: #FFD23F; padding: 10px 26px 12px; border-radius: 999px; }
      #title .t { margin-top: 26px; font-size: 118px; font-weight: 900; line-height: 1.04; color: #fff; text-shadow: 0 4px 0 rgba(0,0,0,0.25), 0 10px 40px rgba(0,0,0,0.85); }
      #title .t em { font-style: normal; color: #2EE6FF; }
      #title .s { margin-top: 22px; display: inline-block; font-size: 38px; font-weight: 800; color: #fff; background: rgba(8,13,22,0.75); padding: 12px 30px 14px; border-radius: 14px; border: 2px solid rgba(255,255,255,0.25); }
      #tplate { background: radial-gradient(ellipse at 50% 30%, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 62%); }
      .hud { position: absolute; left: 60px; right: 60px; top: 1190px; display: flex; gap: 26px; align-items: center; padding: 26px 30px; background: rgba(8,13,22,0.92); border-radius: 24px; border: 3px solid #FF2E63; box-shadow: 0 0 30px rgba(255,46,99,0.45), 0 22px 50px rgba(0,0,0,0.6); opacity: 0; }
      .hud .hi { flex: none; width: 120px; height: 120px; border-radius: 22px; display: flex; align-items: center; justify-content: center; border: 3px solid rgba(255,255,255,0.85); background: #FF2E63; }
      .hud .hi svg { width: 72px; height: 72px; }
      .hud .hk { font-size: 24px; font-weight: 800; letter-spacing: 0.16em; color: #9fb0c4; }
      .hud .ht { margin-top: 4px; font-size: 52px; font-weight: 900; color: #fff; line-height: 1.08; }
      .hud .ht em { font-style: normal; color: #2EE6FF; }
      .hud .hr { margin-top: 8px; display: flex; gap: 22px; align-items: baseline; }
      .hud .hd { font-size: 70px; font-weight: 900; color: #FFD23F; line-height: 1; }
      .hud .hm { font-size: 34px; font-weight: 800; color: #e9eef5; }
      .hud .ha { margin-top: 8px; font-size: 28px; font-weight: 700; color: #9fb0c4; }
      #summary { position: absolute; left: 50px; right: 50px; top: 1000px; padding: 28px 32px 24px; background: rgba(8,13,22,0.93); border-radius: 26px; border: 3px solid #FFD23F; opacity: 0; box-shadow: 0 22px 50px rgba(0,0,0,0.6); }
      #summary .st { font-size: 46px; font-weight: 900; color: #fff; margin-bottom: 10px; }
      .srow { display: grid; grid-template-columns: 58px 1fr auto auto; gap: 18px; align-items: center; padding: 12px 0; border-top: 1px solid rgba(255,255,255,0.14); }
      .srow i { width: 58px; height: 58px; border-radius: 14px; display: flex; align-items: center; justify-content: center; }
      .srow i svg { width: 34px; height: 34px; }
      .srow span { font-size: 36px; font-weight: 800; color: #eef2f7; }
      .srow b { font-size: 40px; font-weight: 900; color: #FFD23F; }
      .srow em { font-style: normal; font-size: 30px; font-weight: 700; color: #9fb0c4; min-width: 120px; text-align: right; }
      .sfoot { margin-top: 8px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.14); font-size: 32px; font-weight: 800; color: #eef2f7; }
      .sfoot em { font-style: normal; color: #2EE6FF; }
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
            <svg id="lines" viewBox="0 0 %W% %H%">%SVG%</svg>
            %LABELS%
            <div class="comet p" id="cm_nA"><div class="cc"></div></div>
            <div class="comet p" id="cm_nB"><div class="cc"></div></div>
            <div class="comet y" id="cm_route"><div class="cc"></div></div>
          </div>
        </div>
      </div>
      <div id="vig" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="1"></div>
      <div id="marks" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="3">
        <div class="poi" id="pB" data-w="%BCX%,%BCY%"><div class="chip pk" id="chipB"><b>ĐƯỜNG RANH GIỚI</b><span>Tây Ninh ⟷ TP.HCM</span></div></div>
        <div class="poi" id="pC" data-w="%CX%,%CY%"><div class="badge" id="badgeC"><svg viewBox="0 0 24 24">%FLAG%</svg></div><div class="chip pk" id="chipC"><b>QUA RANH TP.HCM</b><span>%RM% · %RS%</span></div></div>
        <div id="home" data-w="%HX%,%HY%">
          <div class="ring" id="ring1"></div><div class="ring" id="ring2"></div>
          <div id="homemk">
            <svg class="drop" viewBox="0 0 92 124"><defs><linearGradient id="dg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff3a3f"/><stop offset="1" stop-color="#b80c11"/></linearGradient></defs><path d="M46 121 C46 121 5 70 5 44 A41 41 0 0 1 87 44 C87 70 46 121 46 121 Z" fill="url(#dg)" stroke="#fff" stroke-width="5"/><path d="M28 50 L46 34 L64 50 V64 H28 Z" fill="#fff"/><rect x="41" y="52" width="10" height="12" fill="#c80f14"/></svg>
            <div id="hometag">CĂN NHÀ GỖ<small>Nhà vườn gỗ mái Nhật · 300m²</small></div>
          </div>
        </div>
      </div>
      <div id="hudlayer" class="full clip" data-start="0" data-duration="%DUR%" data-track-index="2">
        <div id="tplate" class="full"></div>
        <div id="title"><div class="k">VỊ TRÍ NHÀ GỖ</div><div class="t">SÁT RANH<br /><em>TP.HCM</em></div><div class="s">Xã Phước Lý · Tây Ninh</div></div>
        <div class="hud" id="hud"><div class="hi"><svg viewBox="0 0 24 24">%FLAG%</svg></div><div class="hb"><div class="hk">TỪ CĂN NHÀ ĐẾN</div><div class="ht">RANH GIỚI <em>TP.HCM</em></div><div class="hr"><span class="hd">%RM%</span><span class="hm">%RS% ô tô</span></div><div class="ha">Chim bay khoảng %AIR%</div></div></div>
        <div id="summary"><div class="st">Từ căn nhà gỗ</div>%SUMMARY%<div class="sfoot">Bên kia ranh: <em>Xã Bình Chánh · TP.HCM</em></div></div>
        <div id="note">Ranh giới hành chính và đường đi theo OpenStreetMap (tham khảo) · thời gian ô tô ước tính</div>
        <div id="credit">Ảnh vệ tinh: Esri, Maxar · Dữ liệu: © OpenStreetMap</div>
      </div>
      %BGM%
      %AUDIO%
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      const root = document.getElementById("root"), world = document.getElementById("world"), tiltEl = document.getElementById("tilt");
      const CAM = %CAM%, SAMP = %SAMP%, DUR = %DUR%;
      const MARKS = Array.from(document.querySelectorAll("[data-w]"));
      MARKS.forEach((el) => { const [x, y] = el.dataset.w.split(",").map(Number); el._wx = x; el._wy = y; });
      const cam = { x: CAM[0][2], y: CAM[0][3], lz: Math.log2(CAM[0][4] * 0.85), t: 20 };
      function apply() {
        const z = Math.pow(2, cam.lz);
        world.style.transform = `translate(${540 - cam.x * z}px, ${900 - cam.y * z}px) scale(${z})`;
        tiltEl.style.transform = `rotateX(${cam.t}deg)`;
        root.style.setProperty("--zi", (1 / z).toFixed(5));
        root.style.setProperty("--tilt", cam.t.toFixed(3) + "deg");
        const a = cam.t * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a), PD = 1800;
        for (const el of MARKS) {
          const sx = 540 + (el._wx - cam.x) * z, sy = 900 + (el._wy - cam.y) * z;
          const yr = (sy - 900) * ca + 900, zr = (sy - 900) * sa, k = PD / (PD - zr);
          el.style.transform = `translate(${(540 + (sx - 540) * k).toFixed(1)}px, ${(800 + (yr - 800) * k).toFixed(1)}px)`;
        }
      }
      apply();
      tl.set(cam, { x: CAM[0][2], y: CAM[0][3], lz: Math.log2(CAM[0][4] * 0.85), t: 20, onComplete: apply }, 0);
      CAM.forEach(([t0, d, x, y, z, t]) => tl.to(cam, { x, y, lz: Math.log2(z), t, duration: d, ease: "sine.inOut", onUpdate: apply }, t0));
      tl.to(cam, { lz: Math.log2(CAM[CAM.length - 1][4] * 1.08), duration: DUR - CAM[CAM.length - 1][0] - CAM[CAM.length - 1][1], ease: "none", onUpdate: apply }, CAM[CAM.length - 1][0] + CAM[CAM.length - 1][1]);

      // imagery layers follow the zoom
      tl.to("#detail", { opacity: 1, duration: 1.4, ease: "sine.inOut" }, 6.4);
      tl.to("#detail", { opacity: 0, duration: 1.2, ease: "sine.inOut" }, 10.4);
      tl.to("#detail", { opacity: 1, duration: 1.2, ease: "sine.inOut" }, 19.6);
      tl.to("#detail", { opacity: 0, duration: 1.0, ease: "sine.inOut" }, 32.6);
      tl.to("#wide", { opacity: 0, duration: 2.0, ease: "sine.inOut" }, 33.2);
      tl.to("#wide", { opacity: 1, duration: 2.0, ease: "sine.inOut" }, 41.0);

      // title
      tl.fromTo("#tplate", { opacity: 0 }, { opacity: 1, duration: 0.6 }, 0.2);
      tl.fromTo("#title .k", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, 0.4);
      tl.fromTo("#title .t", { opacity: 0, scale: 1.25, filter: "blur(10px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.7, ease: "power4.out" }, 0.8);
      tl.fromTo("#title .s", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, 1.4);
      tl.to(["#title", "#tplate"], { opacity: 0, y: -40, duration: 0.6, ease: "power2.in" }, 4.6);

      // home
      tl.fromTo("#homemk", { y: -300, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: "bounce.out" }, 5.6);
      const ringPulse = (t) => tl.fromTo(["#ring1", "#ring2"], { opacity: 0.95, scale: 0.15 }, { opacity: 0, scale: 1.7, duration: 1.8, ease: "power2.out", stagger: 0.6, immediateRender: false }, t);
      [6.3, 13.4, 36.0, 51.4].forEach(ringPulse);
      tl.to("#hometag", { opacity: 0, duration: 0.4 }, 10.2);

      // a path that draws itself with a glowing comet on its tip
      function drawWithComet(key, sel, t0, d) {
        const P = SAMP[key], n = P.length - 1, prog = { p: 0 }, els = document.querySelectorAll(sel), cm = document.getElementById("cm_" + key);
        const draw = () => {
          const f = prog.p * n, k = Math.min(n - 1, Math.floor(f)), r = f - k;
          cm.style.transform = `translate(${P[k][0] + (P[k + 1][0] - P[k][0]) * r}px, ${P[k][1] + (P[k + 1][1] - P[k][1]) * r}px)`;
          els.forEach((el) => (el.style.strokeDashoffset = (1 - prog.p).toFixed(5)));
        };
        tl.set(cm, { opacity: 1 }, t0);
        tl.to(prog, { p: 1, duration: d, ease: "sine.inOut", onUpdate: draw }, t0);
        tl.to(cm, { opacity: 0, duration: 0.4 }, t0 + d);
      }

      // border near the house: drawn out from the crossing in both directions
      drawWithComet("nA", "#b_nA .bu, #b_nA .bg, #b_nA .bc", %T_BORDER%, %D_BORDER%);
      drawWithComet("nB", "#b_nB .bu, #b_nB .bg, #b_nB .bc", %T_BORDER%, %D_BORDER%);
      tl.set(["#b_nA .bf", "#b_nB .bf"], { opacity: 0.95 }, %T_BORDER% + %D_BORDER%);
      tl.fromTo(["#b_nA .bf", "#b_nB .bf"], { strokeDashoffset: 0 }, { strokeDashoffset: -0.6, duration: DUR - %T_BORDER% - %D_BORDER%, ease: "none" }, %T_BORDER% + %D_BORDER%);
      tl.fromTo("#chipB", { opacity: 0, y: 20, xPercent: -50, yPercent: 30 }, { opacity: 1, y: 0, xPercent: -50, yPercent: 30, duration: 0.45, ease: "power3.out" }, %T_BORDER% + 1.2);
      tl.to("#chipB", { opacity: 0, duration: 0.4 }, 18.4);

      // the rest of the boundary, revealed on the wide shot
      ["#b_fA", "#b_fB"].forEach((g) => {
        tl.to(`${g} .bu, ${g} .bg, ${g} .bc`, { strokeDashoffset: 0, duration: 3.2, ease: "sine.inOut" }, %T_FARB%);
        tl.set(`${g} .bf`, { opacity: 0.95 }, %T_FARB% + 3.2);
        tl.fromTo(`${g} .bf`, { strokeDashoffset: 0 }, { strokeDashoffset: -0.3, duration: DUR - %T_FARB% - 3.2, ease: "none" }, %T_FARB% + 3.2);
      });

      // TP.HCM lit up, Tây Ninh side dimmed
      tl.to("#dimTN", { opacity: 1, duration: 1.2, ease: "sine.inOut" }, %T_FILL%);
      tl.to("#hcmFill", { opacity: 1, duration: 1.2, ease: "sine.inOut" }, %T_FILL%);
      tl.to("#hcmEdge", { opacity: 0.75, duration: 1.2, ease: "sine.inOut" }, %T_FILL%);
      tl.to("#hcmFill", { opacity: 0.55, duration: 1.4, ease: "sine.inOut", repeat: 13, yoyo: true }, %T_FILL% + 1.4);

      // flat 3D names
      const pop = (sel, t) => tl.fromTo(sel, { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.9, ease: "back.out(1.7)" }, t);
      const hide = (sel, t) => tl.to(sel, { opacity: 0, duration: 0.5 }, t);
      pop("#tx_hcm", %T_TXT%); pop("#tx_tn", %T_TXT% + 0.7);
      hide(["#tx_hcm", "#tx_tn"], 18.5);
      pop("#tx_hcmF", 35.0); pop("#tx_tnF", 35.7);
      hide(["#tx_hcmF", "#tx_tnF"], 40.8);
      pop("#tx_hcm", 50.8);

      // route from the house to the crossing
      drawWithComet("route", "#route .ru, #route .rg, #route .rc", %T_ROUTE%, %D_ROUTE%);
      tl.set("#route .rf", { opacity: 0.9 }, %T_ROUTE% + %D_ROUTE%);
      tl.fromTo("#route .rf", { strokeDashoffset: 0 }, { strokeDashoffset: -(DUR - %T_ROUTE% - %D_ROUTE%) * 0.25, duration: DUR - %T_ROUTE% - %D_ROUTE%, ease: "none" }, %T_ROUTE% + %D_ROUTE%);
      tl.fromTo("#badgeC", { scale: 0, rotation: -45 }, { scale: 1, rotation: -45, duration: 0.6, ease: "back.out(2.2)" }, %T_ROUTE% + %D_ROUTE%);
      tl.fromTo("#chipC", { opacity: 0, y: 20, xPercent: -50, yPercent: -100 }, { opacity: 1, y: 0, xPercent: -50, yPercent: -100, duration: 0.45, ease: "power3.out" }, %T_ROUTE% + %D_ROUTE% + 0.2);
      tl.to("#chipC", { opacity: 0, duration: 0.4 }, %T_HUD_OUT%);
      tl.fromTo("#hud", { opacity: 0, y: 70 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, %T_HUD%);
      tl.to("#hud", { opacity: 0, y: 30, duration: 0.45, ease: "power2.in" }, %T_HUD_OUT%);
      tl.to("#badgeC", { opacity: 0, duration: 0.3 }, 32.8);
      tl.to("#badgeC", { opacity: 1, duration: 0.4 }, 50.4);

      // summary
      tl.fromTo("#summary", { opacity: 0, y: 70 }, { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" }, %T_SUM%);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
