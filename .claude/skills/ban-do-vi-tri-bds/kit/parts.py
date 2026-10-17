#!/usr/bin/env python3
"""Cat index.html thanh nhieu doan ngan de render tung doan (moi lan render nen phai xong duoi 2 gio).

    python3 parts.py DU_AN SO_DOAN          -> DU_AN/parts/pN/index.html (khong co am thanh)
Render tung doan:  npx hyperframes render --quality high -o renders/pN.mp4 parts/pN
Ghep:              python3 parts.py DU_AN SO_DOAN --join   (ghep hinh + tron tieng tu renders/audio.m4a hoac assets/vo/mix_audio.m4a)
Tieng: render rieng 1 lan bang ban index.html goc chi giu <audio> (xem --audio) hoac dung audio.m4a cua lan render truoc.
"""
import os, re, shutil, subprocess, sys

P = sys.argv[1].rstrip("/"); N = int(sys.argv[2])
html = open(f"{P}/index.html", encoding="utf-8").read()
DUR = float(re.search(r'data-composition-id="main" data-start="0" data-duration="([0-9.]+)"', html).group(1))
cuts = [round(DUR * k / N, 2) for k in range(N + 1)]

if "--join" in sys.argv:
    lst = f"{P}/renders/parts.txt"
    open(lst, "w").write("".join(f"file 'p{k}.mp4'\n" for k in range(N)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", f"{P}/renders/video_only.mp4"], check=True)
    aud = next(a for a in (f"{P}/renders/audio.m4a", f"{P}/assets/vo/mix_audio.m4a") if os.path.exists(a))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{P}/renders/video_only.mp4", "-i", aud, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DUR), f"{P}/renders/master.mp4"], check=True)
    print("ghep xong:", f"{P}/renders/master.mp4"); sys.exit()

silent = re.sub(r'<audio [^>]*></audio>', "", html)
for k in range(N):
    t0, L = cuts[k], round(cuts[k + 1] - cuts[k], 2)
    d = f"{P}/parts/p{k}"
    if os.path.isdir(d): shutil.rmtree(d)
    os.makedirs(d)
    for f in ("hyperframes.json", "package.json", "meta.json"): shutil.copy(f"{P}/{f}", d)
    os.symlink(os.path.abspath(f"{P}/assets"), f"{d}/assets")
    h = silent.replace(f'data-duration="{DUR}"', f'data-duration="{L}"')
    h = h.replace('window.__timelines["main"] = tl;',
                  f'const outer = gsap.timeline({{ paused: true }}); outer.add(tl.tweenFromTo({t0}, {t0 + L}, {{ ease: "none" }}), 0);\n'
                  f'      window.__timelines["main"] = outer;')
    open(f"{d}/index.html", "w", encoding="utf-8").write(h)
    print(f"p{k}: {t0}s -> {t0 + L}s ({L}s)")
