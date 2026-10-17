#!/usr/bin/env python3
"""Quet tien ich quanh nha (ban kinh poi_km) va vung hanh chinh cho video quang cao ban do.

    python3 poi.py config.json PROJECT_DIR

Chay SAU fetch.py (can map/mosaics.json). Ghi ra:
  map/pois.json      ten, icon, toa do, m / giay o to (OSRM), chim bay
  map/regions.json   vien xa / tinh de to mau (Nominatim polygon)
  assets/poi/*.jpg   anh ve tinh can canh tung diem (hoac anh Giang gui: "photo" trong config)
Mang: nominatim.openstreetmap.org, router.project-osrm.org, server.arcgisonline.com.
"""
import hashlib, json, math, os, re, shutil, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageEnhance

UA = "bds-map-video/1.0"
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
P = sys.argv[2]
os.makedirs(f"{P}/map/cache", exist_ok=True); os.makedirs(f"{P}/assets/poi", exist_ok=True)
H = tuple(cfg["home"])
R_KM = cfg.get("poi_km", 5)


def get(u, raw=False):
    cp = f"{P}/map/cache/q_{hashlib.md5(u.encode()).hexdigest()}" + (".bin" if raw else ".json")
    if os.path.exists(cp): return open(cp, "rb").read() if raw else json.load(open(cp, encoding="utf-8"))
    for k in range(6):
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40).read()
            open(cp, "wb").write(b)
            if "nominatim" in u: time.sleep(1.3)
            return b if raw else json.loads(b)
        except Exception as e:
            if k == 5: raise
            w = 4 * 2 ** k; print(f"  mang loi ({e}), cho {w}s"); time.sleep(w)


def km(a, b):
    return math.hypot((a[0] - b[0]) * 110.6, (a[1] - b[1]) * 111.3 * math.cos(math.radians(a[0])))


