#!/usr/bin/env python3
"""Dung index.html cho video ban do vi tri tu config + du lieu fetch.py.

    python3 build.py config.json PROJECT_DIR

Tu dong:
  - camera tung diem dung: khung vua route + nha + diem den + the ten (chip) + the HUD, khong cat chu, khong lo nen den
  - chu 3D in det cua tuyen duong: chon vi tri doc theo duong sao cho khong bi ghim/chip/the nao de len o moi khung hinh
  - huong chip (u/d/l/r) cua tung diem: chon huong khong de len chu 3D, ghim khac, HUD, va nam trong vung an toan
In ra bao cao chong lan; bao cao phai bang 0 truoc khi render.
"""
import json, math, os, shutil, subprocess, sys, wave

KIT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(KIT, "../../../.."))
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
P = sys.argv[2]
m = json.load(open(f"{P}/map/mosaics.json")); R = json.load(open(f"{P}/map/routes.json")); RD = json.load(open(f"{P}/map/roads.json"))
WM = m["wide"]

# ---------- world coordinates (pixels of the z16 wide mosaic) ----------
def px(lat, lon):
    n = 2 ** 16; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return round(x * 256 - WM["tx0"] * 256, 1), round(y * 256 - WM["ty0"] * 256, 1)

def place(mm):
    s = 2 ** (16 - mm["z"]); return {"x": mm["tx0"] * 256 * s - WM["tx0"] * 256, "y": mm["ty0"] * 256 * s - WM["ty0"] * 256, "w": mm["w"] * s, "h": mm["h"] * s}

W, H = WM["w"], WM["h"]; DET = place(m["detail"]); FAR = place(m["far"])
HX, HY = px(*R["home"])

def samples(Pt, n=160):
    L = [0]
    for i in range(1, len(Pt)): L.append(L[-1] + math.hypot(Pt[i][0] - Pt[i - 1][0], Pt[i][1] - Pt[i - 1][1]))
    out = []; j = 0
    for k in range(n + 1):
        t = L[-1] * k / n
        while j < len(L) - 2 and L[j + 1] < t: j += 1
        seg = L[j + 1] - L[j] or 1; f = (t - L[j]) / seg
        out.append([round(Pt[j][0] + (Pt[j + 1][0] - Pt[j][0]) * f, 1), round(Pt[j][1] + (Pt[j + 1][1] - Pt[j][1]) * f, 1)])
    return out

ICON = {
 "road": '<path d="M9 3h6l3 18H6z" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M12 6v3M12 12v3M12 18v2" stroke="#fff" stroke-width="2.2"/>',
 "cross": '<circle cx="12" cy="12" r="9" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M8 12h8M12 8v8" stroke="#fff" stroke-width="2.2"/><path d="M5 9l3-2M19 15l-3 2" stroke="#fff" stroke-width="2.2"/>',
 "market": '<path d="M3 9l2-5h14l2 5" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M3 9h18v3a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z" fill="#fff"/><path d="M5 14v6h14v-6" fill="none" stroke="#fff" stroke-width="2.2"/>',
 "school": '<path d="M2 9l10-5 10 5-10 5z" fill="#fff"/><path d="M6 11v5c3 2.5 9 2.5 12 0v-5" fill="none" stroke="#fff" stroke-width="2.2"/><path d="M21 9v6" stroke="#fff" stroke-width="2"/>',
 "gov": '<path d="M3 9l9-5 9 5z" fill="#fff"/><path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18" stroke="#fff" stroke-width="2.2"/>',
 "hospital": '<rect x="4" y="4" width="16" height="16" rx="3" fill="#fff"/><path d="M12 7.5v9M7.5 12h9" stroke="#E3161B" stroke-width="3.2"/>',
 "city": '<path d="M3 21V11h4V6h5v6h3V3h5v18z" fill="#fff"/><path d="M2 21h20" stroke="#fff" stroke-width="2"/>',
 "park": '<circle cx="12" cy="9" r="6" fill="#fff"/><path d="M12 14v8" stroke="#fff" stroke-width="2.4"/>',
 "shop": '<path d="M4 8h16l-1 13H5z" fill="#fff"/><path d="M8 8a4 4 0 0 1 8 0" fill="none" stroke="#fff" stroke-width="2.2"/>',
 "bridge": '<path d="M2 16h20M5 16v-5M19 16v-5M12 16V8" stroke="#fff" stroke-width="2.2"/><path d="M2 11c4-4 16-4 20 0" fill="none" stroke="#fff" stroke-width="2.2"/>',
}
COLOR = {"road": "#18A9C9", "cross": "#F28C18", "market": "#2BB673", "school": "#3D7BFF", "gov": "#C7372F", "hospital": "#E3161B", "city": "#8E44EC", "park": "#3FA34D", "shop": "#E0629A", "bridge": "#5C6BC0"}
ROADCLS = {"q": "ql1", "t": "tl", "w": "ct"}

