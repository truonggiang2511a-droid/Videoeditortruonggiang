#!/usr/bin/env python3
"""Lay du lieu that cho video ban do vi tri.

    python3 fetch.py config.json PROJECT_DIR

Ghi ra PROJECT_DIR/map/{roads,routes,mosaics}.json va PROJECT_DIR/assets/{wide_z16,detail_z18,far_z14}.jpg.
Can mang toi: nominatim.openstreetmap.org, router.project-osrm.org, server.arcgisonline.com.
"""
import concurrent.futures as cf, json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from PIL import Image

UA = "bds-map-video/1.0"
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
P = sys.argv[2]
os.makedirs(f"{P}/map/cache", exist_ok=True); os.makedirs(f"{P}/assets", exist_ok=True)
H = tuple(cfg["home"])


def get(u):
    """GET json with an on-disk cache (re-runs cost nothing) and polite back-off on 429 / network errors"""
    import hashlib
    cp = f"{P}/map/cache/q_{hashlib.md5(u.encode()).hexdigest()}.json"
    if os.path.exists(cp): return json.load(open(cp, encoding="utf-8"))
    for k in range(6):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40))
            json.dump(d, open(cp, "w", encoding="utf-8"), ensure_ascii=False); return d
        except Exception as e:
            if k == 5: raise
            w = 5 * 2 ** k; print(f"  mang loi ({e}), cho {w}s"); time.sleep(w)


def km(a, b):
    return math.hypot((a[0] - b[0]) * 110.6, (a[1] - b[1]) * 109.3 * math.cos(math.radians(a[0])) / math.cos(math.radians(10.6)))


def nominatim(q, R, geo=False, limit=40):
    vb = f"{H[1]-R},{H[0]+R},{H[1]+R},{H[0]-R}"
    p = {"q": q, "format": "jsonv2", "limit": limit, "viewbox": vb, "bounded": 1, "accept-language": "vi", "namedetails": 1}
    if geo: p.update(polygon_geojson=1, polygon_threshold=0.00005)
    u = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(p)
    import hashlib
    cached = os.path.exists(f"{P}/map/cache/q_{hashlib.md5(u.encode()).hexdigest()}.json")
    r = get(u)
    if not cached: time.sleep(1.6)
    return r
    return r


def dist_line(pt, lines, step=10):
    best = 1e9
    for l in lines:
        for i in range(len(l) - 1):
            (x1, y1), (x2, y2) = l[i], l[i + 1]
            for k in range(step + 1):
                t = k / step; best = min(best, km(pt, (y1 + (y2 - y1) * t, x1 + (x2 - x1) * t)))
    return best


def nearest_on(lines):
    best = None
    for l in lines:
        for i in range(len(l) - 1):
            (x1, y1), (x2, y2) = l[i], l[i + 1]
            for k in range(21):
                t = k / 20; p = (y1 + (y2 - y1) * t, x1 + (x2 - x1) * t); d = km(H, p)
                if not best or d < best[0]: best = (d, p)
    return best[1]


def osrm(at):
    u = f"https://router.project-osrm.org/route/v1/driving/{H[1]},{H[0]};{at[1]},{at[0]}?overview=full&geometries=geojson&steps=true"
    d = get(u)["routes"][0]; return d


def geo_lines(results, keep):
    out = []
    for x in results:
        if x.get("category") != "highway" or not keep(x): continue
        g = x.get("geojson", {})
        if g.get("type") == "LineString": out.append(g["coordinates"])
        elif g.get("type") == "MultiLineString": out += g["coordinates"]
    return out


# 1. stops with known coordinates: real driving routes (with the names/refs of every road used)
routes = {"home": H, "pts": {}}
osrm_refs = set()
def add_route(st, at):
    d = osrm(at)
    for leg in d["legs"]:
        for stp in leg["steps"]:
            if stp.get("ref"): osrm_refs.add(stp["ref"].split(";")[0].strip())
    routes["pts"][st["label"]] = {"at": at, "m": round(d["distance"]), "s": round(d["duration"]), "geom": d["geometry"]["coordinates"], "air_m": round(km(H, at) * 1000)}
    print(f"{st['label']:28s} duong {d['distance']:7.0f} m  oto {d['duration']/60:5.1f} phut  chim bay {km(H, at)*1000:6.0f} m")

for st in cfg["stops"]:
    if "nearest_road" in st: continue
    if "at" in st: at = tuple(st["at"])
    else:
        r = nominatim(st["query"], st.get("radius", 0.3), limit=5)
        if not r: sys.exit(f"khong tim thay: {st['query']}")
        at = (float(r[0]["lat"]), float(r[0]["lon"]))
    add_route(st, at)


