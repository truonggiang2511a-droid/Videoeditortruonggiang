#!/usr/bin/env python3
"""Video quang cao ban do vi tri (kieu "flycam ban do" co giong doc AI).

    python3 promo.py config.json PROJECT_DIR

Can chay truoc: fetch.py (anh ve tinh, duong chinh), poi.py (tien ich + vung hanh chinh), giong doc (assets/vo/...).
Canh quay (tu dong can khung, khong dat tay):
  intro  toan canh tinh/thanh, to mau xa + TP, tieu de          (zoom in cham, xoay nhe)
  border duong ranh phat sang + co "qua ranh" (neu co cfg.border)  (zoom vao, pan doc ranh)
  home   ghim nha + gon song, line ra duong chinh "200 MET"        (zoom sat, day vao)
  roads  ve cac truc lon + chu 3D in det                           (zoom ra, xoay vong)
  near / far / extra  the anh tien ich + so km, so phut (KHONG ve duong toi tien ich)  (pan trai / pan phai)
  slogan quay vong quanh nha + cau slogan
  cta    zoom ve nha + loi keu goi (khong so dien thoai)
In ra bao cao chong chu; mo snapshot kiem tra truoc khi render.
"""
import json, math, os, re, shutil, subprocess, sys, wave

KIT = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
P = sys.argv[2]
WM = json.load(open(f"{P}/map/mosaics.json"))
HOME = tuple(cfg["home"])


def px(lat, lon):
    n = 2 ** 16; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return round(x * 256 - WM["wide"]["tx0"] * 256, 1), round(y * 256 - WM["wide"]["ty0"] * 256, 1)


def place(mm):
    s = 2 ** (16 - mm["z"])
    return {"x": mm["tx0"] * 256 * s - WM["wide"]["tx0"] * 256, "y": mm["ty0"] * 256 * s - WM["wide"]["ty0"] * 256, "w": mm["w"] * s, "h": mm["h"] * s}


W, H = WM["wide"]["w"], WM["wide"]["h"]; DET = place(WM["detail"]); FAR = place(WM["far"])
FAR_R = (FAR["x"], FAR["y"], FAR["x"] + FAR["w"], FAR["y"] + FAR["h"])
OUT = place(WM["outer"]) if "outer" in WM else FAR
OUT_R = (OUT["x"], OUT["y"], OUT["x"] + OUT["w"], OUT["y"] + OUT["h"])
HX, HY = px(*HOME)
MPP = 156543.03 * math.cos(math.radians(HOME[0])) / 2 ** 16  # metres per world px

ICON = {
    "road": '<path d="M9 3h6l3 18H6z" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M12 6v3M12 12v3M12 18v2" stroke="#fff" stroke-width="2.2"/>',
    "market": '<path d="M3 9l2-5h14l2 5" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M3 9h18v3a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z" fill="#fff"/><path d="M5 14v6h14v-6" fill="none" stroke="#fff" stroke-width="2.2"/>',
    "school": '<path d="M2 9l10-5 10 5-10 5z" fill="#fff"/><path d="M6 11v5c3 2.5 9 2.5 12 0v-5" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M21 9v6" stroke="#fff" stroke-width="2"/>',
    "gov": '<path d="M3 9l9-5 9 5z" fill="#fff"/><path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18" stroke="#fff" stroke-width="2.2"/>',
    "hospital": '<rect x="4" y="4" width="16" height="16" rx="3" fill="#fff"/><path d="M12 7.5v9M7.5 12h9" stroke="#E3161B" stroke-width="3.2"/>',
    "clinic": '<rect x="4" y="4" width="16" height="16" rx="3" fill="#fff"/><path d="M12 7.5v9M7.5 12h9" stroke="#E3161B" stroke-width="3.2"/>',
    "city": '<path d="M3 21V11h4V6h5v6h3V3h5v18z" fill="#fff"/><path d="M2 21h20" stroke="#fff" stroke-width="2"/>',
    "park": '<circle cx="12" cy="9" r="6" fill="#fff"/><path d="M12 14v8" stroke="#fff" stroke-width="2.4"/>',
    "shop": '<path d="M4 8h16l-1 13H5z" fill="#fff"/><path d="M8 8a4 4 0 0 1 8 0" fill="none" stroke="#fff" stroke-width="2.2"/>',
    "factory": '<path d="M2 21V10l6 4V10l6 4V6h4l1 15z" fill="#fff"/>',
    "flag": '<path d="M6 21V3.5h10.5l-.9 2.6H20v9.4h-8.8l.9-2.6H8.2V21z" fill="#fff"/>',
}
COLOR = {"market": "#2BB673", "school": "#3D7BFF", "gov": "#C7372F", "hospital": "#E3161B", "clinic": "#E3161B", "city": "#8E44EC",
         "park": "#3FA34D", "shop": "#E0629A", "factory": "#7A5CFF", "road": "#18A9C9", "flag": "#FF2E63"}
ROADCOL = {"q": "#FFB020", "t": "#2EE6FF", "w": "#FF4FD8"}


def km_txt(m): return f"{round(m, -1):.0f} m" if m < 1000 else f"{m/1000:.1f}".replace(".", ",") + " km"
def min_txt(s): return f"~{max(1, round(s / 60))} phút"
def esc(t): return t.replace("&", "&amp;").replace("<", "&lt;")


# ---------- camera (same math as apply() in the template) ----------
PD = 1800
def proj(wx, wy, c):
    x, y, z, t, r = c
    dx, dy = (wx - x) * z, (wy - y) * z
    a = math.radians(r); rx, ry = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
    sx, sy = 540 + rx, 900 + ry
    tt = math.radians(t); yr = (sy - 900) * math.cos(tt) + 900; zr = (sy - 900) * math.sin(tt); k = PD / (PD - zr) if PD - zr > 50 else 36
    return 540 + (sx - 540) * k, 800 + (yr - 800) * k


def fit_cards(pts, tilt, safe, zmin, zmax):
    v = fit(pts, tilt, 0, safe, zmin, zmax, pad=60)
    for _ in range(2):
        wide = pts + [(x + dx / v[2], y) for x, y in pts[1:] for dx in (-150, 150)]
        v = fit(wide, tilt, 0, safe, zmin, zmax, pad=40)
    return v


