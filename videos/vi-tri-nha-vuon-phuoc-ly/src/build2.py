import json, math
D = json.load(open("src/data2.json", encoding="utf-8"))
R = D["routes"]
DUR = 84

def km(m): return f"{m} m" if m < 1000 else f"{m/1000:.1f}".replace(".", ",") + " km"
def mins(s): return f"~{max(1, round(s/60))} phút"

ICON = {
 "road": '<path d="M9 3h6l3 18H6z" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M12 6v3M12 12v3M12 18v2" stroke="#fff" stroke-width="2.2"/>',
 "cross": '<circle cx="12" cy="12" r="9" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M8 12h8M12 8v8" stroke="#fff" stroke-width="2.2"/><path d="M5 9l3-2M19 15l-3 2" stroke="#fff" stroke-width="2.2"/>',
 "market": '<path d="M3 9l2-5h14l2 5" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M3 9h18v3a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z" fill="#fff"/><path d="M5 14v6h14v-6" fill="none" stroke="#fff" stroke-width="2.2"/>',
 "school": '<path d="M2 9l10-5 10 5-10 5z" fill="#fff"/><path d="M6 11v5c3 2.5 9 2.5 12 0v-5" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M21 9v6" stroke="#fff" stroke-width="2"/>',
 "gov": '<path d="M3 9l9-5 9 5z" fill="#fff"/><path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18" stroke="#fff" stroke-width="2.2"/>',
 "hospital": '<rect x="4" y="4" width="16" height="16" rx="3" fill="#fff"/><path d="M12 7.5v9M7.5 12h9" stroke="#E3161B" stroke-width="3.2"/>',
 "city": '<path d="M3 21V11h4V6h5v6h3V3h5v18z" fill="#fff"/><path d="M2 21h20" stroke="#fff" stroke-width="2"/>',
}
COLOR = {"road": "#18A9C9", "cross": "#F28C18", "market": "#2BB673", "school": "#3D7BFF", "gov": "#C7372F", "hospital": "#E3161B", "city": "#8E44EC"}

# key, label, icon, draw start, draw dur, hud start, hud end, card side
STOPS = [
 ("TL835B", "TL835B", "road", 10.2, 4.0, 14.2, 18.0, "u"),
 ("NÚT GIAO BÌNH CHÁNH", "NÚT GIAO QL1A", "cross", 20.2, 5.0, 25.2, 29.2, "u"),
 ("CHỢ BÌNH CHÁNH", "CHỢ BÌNH CHÁNH", "market", 30.0, 4.2, 34.2, 37.6, "u"),
 ("TIỂU HỌC BÌNH CHÁNH", "TIỂU HỌC BÌNH CHÁNH", "school", 38.8, 2.6, None, None, "u"),
 ("UBND XÃ BÌNH CHÁNH", "UBND XÃ BÌNH CHÁNH", "gov", 40.0, 2.6, None, None, "d"),
 ("CHỢ LONG THƯỢNG", "CHỢ LONG THƯỢNG", "market", 45.6, 4.6, 50.2, 54.0, "u"),
 ("BỆNH VIỆN ĐK BÌNH CHÁNH", "BV ĐA KHOA BÌNH CHÁNH", "hospital", 56.4, 4.4, 60.8, 64.4, "u"),
 ("TRUNG TÂM TP.HCM", "TRUNG TÂM TP.HCM", "city", 67.6, 5.6, 73.2, 76.6, "u"),
]
# camera keys: start, dur, x, y, zoom, tilt
HX, HY = D["home"]
CAM = [
 (0.0, 5.0, 1520, 2430, 0.78, 26),
 (5.0, 4.6, HX, HY, 3.0, 38),
 (9.8, 3.0, 1468, 2735, 2.15, 40),
 (17.6, 3.6, 1255, 2350, 0.92, 40),
 (29.4, 2.6, 1340, 2160, 0.86, 40),
 (37.4, 2.6, 1300, 2090, 1.4, 40),
 (43.0, 3.6, 2350, 2900, 0.62, 36),
 (54.2, 3.4, 1900, 1750, 0.6, 28),
 (64.6, 4.6, 4380, -330, 0.155, 10),
 (76.6, 3.4, HX, 2420, 0.82, 32),
]
W, Hh = D["size"]
out = []
paths = []
for i, (k, *_r) in enumerate(STOPS):
    d = R[k]["d"]
    paths.append(f'<g id="g{i}"><path class="ru" d="{d}" pathLength="1" id="ru{i}"/><path class="rg" d="{d}" pathLength="1" id="rg{i}"/><path class="rc" d="{d}" pathLength="1" id="rc{i}"/><path class="rf" d="{d}" pathLength="1" id="rf{i}"/></g>')