def km(mm): return f"{mm} m" if mm < 1000 else f"{mm/1000:.1f}".replace(".", ",") + " km"
def mins(s): return f"~{max(1, round(s/60))} phút"

# ---------- stops ----------
stops = []
for st in cfg["stops"]:
    r = R["pts"][st["label"]]
    Pt = [px(la, lo) for lo, la in r["geom"]]
    mm = st.get("show_m", r["m"]); ss = st.get("show_s", r["s"])
    stops.append(dict(cfg=st, chip=st.get("chip", st["label"]), icon=st["icon"], hud=st.get("hud", True), end=px(*r["at"]),
                      d="M" + " L".join(f"{x},{y}" for x, y in Pt), S=samples(Pt), m=mm, s=ss))

# ---------- camera projection (same math as apply() in template.tpl) ----------
PD = 1800
def proj(wx, wy, c):
    z = c["z"]; a = math.radians(c["t"])
    sx = 540 + (wx - c["x"]) * z; sy = 900 + (wy - c["y"]) * z
    yr = (sy - 900) * math.cos(a) + 900; zr = (sy - 900) * math.sin(a)
    if PD - zr < 300: return float("inf"), float("inf")
    k = PD / (PD - zr)
    return 540 + (sx - 540) * k, 800 + (yr - 800) * k

def unproj(X, Y, c):
    z = c["z"]; a = math.radians(c["t"]); ca, sa = math.cos(a), math.sin(a)
    u = ((Y - 800) * PD - 100 * PD) / (PD * ca + (Y - 800) * sa)
    k = PD / (PD - u * sa); sx = 540 + (X - 540) / k
    return c["x"] + (sx - 540) / z, c["y"] + u / z

def text_w(s, size, k=0.64): return len(s) * size * k
CHIP_H = 86
def chip_wh(s): return max(text_w(s["chip"], 28, 0.66), text_w(km(s["m"]) + " · " + mins(s["s"]), 24, 0.6)) + 44, CHIP_H
def chip_rel(s, side):
    w, h = chip_wh(s)
    return {"u": (-w / 2, -96 - h, w / 2, -96), "d": (-w / 2, 22, w / 2, 22 + h),
            "l": (-44 - w, -46 - h / 2, -44, -46 + h / 2), "r": (44, -46 - h / 2, 44 + w, -46 + h / 2)}[side]
BADGE = (-42, -92, 42, 6)
PIN = (-48, -126, 48, 4)
def tag_rel():
    w = max(text_w(cfg["tag"][0], 42, 0.68), text_w(cfg["tag"][1], 26, 0.58)) + 62
    return (-w / 2, -150 - 112, w / 2, -150)
HUD_RECT = (60, 1200, 1020, 1480)
SUM_RECT = (50, 970, 1030, 1600)
SAFE_X = (70, 1010); SAFE_TOP = 300

def shift(rel, X, Y): return (X + rel[0], Y + rel[1], X + rel[2], Y + rel[3])
def area(r): return max(0, r[2] - r[0]) * max(0, r[3] - r[1])
def inter(a, b): return (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
def grow(r, g): return (r[0] - g, r[1] - g, r[2] + g, r[3] + g)

def clip_poly(poly, r):
    """area of convex polygon poly intersected with rect r (Sutherland-Hodgman)"""
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
    pts = poly
    for inside, isect in ((lambda p: p[0] >= r[0], lambda a, b: ix(a, b, r[0])), (lambda p: p[0] <= r[2], lambda a, b: ix(a, b, r[2])),
                          (lambda p: p[1] >= r[1], lambda a, b: iy(a, b, r[1])), (lambda p: p[1] <= r[3], lambda a, b: iy(a, b, r[3]))):
        if not pts: return 0
        pts = cut(pts, inside, isect)
    if len(pts) < 3: return 0
    return abs(sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))) / 2

def poly_area(p): return abs(sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))) / 2