def fit(pts, tilt, rot, safe, zmin, zmax, pad=60):
    """largest zoom (<= zmax) that keeps every world point inside the safe screen rect"""
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    sx0, sy0, sx1, sy1 = safe[0] + pad, safe[1] + pad, safe[2] - pad, safe[3] - pad
    best = None
    lo, hi = math.log2(zmin), math.log2(zmax)
    for _ in range(26):
        mid = (lo + hi) / 2; z = 2 ** mid
        x, y = cx, cy
        for _ in range(6):  # re-centre so the projected bbox sits in the middle of the safe rect
            S = [proj(p[0], p[1], (x, y, z, tilt, rot)) for p in pts]
            mx = ((min(s[0] for s in S) + max(s[0] for s in S)) / 2 - (sx0 + sx1) / 2)
            my = ((min(s[1] for s in S) + max(s[1] for s in S)) / 2 - (sy0 + sy1) / 2)
            a = math.radians(-rot); ddx, ddy = mx * math.cos(a) - my * math.sin(a), mx * math.sin(a) + my * math.cos(a)
            x += ddx / z; y += ddy / z * 0.85
        S = [proj(p[0], p[1], (x, y, z, tilt, rot)) for p in pts]
        ok = all(sx0 <= s[0] <= sx1 and sy0 <= s[1] <= sy1 for s in S)
        if ok: best = (x, y, z); lo = mid
        else: hi = mid
    if not best: best = (x, y, zmin)
    return best


# ---------- data ----------
pois = json.load(open(f"{P}/map/pois.json", encoding="utf-8"))
for i, p in enumerate(pois): p["i"] = i; p["w"] = px(*p["at"])
regions = json.load(open(f"{P}/map/regions.json", encoding="utf-8")) if os.path.exists(f"{P}/map/regions.json") else []
roads = json.load(open(f"{P}/map/roads.json"))
roads_auto = json.load(open(f"{P}/map/roads_auto.json", encoding="utf-8")) if os.path.exists(f"{P}/map/roads_auto.json") else []
roads_auto = [r for r in roads_auto if r["key"] not in cfg.get("roads_skip", [])]
for r in roads_auto: r["label"] = cfg.get("road_labels", {}).get(r["key"], r["label"])
RL = {k: [[px(la, lo) for lo, la in l] for l in v] for k, v in roads.items()}


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
    for f in (lambda q: q[0] >= x0, lambda q: q[0] <= x1, lambda q: q[1] >= y0, lambda q: q[1] <= y1):
        pass
    poly = cut(poly, lambda q: q[0] >= x0, lambda a, b: ix(a, b, x0)); poly = cut(poly, lambda q: q[0] <= x1, lambda a, b: ix(a, b, x1))
    poly = cut(poly, lambda q: q[1] >= y0, lambda a, b: iy(a, b, y0)); poly = cut(poly, lambda q: q[1] <= y1, lambda a, b: iy(a, b, y1))
    return poly


def inside(pt, ring):
    x, y = pt; c = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay): c = not c
    return c


def d_of(pts, close=False): return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + (" Z" if close else "")


def nearest_on(lines, p):
    best = (1e18, None, 0)
    for l in lines:
        for a, b in zip(l, l[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy or 1
            t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)); q = (a[0] + t * dx, a[1] + t * dy); d = math.dist(p, q)
            if d < best[0]: best = (d, q, math.degrees(math.atan2(dy, dx)))
    return best


for rg in regions:
    rg["w"] = [px(la, lo) for lo, la in rg["ring"]]
    def thin(ring, tol):
        out = [ring[0]]
        for q in ring[1:]:
            if math.dist(q, out[-1]) >= tol: out.append(q)
        return out
    # two copies: a coarse one for the high opening shot, a finer one clipped to the area the other shots can see
    rg["clip_big"] = clip_rect(thin(rg["w"], 60), OUT_R)
    m_ = 2500
    rg["clip"] = clip_rect(thin(rg["w"], 6), (FAR_R[0] + m_, FAR_R[1] + m_, FAR_R[2] - m_, FAR_R[3] - m_))

# border with the neighbouring city: crossing point and the boundary run that passes the house
B = cfg.get("border")
if B:
    brg = next(r for r in regions if r["label"] == B["region"])
    CX, CY = px(*B["cross"])
    ring = brg["w"]; M = 300
    ins = [FAR_R[0] + M < x < FAR_R[2] - M and FAR_R[1] + M < y < FAR_R[3] - M for x, y in ring]
    runs, cur = [], []
    for p_, i_ in zip(ring, ins):
        if i_: cur.append(p_)
        elif cur: runs.append(cur); cur = []
    if cur: runs.append(cur)
    run = min(runs, key=lambda r: min(math.dist(q, (CX, CY)) for q in r))
    kc = min(range(len(run)), key=lambda i: math.dist(run[i], (CX, CY)))
    def split(seq, NEAR=1500):
        near, far = [(CX, CY)], []
        for q in seq: (near if not far and math.dist(q, (CX, CY)) < NEAR else far).append(q)
        if far: far = [near[-1]] + far
        return near, far
    bnA, bfA = split(run[kc::-1]); bnB, bfB = split(run[kc + 1:])

# access road: straight line from the house to the nearest point of the main road + "200 MÉT"
A = cfg.get("access_road")
if A:
    _, (AX, AY), _ = nearest_on(RL[A["key"]], (HX, HY))
    A_M = A.get("show_m") or round(math.dist((HX, HY), (AX, AY)) * MPP)

# ---------- voice segments -> timeline ----------
VO = cfg["vo"]; segs = VO["segs"]
def parts(k): v = segs[k]; return v if isinstance(v[0], list) else [v]
ORDER = [k for k in ["intro", "border", "home", "roads", "near", "far", "extra", "slogan", "cta"] if k in segs]
GAP, SUBGAP = cfg.get("gap", 1.1), cfg.get("sub_gap", 0.9)
T = {}; PARTS = {}; t = cfg.get("vo_start", 2.4)
for k in ORDER:
    t0 = t; PARTS[k] = []
    for j, (a, b) in enumerate(parts(k)):
        PARTS[k].append((a, b, t)); t += b - a + (SUBGAP if j + 1 < len(parts(k)) else 0)
    T[k] = (t0, t - t0); t += GAP + (0.6 if k in ("home", "roads", "extra") else 0) + (0.8 if len(parts(k)) > 1 else 0)
DUR = round(t - GAP + cfg.get("tail", 3.6), 2)
def vt(k, off):
    """offset in the original recording (from the segment's first word) -> video time"""
    o = PARTS[k][0][0] + off; best = PARTS[k][0]
    for pa in PARTS[k]:
        if o >= pa[0]: best = pa
    return best[2] + min(o, best[1] + 0.3) - best[0]

