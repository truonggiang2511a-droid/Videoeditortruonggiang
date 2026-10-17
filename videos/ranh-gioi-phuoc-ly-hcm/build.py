#!/usr/bin/env python3
"""Video 60s: ranh gioi Phuoc Ly (Tay Ninh) - TP.HCM tu can nha go.

Du lieu that trong map/: hcm_osm.json (ranh TP.HCM, Nominatim/OSM), phuoc_ly_osm.json (ranh xa Phuoc Ly),
route_ranh.json (lo trinh OSRM ngan nhat tu nha toi diem qua ranh). Anh ve tinh dung lai cua vi-tri-phuoc-ly-v3.
    python3 build.py
"""
import json, math, os, wave

P = os.path.dirname(os.path.abspath(__file__))
WM = json.load(open(f"{P}/map/mosaics.json"))
HOME = (10.6476555, 106.5708784)
DUR = 60.0


def px(lat, lon):
    n = 2 ** 16; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return round(x * 256 - WM["wide"]["tx0"] * 256, 1), round(y * 256 - WM["wide"]["ty0"] * 256, 1)


def place(mm):
    s = 2 ** (16 - mm["z"])
    return {"x": mm["tx0"] * 256 * s - WM["wide"]["tx0"] * 256, "y": mm["ty0"] * 256 * s - WM["wide"]["ty0"] * 256, "w": mm["w"] * s, "h": mm["h"] * s}


W, H = WM["wide"]["w"], WM["wide"]["h"]; DET = place(WM["detail"]); FAR = place(WM["far"])
HX, HY = px(*HOME)
ring = [px(la, lo) for lo, la in json.load(open(f"{P}/map/hcm_osm.json"))[0]["geojson"]["coordinates"][0]]
best = json.load(open(f"{P}/map/route_ranh.json"))[0]
ROUTE_M, (clo, cla), ROUTE_S = best[0], best[1], best[2]
CX, CY = px(cla, clo)
route = [px(la, lo) for lo, la in best[3]]
# straight-line distance from the house to the nearest point of the HCM boundary (m)
k = 111320; cl = math.cos(math.radians(HOME[0]))
def m_of(a, b): return math.hypot((a[0] - b[0]), (a[1] - b[1])) * 156543.03 * math.cos(math.radians(HOME[0])) / 2 ** 16
def seg_near(p):
    bd, bq = 1e18, None
    for a, b in zip(ring, ring[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy or 1
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)); q = (a[0] + t * dx, a[1] + t * dy); d = math.dist(p, q)
        if d < bd: bd, bq = d, q
    return bd, bq
d_air, _ = seg_near((HX, HY)); AIR_M = m_of((0, 0), (d_air, 0))

# route: cut at the crossing point
ci = min(range(len(route)), key=lambda i: math.dist(route[i], (CX, CY)))
route = route[:ci] + [(CX, CY)]
if math.dist(route[0], (HX, HY)) > 3: route = [(HX, HY)] + route

# border: the boundary run that passes the house, split at the crossing into near / far halves
M = 300
ins = [FAR["x"] + M < x < FAR["x"] + FAR["w"] - M and FAR["y"] + M < y < FAR["y"] + FAR["h"] - M for x, y in ring]
runs, cur = [], []
for p, i in zip(ring, ins):
    if i: cur.append(p)
    elif cur: runs.append(cur); cur = []
if cur: runs.append(cur)
run = min(runs, key=lambda r: min(math.dist(p, (CX, CY)) for p in r))
kc = min(range(len(run)), key=lambda i: math.dist(run[i], (CX, CY)))
NEAR = 1500
def split(seq):
    near, far = [(CX, CY)], []
    for p in seq:
        (near if not far and math.dist(p, (CX, CY)) < NEAR else far).append(p)
    if far: far = [near[-1]] + far
    return near, far
nA, fA = split(run[kc::-1]); nB, fB = split(run[kc + 1:])


def clip_rect(poly, r):
    x0, y0, x1, y1 = r
    def cut(pts, inside, isect):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            if inside(b):
                if not inside(a): out.append(isect(a, b))
                out.append(b)
            elif inside(a): out.append(isect(a, b))
        return out
    def ix(a, b, x): t = (x - a[0]) / ((b[0] - a[0]) or 1e-9); return (x, a[1] + (b[1] - a[1]) * t)
    def iy(a, b, y): t = (y - a[1]) / ((b[1] - a[1]) or 1e-9); return (a[0] + (b[0] - a[0]) * t, y)
    p = poly
    p = cut(p, lambda q: q[0] >= x0, lambda a, b: ix(a, b, x0))
    p = cut(p, lambda q: q[0] <= x1, lambda a, b: ix(a, b, x1))
    p = cut(p, lambda q: q[1] >= y0, lambda a, b: iy(a, b, y0))
    p = cut(p, lambda q: q[1] <= y1, lambda a, b: iy(a, b, y1))
    return p


