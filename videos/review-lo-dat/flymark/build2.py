#!/usr/bin/env python3
"""Flycam lot marking v2 (HyperFrames), ground-plane locked.

Each clip: a ground layer drawn in anchor-frame pixels (road glow band, flat painted road name, lot glow rings) that is
re-projected every frame with the tracked ground homography (work/track_h.py), plus an upright screen-space pin + tag at
the projected lot point and an optional info card.
    python3 flymark/build2.py [name ...]
"""
import json, math, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__)); P = os.path.dirname(ROOT); W = f"{P}/work"; FPS = 30

CLIPS = {
 "m1016b": {"src": "m1016b_clean", "H": "H1016b", "in": 0.0, "dur": 5.0, "lot": [850, 1320],
            "pin": {"t": 0.15, "small": "LÔ ĐẤT", "big": "5M × 15M"}},
 "m0316": {"src": "DJI_0316_1080", "H": "H316", "in": 4.0, "dur": 7.0, "lot": [130, 1233],
           "road": [[120, 960], [150, 1020], [200, 1087], [247, 1167], [273, 1247], [300, 1340], [300, 1433], [307, 1527], [320, 1647]],
           "road_text": {"text": "ĐƯỜNG D3", "a": 4, "b": 6, "size": 40}, "road_t": 0.3,
           "pin": {"t": 0.9, "small": "LÔ ĐẤT", "big": "5M × 15M"},
           "card": {"t": 0.5, "small": "TRỤC ĐƯỜNG D3", "big": "RỘNG 13M", "ribbon": "LÒNG ĐƯỜNG 6M • VỈA HÈ 3,5M"}},
 "m1016": {"src": "m1016_clean", "H": "H1016", "in": 0.0, "dur": 7.5, "lot": [865, 776],
           "pin": {"t": 0.2, "small": "VỊ TRÍ LÔ ĐẤT", "big": "THE SOL CITY"}},
 "m0256": {"src": "DJI_0256_1080", "H": "H256", "in": 18.0, "dur": 4.5, "lot": [940, 1613],
           "road": [[800, 1120], [807, 1320], [820, 1520], [847, 1720], [860, 1920]],
           "road_text": {"text": "ĐƯỜNG D3", "a": 0, "b": 2, "size": 46}, "road_t": 0.2,
           "pin": {"t": 0.5, "small": "LÔ ĐẤT", "big": "THE SOL CITY"},
           "card": {"t": 0.3, "small": "CÁCH CHỢ HƯNG LONG", "big": "500M", "ribbon": "GIÁP RANH HƯNG LONG • BÌNH CHÁNH"}},
}

TPL = open(f"{ROOT}/tpl2.html", encoding="utf-8").read()


def matrix3d(h):
    a, b, c, d, e, f, g, hh, i = h
    return [a, d, 0, g, b, e, 0, hh, 0, 0, 1, 0, c, f, 0, i]