T_TITLE_OUT0 = min(T["intro"][0] + T["intro"][1] + 0.2, 4.4)
# ---------- shots ----------
SAFE_CARDS = (60, 330, 1020, 1480)
SAFE_FULL = (60, 330, 1020, 1520)
near_pois = [p for p in pois if p["air_m"] <= cfg.get("near_m", 2500)]
far_pois = [p for p in pois if p["air_m"] > cfg.get("near_m", 2500)]
extra_pois = [p for p in far_pois if p["icon"] in ("hospital",) and "extra" in segs]
far_pois = [p for p in far_pois if p not in extra_pois]
CAMS = []  # [t0, dur, x, y, z, tilt, rot]
def cam(t0, d, xyz, tilt, rot): CAMS.append([round(t0, 2), round(d, 2), round(xyz[0], 1), round(xyz[1], 1), round(xyz[2], 4), tilt, rot])

hcm_far = None
# intro: wide view over both regions
pts_intro = [(HX, HY)] + [p["w"] for p in pois]
if B: pts_intro += [(CX, CY)]
def clamp_to(R, x, y, z, m=1.25):
    hw, hh = 640 * m / z, 1250 * m / z
    return (min(max(x, R[0] + hw), R[2] - hw), min(max(y, R[1] + hh), R[3] - hh))
zi0 = max(0.056, 1250 * 1.25 * 2 / (OUT_R[3] - OUT_R[1]), 640 * 1.25 * 2 / (OUT_R[2] - OUT_R[0]))
zi1 = max(0.2, 1250 * 1.25 * 2 / (FAR_R[3] - FAR_R[1]))
ix, iy = HX, HY - 600 / zi0
if B: ix, iy = HX + (CX - HX) * 6, HY + (CY - HY) * 6 - 500 / zi0
ix, iy = clamp_to(OUT_R, ix, iy, zi0)
CAMS.append([0, 0.01, round(ix, 1), round(iy, 1), round(zi0, 4), 8, -10])
cam(0.02, T["intro"][0] + T["intro"][1] + 0.6, clamp_to(FAR_R, HX, HY - 250 / zi1, zi1) + (zi1,), 16, 0)
SHOTS = {}
# border
if B and "border" in T:
    t0 = T["border"][0] - 1.4
    bpts = [q for q in bnA + bnB if math.dist(q, (CX, CY)) < 700]
    v = fit([(HX, HY), (CX, CY)] + bpts[::3], 30, 0, (60, 520, 1020, 1400), 0.4, 1.2, pad=110)
    cam(t0, 1.8, v, 30, 0); SHOTS["border"] = (t0 + 1.8, v, 30, 0)
    cam(t0 + 1.9, T["border"][1] + 0.4, (v[0] + 140 / v[2], v[1] - 30 / v[2], v[2] * 1.06), 32, 0)  # pan right along the boundary
# home
t0 = T["home"][0] - 1.6
hp = [(HX, HY)] + ([(AX, AY)] if A else [])
v = fit(hp + [(HX, HY - 260), (HX + 140, HY + 40), (HX - 140, HY + 40)], 40, 0, (60, 380, 1020, 1300), 1.4, 3.4, pad=80)
cam(t0, 2.0, v, 40, 0); SHOTS["home"] = (t0 + 2.0, v, 40, 0)
cam(t0 + 2.05, T["home"][1] + 1.6, (v[0], v[1], v[2] * 1.12), 42, 0)  # slow push-in
# roads: orbit while the axes draw
t0 = T["roads"][0] - 1.4
rpts = [(HX, HY)]
for r in roads_auto:
    for l in RL[r["key"]]:
        rpts += [q for q in l[::3] if math.dist(q, (HX, HY)) < 2600]
v = fit(rpts, 28, 8, SAFE_FULL, 0.2, 0.7, pad=70); v = (v[0], v[1], v[2] * 0.78)
cam(t0, 1.8, v, 28, 8); SHOTS["roads"] = (t0 + 1.8, v, 28, 8)
cam(t0 + 1.85, T["roads"][1] + 1.6, (v[0], v[1], v[2] * 1.04), 30, -8)
# POI groups: pan left for the near group, pan right for the far one
cues = cfg.get("poi_cues", {})
def cue(key, p, j, n): return vt(key, cues[p["label"]]) if p["label"] in cues else T[key][0] + 0.4 + j * (T[key][1] - 0.8) / max(1, n)
UNITS = []  # (key, pois, t_cards_in, t_cards_out, t_layout, t_layout_end)
CARD_SAFE = (90, 640, 990, 1420)  # points sit low so the cards above them have room
def poi_shot(key, group, t0, pan, tilt=32):
    pts = [(HX, HY)] + [p["w"] for p in group]
    v = fit_cards(pts, tilt, CARD_SAFE, 0.12, 1.3)
    cam(t0, 1.8, v, tilt, 0); SHOTS[key] = (t0 + 1.8, v, tilt, 0)
    cam(t0 + 1.85, T[key][1] + 0.9, (v[0] + pan / v[2], v[1], v[2] * 1.04), tilt + 2, 0)
    UNITS.append((key, group, None, T[key][0] + T[key][1] + 0.7, T[key][0] + T[key][1] * 0.5, T[key][0] + T[key][1]))
def follow_shot(key, group, tilt=32):
    """far places: the camera pans left / right to each cluster in the order they are spoken"""
    order = sorted(group, key=lambda p: cue(key, p, group.index(p), len(group)))
    clusters = []
    for p in order:
        if clusters and math.dist(p["w"], clusters[-1][-1]["w"]) < 1400: clusters[-1].append(p)
        else: clusters.append([p])
    for ci, cl in enumerate(clusters):
        tc = cue(key, cl[0], group.index(cl[0]), len(group))
        t_end = cue(key, clusters[ci + 1][0], group.index(clusters[ci + 1][0]), len(group)) - 1.25 if ci + 1 < len(clusters) else T[key][0] + T[key][1] + 0.9
        v = fit_cards([(HX, HY)] + [p["w"] for p in cl], tilt, CARD_SAFE, 0.12, 0.9)
        t0 = tc - 1.25
        cam(t0, 1.15, v, tilt, 0)
        if ci == 0: SHOTS[key] = (t0 + 1.15, v, tilt, 0)
        drift = 50 if v[0] > HX else -50
        cam(t0 + 1.2, max(0.4, t_end - t0 - 1.2), (v[0] + drift / v[2], v[1], v[2] * 1.03), tilt + 1, 0)
        UNITS.append((key, cl, None, t_end, t0 + 1.2 + (t_end - t0 - 1.2) * 0.4, t_end))