RECT = (FAR["x"], FAR["y"], FAR["x"] + FAR["w"], FAR["y"] + FAR["h"])
hcm = clip_rect(ring, RECT)
def d_of(pts, close=False): return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + (" Z" if close else "")
rect_d = f"M{RECT[0]},{RECT[1]} H{RECT[2]} V{RECT[3]} H{RECT[0]} Z"


def samples(pts, n=140):
    L = [0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + math.dist(a, b))
    out, j = [], 0
    for i in range(n + 1):
        s = L[-1] * i / n
        while j < len(L) - 2 and L[j + 1] < s: j += 1
        t = (s - L[j]) / ((L[j + 1] - L[j]) or 1)
        out.append([round(pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t, 1), round(pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t, 1)])
    return out


def km(mm): return f"{round(mm, -1):.0f} m" if mm < 1000 else f"{mm/1000:.1f}".replace(".", ",") + " km"
def mins(s): return f"~{max(1, round(s / 60))} phút"


# ---------- timeline ----------
# camera keys: t0, duration, x, y, zoom, tilt
MIDX, MIDY = (HX + CX) / 2, (HY + CY) / 2
CAM = [
    [0.0, 5.0, 1500, 2350, 0.42, 26],
    [5.0, 4.6, HX, HY + 8, 3.0, 38],
    [10.2, 3.2, 1290, 2720, 1.05, 34],
    [18.6, 3.0, MIDX + 10, MIDY + 60, 2.7, 40],
    [32.6, 3.4, 2300, 400, 0.13, 12],
    [41.0, 4.2, 300, 2250, 0.5, 26],
    [45.6, 4.2, 2300, 2650, 0.5, 26],
    [50.2, 3.0, 1290, 2930, 1.25, 34],
]
T_BORDER, D_BORDER = 11.4, 3.6
T_FILL = 14.6
T_TXT = 15.6
T_ROUTE, D_ROUTE = 21.2, 3.8
T_HUD, T_HUD_OUT = T_ROUTE + D_ROUTE + 0.3, 31.6
T_FARB = 34.2
T_SUM = 53.6

# labels (flat 3D text lying on the ground)
LBL = [
    {"id": "tx_hcm", "x": 1250, "y": 2395, "size": 120, "cls": "c", "big": "TP.HCM", "small": "XÃ BÌNH CHÁNH"},
    {"id": "tx_tn", "x": 1020, "y": 3085, "size": 64, "cls": "w", "big": "TÂY NINH", "small": "XÃ PHƯỚC LÝ"},
    {"id": "tx_hcmF", "x": 3300, "y": -700, "size": 1050, "cls": "c", "big": "TP.HCM", "small": ""},
    {"id": "tx_tnF", "x": 900, "y": 4250, "size": 560, "cls": "w", "big": "TÂY NINH", "small": ""},
]


def label_html(L):
    t = L["big"] + (f'<br><small>{L["small"]}</small>' if L["small"] else "")
    return (f'<div class="roadtxt {L["cls"]}" style="left:{L["x"]}px;top:{L["y"]}px;font-size:{L["size"]}px;--a:0deg">'
            f'<span class="rti" id="{L["id"]}"><span class="ex">{t}</span><span class="fc">{t}</span></span></div>')


FLAG = '<path d="M6 21V3.5h10.5l-.9 2.6H20v9.4h-8.8l.9-2.6H8.2V21z" fill="#fff"/>'
svg = (f'<path id="dimTN" d="{rect_d} {d_of(hcm, True)}" fill-rule="evenodd"/>'
       f'<path id="hcmFill" d="{d_of(hcm, True)}"/>'
       f'<clipPath id="hcmClip"><path d="{d_of(hcm, True)}"/></clipPath>'
       f'<path id="hcmEdge" d="{d_of(hcm, True)}" clip-path="url(#hcmClip)"/>')
for nm, pts in (("nA", nA), ("nB", nB), ("fA", fA), ("fB", fB)):
    if len(pts) < 2: continue
    dd = d_of(pts)
    svg += (f'<g id="b_{nm}"><path class="bu" d="{dd}" pathLength="1"/><path class="bg" d="{dd}" pathLength="1"/>'
            f'<path class="bc" d="{dd}" pathLength="1"/><path class="bf" d="{dd}" pathLength="1"/></g>')
rd = d_of(route)
svg += (f'<g id="route"><path class="ru" d="{rd}" pathLength="1"/><path class="rg" d="{rd}" pathLength="1"/>'
        f'<path class="rc" d="{rd}" pathLength="1"/><path class="rf" d="{rd}" pathLength="1"/></g>')