# ---------- camera fitting ----------
def fit(items, safe, tilt_fn, zmax, zmin=0.1):
    """items: [(wx, wy, rel_rect)]. Largest zoom (<= zmax) and centre so every item box lies in `safe`."""
    sc = ((safe[0] + safe[2]) / 2, (safe[1] + safe[3]) / 2)
    def place_at(z):
        c = {"x": sum(i[0] for i in items) / len(items), "y": sum(i[1] for i in items) / len(items), "z": z, "t": tilt_fn(z)}
        xs = [i[0] for i in items]; ys = [i[1] for i in items]
        c["x"], c["y"] = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        for _ in range(30):
            B = bbox(items, c)
            if not all(map(math.isfinite, B)): return c, False
            dx, dy = sc[0] - (B[0] + B[2]) / 2, sc[1] - (B[1] + B[3]) / 2
            if abs(dx) < 0.5 and abs(dy) < 0.5: break
            c["x"] -= 0.8 * dx / z; c["y"] -= 0.8 * dy / (z * math.cos(math.radians(c["t"])))
        B = bbox(items, c)
        ok = all(map(math.isfinite, B)) and B[2] - B[0] <= safe[2] - safe[0] and B[3] - B[1] <= safe[3] - safe[1]
        return c, ok
    lo, hi = math.log2(zmin), math.log2(zmax)
    c, ok = place_at(zmax)
    if ok: return no_black(c)
    for _ in range(26):
        mid = (lo + hi) / 2; c2, ok = place_at(2 ** mid)
        if ok: lo = mid
        else: hi = mid
    return no_black(place_at(2 ** lo)[0])

def bbox(items, c):
    xs0, ys0, xs1, ys1 = [], [], [], []
    for wx, wy, rel in items:
        X, Y = proj(wx, wy, c); xs0.append(X + rel[0]); ys0.append(Y + rel[1]); xs1.append(X + rel[2]); ys1.append(Y + rel[3])
    return min(xs0), min(ys0), max(xs1), max(ys1)

def covered(c):
    for X, Y in ((0, 0), (1080, 0), (0, 1920), (1080, 1920), (540, 0)):
        wx, wy = unproj(X, Y, c)
        if not (FAR["x"] <= wx <= FAR["x"] + FAR["w"] and FAR["y"] <= wy <= FAR["y"] + FAR["h"]): return False
    return True

def no_black(c):
    z0 = c["z"]
    while not covered(c) and c["z"] < z0 * 1.25: c["z"] *= 1.02
    return c

def tilt_for(z): return max(10.0, min(40.0, 40 + 12 * math.log2(z / 0.8)))

PT = (-24, -24, 24, 24)
def stop_items(i, side, labels):
    s = stops[i]; ex, ey = s["end"]
    it = [(x, y, PT) for x, y in s["S"][::4]]
    it += [(ex, ey, BADGE), (ex, ey, chip_rel(s, side)), (HX, HY, PIN)]
    xs = [p[0] for p in it]; ys = [p[1] for p in it]; mx = (max(xs) - min(xs)) * 0.3 + 150; my = (max(ys) - min(ys)) * 0.3 + 150
    for L in labels:
        if L["si"] > i: continue
        # a road name revealed in this shot, or already on screen close to it, must sit fully inside the frame
        if L["si"] == i or (min(xs) - mx < L["x"] < max(xs) + mx and min(ys) - my < L["y"] < max(ys) + my):
            it += [(x, y, (-10, -10, 10, 10)) for x, y in label_corners(L)]
    return it

def label_zmax(i):
    w = [text_w(rd["label"], rd.get("size", 90), 0.68) for rd in cfg.get("roads", []) if rd.get("label") and rd["reveal_with"] == stops[i]["cfg"]["label"]]
    return 0.5 * (SAFE_X[1] - SAFE_X[0]) / max(w) if w else 9

def safe_for(hud): return (SAFE_X[0], SAFE_TOP, SAFE_X[1], (HUD_RECT[1] - 24) if hud else 1500)

# ---------- timeline ----------
def draw_dur(mm): return round(min(5.6, max(2.8, 3.2 + 0.8 * math.log2(max(mm, 200) / 1000))), 1)