# 2. major roads: given in config, or scanned automatically (expressways, ring roads, national + provincial roads)
def slug(t):
    t = unicodedata.normalize("NFKD", t.replace("đ", "d").replace("Đ", "D"))
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if not unicodedata.combining(c)).lower())


def short_name(n):
    n = re.sub(r"^(Đường|đường)\s+", "", n).replace("Thành phố Hồ Chí Minh", "TP.HCM").replace(" - ", " – ")
    return n


def road_label(typ, ref, name):
    nl = (name or "").lower()
    if "vành đai" in nl:
        m_ = re.search(r"vành đai\s*(\d+)", nl); return "VÀNH ĐAI " + (m_.group(1) if m_ else ""), "w", 96
    if typ == "motorway" or "cao tốc" in nl:
        n = short_name(name or "")
        n = re.sub(r"^(cao tốc|Cao tốc|Cao Tốc)\s*", "", n).strip()
        # long names go on a smaller second line so the label stays big enough to read
        return ("CAO TỐC\n" + n.upper()) if n else "CAO TỐC", "w", 96
    if ref and ref.upper().startswith("QL"):
        num = re.sub(r"[^0-9A-Z]", "", ref.upper()[2:]); num = "1A" if num == "1" else num
        return "QUỐC LỘ " + num, "q", 120
    if ref and re.match(r"(ĐT|DT|TL|HL)", ref.upper()):
        return "TL" + re.sub(r"[^0-9A-Z]", "", ref.upper()[2:]), "t", 80
    return short_name(name).upper(), "t", 76


roads, road_cfg = {}, []
SKIP = re.compile(r"dẫn|gom|song hành|hẻm|cầu vượt|nhánh|link", re.I)
MAJOR = {"motorway", "trunk", "primary", "secondary"}
if cfg.get("roads"):
    for rd in cfg["roads"]:
        lines = []
        for q in rd["queries"]:
            lines += geo_lines(nominatim(q, rd.get("radius", 0.08), geo=True), lambda x: True)
        roads[rd["key"]] = lines; print(f"road {rd['key']}: {len(lines)} doan")