pois = []; huds = []
for i, (k, lab, ic, t0, dd, h0, h1, side) in enumerate(STOPS):
    x, y = R[k]["end"]
    pois.append(f'<div class="poi {side}" id="p{i}" data-w="{x},{y}"><div class="cs"><div class="badge" id="b{i}" style="background:{COLOR[ic]}"><svg viewBox="0 0 24 24">{ICON[ic]}</svg></div><div class="chip" id="c{i}"><b>{lab}</b><span>{km(R[k]["m"])} · {mins(R[k]["s"])}</span></div></div></div>')
    if h0 is not None:
        huds.append(f'<div class="hud" id="h{i}"><div class="hi" style="background:{COLOR[ic]}"><svg viewBox="0 0 24 24">{ICON[ic]}</svg></div><div class="hb"><div class="hk">TỪ CĂN NHÀ ĐẾN</div><div class="ht">{lab}</div><div class="hr"><span class="hd">{km(R[k]["m"])}</span><span class="hm">{mins(R[k]["s"])} ô tô</span></div></div></div>')
comet = ''.join(f'<div class="comet" id="cm{i}"><div class="cc"></div></div>' for i in range(len(STOPS)))
L = D["labels"]
def rt(lid, text, cls, size):
    a = L[lid]
    return (f'<div class="roadtxt {cls}" style="left:{a["x"]}px;top:{a["y"]}px;font-size:{size}px;--a:{a["a"]}deg">'
            f'<span class="rti" id="t_{lid}"><span class="ex">{text}</span><span class="fc">{text}</span></span></div>')
summary = "".join(
    f'<div class="srow"><i style="background:{COLOR[ic]}"><svg viewBox="0 0 24 24">{ICON[ic]}</svg></i><span>{n}</span><b>{km(R[k]["m"])}</b><em>{mins(R[k]["s"])}</em></div>'
    for n, k, ic in [("TL835B", "TL835B", "road"), ("Nút giao QL1A", "NÚT GIAO BÌNH CHÁNH", "cross"), ("Chợ Bình Chánh", "CHỢ BÌNH CHÁNH", "market"),
                     ("Chợ Long Thượng", "CHỢ LONG THƯỢNG", "market"), ("Trung tâm TP.HCM", "TRUNG TÂM TP.HCM", "city")])
# SFX schedule
sfx = [("riser", 0.0), ("boom", 0.9)]
for (t, d, *_r) in CAM[1:]:
    sfx.append(("whoosh", t))
sfx.append(("pop", 8.7))
for i, (k, lab, ic, t0, dd, h0, h1, side) in enumerate(STOPS):
    sfx.append(("draw", t0)); sfx.append(("pop", t0 + dd))
    if h0 is not None: sfx.append(("chime", h0))
sfx.append(("chime", 77.4))
SFXLEN = {"riser": 1.5, "boom": 1.8, "whoosh": 1.4, "pop": 0.35, "chime": 1.6, "draw": 3.0, "swish": 0.6}
VOL = {"riser": 0.5, "boom": 0.8, "whoosh": 0.55, "pop": 0.6, "chime": 0.5, "draw": 0.35}
audio = "".join(
    f'<audio id="sfx{i}" class="clip" src="assets/sfx/{n}.wav" data-start="{t:.2f}" data-duration="{min(SFXLEN[n], DUR - t):.2f}" data-track-index="{10 + i % 6}" data-volume="{VOL[n]}"></audio>'
    for i, (n, t) in enumerate(sorted(sfx, key=lambda s: s[1])))
tpl = open("src/template2.tpl", encoding="utf-8").read()
rep = {
 "%DUR%": str(DUR), "%W%": str(W), "%H%": str(Hh), "%HX%": str(HX), "%HY%": str(HY),
 "%DX%": str(D["detail"]["x"]), "%DY%": str(D["detail"]["y"]), "%DW%": str(D["detail"]["w"]), "%DH%": str(D["detail"]["h"]),
 "%FX%": str(D["far"]["x"]), "%FY%": str(D["far"]["y"]), "%FW%": str(D["far"]["w"]), "%FH%": str(D["far"]["h"]),
 "%ROADS%": f'<path id="rd_ql1" class="road ql1" d="{D["roads"]["ql1"]}" pathLength="1"/><path id="rd_ct" class="road ct" d="{D["roads"]["caotoc"]}" pathLength="1"/><path id="rd_835" class="road tl" d="{D["roads"]["tl835b"]}" pathLength="1"/>',
 "%ROUTES%": "".join(paths), "%POIS%": "".join(pois), "%HUD%": "".join(huds), "%COMET%": comet,
 "%ROADTXT%": rt("ql1", "QUỐC LỘ 1A", "q", 120) + rt("tl835b", "TL835B", "t", 78) + rt("caotoc", "CAO TỐC", "w", 74),
 "%SUMMARY%": summary, "%AUDIO%": audio,
 "%STOPS%": json.dumps([[t0, dd, h0, h1] for (_, _, _, t0, dd, h0, h1, _) in STOPS]),
 "%SAMPLES%": json.dumps([R[k]["S"] for (k, *_r) in STOPS]),
 "%CAM%": json.dumps(CAM),
}
for k, v in rep.items(): tpl = tpl.replace(k, v)
open("index.html", "w", encoding="utf-8").write(tpl)
print("built", len(tpl) // 1024, "KB", "sfx", len(sfx))