def search(q, R):
    p = {"q": q, "format": "jsonv2", "limit": 40, "viewbox": f"{H[1]-R},{H[0]+R},{H[1]+R},{H[0]-R}", "bounded": 1,
         "accept-language": "vi"}
    return get("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(p))


# category: queries, accepted (category, type), icon, how many to keep
CATS = [
    ("market", ["chợ"], {("amenity", "marketplace")}, 3),
    ("school", ["trường"], {("amenity", "school")}, 2),
    ("gov", ["Ủy ban nhân dân"], {("office", "government"), ("amenity", "townhall")}, 1),
    ("hospital", ["bệnh viện"], {("amenity", "hospital")}, 1),
    ("clinic", ["trạm y tế"], {("amenity", "clinic")}, 1),
    ("shop", ["Bách hóa Xanh", "Co.opmart", "siêu thị", "WinMart"], {("shop", "supermarket"), ("shop", "convenience"), ("shop", "mall")}, 1),
    ("park", ["công viên"], {("leisure", "park")}, 1),
    ("factory", ["khu công nghiệp"], {("landuse", "industrial")}, 1),
]
ABBR = [(r"^Trường Trung học phổ thông", "Trường THPT"), (r"^Trường Trung học cơ sở", "Trường THCS"),
        (r"^Ủy ban nhân dân", "UBND"), (r"^Khu Công nghiệp", "KCN"), (r"^Khu công nghiệp", "KCN"),
        (r"^Bệnh viện Đa khoa", "BV Đa khoa"), (r"\s*\(.*\)$", "")]


def short(n):
    for a, b in ABBR: n = re.sub(a, b, n, flags=re.I)
    return n.strip()


def osrm(at):
    u = f"https://router.project-osrm.org/route/v1/driving/{H[1]},{H[0]};{at[1]},{at[0]}?overview=false"
    r = get(u)["routes"][0]; return round(r["distance"]), round(r["duration"])


skip = set(cfg.get("poi_skip", []))
pois = []
if cfg.get("poi_scan", True):
    R = R_KM / 111.0
    for icon, qs, ok, keep in CATS:
        if icon in cfg.get("poi_skip_cats", []): continue
        seen, found = set(), []
        for q in qs:
            for x in search(q, R):
                if (x.get("category"), x.get("type")) not in ok or not x.get("name"): continue
                at = (float(x["lat"]), float(x["lon"])); d = km(H, at)
                nm = short(x["name"])
                if d > R_KM or nm in seen or nm in skip: continue
                seen.add(nm); found.append({"label": nm, "icon": icon, "at": at, "air_m": round(d * 1000)})
        found.sort(key=lambda p: p["air_m"])
        pois += found[:keep]
extra = []
for e in cfg.get("pois_extra", []):
    extra.append({"label": e["label"], "icon": e["icon"], "at": tuple(e["at"]), "air_m": round(km(H, e["at"]) * 1000), **{k: e[k] for k in e if k in ("show_m", "show_s", "photo")}})
# drop near-duplicates (same place found twice, < 60 m apart)
# drop near-duplicates (same place found twice, < 120 m apart); places Giang named are always kept
out = list(extra)
for p in sorted(pois, key=lambda p: p["air_m"]):
    if any(km(p["at"], q["at"]) < 0.12 and p["icon"] == q["icon"] for q in out): continue
    if len(out) >= cfg.get("max_pois", 9): break
    out.append(p)
pois = sorted(out, key=lambda p: p["air_m"])
for p in pois:
    p["m"], p["s"] = osrm(p["at"])
    if "show_m" in p: p["m"] = p["show_m"]
    if "show_s" in p: p["s"] = p["show_s"]
    print(f"  {p['icon']:9s} {p['label']:38s} chim bay {p['air_m']:5d} m   o to {p['m']:5d} m  {p['s']/60:4.1f} phut")


# close-up picture of every place: the user's photo when given, else a sharp satellite crop
def txy(lat, lon, z):
    n = 2 ** z; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def sat_crop(at, z, out, W=480, Hh=320):
    x, y = txy(at[0], at[1], z); px, py = x * 256, y * 256
    x0, y0 = int((px - W / 2) // 256), int((py - Hh / 2) // 256); x1, y1 = int((px + W / 2) // 256), int((py + Hh / 2) // 256)
    img = Image.new("RGB", ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
    for tx in range(x0, x1 + 1):
        for ty in range(y0, y1 + 1):
            cp = f"{P}/map/cache/{z}_{tx}_{ty}.jpg"
            if not os.path.exists(cp):
                u = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{ty}/{tx}"
                open(cp, "wb").write(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read())
            img.paste(Image.open(cp).convert("RGB"), ((tx - x0) * 256, (ty - y0) * 256))
    l, t = px - W / 2 - x0 * 256, py - Hh / 2 - y0 * 256
    im = img.crop((int(l), int(t), int(l) + W, int(t) + Hh))
    im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.2)).enhance(1.1)
    im.save(out, quality=90)


for i, p in enumerate(pois):
    out = f"{P}/assets/poi/p{i}.jpg"
    if p.get("photo"):
        im = Image.open(p["photo"]).convert("RGB"); r = max(480 / im.width, 320 / im.height)
        im = im.resize((round(im.width * r), round(im.height * r))); l, t = (im.width - 480) // 2, (im.height - 320) // 2
        im.crop((l, t, l + 480, t + 320)).save(out, quality=90); p["img_src"] = "anh"
    else:
        sat_crop(p["at"], 17 if p["icon"] in ("factory", "park") else 18, out); p["img_src"] = "ve tinh"
    p["img"] = f"assets/poi/p{i}.jpg"
# the sharp z16 layer must cover every place shown (fetch.py sized it for the route stops only)
WM = json.load(open(f"{P}/map/mosaics.json"))
def inside_wide(at, pad=0.006):
    w = WM["wide"]; x, y = txy(at[0], at[1], 16)
    m = pad / 360 * 2 ** 16; return w["tx0"] + m < x < w["tx0"] + w["w"] / 256 - m and w["ty0"] + m < y < w["ty0"] + w["h"] / 256 - m
if pois and not all(inside_wide(p["at"]) for p in pois):
    w = WM["wide"]; n = 2 ** 16
    lon0 = w["tx0"] / n * 360 - 180; lon1 = (w["tx0"] + w["w"] / 256) / n * 360 - 180
    def lat_of(ty): return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty / n))))
    la = [p["at"][0] for p in pois] + [lat_of(w["ty0"]), lat_of(w["ty0"] + w["h"] / 256)]
    lo = [p["at"][1] for p in pois] + [lon0, lon1]
    pad = 0.012
    x0, y0 = txy(max(la) + pad, min(lo) - pad, 16); x1, y1 = txy(min(la) - pad, max(lo) + pad, 16)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    img = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (30, 34, 40))
    import concurrent.futures as cf
    def one(t):
        tx, ty = t; cp = f"{P}/map/cache/16_{tx}_{ty}.jpg"
        if not os.path.exists(cp):
            u = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/16/{ty}/{tx}"
            open(cp, "wb").write(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read())
        return t, cp
    with cf.ThreadPoolExecutor(8) as ex:
        for (tx, ty), cp in ex.map(one, [(a, b) for a in range(tx0, tx1 + 1) for b in range(ty0, ty1 + 1)]):
            img.paste(Image.open(cp).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
    img.save(f"{P}/assets/wide_z16.jpg", quality=90)
    WM["wide"] = dict(z=16, tx0=tx0, ty0=ty0, w=img.size[0], h=img.size[1]); json.dump(WM, open(f"{P}/map/mosaics.json", "w"))
    print("  mo rong lop anh z16:", img.size)
# outer layer (z12, ~150 km) for the opening shot: the whole province / city from high up
if "outer" not in WM:
    span = cfg.get("outer_deg", 0.55)
    x0, y0 = txy(H[0] + span, H[1] - span * 0.75, 12); x1, y1 = txy(H[0] - span, H[1] + span * 0.75, 12)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    img = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (30, 34, 40))
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            cp = f"{P}/map/cache/12_{tx}_{ty}.jpg"
            if not os.path.exists(cp):
                u = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/12/{ty}/{tx}"
                open(cp, "wb").write(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read())
            img.paste(Image.open(cp).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
    img.save(f"{P}/assets/outer_z12.jpg", quality=90)
    WM["outer"] = dict(z=12, tx0=tx0, ty0=ty0, w=img.size[0], h=img.size[1]); json.dump(WM, open(f"{P}/map/mosaics.json", "w"))
    print("  lop anh toan canh z12:", img.size)
json.dump(pois, open(f"{P}/map/pois.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# administrative areas to light up: {"label", "at": [lat, lon], "zoom": 14 (xa/phuong) | 10 (tinh/thanh pho)} or {"query"}
regions = []
for rg in cfg.get("regions", []):
    if "query" in rg:
        r = get("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": rg["query"], "format": "jsonv2", "polygon_geojson": 1, "polygon_threshold": 0.00003, "limit": 1}))[0]
    else:
        r = get("https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode({"lat": rg["at"][0], "lon": rg["at"][1], "format": "jsonv2", "zoom": rg.get("zoom", 14), "polygon_geojson": 1, "polygon_threshold": 0.00003}))
    g = r["geojson"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    ring = max((pp[0] for pp in polys), key=len)
    regions.append({**rg, "osm_name": r.get("display_name", ""), "ring": ring})
    print(f"  vung {rg['label']!r}: {r.get('display_name','')[:60]} ({len(ring)} diem)")
json.dump(regions, open(f"{P}/map/regions.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"xong: {len(pois)} tien ich, {len(regions)} vung")
