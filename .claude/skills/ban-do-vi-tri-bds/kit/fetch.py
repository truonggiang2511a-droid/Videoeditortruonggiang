#!/usr/bin/env python3
"""Lay du lieu that cho video ban do vi tri.

    python3 fetch.py config.json PROJECT_DIR

Ghi ra PROJECT_DIR/map/{roads,routes,mosaics}.json va PROJECT_DIR/assets/{wide_z16,detail_z18,far_z14}.jpg.
Can mang toi: nominatim.openstreetmap.org, router.project-osrm.org, server.arcgisonline.com.
"""
import concurrent.futures as cf, io, json, math, os, sys, time, urllib.parse, urllib.request
from PIL import Image

UA = "bds-map-video/1.0"
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
P = sys.argv[2]
os.makedirs(f"{P}/map/cache", exist_ok=True); os.makedirs(f"{P}/assets", exist_ok=True)
H = tuple(cfg["home"])


def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40))


def km(a, b):
    return math.hypot((a[0] - b[0]) * 110.6, (a[1] - b[1]) * 109.3 * math.cos(math.radians(a[0])) / math.cos(math.radians(10.6)))


def nominatim(q, R, geo=False, limit=40):
    vb = f"{H[1]-R},{H[0]+R},{H[1]+R},{H[0]-R}"
    p = {"q": q, "format": "jsonv2", "limit": limit, "viewbox": vb, "bounded": 1, "accept-language": "vi"}
    if geo: p.update(polygon_geojson=1, polygon_threshold=0.00005)
    r = get("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(p)); time.sleep(1.3)
    return r


# 1. road geometries for the flat 3D road names and road glow
roads = {}
for rd in cfg.get("roads", []):
    lines = []
    for q in rd["queries"]:
        for x in nominatim(q, rd.get("radius", 0.08), geo=True):
            g = x.get("geojson", {})
            if x.get("category") != "highway": continue
            if g.get("type") == "LineString": lines.append(g["coordinates"])
            elif g.get("type") == "MultiLineString": lines += g["coordinates"]
    roads[rd["key"]] = lines
    print(f"road {rd['key']}: {len(lines)} doan")
json.dump(roads, open(f"{P}/map/roads.json", "w"))


def nearest_on(lines):
    best = None
    for l in lines:
        for i in range(len(l) - 1):
            (x1, y1), (x2, y2) = l[i], l[i + 1]
            for k in range(21):
                t = k / 20; p = (y1 + (y2 - y1) * t, x1 + (x2 - x1) * t); d = km(H, p)
                if not best or d < best[0]: best = (d, p)
    return best[1]


# 2. stop coordinates + real driving routes
routes = {"home": H, "pts": {}}
for st in cfg["stops"]:
    if "at" in st: at = tuple(st["at"])
    elif "nearest_road" in st: at = nearest_on(roads[st["nearest_road"]])
    else:
        r = nominatim(st["query"], st.get("radius", 0.3), limit=5)
        if not r: sys.exit(f"khong tim thay: {st['query']}")
        at = (float(r[0]["lat"]), float(r[0]["lon"]))
    u = f"https://router.project-osrm.org/route/v1/driving/{H[1]},{H[0]};{at[1]},{at[0]}?overview=full&geometries=geojson"
    d = get(u)["routes"][0]; time.sleep(1)
    routes["pts"][st["label"]] = {"at": at, "m": round(d["distance"]), "s": round(d["duration"]), "geom": d["geometry"]["coordinates"], "air_m": round(km(H, at) * 1000)}
    print(f"{st['label']:28s} duong {d['distance']:7.0f} m  oto {d['duration']/60:5.1f} phut  chim bay {km(H, at)*1000:6.0f} m")
json.dump(routes, open(f"{P}/map/routes.json", "w"), ensure_ascii=False)


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