def build_timeline(sides, labels=()):
    keys = []; sched = []
    near = [i for i, s in enumerate(stops) if not s["cfg"].get("far")]
    ov_items = [(HX, HY, PIN)] + [(stops[i]["end"][0], stops[i]["end"][1], BADGE) for i in near]
    ov = fit(ov_items, (SAFE_X[0], 560, SAFE_X[1], 1500), lambda z: 26, 1.2)
    keys.append([0.0, 5.0, ov]); home = fit([(HX, HY, PIN), (HX, HY, tag_rel())], (SAFE_X[0], SAFE_TOP, SAFE_X[1], 1200), lambda z: 38, 3.0)
    keys.append([5.0, 4.6, home])
    T = 9.8; prevz = home["z"]
    for i, s in enumerate(stops):
        c = fit(stop_items(i, sides[i], labels), safe_for(s["hud"]), tilt_for, min(s["cfg"].get("zmax", 2.4), label_zmax(i)))
        cm = 4.6 if abs(math.log2(c["z"] / prevz)) > 2 else 3.0
        keys.append([round(T, 2), cm, c]); prevz = c["z"]
        t0 = round(T + 0.4, 2); dd = draw_dur(s["m"]); end = t0 + dd
        if s["hud"]: h0, h1 = round(end, 2), round(end + 3.8, 2); nxt = h1 - 0.4
        else: h0 = h1 = None; nxt = end + 2.6
        sched.append([t0, dd, h0, h1]); T = nxt
    back_items = [(HX, HY, PIN)] + [(stops[i]["end"][0], stops[i]["end"][1], BADGE) for i in near]
    back = fit(back_items, (SAFE_X[0], SAFE_TOP, SAFE_X[1], SUM_RECT[1] - 20), lambda z: 32, 1.4)
    keys.append([round(T, 2), 3.4, back])
    return keys, sched, round(T, 2)

# ---------- what is on screen while a camera key holds ----------
def hidden_badges(keys, sched, sides, labels=()):
    """earlier pins that would sit under the current chip / pin / HUD / summary fade out for that shot"""
    hid = {}; last = len(keys) - 1
    for ki, (t0, d, c) in enumerate(keys):
        nxt = keys[ki + 1][0] if ki < last else 999
        cur = ki - 2 if 2 <= ki < 2 + len(stops) else None
        clear = []
        if cur is not None:
            X, Y = proj(*stops[cur]["end"], c)
            clear += [grow(shift(chip_rel(stops[cur], sides[cur]), X, Y), 10), grow(shift(BADGE, X, Y), 6)]
            if sched[cur][2] is not None: clear.append(HUD_RECT)
        if ki == last: clear.append(SUM_RECT)
        hs = set()
        for k, (s0, dd, h0, h1) in enumerate(sched):
            if k == cur or s0 + dd >= nxt: continue
            X, Y = proj(*stops[k]["end"], c); b = shift(BADGE, X, Y)
            if any(area(inter(b, r)) > 0 for r in clear): hs.add(k)
            # wide shots: a pin never sits on a flat road name, it steps aside for that shot
            elif c["z"] < 0.6 and any(clip_poly(label_poly(L, c), grow(b, 4)) > 0 for L in labels if L["t"] < nxt): hs.add(k)
        hid[ki] = hs
    return hid

def frames(keys, sched, back_t, sides, labels):
    """per camera key once it has settled: (key index, cam, [(name, screen box)], [(road text, screen polygon)])"""
    out = []; last = len(keys) - 1
    for ki, (t0, d, c) in enumerate(keys):
        nxt = keys[ki + 1][0] if ki < last else 999
        boxes = []; hs = hidden_badges(keys, sched, sides, labels)[ki]
        HXs, HYs = proj(HX, HY, c)
        if nxt > _T["homein"]: boxes.append(("nhà", shift(PIN, HXs, HYs)))
        if ki < 3: boxes.append(("tên nhà", shift(tag_rel(), HXs, HYs)))
        for i, (s0, dd, h0, h1) in enumerate(sched):
            if s0 + dd >= nxt: continue
            X, Y = proj(*stops[i]["end"], c)
            if i not in hs: boxes.append((f"ghim {stops[i]['chip']}", shift(BADGE, X, Y)))
            if ki == 2 + i:
                boxes.append((f"thẻ {stops[i]['chip']}", shift(chip_rel(stops[i], sides[i]), X, Y)))
                if h0 is not None: boxes.append(("HUD", HUD_RECT))
        if ki == last: boxes.append(("bảng tóm tắt", SUM_RECT))
        vis = [(L["text"], label_poly(L, c)) for L in labels if L["t"] < nxt]
        out.append((ki, c, boxes, vis))
    return out

_T = {}
def cfg_t(k): return _T[k]

def label_corners(L):
    w, h = text_w(L["text"], L["size"], 0.68) + 0.1 * L["size"], L["size"] * 1.25
    a = math.radians(L["a"]); ca, sa = math.cos(a), math.sin(a)
    return [(L["x"] + dx * ca - dy * sa, L["y"] + dx * sa + dy * ca) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]