if near_pois and "near" in T: poi_shot("near", near_pois, T["near"][0] - 1.3, -70)
if far_pois and "far" in T: follow_shot("far", far_pois)
if extra_pois and "extra" in T: poi_shot("extra", extra_pois, T["extra"][0] - 1.4, 40)
# slogan: orbit around the house with every place on screen
t0 = T["slogan"][0] - 1.4
v = fit([(HX, HY)] + [p["w"] for p in near_pois], 36, 0, (90, 620, 990, 1450), 0.2, 0.9, pad=60)
cam(t0, 1.8, (HX, HY + 120 / v[2], v[2]), 36, 0); SHOTS["slogan"] = (t0 + 1.8, (HX, HY + 120 / v[2], v[2]), 36, 0)
cam(t0 + 1.85, T["slogan"][1] + 1.6, (HX, HY + 120 / v[2], v[2] * 1.08), 38, 60)
# cta: back to the house
t0 = T["cta"][0] - 1.0
cam(t0, 1.6, (HX, HY + 120, 2.2), 44, 18); SHOTS["cta"] = (t0 + 1.6, (HX, HY + 120, 2.2), 44, 18)
cam(t0 + 1.65, DUR - t0 - 1.65, (HX, HY + 110, 2.45), 46, 26)


def cam_at(tq):
    s = [CAMS[0][2], CAMS[0][3], math.log2(CAMS[0][4]), CAMS[0][5], CAMS[0][6]]
    for t0, d, x, y, z, ti, ro in CAMS:
        if tq <= t0: break
        f = min(1, (tq - t0) / d) if d > 0 else 1; e = -(math.cos(math.pi * f) - 1) / 2
        tgt = [x, y, math.log2(z), ti, ro]
        s = [a + (b - a) * e for a, b in zip(s, tgt)]
    return (s[0], s[1], 2 ** s[2], s[3], s[4])


# ---------- card layout (screen space, chosen once per shot) ----------
CW, CH = 270, 236  # card box: picture 270x170 + name + distance
HOME_TAG = (-150, -230, 150, -130)
def rect_overlap(a, b): return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
OFFS = [(0, -150), (-170, -130), (170, -130), (0, -250), (-200, -60), (200, -60), (0, 150), (-180, 120), (180, 120)]
layout = {}
report = []
for key, group, _, t_out, t_lay, t_lay2 in UNITS:
    c = cam_at(t_lay); c2 = cam_at(t_lay2)
    hx, hy = proj(HX, HY, c)
    taken = [(hx + HOME_TAG[0], hy + HOME_TAG[1], hx + HOME_TAG[2], hy + 10)]
    pts = {p["i"]: proj(*p["w"], c) for p in group}
    for p in group: taken.append((pts[p["i"]][0] - 34, pts[p["i"]][1] - 34, pts[p["i"]][0] + 34, pts[p["i"]][1] + 34))
    for p in sorted(group, key=lambda p: pts[p["i"]][1]):
        sx, sy = pts[p["i"]]; sx2, sy2 = proj(*p["w"], c2)
        best = None
        for ox, oy in OFFS:
            cx_, cy_ = sx + ox, sy + oy
            box = (cx_ - CW / 2, cy_ - CH if oy < 0 else cy_, cx_ + CW / 2, cy_ if oy < 0 else cy_ + CH)
            box2 = (box[0] + sx2 - sx, box[1] + sy2 - sy, box[2] + sx2 - sx, box[3] + sy2 - sy)
            cost = sum(rect_overlap(box, r) for r in taken) * 3
            for bb in (box, box2):
                cost += 40 * (max(0, SAFE_CARDS[0] - bb[0]) + max(0, bb[2] - SAFE_CARDS[2]) + max(0, SAFE_CARDS[1] - bb[1]) + max(0, bb[3] - SAFE_CARDS[3])) * CH
            cost += (abs(ox) + abs(oy)) * 2
            if best is None or cost < best[0]: best = (cost, ox, oy, box)
        cost, ox, oy, box = best
        taken.append(box); layout[p["i"]] = (ox, oy)
        if cost > 5000: report.append(f"! the {p['label']} ({key}) chen / sat mep: cost {cost:.0f}")


# ---------- flat 3D labels (world space) ----------
LBL = []
def add_label(id_, x, y, size, cls, big, small="", ang=0):
    LBL.append(dict(id=id_, x=round(x, 1), y=round(y, 1), size=round(size), cls=cls, big=big, small=small, a=round(ang, 1)))

def first_inside(start, d, ring, steps, avoid=()):
    for s in steps:
        q = (start[0] + d[0] * s, start[1] + d[1] * s)
        if inside(q, ring) and all(math.dist(q, a) > 260 for a in avoid): return q
    return (start[0] + d[0] * steps[0], start[1] + d[1] * steps[0])

ci_ = cam_at(T["intro"][0] + T["intro"][1] + 0.3); ci0_ = cam_at(T_TITLE_OUT0 + 0.8)
used = [proj(HX, HY, ci_)]
for rg in regions:
    sty = "c" if rg.get("color") == "cyan" else "g"
    if B and rg["label"] == B["region"]:
        dx, dy = CX - HX, CY - HY; n = math.hypot(dx, dy); d = (dx / n, dy / n)
        q = first_inside((CX, CY), d, rg["w"], range(380, 1600, 60), avoid=[p["w"] for p in pois])
        add_label("rl_near_" + str(regions.index(rg)), q[0], q[1], 64 / SHOTS["border"][1][2], sty, rg["label"], rg.get("near_sub", ""))
    # wide shot name: a point inside the area that lands low on screen (under the title), away from the pin and other names
    best = None
    for gx in range(30):
        for gy in range(30):
            q = (ci_[0] + (gx / 29 - 0.5) * 1300 / ci_[2], ci_[1] + (gy / 29 - 0.5) * 2600 / ci_[2])
            s_ = proj(q[0], q[1], ci_)
            szp = 52 if rg.get("sub") else 70; half = max(len(rg["label"]), len(rg.get("sub", "")) * 0.42) * 0.68 * szp / 2
            s0_ = proj(q[0], q[1], ci0_)
            if not all(60 + half < u_[0] < 1020 - half and 640 < u_[1] < 1620 for u_ in (s_, s0_)) or not inside(q, rg["w"]): continue
            if not all(inside((q[0] + ox / ci_[2], q[1]), rg["w"]) for ox in (-40, 40)): continue
            if math.dist(s_, used[0]) < 300 or abs(s_[0] - used[0][0]) < 260 and -330 < s_[1] - used[0][1] < 90: continue
            cost = -min(math.dist(s_, u) for u in used) + abs(s_[1] - 1050) * 0.2
            if best is None or cost < best[0]: best = (cost, q, s_)
    if not best: report.append(f"! khong dat duoc ten vung {rg['label']}"); continue
    used.append(best[2])
    add_label("rl_far_" + str(regions.index(rg)), best[1][0], best[1][1], (52 if rg.get("sub") else 70) / ci_[2], sty, rg["label"], rg.get("sub", ""))