else:
    R_SCAN = cfg.get("scan_deg", 0.07)
    found = {}  # group key -> (type, ref, name, query)
    rank = {"motorway": 0, "trunk": 1, "primary": 2, "secondary": 3}
    for q in ["Cao tốc", "Vành đai", "Quốc lộ", "Đường tỉnh", "Tỉnh lộ", "Đại lộ"] + sorted(osrm_refs):
        for x in nominatim(q, R_SCAN):
            if x.get("category") != "highway": continue
            typ = x.get("type"); nd = x.get("namedetails") or {}
            name = nd.get("name") or x.get("name") or ""; ref = (nd.get("ref") or "").split(";")[0].strip()
            if typ not in MAJOR or SKIP.search(name): continue
            if typ == "secondary" and not ref: continue
            if typ == "motorway" or "vành đai" in name.lower(): gk, qq = slug(short_name(name)), name
            elif ref: gk, qq = slug(ref), ref
            else: gk, qq = slug(name), name
            pd = km(H, (float(x["lat"]), float(x["lon"])))
            if gk and (gk not in found or (rank[typ], pd) < (rank[found[gk][0]], found[gk][4])): found[gk] = (typ, ref, name, qq, pd)
    print("tim thay", len(found), "tuyen chinh:", ", ".join(v[1] or v[2] for v in found.values()))
    allroutes = [v["geom"] for v in routes["pts"].values()]
    cands = []
    # nearest few of each class only, so we don't hammer Nominatim for roads 8 km away
    order = sorted(found.items(), key=lambda kv: (rank[kv[1][0]], kv[1][4]))
    order = [kv for kv in order if kv[1][4] < cfg.get("road_km", 4) + 4][: cfg.get("max_roads", 5) + 5]
    for gk, (typ, ref, name, qq, _pd) in order:
        res = nominatim(qq, R_SCAN, geo=True, limit=50)
        lines = geo_lines(res, lambda x: ((x.get("namedetails") or {}).get("ref") or "").split(";")[0].strip() == ref if ref and typ != "motorway"
                          else (((x.get("namedetails") or {}).get("name") or "") == name))
        if not lines: continue
        dh = dist_line(H, lines)
        dr = min([min(dist_line((la, lo), lines, 2) for lo, la in g[::max(1, len(g) // 40)]) for g in allroutes] or [99])
        if dh > cfg.get("road_km", 4) and dr > 0.3: continue
        label, style, size = road_label(typ, ref, name)
        key = slug(label)[:16] or gk
        if key in roads: roads[key] += lines; continue
        roads[key] = lines
        cands.append(dict(key=key, label=label, style=style, size=size, _rank=rank[typ], _d=min(dh, dr)))
    cands.sort(key=lambda c: (c["_rank"], c["_d"]))
    # two names on the same carriageway (e.g. an expressway sharing a stretch with Vanh dai 3): keep the first only
    def overlap1(a, b):
        pts = [(la, lo) for l in roads[a] for lo, la in l if km(H, (la, lo)) < cfg.get("road_km", 4) + 1]
        pts = pts[:: max(1, len(pts) // 150)]
        return sum(dist_line(p, roads[b], 1) < 0.08 for p in pts) / len(pts) if pts else 0
    def overlap(a, b): return max(overlap1(a, b), overlap1(b, a))
    road_cfg = []
    for c in cands:
        if any(overlap(c["key"], o["key"]) > 0.5 for o in road_cfg): print(f"  bo {c['label']}: trung tuyen voi chu khac"); continue
        road_cfg.append(c)
    road_cfg = road_cfg[: cfg.get("max_roads", 5)]
    for c in road_cfg: print(f"  chu 3D: {c['label']:32s} cach nha {c['_d']:.1f} km")
json.dump(roads, open(f"{P}/map/roads.json", "w"))

for st in cfg["stops"]:
    if "nearest_road" in st:
        if st["nearest_road"] not in roads: sys.exit(f"nearest_road '{st['nearest_road']}' khong co, cac khoa: {list(roads)}")
        add_route(st, nearest_on(roads[st["nearest_road"]]))
# keep config order
routes["pts"] = {st["label"]: routes["pts"][st["label"]] for st in cfg["stops"]}
json.dump(routes, open(f"{P}/map/routes.json", "w"), ensure_ascii=False)

# which stop reveals each auto road name: the first route that runs on / beside it, else the closest one
if road_cfg:
    for c in road_cfg:
        ds = []
        for st in cfg["stops"]:
            g = routes["pts"][st["label"]]["geom"]
            ds.append(min(dist_line((la, lo), roads[c["key"]], 2) for lo, la in g[::max(1, len(g) // 40)] + [g[-1]]))
        hit = [i for i, st in enumerate(cfg["stops"]) if st.get("nearest_road") == c["key"]] + [i for i, d in enumerate(ds) if d < 0.15]
        c["reveal_with"] = cfg["stops"][hit[0] if hit else ds.index(min(ds))]["label"]
        del c["_rank"], c["_d"]
    json.dump(road_cfg, open(f"{P}/map/roads_auto.json", "w"), ensure_ascii=False, indent=1)


# 3. satellite mosaics (Esri World Imagery)
def xy(lat, lon, z):
    n = 2 ** z; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def mosaic(z, lat1, lon1, lat2, lon2, out):
    x0, y0 = xy(lat1, lon1, z); x1, y1 = xy(lat2, lon2, z)
    tx0, tx1 = int(min(x0, x1)), int(max(x0, x1)); ty0, ty1 = int(min(y0, y1)), int(max(y0, y1))
    img = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (30, 34, 40))
    def one(t):
        x, y = t; p = f"{P}/map/cache/{z}_{x}_{y}.jpg"
        if not os.path.exists(p):
            u = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            open(p, "wb").write(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read())
        return t, p
    with cf.ThreadPoolExecutor(8) as ex:
        for (x, y), p in ex.map(one, [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]):
            try: img.paste(Image.open(p).convert("RGB"), ((x - tx0) * 256, (y - ty0) * 256))
            except Exception as e: print("o anh loi", p, e)
    img.save(out, quality=92); print(out, img.size)
    return dict(z=z, tx0=tx0, ty0=ty0, w=img.size[0], h=img.size[1])


FAR_KM = cfg.get("far_km", 9)
pts = [v["at"] for v in routes["pts"].values()]
near = [p for p in pts if km(H, p) <= FAR_KM] + [H]
far = [p for p in pts if km(H, p) > FAR_KM]
pad = 0.014
la = [p[0] for p in near]; lo = [p[1] for p in near]
m = {"wide": mosaic(16, max(la) + pad, min(lo) - pad, min(la) - pad, max(lo) + pad, f"{P}/assets/wide_z16.jpg"),
     "detail": mosaic(18, H[0] + 0.005, H[1] - 0.006, H[0] - 0.005, H[1] + 0.006, f"{P}/assets/detail_z18.jpg")}
allp = pts + [H]
la = [p[0] for p in allp]; lo = [p[1] for p in allp]
# the far layer always exists (it fills the edges of the wide layer); much larger when a stop is far away
fp = 0.09 if far else 0.05
m["far"] = mosaic(14, max(la) + fp, min(lo) - fp, min(la) - fp, max(lo) + fp, f"{P}/assets/far_z14.jpg")
json.dump(m, open(f"{P}/map/mosaics.json", "w"))
print("xong")