def label_poly(L, c): return [proj(x, y, c) for x, y in label_corners(L)]

# ---------- road label placement ----------
def road_lines(keys_):
    out = []
    for k in keys_:
        for l in RD.get(k, []): out.append([px(la, lo) for lo, la in l])
    return out

def candidates(lines, step=45):
    cands = []
    for l in lines:
        acc = 0
        for i in range(1, len(l)):
            (x1, y1), (x2, y2) = l[i - 1], l[i]; seg = math.hypot(x2 - x1, y2 - y1)
            n = int((acc + seg) // step) - int(acc // step)
            for k in range(n):
                f = ((int(acc // step) + k + 1) * step - acc) / (seg or 1)
                x, y = x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
                a = math.degrees(math.atan2(y2 - y1, x2 - x1))
                if a > 90: a -= 180
                if a <= -90: a += 180
                cands.append((x, y, a))
            acc += seg
    # smooth the angle with neighbours so the label follows the road, not one kinked segment
    return cands

def label_cost(L, fr_list, sides_boxes_only=False):
    cost = 0
    for ki, c, boxes, vis in fr_list:
        poly = label_poly(L, c); pa = poly_area(poly) or 1
        f = clip_poly(poly, (0, 0, 1080, 1920)) / pa
        if 0.02 < f < 0.98: cost += min(f, 1 - f) * pa * 25  # half a road name hanging off the edge looks broken
        for name, b in boxes: cost += clip_poly(poly, grow(b, 14)) * 40
        for txt, other in vis:
            if txt == L["text"]: continue
            ob = (min(p[0] for p in other), min(p[1] for p in other), max(p[0] for p in other), max(p[1] for p in other))
            cost += clip_poly(poly, grow(ob, 10)) * 40
    return cost

def place_labels(keys, sched, back_t, sides):
    labels = []
    for rd in cfg.get("roads", []):
        if not rd.get("label"): continue
        si = next(i for i, s in enumerate(stops) if s["cfg"]["label"] == rd["reveal_with"])
        t_rev = sched[si][0] + 0.3 * sched[si][1]
        rc = keys[2 + si][2]
        lines = road_lines(rd.get("lines", [rd["key"]]))
        best = None
        for x, y, a in candidates(lines):
            if not (40 < x < W - 40 and 40 < y < H - 40): continue
            if abs(a) > 55: continue
            L = dict(text=rd["label"], size=rd.get("size", 90), x=x, y=y, a=a, cls=rd.get("style", "t"), key=rd["key"], t=t_rev + 1.0, si=si)
            poly = label_poly(L, rc)
            # must sit fully in the safe frame when it is revealed
            out_frame = poly_area(poly) - clip_poly(poly, (SAFE_X[0], SAFE_TOP, SAFE_X[1], safe_for(stops[si]["hud"])[3]))
            fr = [f for f in frames(keys, sched, back_t, sides, labels) if f[0] >= 2 + si]
            cx = sum(p[0] for p in poly) / 4; cy = sum(p[1] for p in poly) / 4
            cost = out_frame * 60 + label_cost(L, fr) + math.hypot(cx - 540, cy - 760) * 2
            if best is None or cost < best[0]: best = (cost, L)
        labels.append(best[1])
    return labels

# ---------- chip side choice ----------
ORDER = ["u", "r", "l", "d"]
def choose_sides(keys, sched, back_t, sides, labels):
    new = list(sides)
    for i in range(len(stops)):
        ki = 2 + i; c = keys[ki][2]
        fr = frames(keys, sched, back_t, new, labels)[ki]
        X, Y = proj(*stops[i]["end"], c)
        safe = safe_for(stops[i]["hud"])
        others = [b for n, b in fr[2] if not n.startswith("thẻ")and n != f"ghim {stops[i]['chip']}"]
        best = None
        for j, sd in enumerate(ORDER):
            r = shift(chip_rel(stops[i], sd), X, Y)
            cost = j * 50 + (area(r) - area(inter(r, safe))) * 8
            for b in others: cost += area(inter(grow(r, 12), b)) * 5
            for _, poly in fr[3]: cost += clip_poly(poly, grow(r, 12)) * 8
            if best is None or cost < best[0]: best = (cost, sd)
        new[i] = best[1]
    return new

def report(keys, sched, back_t, sides, labels):
    """errors = text covered (road names, chips, HUD, summary, cut-off chips, black edges). notes = icon touching icon."""
    bad, note = [], []
    TEXT = ("thẻ", "HUD", "bảng", "tên nhà")
    for ki, c, boxes, vis in frames(keys, sched, back_t, sides, labels):
        for txt, poly in vis:
            for name, b in boxes:
                a = clip_poly(poly, grow(b, 4))
                if a > 150: bad.append(f"khung {ki}: {name} đè chữ {txt} ({a:.0f}px²)")
            if poly_area(poly) - clip_poly(poly, (0, 0, 1080, 1920)) > 0.25 * poly_area(poly) and any(L["text"] == txt and L["si"] + 2 == ki for L in labels):
                bad.append(f"khung {ki}: chữ {txt} bị cắt ngoài khung lúc hiện")
        for j in range(len(boxes)):
            for k in range(j + 1, len(boxes)):
                (n1, b1), (n2, b2) = boxes[j], boxes[k]
                a = area(inter(b1, b2))
                if a < 150: continue
                if n1.startswith(TEXT) or n2.startswith(TEXT): bad.append(f"khung {ki}: {n1} đè {n2} ({a:.0f}px²)")
                elif not (n1.startswith("ghim") and n2.startswith("ghim")): note.append(f"khung {ki}: {n1} chạm {n2}")
        if 2 <= ki < 2 + len(stops):
            i = ki - 2; X, Y = proj(*stops[i]["end"], c); r = shift(chip_rel(stops[i], sides[i]), X, Y)
            if r[1] < SAFE_TOP - 20 or r[0] < 40 or r[2] > 1040 or r[3] > 1880: bad.append(f"khung {ki}: thẻ {stops[i]['chip']} ra ngoài vùng an toàn / bị cắt")
        if not covered(c): bad.append(f"khung {ki}: lộ nền đen ngoài ảnh vệ tinh")
    return bad, note

# ---------- solve ----------
_T["homein"] = 8.0
sides = [s["cfg"].get("side", "u") for s in stops]
locked = [("side" in s["cfg"]) for s in stops]
keys, sched, back_t = build_timeline(sides)
labels = place_labels(keys, sched, back_t, sides)
for it in range(3):
    ns = choose_sides(keys, sched, back_t, sides, labels)
    sides = [sides[i] if locked[i] else ns[i] for i in range(len(stops))]
    keys, sched, back_t = build_timeline(sides, labels)
    labels = place_labels(keys, sched, back_t, sides)
keys, sched, back_t = build_timeline(sides, labels)
bad, note = report(keys, sched, back_t, sides, labels)

TAGOUT = keys[3][0] + 1.0 if len(keys) > 3 else 19
SUMT = back_t + 2.0; DUR = round(SUMT + 5.4, 1)

# ---------- HTML ----------
def rt(L):
    return (f'<div class="roadtxt {L["cls"]}" style="left:{L["x"]:.1f}px;top:{L["y"]:.1f}px;font-size:{L["size"]}px;--a:{L["a"]:.1f}deg">'
            f'<span class="rti" id="t_{L["key"]}"><span class="ex">{L["text"]}</span><span class="fc">{L["text"]}</span></span></div>')

def line_d(lines): return " ".join("M" + " L".join(f"{x},{y}" for x, y in l) for l in lines)
roads_svg = "".join(f'<path id="rd_{rd["key"]}" class="road {ROADCLS[rd.get("style", "t")]}" d="{line_d(road_lines(rd.get("lines", [rd["key"]])))}" pathLength="1"/>' for rd in cfg.get("roads", []))
paths = "".join(f'<g id="g{i}"><path class="ru" d="{s["d"]}" pathLength="1" id="ru{i}"/><path class="rg" d="{s["d"]}" pathLength="1" id="rg{i}"/><path class="rc" d="{s["d"]}" pathLength="1" id="rc{i}"/><path class="rf" d="{s["d"]}" pathLength="1" id="rf{i}"/></g>' for i, s in enumerate(stops))
pois = "".join(f'<div class="poi {sides[i]}" id="p{i}" data-w="{s["end"][0]},{s["end"][1]}"><div class="cs"><div class="badge" id="b{i}" style="background:{COLOR[s["icon"]]}"><svg viewBox="0 0 24 24">{ICON[s["icon"]]}</svg></div><div class="chip" id="c{i}"><b>{s["chip"]}</b><span>{km(s["m"])} · {mins(s["s"])}</span></div></div></div>' for i, s in enumerate(stops))
huds = "".join(f'<div class="hud" id="h{i}"><div class="hi" style="background:{COLOR[s["icon"]]}"><svg viewBox="0 0 24 24">{ICON[s["icon"]]}</svg></div><div class="hb"><div class="hk">TỪ CĂN NHÀ ĐẾN</div><div class="ht">{s["chip"]}</div><div class="hr"><span class="hd">{km(s["m"])}</span><span class="hm">{mins(s["s"])} ô tô</span></div></div></div>' for i, s in enumerate(stops) if s["hud"])
comet = "".join(f'<div class="comet" id="cm{i}"><div class="cc"></div></div>' for i in range(len(stops)))
byl = {s["cfg"]["label"]: s for s in stops}
summary = "".join(f'<div class="srow"><i style="background:{COLOR[byl[k]["icon"]]}"><svg viewBox="0 0 24 24">{ICON[byl[k]["icon"]]}</svg></i><span>{n}</span><b>{km(byl[k]["m"])}</b><em>{mins(byl[k]["s"])}</em></div>' for n, k in cfg["summary"])

layer = []; det = False; wide = True
for t0, d, c in keys:
    if c["z"] >= 1.5 and not det: layer.append(f'tl.to("#detail", {{ opacity: 1, duration: 1.4, ease: "sine.inOut" }}, {t0 + d * 0.35:.2f});'); det = True
    elif c["z"] < 1.5 and det: layer.append(f'tl.to("#detail", {{ opacity: 0, duration: 1.2, ease: "sine.inOut" }}, {t0:.2f});'); det = False
    if c["z"] < 0.3 and wide: layer.append(f'tl.to("#wide", {{ opacity: 0, duration: 2.0, ease: "sine.inOut" }}, {t0 + 0.6:.2f});'); wide = False
    elif c["z"] >= 0.3 and not wide: layer.append(f'tl.to("#wide", {{ opacity: 1, duration: 2.0, ease: "sine.inOut" }}, {t0 + 0.2:.2f});'); wide = True
HID = hidden_badges(keys, sched, sides, labels)
prev = set()
for ki, (t0, d, c) in enumerate(keys):
    for k in sorted(HID[ki] - prev): layer.append(f'tl.to("#b{k}", {{ opacity: 0, duration: 0.35 }}, {t0 + 0.2:.2f});')
    for k in sorted(prev - HID[ki]): layer.append(f'tl.to("#b{k}", {{ opacity: 1, duration: 0.35 }}, {t0 + 0.2:.2f});')
    prev = HID[ki]
roadjs = []
for rd in cfg.get("roads", []):
    si = next(i for i, s in enumerate(stops) if s["cfg"]["label"] == rd["reveal_with"]); tr = sched[si][0] + 0.3 * sched[si][1]
    roadjs.append(f'tl.to("#rd_{rd["key"]}", {{ strokeDashoffset: 0, duration: 2.0, ease: "sine.inOut" }}, {tr:.2f});')
    if rd.get("label"): roadjs.append(f'tl.fromTo("#t_{rd["key"]}", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.9, ease: "back.out(1.7)" }}, {tr + 1.0:.2f});')

sfx = [("riser", 0.0), ("boom", 0.9), ("pop", 8.7)] + [("whoosh", k[0]) for k in keys[1:]]
for t0, dd, h0, h1 in sched:
    sfx += [("draw", t0), ("pop", t0 + dd)] + ([("chime", h0)] if h0 is not None else [])
sfx.append(("chime", SUMT - 1.2))
SFXLEN = {"riser": 1.5, "boom": 1.8, "whoosh": 1.4, "pop": 0.35, "chime": 1.6, "draw": 3.0, "swish": 0.6}
VOL = {"riser": 0.5, "boom": 0.8, "whoosh": 0.55, "pop": 0.6, "chime": 0.5, "draw": 0.35}
audio = "".join(f'<audio id="sfx{i}" class="clip" src="assets/sfx/{n}.wav" data-start="{t:.2f}" data-duration="{min(SFXLEN[n], DUR - t):.2f}" data-track-index="{10 + i % 6}" data-volume="{VOL[n]}"></audio>' for i, (n, t) in enumerate(sorted(sfx, key=lambda s: s[1])))

# assets: fonts, gsap, sfx, bgm
os.makedirs(f"{P}/assets/fonts", exist_ok=True); os.makedirs(f"{P}/assets/vendor", exist_ok=True)
for f in ("Bold", "ExtraBold", "Black"):
    shutil.copy(f"{REPO}/ea_video/kit/fonts/BeVietnamPro-{f}.ttf", f"{P}/assets/fonts/")
shutil.copy(f"{KIT}/vendor/gsap.min.js", f"{P}/assets/vendor/")
bgm_path = cfg.get("bgm", "assets/bgm.wav")
need_bgm = not os.path.exists(f"{P}/{bgm_path}")
if need_bgm or not os.path.exists(f"{P}/assets/sfx/pop.wav"):
    subprocess.run([sys.executable, f"{KIT}/sfx.py", str(DUR + 1 if need_bgm else 0)], cwd=P, check=True)
with wave.open(f"{P}/{bgm_path}") as w: BL = w.getnframes() / w.getframerate()
bgm = []; t = 0; n = 0
while t < DUR - 0.05:
    d = min(BL, DUR - t); bgm.append(f'<audio id="bgm{n}" class="clip" src="{bgm_path}" data-start="{t:.2f}" data-duration="{d:.2f}" data-media-start="0" data-track-index="{8 + n % 2}" data-volume="{cfg.get("bgm_volume", 0.3)}"></audio>'); t += d; n += 1

cams = [[t0, d, round(c["x"], 1), round(c["y"], 1), round(c["z"], 4), round(c["t"], 1)] for t0, d, c in keys]
rep = {
 "%DUR%": str(DUR), "%W%": str(W), "%H%": str(H), "%HX%": str(HX), "%HY%": str(HY),
 "%DX%": str(DET["x"]), "%DY%": str(DET["y"]), "%DW%": str(DET["w"]), "%DH%": str(DET["h"]),
 "%FX%": str(FAR["x"]), "%FY%": str(FAR["y"]), "%FW%": str(FAR["w"]), "%FH%": str(FAR["h"]),
 "%ROADS%": roads_svg, "%ROUTES%": paths, "%POIS%": pois, "%HUD%": huds, "%COMET%": comet,
 "%ROADTXT%": "".join(rt(L) for L in labels), "%SUMMARY%": summary, "%AUDIO%": audio, "%BGM%": "".join(bgm),
 "%STOPS%": json.dumps(sched), "%SAMPLES%": json.dumps([s["S"] for s in stops]), "%CAM%": json.dumps(cams),
 "%LAYERJS%": "\n      ".join(layer), "%ROADJS%": "\n      ".join(roadjs),
 "%HOMEIN%": str(_T["homein"]), "%BACK%": str(back_t), "%TAGOUT%": f"{TAGOUT:.2f}", "%SUMT%": f"{SUMT:.2f}",
 "%TK%": cfg["title"]["kicker"], "%T1%": cfg["title"]["line1"], "%T2%": cfg["title"]["line2"], "%TSUB%": cfg["title"]["sub"],
 "%TAG1%": cfg["tag"][0], "%TAG2%": cfg["tag"][1],
}
tpl = open(f"{KIT}/template.tpl", encoding="utf-8").read()
for k in sorted(rep, key=len, reverse=True): tpl = tpl.replace(k, rep[k])
left = sorted(set(__import__("re").findall(r"%[A-Z0-9]+%", tpl)))
if left: sys.exit(f"con placeholder chua dien: {left}")
open(f"{P}/index.html", "w", encoding="utf-8").write(tpl)
json.dump({"dur": DUR, "cams": cams, "stops": sched, "sides": sides, "labels": labels, "back": back_t, "summary_t": SUMT,
           "check_at": [round(max(k[0] + k[1], s0 + dd) + 1.0, 2) for k, (s0, dd, h0, h1) in zip(keys[2:], sched)] + [round(SUMT + 1.5, 2)]},
          open(f"{P}/map/layout.json", "w"), ensure_ascii=False, indent=1)
print(f"index.html {len(tpl)//1024} KB · {DUR}s · {len(sfx)} sfx")
for i, s in enumerate(stops): print(f"  {s['chip']:26s} zoom {keys[2+i][2]['z']:.3f} tilt {keys[2+i][2]['t']:.0f} chip {sides[i]}  {km(s['m'])} {mins(s['s'])}")
for L in labels: print(f"  chu 3D {L['text']:12s} @ {L['x']:.0f},{L['y']:.0f} goc {L['a']:.1f}")
print("Kiem tra chong chu:", "OK, khong co gi de len nhau" if not bad else "")
for b in bad: print("  !", b)
for b in note: print("  (ghi chú)", b)
print("Chup kiem tra tai cac giay:", ",".join(str(x) for x in json.load(open(f"{P}/map/layout.json"))["check_at"]))