bp = next((p for p in samples(nB, 90) if math.dist(p, (CX, CY)) > 330), nB[-1])
BCH = (round(bp[0], 1), round(bp[1], 1))
SAMP = {"nA": samples(nA, 90), "nB": samples(nB, 90), "route": samples(route, 120)}
SAMP = {k: v for k, v in SAMP.items() if len(v) > 2}

# audio
sfx = [("riser", 0.0), ("boom", 0.9), ("pop", 8.7)] + [("whoosh", c[0]) for c in CAM[1:]]
sfx += [("draw", T_BORDER), ("chime", T_FILL), ("pop", T_TXT + 0.9), ("draw", T_ROUTE), ("pop", T_ROUTE + D_ROUTE), ("chime", T_HUD),
        ("boom", T_FARB), ("chime", T_SUM)]
SFXLEN = {"riser": 1.5, "boom": 1.8, "whoosh": 1.4, "pop": 0.35, "chime": 1.6, "draw": 3.0}
VOL = {"riser": 0.5, "boom": 0.7, "whoosh": 0.55, "pop": 0.6, "chime": 0.5, "draw": 0.35}
audio = "".join(f'<audio id="sfx{i}" class="clip" src="assets/sfx/{n}.wav" data-start="{t:.2f}" data-duration="{min(SFXLEN[n], DUR - t):.2f}" data-track-index="{10 + i % 6}" data-volume="{VOL[n]}"></audio>'
                for i, (n, t) in enumerate(sorted(sfx, key=lambda s: s[1])))
bgm = ""
if os.path.exists(f"{P}/assets/bgm.wav"):
    with wave.open(f"{P}/assets/bgm.wav") as w: BL = w.getnframes() / w.getframerate()
    t = 0; n = 0
    while t < DUR - 0.05:
        d = min(BL, DUR - t)
        bgm += f'<audio id="bgm{n}" class="clip" src="assets/bgm.wav" data-start="{t:.2f}" data-duration="{d:.2f}" data-media-start="0" data-track-index="{8 + n % 2}" data-volume="0.3"></audio>'
        t += d; n += 1

summary = "".join(f'<div class="srow"><i style="background:{c}"><svg viewBox="0 0 24 24">{ic}</svg></i><span>{a}</span><b>{b}</b><em>{e}</em></div>' for c, ic, a, b, e in [
    ("#FF3B5C", FLAG, "Ranh TP.HCM (ô tô)", km(ROUTE_M), mins(ROUTE_S)),
    ("#2EC4FF", '<circle cx="12" cy="12" r="7" fill="none" stroke="#fff" stroke-width="2.6"/><circle cx="12" cy="12" r="2.6" fill="#fff"/>', "Chim bay tới ranh", km(AIR_M), ""),
])

rep = {
    "%DUR%": str(DUR), "%W%": str(W), "%H%": str(H), "%HX%": str(HX), "%HY%": str(HY), "%CX%": str(CX), "%CY%": str(CY),
    "%DX%": str(DET["x"]), "%DY%": str(DET["y"]), "%DW%": str(DET["w"]), "%DH%": str(DET["h"]),
    "%FX%": str(FAR["x"]), "%FY%": str(FAR["y"]), "%FW%": str(FAR["w"]), "%FH%": str(FAR["h"]),
    "%SVG%": svg, "%LABELS%": "".join(label_html(L) for L in LBL), "%CAM%": json.dumps(CAM), "%SAMP%": json.dumps(SAMP),
    "%FLAG%": FLAG, "%BCX%": str(BCH[0]), "%BCY%": str(BCH[1]), "%RM%": km(ROUTE_M), "%RS%": mins(ROUTE_S), "%AIR%": km(AIR_M), "%SUMMARY%": summary,
    "%AUDIO%": audio, "%BGM%": bgm,
    "%T_BORDER%": str(T_BORDER), "%D_BORDER%": str(D_BORDER), "%T_FILL%": str(T_FILL), "%T_TXT%": str(T_TXT),
    "%T_ROUTE%": str(T_ROUTE), "%D_ROUTE%": str(D_ROUTE), "%T_HUD%": str(T_HUD), "%T_HUD_OUT%": str(T_HUD_OUT),
    "%T_FARB%": str(T_FARB), "%T_SUM%": str(T_SUM),
}
html = open(f"{P}/template.tpl", encoding="utf-8").read()
for a, b in rep.items(): html = html.replace(a, b)
open(f"{P}/index.html", "w", encoding="utf-8").write(html)
json.dump({"route_m": ROUTE_M, "route_s": ROUTE_S, "air_m": round(AIR_M), "cross": [cla, clo], "home": HOME, "cams": CAM},
          open(f"{P}/map/layout.json", "w"), indent=1)
print(f"index.html {len(html)//1024} KB · route {ROUTE_M} m {ROUTE_S}s · air {AIR_M:.0f} m · border near {len(nA)}+{len(nB)} far {len(fA)}+{len(fB)} pts")