# road names: on a stretch of each road that stays on screen through the whole orbit, clear of the house label and other names
rcs = [cam_at(SHOTS["roads"][0] - 0.2), cam_at(T["roads"][0] + T["roads"][1] * 0.5), cam_at(T["roads"][0] + T["roads"][1] + 0.6)]
road_boxes = []
def lbl_box(q, ang, wv, hv, c):
    s_ = proj(q[0], q[1], c); a = math.radians(ang + c[4])
    hw = (abs(math.cos(a)) * wv + abs(math.sin(a)) * hv) / 2; hh = (abs(math.sin(a)) * wv + abs(math.cos(a)) * hv) / 2 * math.cos(math.radians(c[3]))
    return (s_[0] - hw, s_[1] - hh, s_[0] + hw, s_[1] + hh)
for r in roads_auto:
    z_ = rcs[1][2]; size = round(54 / z_); text = r["label"]
    lines = text.split("\n"); em_w = max(len(lines[0]), len(lines[1]) * 0.42 if len(lines) > 1 else 0)
    wv = em_w * size * 0.66 * z_
    if wv > 700: size = round(size * 700 / wv); wv = 700
    hv = size * z_ * (1.55 if len(lines) > 1 else 1.05)
    best = None
    for l in RL[r["key"]]:
        for a_, b_ in zip(l, l[1:]):
            ang = math.degrees(math.atan2(b_[1] - a_[1], b_[0] - a_[0]))
            if ang > 90: ang -= 180
            if ang < -90: ang += 180
            nseg = max(1, int(math.dist(a_, b_) / 60))
            for f in [(j_ + 0.5) / nseg for j_ in range(nseg)]:
                q = (a_[0] + (b_[0] - a_[0]) * f, a_[1] + (b_[1] - a_[1]) * f)
                cost = 0
                for c in rcs:
                    bx = lbl_box(q, ang, wv, hv, c); hs = proj(HX, HY, c)
                    cost += 220 * (max(0, 50 - bx[0]) + max(0, bx[2] - 1030) + max(0, 320 - bx[1]) + max(0, bx[3] - 1480))
                    cost += rect_overlap(bx, (hs[0] - 190, hs[1] - 260, hs[0] + 190, hs[1] + 50)) * 4
                    cost += sum(rect_overlap(bx, o) for o in road_boxes if o[4] == rcs.index(c)) * 4
                cost += abs(proj(q[0], q[1], rcs[1])[1] - 950) * 0.3
                if best is None or cost < best[0]: best = (cost, q, ang)
                if os.environ.get("DBG") == r["key"] and proj(q[0], q[1], rcs[1])[1] < 700: print("DBG", [round(v) for v in proj(q[0], q[1], rcs[1])], round(cost), round(ang))
    if not best: continue
    cost, q, ang = best
    if cost > 4000:
        bx = [tuple(round(v) for v in lbl_box(q, ang, wv, hv, c)) for c in rcs]
        report.append(f"! chu duong {text!r} bi chen / sat mep (cost {cost:.0f}) w{wv:.0f} h{hv:.0f} {bx}")
    for ci, c in enumerate(rcs): road_boxes.append(lbl_box(q, ang, wv, hv, c) + (ci,))
    big, small = (lines[0], lines[1]) if len(lines) > 1 else (text, "")
    add_label("rd_" + r["key"], q[0], q[1], size, r["style"], big, small, ang)

if A:
    ang = math.degrees(math.atan2(AY - HY, AX - HX))
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    hz = SHOTS["home"][1][2]
    add_label("acc_txt", (HX + AX) / 2, (HY + AY) / 2, 44 / hz, "y", f"{A_M} MÉT", "", ang)
    _, aq, aang = nearest_on(RL[A["key"]], (AX, AY))
    nrm = (math.cos(math.radians(aang + 90)), math.sin(math.radians(aang + 90)))
    side = 1 if (nrm[0] * (HX - AX) + nrm[1] * (HY - AY)) < 0 else -1
    if aang > 90: aang -= 180
    if aang < -90: aang += 180
    add_label("acc_road", AX + nrm[0] * side * 55 / hz, AY + nrm[1] * side * 55 / hz, 40 / hz, "t", A.get("label", ""), "", aang)

# ---------- html ----------
def label_html(L):
    t = esc(L["big"]) + (f"<br><small>{esc(L['small'])}</small>" if L["small"] else "")
    return (f'<div class="flat {L["cls"]}" style="left:{L["x"]}px;top:{L["y"]}px;font-size:{L["size"]}px;--a:{L["a"]}deg">'
            f'<span class="rti" id="{L["id"]}"><span class="ex">{t}</span><span class="fc">{t}</span></span></div>')

svg = ""; regsvg = ""
REG_FILL = {"cyan": ("rgba(46,214,255,0.22)", "#2EE6FF"), "green": ("rgba(52,226,128,0.26)", "#3BF08A")}
for i, rg in enumerate(regions):
    fill, edge = REG_FILL.get(rg.get("color", "green"))
    svg_r = f'<g class="reg" id="reg{i}" style="--edge:{edge}">'
    for nm, key, zr in (("b", "clip_big", "0,0.3"), ("n", "clip", "0.3,99")):
        if len(rg[key]) < 3: continue
        d = d_of(rg[key], True)
        svg_r += (f'<g class="lodz" data-z="{zr}"><path class="rfill" d="{d}" fill="{fill}"/><path class="redge" d="{d}"/>'
                  f'<path class="rline" d="{d}" pathLength="1"/></g>')
    regsvg += svg_r + '</g>'
if B:
    for nm, pts in (("nA", bnA), ("nB", bnB), ("fA", bfA), ("fB", bfB)):
        if len(pts) < 2: continue
        d = d_of(pts)
        svg += (f'<g id="b_{nm}"><path class="bu" d="{d}" pathLength="1"/><path class="bg" d="{d}" pathLength="1"/>'
                f'<path class="bc" d="{d}" pathLength="1"/><path class="bf" d="{d}" pathLength="1"/></g>')
for r in roads_auto:
    d = " ".join(d_of(l) for l in RL[r["key"]])
    col = ROADCOL[r["style"]]
    svg += (f'<g class="road" id="road_{r["key"]}" style="--rc:{col}"><path class="rgl" d="{d}" pathLength="1"/>'
            f'<path class="rco" d="{d}" pathLength="1"/><path class="rda" d="{d}"/></g>')
