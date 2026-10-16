<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #05080d; }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: Inter, sans-serif; --zi: 1; --tilt: 0deg; background: #05080d; }
      .full { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
      #stage { perspective: 1700px; perspective-origin: 540px 820px; overflow: hidden; }
      #tilt { transform-style: preserve-3d; transform-origin: 540px 900px; }
      #world { position: absolute; left: 0; top: 0; width: %W%px; height: %H%px; transform-origin: 0 0; transform-style: preserve-3d; }
      #world img { position: absolute; display: block; }
      #wide { left: 0; top: 0; width: %W%px; height: %H%px; filter: saturate(1.08) contrast(1.05) brightness(0.92); }
      #detail { left: %DX%px; top: %DY%px; width: %DW%px; height: %DH%px; opacity: 0; filter: saturate(1.08) contrast(1.05) brightness(0.95); }
      svg#lines { position: absolute; left: 0; top: 0; width: %W%px; height: %H%px; overflow: visible; }
      .road { fill: none; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0.95; }
      .road.ql1 { stroke: #FFB020; stroke-width: calc(9px * var(--zi)); filter: drop-shadow(0 0 6px rgba(255,176,32,0.9)); }
      .road.tl { stroke: #34E1FF; stroke-width: calc(9px * var(--zi)); filter: drop-shadow(0 0 6px rgba(52,225,255,0.9)); }
      .road.ct { stroke: #ffffff; stroke-width: calc(7px * var(--zi)); filter: drop-shadow(0 0 5px rgba(255,255,255,0.8)); }
      .route { fill: none; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1; stroke-dashoffset: 1; }
      .route.glow { stroke: rgba(255,214,64,0.55); stroke-width: calc(22px * var(--zi)); filter: blur(calc(4px * var(--zi))); }
      .route.core { stroke: #FFF4C2; stroke-width: calc(6px * var(--zi)); }
      /* flat 3D road text: painted on the ground plane, thick extrusion */
      .roadtxt { position: absolute; transform: translate(-50%, -50%) rotate(var(--a)); white-space: nowrap; font-weight: 900; letter-spacing: 0.04em; line-height: 1; }
      .rti { display: inline-block; opacity: 0; }
      .roadtxt.y { color: #FFE680; -webkit-text-stroke: 2px #4a3000; text-shadow: 0 1px 0 #c98a00, 0 2px 0 #b37a00, 0 3px 0 #9c6a00, 0 4px 0 #855a00, 0 5px 0 #6e4a00, 0 8px 14px rgba(0,0,0,0.8); }
      .roadtxt.c { color: #B8F8FF; -webkit-text-stroke: 2px #063a44; text-shadow: 0 1px 0 #1aa9c4, 0 2px 0 #1697ae, 0 3px 0 #128598, 0 4px 0 #0e7382, 0 5px 0 #0a616c, 0 8px 14px rgba(0,0,0,0.8); }
      .roadtxt.w { color: #ffffff; -webkit-text-stroke: 2px #2a323c; text-shadow: 0 1px 0 #b9c2cc, 0 2px 0 #a2acb7, 0 3px 0 #8b96a2, 0 4px 0 #74808d, 0 7px 12px rgba(0,0,0,0.8); }
      /* upright billboards: undo zoom and tilt so they stay readable */
      .poi, #home { position: absolute; width: 0; height: 0; transform-style: preserve-3d; }
      .poi .bb, .poi > .pin, .poi > .card, #home > * { transform-origin: 0 0; }
      .poi { opacity: 0; }
      .poi .pin { position: absolute; left: 0; top: 0; width: 26px; height: 26px; margin: -13px 0 0 -13px; border-radius: 50%; background: #FFD23F; border: 5px solid #fff; box-shadow: 0 0 0 6px rgba(255,210,63,0.35), 0 6px 16px rgba(0,0,0,0.6); transform: scale(var(--zi)) rotateX(calc(-1 * var(--tilt))); transform-origin: 50% 50%; }
      .poi .card { position: absolute; left: 0; top: 0; transform: rotateX(calc(-1 * var(--tilt))) scale(var(--zi)) translate(-50%, -100%) translateY(-34px); transform-origin: 0 0; background: rgba(8,14,24,0.88); border: 2px solid rgba(255,210,63,0.9); border-radius: 14px; padding: 12px 20px 14px; white-space: nowrap; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
      .poi.d .card { transform: rotateX(calc(-1 * var(--tilt))) scale(var(--zi)) translate(-50%, 0) translateY(34px); }
      .poi .card b { display: block; color: #fff; font-size: 30px; font-weight: 900; letter-spacing: 0.01em; }
      .poi .card span { display: block; margin-top: 4px; color: #FFD23F; font-size: 26px; font-weight: 800; font-variant-numeric: tabular-nums; }
      #home { left: %HX%px; top: %HY%px; }
      #home .ringwrap { position: absolute; left: 0; top: 0; transform: scale(var(--zi)); transform-origin: 0 0; }
      #home .ring { position: absolute; left: -90px; top: -90px; width: 180px; height: 180px; border-radius: 50%; border: 6px solid #FFD23F; transform-origin: 50% 50%; opacity: 0; }
      #homemk { position: absolute; left: 0; top: 0; }
      #home .mk { position: absolute; left: 0; top: 0; transform: rotateX(calc(-1 * var(--tilt))) scale(var(--zi)); transform-origin: 0 0; }
      #home .mk .drop { position: absolute; left: -44px; top: -118px; width: 88px; height: 118px; }
      #home .mk .tag { position: absolute; left: 0; top: -150px; transform: translate(-50%, -100%); background: #E3161B; color: #fff; font-weight: 900; font-size: 40px; padding: 12px 26px 16px; border-radius: 12px; white-space: nowrap; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; line-height: 1.15; }
      #home .mk .tag small { display: block; font-size: 26px; font-weight: 700; color: #FFE7A6; }
      /* HUD (screen space) */
      #title { position: absolute; left: 60px; right: 60px; top: 300px; text-align: center; color: #fff; }
      #title .k { font-size: 30px; font-weight: 800; letter-spacing: 0.18em; color: #FFD23F; }
      #title .t { margin-top: 10px; font-size: 76px; font-weight: 900; line-height: 1.05; text-shadow: 0 6px 30px rgba(0,0,0,0.8); }
      #title .s { margin-top: 14px; font-size: 36px; font-weight: 700; color: #e9eef5; text-shadow: 0 4px 20px rgba(0,0,0,0.8); }
      .hud { position: absolute; left: 70px; right: 70px; top: 1230px; padding: 26px 34px 30px; background: rgba(8,14,24,0.86); border-radius: 22px; border: 2px solid rgba(255,210,63,0.75); box-shadow: 0 20px 50px rgba(0,0,0,0.55); opacity: 0; }
      .hud .hk { font-size: 26px; font-weight: 800; letter-spacing: 0.16em; color: #9fb0c4; }
      .hud .ht { margin-top: 6px; font-size: 64px; font-weight: 900; color: #fff; line-height: 1.05; }
      .hud .hr { margin-top: 14px; display: flex; gap: 28px; align-items: baseline; }
      .hud .hd { font-size: 76px; font-weight: 900; color: #FFD23F; font-variant-numeric: tabular-nums; }
      .hud .hm { font-size: 46px; font-weight: 800; color: #e9eef5; }
      #summary { position: absolute; left: 60px; right: 60px; top: 1060px; padding: 30px 36px; background: rgba(8,14,24,0.9); border-radius: 24px; border: 2px solid rgba(255,210,63,0.8); opacity: 0; }
      #summary .st { font-size: 44px; font-weight: 900; color: #fff; margin-bottom: 12px; }
      .srow { display: grid; grid-template-columns: 1fr auto auto; gap: 22px; align-items: baseline; padding: 12px 0; border-top: 1px solid rgba(255,255,255,0.14); }
      .srow span { font-size: 36px; font-weight: 800; color: #e9eef5; }
      .srow b { font-size: 40px; font-weight: 900; color: #FFD23F; font-variant-numeric: tabular-nums; }
      .srow i { font-style: normal; font-size: 32px; font-weight: 700; color: #9fb0c4; min-width: 150px; text-align: right; }
      #credit { position: absolute; left: 0; right: 0; bottom: 70px; text-align: center; font-size: 20px; font-weight: 600; color: rgba(255,255,255,0.75); text-shadow: 0 2px 6px rgba(0,0,0,0.9); }
      #note { position: absolute; left: 0; right: 0; bottom: 100px; text-align: center; font-size: 22px; font-weight: 600; color: rgba(255,255,255,0.8); text-shadow: 0 2px 6px rgba(0,0,0,0.9); }
      #vig { pointer-events: none; background: radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%), linear-gradient(180deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 72%, rgba(0,0,0,0.5) 100%); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="60" data-width="1080" data-height="1920">
      <div id="stage" class="full clip" data-start="0" data-duration="60" data-track-index="0">
        <div id="tilt" class="full">
          <div id="world">
            <img id="wide" src="assets/wide_z16.jpg" alt="" />
            <img id="detail" src="assets/detail_z18.jpg" alt="" />
            <svg id="lines" viewBox="0 0 %W% %H%">%ROADS%%ROUTES%</svg>
            %ROADTXT%
            %POIS%
            <div id="home">
              <div class="ringwrap"><div class="ring" id="ring1"></div><div class="ring" id="ring2"></div></div>
              <div class="mk"><div id="homemk">
                <svg class="drop" viewBox="0 0 88 118"><path d="M44 116 C44 116 4 66 4 42 A40 40 0 0 1 84 42 C84 66 44 116 44 116 Z" fill="#E3161B" stroke="#fff" stroke-width="5"/><circle cx="44" cy="42" r="16" fill="#fff"/></svg>
                <div class="tag" id="hometag">CĂN NHÀ<small>Nhà vườn gỗ mái Nhật · 300m²</small></div>
              </div></div>
            </div>
          </div>
        </div>
      </div>
      <div id="vig" class="full clip" data-start="0" data-duration="60" data-track-index="1"></div>
      <div id="hudlayer" class="full clip" data-start="0" data-duration="60" data-track-index="2">
        <div id="title"><div class="k">VỊ TRÍ</div><div class="t">NHÀ VƯỜN<br />GỖ MÁI NHẬT</div><div class="s">Phước Lý · Cần Giuộc · Long An</div></div>
        %HUD%
        <div id="summary"><div class="st">Từ căn nhà đi</div>%SUMMARY%</div>
        <div id="note">Quãng đường theo bản đồ OpenStreetMap · thời gian ô tô ước tính</div>
        <div id="credit">Ảnh vệ tinh: Esri, Maxar · Dữ liệu đường: © OpenStreetMap</div>
      </div>
      <audio id="bgm" class="clip" src="assets/bgm.wav" data-start="0" data-duration="60" data-track-index="3" data-volume="0.35"></audio>
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      const root = document.getElementById("root");
      const world = document.getElementById("world");
      const tilt = document.getElementById("tilt");
      const cam = { x: 1500, y: 2250, z: 0.62, t: 0 };
      function apply() {
        world.style.transform = `translate(${540 - cam.x * cam.z}px, ${900 - cam.y * cam.z}px) scale(${cam.z})`;
        tilt.style.transform = `rotateX(${cam.t}deg)`;
        root.style.setProperty("--zi", (1 / cam.z).toFixed(5));
        root.style.setProperty("--tilt", cam.t.toFixed(3) + "deg");
      }
      apply();
      const C = (t, d, to, ease) => tl.to(cam, Object.assign({ duration: d, ease: ease || "power2.inOut", onUpdate: apply }, to), t);
      // camera path
      tl.set(cam, { x: 1500, y: 2250, z: 0.62, t: 0, onComplete: apply }, 0);
      C(0, 4.6, { x: 1480, y: 2420, z: 0.8, t: 18 }, "sine.inOut");
      C(4.6, 4.4, { x: %HX%, y: %HY%, z: 3.0, t: 38 });
      C(9.0, 3.4, { x: 1468, y: 2730, z: 2.1, t: 40 });
      C(16.0, 3.6, { x: 1260, y: 2340, z: 0.92, t: 42 });
      C(26.0, 2.6, { x: 1350, y: 2160, z: 0.85, t: 42 });
      C(32.8, 2.4, { x: 1290, y: 2080, z: 1.45, t: 40 });
      C(40.6, 3.6, { x: 1950, y: 1720, z: 0.6, t: 16 });
      C(51.2, 3.8, { x: %HX%, y: 2380, z: 0.85, t: 34 });
      // near-POI cards step aside for the wide view and the summary; pins stay
      tl.to(["#p0 .card", "#p1 .card", "#p2 .card", "#p3 .card", "#p4 .card"], { opacity: 0, duration: 0.6 }, 41.0);
      tl.to(["#p5 .card", "#p6 .card"], { opacity: 0, duration: 0.6 }, 51.4);
      tl.to("#hometag", { opacity: 0, duration: 0.5 }, 33.0);
      tl.to("#hometag", { opacity: 1, duration: 0.5 }, 52.0);
      // title
      tl.fromTo("#title", { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" }, 0.3);
      tl.to("#title", { opacity: 0, y: -30, duration: 0.6, ease: "power2.in" }, 5.2);
      // detail imagery fades in as we get close, out when we leave
      tl.to("#detail", { opacity: 1, duration: 1.4, ease: "power1.inOut" }, 6.2);
      tl.to("#detail", { opacity: 0, duration: 1.2, ease: "power1.inOut" }, 16.4);
      tl.to("#detail", { opacity: 1, duration: 1.0, ease: "power1.inOut" }, 33.4);
      tl.to("#detail", { opacity: 0, duration: 1.0, ease: "power1.inOut" }, 40.8);
      // home marker
      tl.fromTo("#homemk", { y: -260, opacity: 0 }, { y: 0, opacity: 1, duration: 0.7, ease: "bounce.out" }, 7.4);
      tl.fromTo(["#ring1", "#ring2"], { opacity: 0.9, scale: 0.2 }, { opacity: 0, scale: 1.6, duration: 1.6, ease: "power2.out", stagger: 0.5 }, 8.0);
      tl.fromTo(["#ring1", "#ring2"], { opacity: 0.9, scale: 0.2 }, { opacity: 0, scale: 1.6, duration: 1.6, ease: "power2.out", stagger: 0.5, immediateRender: false }, 52.6);
      // routes
      const DRAW = %DRAW%;
      for (const id in DRAW) {
        const [t0, d] = DRAW[id];
        const core = id.replace("r", "rc");
        tl.to(["#" + id, "#" + core], { strokeDashoffset: 0, duration: d, ease: "power1.inOut" }, t0);
      }
      // road highlights + flat 3D road names
      tl.to("#rd_835", { strokeDashoffset: 0, duration: 1.6, ease: "power2.out" }, 11.2);
      tl.fromTo("#t_tl835b_i", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.8, ease: "back.out(1.6)" }, 12.0);
      tl.to("#rd_ql1", { strokeDashoffset: 0, duration: 2.2, ease: "power2.out" }, 20.6);
      tl.fromTo("#t_ql1_i", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.9, ease: "back.out(1.6)" }, 21.6);
      tl.to("#rd_ct", { strokeDashoffset: 0, duration: 2.0, ease: "power2.out" }, 22.6);
      tl.fromTo("#t_caotoc_i", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.8, ease: "back.out(1.6)" }, 23.4);
      // POI pins
      const POIT = %POIT%;
      POIT.forEach((t, i) => tl.fromTo("#p" + i, { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "power2.out" }, t));
      // HUD cards
      const HUDT = %HUDT%;
      HUDT.forEach(([a, b], i) => {
        tl.fromTo("#h" + i, { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }, a);
        tl.to("#h" + i, { opacity: 0, y: 30, duration: 0.4, ease: "power2.in" }, b - 0.4);
      });
      // summary
      tl.fromTo("#summary", { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out" }, 54.2);
      tl.to({}, { duration: 0.01 }, 59.99);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