def build(name, c):
    d = f"{ROOT}/{name}"
    if os.path.isdir(d): shutil.rmtree(d)
    os.makedirs(f"{d}/assets/vendor"); os.makedirs(f"{d}/assets/fonts"); os.makedirs(f"{d}/assets/sfx")
    for f in ("hyperframes.json", "package.json", "CLAUDE.md", "AGENTS.md"): shutil.copy(f"{P}/hook/{f}", d)
    json.dump({"id": f"fly-{name}", "name": f"fly-{name}"}, open(f"{d}/meta.json", "w"))
    shutil.copy(f"{P}/hook/assets/vendor/gsap.min.js", f"{d}/assets/vendor/")
    for f in ("ExtraBold", "Black"): shutil.copy(f"{P}/hook/assets/fonts/BeVietnamPro-{f}.ttf", f"{d}/assets/fonts/")
    for s in ("pop", "whoosh", "chime", "swish"): shutil.copy(f"{P}/hook/assets/sfx/{s}.wav" if os.path.exists(f"{P}/hook/assets/sfx/{s}.wav") else f"{P}/../vi-tri-nha-vuon-phuoc-ly/assets/sfx/{s}.wav", f"{d}/assets/sfx/")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["in"]), "-i", f"{W}/fly/{c['src']}.mp4", "-t", str(c["dur"]),
                    "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p", "-an", f"{d}/assets/shot.mp4"], check=True)
    Hall = json.load(open(f"{W}/{c['H']}.json"))["H"]
    f0 = round(c["in"] * FPS); nf = round(c["dur"] * FPS) + 2
    Hs = Hall[f0:f0 + nf]
    lot = c["lot"]
    lots = []
    for h in Hs:
        x, y, z = (h[0] * lot[0] + h[1] * lot[1] + h[2], h[3] * lot[0] + h[4] * lot[1] + h[5], h[6] * lot[0] + h[7] * lot[1] + h[8])
        lots.append([round(x / z, 1), round(y / z, 1)])
    M = [[round(v, 8) for v in matrix3d(h)] for h in Hs]
    # ground layer (anchor-frame pixels)
    g = []
    if c.get("road"):
        pts = " ".join(f"{x},{y}" for x, y in c["road"])
        g.append(f'<polyline class="rg" points="{pts}"/><polyline class="rc" points="{pts}" pathLength="1"/><polyline class="rf" points="{pts}" pathLength="1"/>')
        rt = c["road_text"]; (x1, y1), (x2, y2) = c["road"][rt["a"]], c["road"][rt["b"]]
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1)); cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        g.append(f'<text class="rt" x="{cx:.1f}" y="{cy:.1f}" font-size="{rt["size"]}" transform="rotate({ang:.1f} {cx:.1f} {cy:.1f})" dominant-baseline="middle" text-anchor="middle">{rt["text"]}</text>')
    lx, ly = lot
    g.append(f'<g id="lotg"><ellipse class="lr" cx="{lx}" cy="{ly}" rx="46" ry="46"/><ellipse class="lr l2" cx="{lx}" cy="{ly}" rx="46" ry="46"/><ellipse class="lf" cx="{lx}" cy="{ly}" rx="40" ry="40"/></g>')
    ground = '<svg id="gsvg" width="1080" height="1920" viewBox="0 0 1080 1920">' + "".join(g) + "</svg>"
    pin = c["pin"]
    card = c.get("card")
    card_html = (f'<div class="card" id="card"><div class="s">{card["small"]}</div><div class="b">{card["big"]}</div><div class="rb">{card["ribbon"]}</div></div>' if card else "")
    audio = [f'<audio id="a1" class="clip" src="assets/sfx/pop.wav" data-start="{pin["t"] + 0.5:.2f}" data-duration="0.4" data-track-index="8" data-volume="0.55"></audio>']
    if card: audio.append(f'<audio id="a2" class="clip" src="assets/sfx/chime.wav" data-start="{card["t"]:.2f}" data-duration="1.4" data-track-index="9" data-volume="0.45"></audio>')
    if c.get("road"): audio.append(f'<audio id="a3" class="clip" src="assets/sfx/swish.wav" data-start="{c["road_t"]:.2f}" data-duration="0.6" data-track-index="10" data-volume="0.4"></audio>')
    rep = {"%DUR%": str(c["dur"]), "%GROUND%": ground, "%CARD%": card_html, "%PSMALL%": pin["small"], "%PBIG%": pin["big"],
           "%AUDIO%": "\n".join(audio), "%M%": json.dumps(M), "%LOT%": json.dumps(lots),
           "%PIN_T%": str(pin["t"]), "%CARD_T%": str(card["t"]) if card else "-1", "%ROAD_T%": str(c.get("road_t", -1))}
    html = TPL
    for k, v in rep.items(): html = html.replace(k, v)
    open(f"{d}/index.html", "w", encoding="utf-8").write(html)
    print(name, c["dur"], "s", len(Hs), "frames")


if __name__ == "__main__":
    for n in (sys.argv[1:] or CLIPS): build(n, CLIPS[n])