if A:
    d = d_of([(HX, HY), (AX, AY)])
    svg += f'<g id="acc"><path class="ag" d="{d}" pathLength="1"/><path class="ac" d="{d}" pathLength="1"/></g>'

def card_html(p):
    ox, oy = layout.get(p["i"], (0, -150))
    up = oy < 0
    stem = math.hypot(ox, oy)
    ang = math.degrees(math.atan2(-ox, oy))  # rotate a downward stem onto the card
    return (f'<div class="poi" id="poi{p["i"]}" data-w="{p["w"][0]},{p["w"][1]}">'
            f'<div class="stem" style="height:{stem:.0f}px;transform:rotate({ang:.1f}deg)"><i id="st{p["i"]}"></i></div>'
            f'<div class="badge" id="bd{p["i"]}" style="--c:{COLOR[p["icon"]]}"><svg viewBox="0 0 24 24">{ICON[p["icon"]]}</svg></div>'
            f'<div class="card {"up" if up else "dn"}" id="cd{p["i"]}" style="left:{ox:.0f}px;top:{oy:.0f}px">'
            f'<div class="ph"><img src="{p["img"]}" alt=""/><i>{"ẢNH VỆ TINH" if p.get("img_src") != "anh" else ""}</i></div>'
            f'<b>{esc(p["label"])}</b><span>{km_txt(p["m"])} · {min_txt(p["s"])}</span></div></div>')

group_of = {p["i"]: k for k, g in (("near", near_pois), ("far", far_pois), ("extra", extra_pois)) for p in g}
cards = "".join(card_html(p) for p in pois if p["i"] in group_of)

# ---------- timeline js ----------
js = []
def J(s): js.append(s)
# layers
if "outer" in WM: J('tl.fromTo("#far", { opacity: 0 }, { opacity: 1, duration: 2.4, ease: "sine.inOut" }, %.2f);' % (T["intro"][0] + 0.6))
J('tl.to("#wide", { opacity: 1, duration: 1.6, ease: "sine.inOut" }, %.2f);' % (T["intro"][0] + T["intro"][1] - 0.6))
J('tl.to("#detail", { opacity: 1, duration: 1.2, ease: "sine.inOut" }, %.2f);' % (SHOTS["home"][0] - 1.2))
J('tl.to("#detail", { opacity: 0, duration: 1.0, ease: "sine.inOut" }, %.2f);' % (SHOTS["roads"][0] - 1.8))
J('tl.to("#detail", { opacity: 1, duration: 1.0, ease: "sine.inOut" }, %.2f);' % (SHOTS["cta"][0] - 1.2))
# title
J('tl.fromTo("#title .k", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, 0.3);')
J('tl.fromTo("#title .t", { opacity: 0, scale: 1.25, filter: "blur(10px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.8, ease: "power4.out" }, 0.6);')
J('tl.fromTo("#title .s", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, 1.2);')
J('tl.fromTo("#tplate", { opacity: 0 }, { opacity: 1, duration: 0.6 }, 0.1);')
T_TITLE_OUT = min(T["intro"][0] + T["intro"][1] + 0.2, 4.4)
J('tl.to(["#title", "#tplate"], { opacity: 0, y: -40, duration: 0.5, ease: "power2.in" }, %.2f);' % T_TITLE_OUT)
# home pin + label from the start, ripples all the way
J('tl.fromTo("#homemk", { y: -300, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: "bounce.out" }, 1.2);')
J('tl.fromTo("#hlabel", { opacity: 0, y: 16, scale: 0.8 }, { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: "back.out(2)" }, 1.7);')
J('for (let k = 0; 1.9 + k * 1.1 < DUR - 1.6; k++) tl.fromTo(".rip", { scale: 0.12, opacity: 0.95 }, { scale: 1.6, opacity: 0, duration: 2.2, ease: "power2.out", stagger: 0.55, immediateRender: false }, 1.9 + k * 1.65);')
J('tl.to("#hlabel", { boxShadow: "0 0 0 3px #2EE6FF, 0 0 46px rgba(46,230,255,0.95)", duration: 0.8, repeat: %d, yoyo: true, ease: "sine.inOut" }, 2.2);' % int((DUR - 4) / 0.8))
# regions
for i, rg in enumerate(regions):
    J('tl.to("#reg%d", { opacity: 1, duration: 1.2, ease: "sine.inOut" }, %.2f);' % (i, 1.6 + i * 1.2))
    J('tl.to("#reg%d .rline", { strokeDashoffset: 0, duration: 2.4, ease: "sine.inOut" }, %.2f);' % (i, 1.6 + i * 1.2))
for L in LBL:
    if L["id"].startswith("rl_far"):
        k = int(L["id"].split("_")[-1])
        J('tl.fromTo("#%s", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.9, ease: "back.out(1.7)" }, %.2f);' % (L["id"], T_TITLE_OUT + 0.4 + k * 0.6))
        J('tl.to("#%s", { opacity: 0, duration: 0.6 }, %.2f);' % (L["id"], T["intro"][0] + T["intro"][1] + 0.4))
# border
if B:
    tb = SHOTS["border"][0] - 0.4
    J(f'drawWithComet("nA", "#b_nA .bu, #b_nA .bg, #b_nA .bc", {tb:.2f}, 2.6);')
    J(f'drawWithComet("nB", "#b_nB .bu, #b_nB .bg, #b_nB .bc", {tb:.2f}, 2.6);')
    J('["#b_fA", "#b_fB"].forEach((g) => { if (document.querySelector(g)) tl.to(`${g} .bu, ${g} .bg, ${g} .bc`, { strokeDashoffset: 0, duration: 2.0, ease: "sine.inOut" }, %.2f); });' % (tb + 2.0))
    J('tl.set(".bf", { opacity: 0.95 }, %.2f); tl.fromTo(".bf", { strokeDashoffset: 0 }, { strokeDashoffset: -0.5, duration: %.2f, ease: "none" }, %.2f);' % (tb + 2.6, DUR - tb - 2.6, tb + 2.6))
    J('tl.fromTo("#badgeX", { scale: 0, rotation: -45 }, { scale: 1, rotation: -45, duration: 0.6, ease: "back.out(2.2)" }, %.2f);' % (tb + 2.4))
    J('tl.fromTo("#chipX", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.45, ease: "power3.out" }, %.2f);' % (tb + 2.7))
    J('tl.to("#chipX", { opacity: 0, duration: 0.4 }, %.2f);' % (T["border"][0] + T["border"][1] + 0.6))
    J('tl.to("#badgeX", { opacity: 0, duration: 0.4 }, %.2f);' % (SHOTS["roads"][0] - 1.6))
    for L in LBL:
        if L["id"].startswith("rl_near"):
            J('tl.fromTo("#%s", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.9, ease: "back.out(1.7)" }, %.2f);' % (L["id"], tb + 1.4))
            J('tl.to("#%s", { opacity: 0, duration: 0.5 }, %.2f);' % (L["id"], SHOTS["home"][0] - 2.0))
# home: access line + "200 MÉT"
if A:
    th = SHOTS["home"][0]
    J('tl.to("#acc .ag, #acc .ac", { strokeDashoffset: 0, duration: 1.4, ease: "power2.inOut" }, %.2f);' % (th + 0.2))
    J('tl.fromTo("#acc_txt", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.7, ease: "back.out(2)" }, %.2f);' % (th + 1.4))
    J('tl.fromTo("#acc_road", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.7, ease: "back.out(2)" }, %.2f);' % (th + 0.9))
    J('tl.to(["#acc_txt", "#acc_road"], { opacity: 0, duration: 0.5 }, %.2f);' % (SHOTS["roads"][0] - 1.8))
    J('tl.to(["#acc_txt"], { opacity: 1, duration: 0.5 }, %.2f);' % (SHOTS["cta"][0] - 0.4))
# roads
tr = SHOTS["roads"][0] - 0.6
for k, r in enumerate(roads_auto):
    J('tl.to("#road_%s .rgl, #road_%s .rco", { strokeDashoffset: 0, duration: 1.8, ease: "sine.inOut" }, %.2f);' % (r["key"], r["key"], tr + k * 0.5))
    J('tl.set("#road_%s .rda", { opacity: 1 }, %.2f);' % (r["key"], tr + k * 0.5 + 1.6))
    J('tl.fromTo("#rd_%s", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.9, ease: "back.out(1.7)" }, %.2f);' % (r["key"], tr + k * 0.5 + 1.2))
    J('tl.to("#rd_%s", { opacity: 0, duration: 0.5 }, %.2f);' % (r["key"], T["roads"][0] + T["roads"][1] + 0.8))
J('tl.fromTo(".rda", { strokeDashoffset: 0 }, { strokeDashoffset: -%d, duration: %.2f, ease: "none" }, %.2f);' % (int((DUR - tr) * 120), DUR - tr, tr))
# poi cards: badge pops, card slides from the stem; previous group keeps only its badge
full_group = {"near": near_pois, "far": far_pois, "extra": extra_pois}
for key, group, _, t_out, _, _ in UNITS:
    t0, d = T[key]; fg = full_group[key]
    for p in group:
        tc = cue(key, p, fg.index(p), len(fg))
        J('tl.fromTo("#bd%d", { scale: 0 }, { scale: 1, duration: 0.5, ease: "back.out(2.4)" }, %.2f);' % (p["i"], tc - 0.3))
        J('tl.fromTo("#st%d", { scaleY: 0 }, { scaleY: 1, duration: 0.35, ease: "power2.out" }, %.2f);' % (p["i"], tc))
        J('tl.fromTo("#cd%d", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.8)" }, %.2f);' % (p["i"], tc + 0.2))
        J('tl.to(["#cd%d", "#st%d"], { opacity: 0, duration: 0.35 }, %.2f);' % (p["i"], p["i"], t_out))
# slogan + cta
ts = T["slogan"][0]
J('tl.fromTo("#slogan .l1", { opacity: 0, y: 30, clipPath: "inset(0 100%% 0 0)" }, { opacity: 1, y: 0, clipPath: "inset(0 0%% 0 0)", duration: 0.9, ease: "power2.out" }, %.2f);' % (ts))
J('tl.fromTo("#slogan .l2", { opacity: 0, y: 30, clipPath: "inset(0 100%% 0 0)" }, { opacity: 1, y: 0, clipPath: "inset(0 0%% 0 0)", duration: 0.9, ease: "power2.out" }, %.2f);' % (ts + 1.4))
J('tl.to("#slogan", { opacity: 0, y: -30, duration: 0.5 }, %.2f);' % (T["slogan"][0] + T["slogan"][1] + 0.8))
J('tl.to("#splate", { opacity: 1, duration: 0.6 }, %.2f); tl.to("#splate", { opacity: 0, duration: 0.6 }, %.2f);' % (ts - 0.3, T["slogan"][0] + T["slogan"][1] + 0.8))
tcta = T["cta"][0]
J('tl.fromTo("#cta .c1", { opacity: 0, scale: 1.6 }, { opacity: 1, scale: 1, duration: 0.6, ease: "power4.out" }, %.2f);' % (tcta - 0.1))
J('tl.fromTo("#cta .c2", { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, %.2f);' % (tcta + 0.9))
J('tl.to("#cta .c1", { scale: 1.06, duration: 0.6, repeat: 5, yoyo: true, ease: "sine.inOut" }, %.2f);' % (tcta + 0.8))

# ---------- audio ----------
sfx = [("riser", 0.0), ("boom", 0.9), ("pop", 1.6)] + [("whoosh", c[0]) for c in CAMS[2:] if c[1] < 2.5]
if B: sfx += [("draw", SHOTS["border"][0] - 0.4), ("chime", SHOTS["border"][0] + 2.3)]
if A: sfx += [("draw", SHOTS["home"][0] + 0.2), ("chime", SHOTS["home"][0] + 1.4)]
sfx += [("swish", tr + k * 0.5) for k in range(len(roads_auto))]
for key, group in (("near", near_pois), ("far", far_pois), ("extra", extra_pois)):
    if key not in T: continue
    for j, p in enumerate(group):
        sfx.append(("pop", cue(key, p, j, len(group)) + 0.2))
sfx += [("chime", ts), ("boom", tcta - 0.1)]
SFXLEN = {"riser": 1.5, "boom": 1.8, "whoosh": 1.4, "pop": 0.35, "chime": 1.6, "draw": 3.0, "swish": 0.6}
VOL = {"riser": 0.45, "boom": 0.6, "whoosh": 0.45, "pop": 0.5, "chime": 0.4, "draw": 0.28, "swish": 0.32}
sfx = [s for s in sfx if s[1] < DUR - 0.3]
audio = "".join(f'<audio id="sfx{i}" class="clip" src="assets/sfx/{n}.wav" data-start="{t:.2f}" data-duration="{min(SFXLEN[n], DUR - t):.2f}" data-track-index="{12 + i % 6}" data-volume="{VOL[n]}"></audio>'
                for i, (n, t) in enumerate(sorted(sfx, key=lambda s: s[1])))
vo = "".join(f'<audio id="vo_{k}_{j}" class="clip" src="{VO["file"]}" data-start="{tt:.2f}" data-media-start="{a:.3f}" data-duration="{b - a:.3f}" data-track-index="{9 + (n + j) % 2}" data-volume="{VO.get("volume", 1.0)}"></audio>'
             for n, k in enumerate(ORDER) for j, (a, b, tt) in enumerate(PARTS[k]))
if not os.path.exists(f"{P}/assets/bgm.wav") or wave.open(f"{P}/assets/bgm.wav").getnframes() / 44100 < DUR:
    subprocess.run([sys.executable, f"{KIT}/sfx.py", str(DUR + 1)], cwd=P, check=True)
bgm = f'<audio id="bgm" class="clip" src="assets/bgm.wav" data-start="0" data-duration="{DUR:.2f}" data-media-start="0" data-track-index="8" data-volume="{cfg.get("bgm_volume", 0.16)}"></audio>'

# ---------- write ----------
ti = cfg["title"]
X_HTML = ""
if B:
    cb = cam_at(SHOTS["border"][0] + 1.0); hs = proj(HX, HY, cb); xs_ = proj(CX, CY, cb)
    chip_dx = 230 if xs_[0] >= hs[0] else -230
    if not (300 < xs_[0] + chip_dx < 780): chip_dx = -chip_dx
    X_HTML = (f'<div class="poi" id="pX" data-w="{CX},{CY}"><div class="badge flagb" id="badgeX" style="--c:#FF2E63"><svg viewBox="0 0 24 24">{ICON["flag"]}</svg></div>'
              f'<div class="chipx" id="chipX" style="left:{chip_dx}px"><b>{esc(B.get("chip", "QUA RANH " + B["region"]))}</b><span>{km_txt(B["m"])} · {min_txt(B["s"])} ô tô</span></div></div>')
rep = {
    "%DUR%": str(DUR), "%W%": str(W), "%H%": str(H), "%HX%": str(HX), "%HY%": str(HY),
    "%DX%": str(DET["x"]), "%DY%": str(DET["y"]), "%DW%": str(DET["w"]), "%DH%": str(DET["h"]),
    "%OX%": str(OUT["x"]), "%OY%": str(OUT["y"]), "%OWN%": str(WM.get("outer", WM["far"])["w"]), "%OHN%": str(WM.get("outer", WM["far"])["h"]),
    "%OS%": str(2 ** (16 - WM.get("outer", WM["far"])["z"])),
    "%FX%": str(FAR["x"]), "%FY%": str(FAR["y"]), "%FW%": str(FAR["w"]), "%FH%": str(FAR["h"]),
    "%SVG%": svg, "%REGSVG%": regsvg, "%LABELS%": "".join(label_html(L) for L in LBL), "%CARDS%": cards + X_HTML,
    "%TK%": esc(ti["kicker"]), "%T1%": esc(ti["line1"]), "%T2%": esc(ti["line2"]), "%TSUB%": esc(ti["sub"]),
    "%HTAG%": esc(cfg.get("home_tag", "VỊ TRÍ CĂN NHÀ")),
    "%SL1%": esc(cfg["slogan"][0]), "%SL2%": esc(cfg["slogan"][1]), "%CTA1%": esc(cfg["cta"][0]), "%CTA2%": esc(cfg["cta"][1]),
    "%CAM%": json.dumps(CAMS), "%SAMP%": json.dumps({}), "%JS%": "\n      ".join(js), "%AUDIO%": audio + vo + bgm,
    "%NOTE%": esc(cfg.get("note", "Khoảng cách ô tô theo OpenStreetMap, thời gian ước tính · ranh giới hành chính tham khảo")),
}
if B:
    def samples(pts, n=90):
        L = [0]
        for a, b in zip(pts, pts[1:]): L.append(L[-1] + math.dist(a, b))
        out, j = [], 0
        for i in range(n + 1):
            s = L[-1] * i / n
            while j < len(L) - 2 and L[j + 1] < s: j += 1
            t_ = (s - L[j]) / ((L[j + 1] - L[j]) or 1)
            out.append([round(pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t_, 1), round(pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t_, 1)])
        return out
    rep["%SAMP%"] = json.dumps({"nA": samples(bnA), "nB": samples(bnB)})
# satellite layers: colour grade baked into the pixels (no per-frame CSS filters) + smaller copies for zoomed-out shots
def bake(src, dst, k, sat, con, bri):
    if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(src): return
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(src).convert("RGB")
    if k > 1: im = im.resize((im.width // k, im.height // k), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255
    l = (a * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    a = l + (a - l) * sat; a = (a - 0.5) * con + 0.5; a = a * bri
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(dst, quality=92)
os.makedirs(f"{P}/assets/lod", exist_ok=True)
GRADE = {"far": (1.08, 1.05, 0.86), "wide": (1.15, 1.08, 0.9), "detail": (1.12, 1.06, 0.94), "outer": (1.1, 1.05, 0.85)}
SRC = {"far": "far_z14.jpg", "wide": "wide_z16.jpg", "detail": "detail_z18.jpg", "outer": "outer_z12.jpg"}
for nm, ks in (("far", (1, 2)), ("wide", (1, 2, 4)), ("detail", (1,)), ("outer", (1,))):
    if not os.path.exists(f"{P}/assets/{SRC[nm]}"): continue
    for k in ks: bake(f"{P}/assets/{SRC[nm]}", f"{P}/assets/lod/{nm}_{k}.jpg", k, *GRADE[nm])
html = open(f"{KIT}/template_promo.tpl", encoding="utf-8").read()
for a, b in rep.items(): html = html.replace(a, b)
open(f"{P}/index.html", "w", encoding="utf-8").write(html)
for f in ("gsap.min.js",):
    os.makedirs(f"{P}/assets/vendor", exist_ok=True)
    if not os.path.exists(f"{P}/assets/vendor/{f}"): shutil.copy(f"{KIT}/vendor/{f}", f"{P}/assets/vendor/{f}")
json.dump({"dur": DUR, "T": T, "cams": CAMS, "shots": {k: v[0] for k, v in SHOTS.items()}, "layout": layout}, open(f"{P}/map/promo_layout.json", "w"), indent=1)
print(f"index.html {len(html)//1024} KB · {DUR}s")
print("canh:", ", ".join(f"{k} {v[0]:.1f}s" for k, v in SHOTS.items()))
snap = sorted({round(T[k][0] + T[k][1] * f, 1) for k in ORDER for f in (0.5, 0.95)})
print("snapshot --at", ",".join(str(s) for s in snap))
print("\n".join(report) if report else "Kiem tra the tien ich: OK")
