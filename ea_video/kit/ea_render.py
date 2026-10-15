#!/usr/bin/env python3
"""Bo dung video EA Bot vang: kich ban JSON -> video doc 9:16 co avatar noi, chu, phu de, nhac.

  python3 kit/ea_render.py kich_ban.json --describe                 # soat kich ban: moc thoi gian, loi cam ket, so dien thoai, chu tran
  python3 kit/ea_render.py kich_ban.json --sheet work/sheet.jpg     # bang khung moi 1.5s (mo bang Read)
  python3 kit/ea_render.py kich_ban.json --frames 1.2,4,9.5         # xuat khung PNG vao work/qc/
  python3 kit/ea_render.py kich_ban.json --preview --out xem_nhanh.mp4
  python3 kit/ea_render.py kich_ban.json --out ban_1080.mp4          # ban xuat (bi chan neu con [LOI])
  python3 kit/ea_render.py kich_ban.json --cover anh_bia.jpg
Tuy chon: --work work (thu muc tam), --brand kit/brand_ea.json, --revoice (doc lai giong), --force (bo qua chan [LOI]).
"""
import argparse, hashlib, json, math, os, re, subprocess, sys, time, unicodedata, difflib
import numpy as np
import skia

KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
import ea_style as S
import ea_text as T
import ea_voice as V
import ea_audio as A
import ea_broll as B
from ea_avatar import Bot, studio

W, H = 1080, 1920
XF = 0.22                      # thoi gian hoa canh (giay)

BANNED = ["cam kết lợi nhuận", "đảm bảo lợi nhuận", "lợi nhuận đảm bảo", "chắc chắn lãi", "chắc chắn có lãi", "chắc chắn thắng", "không bao giờ thua",
          "không thua lỗ", "không lỗ", "không rủi ro", "không có rủi ro", "zero rủi ro", "an toàn tuyệt đối", "an toàn 100", "thắng 100", "100% thắng",
          "lãi mỗi ngày", "lãi đều mỗi", "x2 tài khoản", "nhân đôi tài khoản", "gấp đôi tài khoản", "làm giàu nhanh", "thu nhập thụ động đảm bảo",
          "không bao giờ cháy", "không thể cháy", "không cháy tài khoản", "winrate 100", "bao lỗ", "hoàn tiền nếu lỗ", "lợi nhuận khủng", "siêu lợi nhuận",
          "kiếm tiền tự động mỗi ngày", "ăn chắc", "chắc ăn"]
RATE = re.compile(r"(lãi|lời|lợi nhuận|profit)\s*[^.,]{0,12}?\d+([.,]\d+)?\s*%|\d+([.,]\d+)?\s*%\s*(mỗi|/|một)\s*(ngày|tuần|tháng|năm)", re.I)
PHONE = re.compile(r"(?<!\d)(0|\+84)[\d .\-]{8,13}\d(?!\d)")


def low(s):
    return unicodedata.normalize("NFC", s).lower()


def norm_tok(s):
    s = unicodedata.normalize("NFD", low(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"[^a-z0-9]", "", s)


# ------------------------------------------------------------------ nap kich ban
def load(path, brand_path=None):
    sc = json.load(open(path, encoding="utf-8"))
    bp = brand_path or sc.get("brand") or os.path.join(KIT, "brand_ea.json")
    if not os.path.isabs(bp) and not os.path.exists(bp):
        bp = os.path.join(os.path.dirname(os.path.abspath(path)), bp)
    brand = json.load(open(bp, encoding="utf-8")) if os.path.exists(bp) else {}
    base = os.path.dirname(os.path.abspath(path))
    for s in sc["scenes"]:
        for k in ("file", "voice_file"):
            if s.get(k) and not os.path.isabs(s[k]):
                s[k] = os.path.join(base, s[k])
    v = sc.get("voice", {})
    if v.get("file") and not os.path.isabs(v["file"]):
        v["file"] = os.path.join(base, v["file"])
    m = sc.get("music", {})
    if m.get("file") and not os.path.isabs(m["file"]):
        m["file"] = os.path.join(base, m["file"])
    return sc, brand


def texts_of(scene):
    tx = scene.get("text")
    if not tx:
        return []
    return tx if isinstance(tx, list) else [tx]


def all_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in ("style", "at", "y", "size", "sizes", "count"):
                yield from all_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from all_strings(v)


def check(sc, brand):
    """-> list[(muc, noi dung)]  muc: LOI (chan ban xuat) | CANH BAO."""
    out = []
    for i, s in enumerate(sc["scenes"]):
        blobs = [("loi", s.get("say", ""))] + [("chu", x) for t in texts_of(s) for x in all_strings(t)]
        for kind, b in blobs:
            lb = low(S.strip_marks(b))
            for w in BANNED:
                if w in lb:
                    out.append(("LOI", f"canh {i + 1} ({kind}): cum hua hen \"{w}\" -> chi noi tinh nang, khong hua loi nhuan"))
            if RATE.search(lb):
                out.append(("LOI", f"canh {i + 1} ({kind}): ti le loi nhuan \"{RATE.search(lb).group(0)}\" -> bo, khong dua % loi nhuan len video"))
            if kind == "chu" and PHONE.search(b) and not brand.get("show_phone"):
                out.append(("LOI", f"canh {i + 1}: so dien thoai tren hinh \"{PHONE.search(b).group(0)}\" -> chi ghi trong mo ta / binh luan ghim"))
    if sc.get("disclaimer", True) is False:
        out.append(("CANH BAO", "da tat dong canh bao rui ro - quang cao tai chinh tren Facebook/TikTok nen giu"))
    if not any(t.get("style") == "cta" for s in sc["scenes"] for t in texts_of(s)):
        out.append(("CANH BAO", "chua co canh CTA (style cta) o cuoi"))
    return out


# ------------------------------------------------------------------ khop chu voi loi
def find_phrase(words, phrase, t_scene0):
    """Tim cum chu trong loi cua canh -> giay tuong doi canh, hoac None."""
    p = [norm_tok(x) for x in S.strip_marks(phrase).split() if norm_tok(x)]
    ws = [norm_tok(w["w"]) for w in words]
    if not p or not ws:
        return None
    best, bi = 0.0, None
    L = len(p)
    for i in range(len(ws)):
        win = ws[i:i + L]
        r = difflib.SequenceMatcher(None, p, win).ratio()
        if win and win[0] == p[0]:
            r += 0.15
        if r > best:
            best, bi = r, i
    if bi is not None and best >= 0.62:
        return max(0.0, words[bi]["t0"] - t_scene0 - 0.08)
    return None


def resolve_at(at, words, t0, default):
    if at is None:
        return default
    if isinstance(at, (int, float)):
        return float(at)
    if isinstance(at, str) and at.startswith("@"):
        r = find_phrase(words, at[1:], t0)
        return default if r is None else r
    return default


# ------------------------------------------------------------------ dung dong thoi gian
class Plan:
    def __init__(self, sc, brand, timing, fps):
        self.sc, self.brand, self.timing, self.fps = sc, brand, timing, fps
        self.scenes = []
        self.warn = []
        self.events = []
        prev_vis = None; bot_k = 0
        for i, (s, st) in enumerate(zip(sc["scenes"], timing["scenes"])):
            t0, t1 = st["t0"], st["t1"]
            dur = t1 - t0
            words = st.get("words", [])
            vend = st.get("voice_end", t1) - t0
            vis = s.get("visual", "bot")
            shot = s.get("shot")
            if vis == "bot" and not shot:
                shot = ["medium", "close"][bot_k % 2]; bot_k += 1
            ovs = []
            for tx in texts_of(s):
                t_in = resolve_at(tx.get("at"), words, t0, 0.15)
                t_out = resolve_at(tx.get("until"), words, t0, dur - 0.04)
                kind = tx.get("style", "title")
                key = {"title": "lines", "stack": "lines", "headline": "bullets", "box": "items", "checklist": "items"}.get(kind)
                subs = tx.get(key) or [] if key else []
                times = []
                n = len(subs)
                span_end = max(t_in + 0.6, min(vend, dur) - 0.35)
                for k, it in enumerate(subs):
                    txt = it["text"] if isinstance(it, dict) else it
                    at = it.get("at") if isinstance(it, dict) else None
                    if at is not None:
                        r = resolve_at(at, words, t0, None)
                    else:
                        r = find_phrase(words, txt, t0) if kind in ("headline", "box", "checklist") else None
                    if r is None:
                        if kind in ("title", "stack"):
                            r = t_in + k * (0.32 if kind == "title" else 0.22)
                        else:
                            lo_ = t_in + (0.7 if kind == "headline" else 0.0)
                            r = lo_ + k * (span_end - lo_) / max(1, n)
                    times.append(max(t_in, r) - t_in)
                for k in range(1, len(times)):                       # thu tu tang dan
                    times[k] = max(times[k], times[k - 1] + 0.25)
                ov = T.Overlay(tx, t_in, t_out, times)
                ovs.append(ov)
                # tieng dong
                if kind in ("title", "stat"):
                    self.events.append((t0 + t_in + 0.05, "boom", 0.55))
                if kind in ("headline", "checklist"):
                    for tt in times:
                        self.events.append((t0 + t_in + tt + (0.7 if kind == "headline" and False else 0), "tick", 0.45))
                if kind == "box":
                    for tt in times[1:]:
                        self.events.append((t0 + t_in + tt, "whoosh", 0.22))
                if kind == "cta":
                    self.events.append((t0 + t_in, "riser", 0.5))
                    self.events.append((t0 + t_in + 0.05, "shine", 0.6))
                # chu doc kip khong
                nwords = sum(len(S.strip_marks(x).split()) for x in all_strings(tx))
                show = t_out - t_in
                if nwords and show < nwords * 0.22 + 0.6:
                    self.warn.append(f"canh {i + 1}: chu '{kind}' hien {show:.1f}s cho {nwords} chu - hoi nhanh, keo dai loi hoac bot chu")
            if i > 0 and vis != prev_vis or (i > 0 and vis == "bot" and prev_vis == "bot"):
                self.events.append((t0, "whoosh", 0.45 if vis != prev_vis else 0.18))
            prev_vis = vis
            self.scenes.append({"i": i, "s": s, "t0": t0, "t1": t1, "dur": dur, "vis": vis, "shot": shot, "ovs": ovs, "words": words,
                                "obj": None})
        self.total = timing["total"]
        self.n = int(math.ceil(self.total * fps))
        allw = []
        for sc_ in self.scenes:
            if sc_["s"].get("caption", True):
                allw += T.chunk_words(sc_["words"], sc.get("caption_words", 4))
        self.captions = allw

    def scene_at(self, t):
        for s in self.scenes:
            if s["t0"] <= t < s["t1"]:
                return s
        return self.scenes[-1]


# ------------------------------------------------------------------ ve
class Renderer:
    def __init__(self, plan, voice_wav, scale=1.0):
        self.p = plan; self.k = scale
        self.bot = Bot(plan.brand.get("avatar"))
        self.bg = studio(W, H)
        self.lv, self.bd, self.talk = V.mouth_tracks(voice_wav, plan.fps, plan.n + 2)
        self.disc = plan.brand.get("disclaimer", "Giao dịch vàng có rủi ro · Không phải lời khuyên đầu tư")
        self.wm = plan.sc.get("watermark", plan.brand.get("watermark"))

    def visual(self, cv, sc, lt, f):
        s = sc["s"]; vis = sc["vis"]
        blur = float(s.get("blur", 0))
        if blur:
            bp = skia.Paint(); bp.setImageFilter(skia.ImageFilters.Blur(14 * blur, 14 * blur)); cv.saveLayer(None, bp)
        if vis == "bot":
            self._bot(cv, sc, lt, f)
        elif vis in ("chart", "mtf", "clock"):
            if sc["obj"] is None:
                if vis == "chart" and s.get("mode") in ("dca", "pause"):
                    sc["obj"] = B.DcaChart(W, H, s["mode"], s.get("seed", {"dca": 45, "pause": 26}[s["mode"]]), s.get("symbol", "XAUUSD"), s.get("tf", "M15"), labels=s.get("labels"))
                elif vis == "chart":
                    sc["obj"] = B.Chart(W, H, s.get("mode", "trend"), s.get("seed", 11 + sc["i"]), s.get("symbol", "XAUUSD"), s.get("tf", "M15"))
                elif vis == "mtf":
                    sc["obj"] = B.MTF(W, H, notes=tuple(s.get("notes", ("XU HƯỚNG", "VÙNG HỒI", "TÍN HIỆU"))))
                else:
                    sc["obj"] = B.Clock(W, H, s.get("center", "24/7"), s.get("sub", "EA KHÔNG NGỦ"))
            z = 1.0 + 0.05 * S.ease_in_out(lt / max(sc["dur"], 0.5))
            cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-W / 2, -H / 2)
            sc["obj"].draw(cv, lt, sc["dur"])
            cv.restore()
            if vis == "chart":
                B.finish(cv, W, H, dim=float(s.get("dim", 0.28)))
        elif vis == "aroll":
            if sc["obj"] is None:
                sc["obj"] = B.VideoClip(s["file"], W, H, self.p.fps, float(s.get("in", 0)), grade=False)
            off = self.p.timing["scenes"][sc["i"]].get("aroll_t", sc["t0"]) - sc["t0"]
            img = sc["obj"].frame(max(0.0, lt - off))
            if img is not None:
                cv.drawImage(img, 0, 0)
            cv.drawRect(skia.Rect.MakeXYWH(0, H * 0.5, W, H * 0.5), S.paint(shader=S.lin(0, H * 0.5, 0, H, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(140, 0, 0, 0)])))
        elif vis == "video":
            if sc["obj"] is None:
                sc["obj"] = B.VideoClip(s["file"], W, H, self.p.fps, float(s.get("start", 0)))
            img = sc["obj"].frame(lt)
            if img is not None:
                z = 1.0 + 0.06 * S.ease_in_out(lt / max(sc["dur"], 0.5))
                cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-W / 2, -H / 2)
                cv.drawImage(img, 0, 0); cv.restore()
            B.finish(cv, W, H, dim=float(s.get("dim", 0.32)))
        if blur:
            cv.restore()
        if s.get("pip") and vis != "bot":
            self._pip(cv, sc, lt, f)

    def _look(self, sc, lt):
        for ov in sc["ovs"]:
            if ov.t_in - 0.2 <= lt <= ov.t_out:
                return {"stack": (-0.6, 0.25), "headline": (-0.5, -0.3), "chapter": (-0.5, -0.3), "checklist": (-0.4, 0.4)}.get(ov.kind, (0.0, 0.45))
        return (0.0, 0.0)

    def _bot(self, cv, sc, lt, f):
        cv.drawImage(self.bg, 0, 0)
        shot = sc["shot"]
        s_, cy = {"medium": (1.0, 0.285), "close": (1.2, 0.30), "wide": (0.84, 0.30)}.get(shot, (1.0, 0.285))
        # punch-in nhe dau canh
        z = 1.0 + 0.035 * (1 - S.ease_out(lt / 0.5))
        look = sc["s"].get("look")
        look = {"left": (-0.6, 0.1), "right": (0.6, 0.1), "down": (0, 0.5), "center": (0, 0)}.get(look, None) if isinstance(look, str) else look
        if look is None:
            look = self._look(sc, lt)
        mood = sc["s"].get("mood", "neutral")
        fi = min(f, len(self.lv) - 1)
        pres = max([ov.presence(lt) for ov in sc["ovs"] if ov.kind in ("title", "box", "stack", "checklist", "cta", "stat")] or [0])
        cv.save(); cv.translate(W / 2, H * cy); cv.scale(z, z); cv.translate(-W / 2, -H * cy)
        self.bot.draw(cv, W / 2, H * cy, s_, self.p.scenes[0]["t0"] + f / self.p.fps, level=float(self.lv[fi]), bands=self.bd[fi],
                      look=look, mood=mood, talk=float(self.talk[fi]), detail=1 - 0.9 * pres)
        cv.restore()
        # lam toi phan duoi cho chu
        cv.drawRect(skia.Rect.MakeXYWH(0, H * 0.5, W, H * 0.5), S.paint(shader=S.lin(0, H * 0.5, 0, H, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(150, 0, 0, 0)])))

    def _pip(self, cv, sc, lt, f):
        cx, cy, r = W - 190, H * 0.62, 140
        cv.save()
        path = skia.Path(); path.addCircle(cx, cy, r)
        cv.drawCircle(cx, cy, r + 8, S.paint((0, 0, 0), 0.5, blur=14))
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        cv.drawImage(self.bg, 0, 0)
        fi = min(f, len(self.lv) - 1)
        self.bot.draw(cv, cx, cy + 20, 0.42, f / self.p.fps, float(self.lv[fi]), self.bd[fi], look=(-0.5, 0), talk=float(self.talk[fi]), body=False)
        cv.restore()
        cv.drawCircle(cx, cy, r, S.paint("gold", 0.95, stroke=5))

    def frame(self, f, captions=True):
        t = f / self.p.fps
        surf = skia.Surface(int(W * self.k), int(H * self.k))
        cv = surf.getCanvas()
        cv.scale(self.k, self.k)
        cv.clear(S.col("bg"))
        sc = self.p.scene_at(t)
        lt = t - sc["t0"]
        self.visual(cv, sc, lt, f)
        prev = self.p.scenes[sc["i"] - 1] if sc["i"] > 0 else None
        if prev is not None and lt < XF and not (prev["vis"] == "bot" and sc["vis"] == "bot"):   # bot -> bot: cat thang (jump cut)
            a = 1 - S.ease_in_out(lt / XF)
            cv.saveLayerAlpha(None, int(255 * a))
            self.visual(cv, prev, t - prev["t0"], f)
            for ov in prev["ovs"]:
                ov.draw(cv, t - prev["t0"])
            cv.restore()
        if sc["vis"] in ("bot", "aroll"):
            pres = max([ov.presence(lt) for ov in sc["ovs"] if ov.kind in ("title", "box", "stack", "checklist", "cta", "stat")] or [0])
            if pres > 0:
                cv.drawRect(skia.Rect.MakeXYWH(0, H * 0.40, W, H * 0.6), S.paint(shader=S.lin(0, H * 0.40, 0, H * 0.78, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(int(175 * pres), 4, 4, 6), skia.ColorSetARGB(int(205 * pres), 4, 4, 6)], [0, 0.35, 1])))
        for ov in sc["ovs"]:
            ov.draw(cv, lt)
        if captions:
            T.draw_caption(cv, t, self.p.captions, karaoke=self.p.sc.get("karaoke", True))
        if self.p.sc.get("disclaimer", True):
            T.draw_disclaimer(cv, self.disc)
        if self.wm and not any(ov.kind in ("chapter", "headline") and ov.presence(lt) > 0 for ov in sc["ovs"]):
            T.draw_watermark(cv, self.wm)
        return surf.makeImageSnapshot()


# ------------------------------------------------------------------ chuan bi
def prepare(args, log=print):
    sc, brand = load(args.script, args.brand)
    os.makedirs(args.work, exist_ok=True)
    key = hashlib.md5(json.dumps([sc.get("voice"), [(s.get("say"), s.get("voice_file"), s.get("hold"), s.get("dur"), s.get("visual") == "aroll" and [s.get("file"), s.get("in"), s.get("out")]) for s in sc["scenes"]], brand.get("doc")],
                                 ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    kf = os.path.join(args.work, "voice.key")
    tp = os.path.join(args.work, "timing.json")
    if not args.revoice and os.path.exists(kf) and open(kf).read() == key and os.path.exists(tp):
        timing = json.load(open(tp, encoding="utf-8"))
        log(f"[giong] dung lai giong da doc ({timing['total']:.1f}s) - them --revoice de doc lai")
    else:
        timing = V.build(sc, args.work, brand, log)
        open(kf, "w").write(key)
    plan = Plan(sc, brand, timing, sc.get("fps", 30))
    return sc, brand, timing, plan


def describe(sc, brand, plan):
    print(f"[tong] {plan.total:.1f}s, {len(plan.scenes)} canh, {plan.fps} khung/giay, giong: {sc.get('voice', {}).get('engine', 'offline')}")
    for s in plan.scenes:
        say = s["s"].get("say", "")
        print(f"[canh {s['i'] + 1:2d}] {s['t0']:6.2f}-{s['t1']:6.2f}s  {s['vis']:<6} {s['shot'] or '':<6} | {say[:70]}")
        for ov in s["ovs"]:
            first = next(iter(all_strings(ov.s)), "")
            ts = ", ".join(f"{ov.t_in + x:.1f}" for x in ov.times) if ov.times else ""
            print(f"           chu {ov.kind:<9} {ov.t_in:4.1f}-{ov.t_out:4.1f}s  \"{S.strip_marks(first)[:40]}\"" + (f"  muc con @ {ts}" if ts else ""))
    for w in plan.warn:
        print("[nhip]", w)
    issues = check(sc, brand)
    for lv, m in issues:
        print(f"[{lv}]", m)
    if not any(lv == "LOI" for lv, _ in issues):
        print("[soat] khong co loi cam ket loi nhuan / so dien thoai tren hinh")
    return issues


def render_video(args, sc, brand, plan, out, preview, log=print):
    mixw = os.path.join(args.work, "mix.wav")
    A.mix(os.path.join(args.work, "voice.wav"), plan.events, plan.total, sc.get("music", {"style": "dark_pad"}), mixw)
    k = 0.5 if preview else 1.0
    r = Renderer(plan, os.path.join(args.work, "voice.wav"), k)
    w, h = int(W * k), int(H * k)
    vcodec = ["-c:v", "libx264", "-preset", "ultrafast" if preview else "medium", "-crf", "27" if preview else "18", "-pix_fmt", "yuv420p"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r", str(plan.fps), "-i", "-",
           "-i", mixw, "-map", "0:v", "-map", "1:a"] + vcodec + ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                                                                  "-movflags", "+faststart", "-shortest", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start = time.time()
    for f in range(plan.n):
        img = r.frame(f)
        pr.stdin.write(img.tobytes())
        if f % (plan.fps * 5) == 0:
            el = time.time() - t_start
            log(f"[dung] {f / plan.fps:5.1f}/{plan.total:.1f}s  ({el:.0f}s)", )
    pr.stdin.close(); pr.wait()
    for s in plan.scenes:
        if isinstance(s.get("obj"), B.VideoClip):
            s["obj"].close()
    log(f"[xong] {out}  ({time.time() - t_start:.0f}s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--work", default="work")
    ap.add_argument("--brand")
    ap.add_argument("--describe", action="store_true")
    ap.add_argument("--sheet"); ap.add_argument("--step", type=float, default=1.5)
    ap.add_argument("--frames"); ap.add_argument("--frames-dir", default=None)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--cover")
    ap.add_argument("--revoice", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sc, brand, timing, plan = prepare(a)
    issues = describe(sc, brand, plan) if (a.describe or a.out) else check(sc, brand)
    voice = os.path.join(a.work, "voice.wav")
    if a.sheet:
        r = Renderer(plan, voice, 0.25)
        ts = list(np.arange(0.4, plan.total, a.step))
        cols = 6; rows = int(math.ceil(len(ts) / cols))
        cw, ch = int(W * 0.25), int(H * 0.25)
        sh = skia.Surface(cw * cols, ch * rows); c2 = sh.getCanvas(); c2.clear(S.col((0, 0, 0)))
        f_ = S.font("mono_b", 22)
        for i, t in enumerate(ts):
            img = r.frame(int(t * plan.fps))
            x, y = (i % cols) * cw, (i // cols) * ch
            c2.drawImage(img, x, y)
            c2.drawRect(skia.Rect.MakeXYWH(x, y, 80, 30), S.paint((0, 0, 0), 0.7))
            c2.drawString(f"{t:.1f}", x + 6, y + 23, f_, S.paint("gold_hi"))
        sh.makeImageSnapshot().save(a.sheet, skia.kJPEG, 85)
        print("[bang khung]", a.sheet)
    if a.frames:
        d = a.frames_dir or os.path.join(a.work, "qc")
        os.makedirs(d, exist_ok=True)
        r = Renderer(plan, voice, 1.0)
        for t in [float(x) for x in a.frames.split(",") if x.strip()]:
            p = os.path.join(d, f"f_{t:06.2f}.png")
            r.frame(int(t * plan.fps)).save(p, skia.kPNG)
            print("[khung]", p)
    if a.cover:
        r = Renderer(plan, voice, 1.0)
        s0 = plan.scenes[0]
        t = s0["t0"] + (max([ov.t_in + (max(ov.times) if ov.times else 0) for ov in s0["ovs"]] or [0.5]) + 0.6)
        t = min(t, s0["t1"] - 0.3)
        r.frame(int(t * plan.fps), captions=False).save(a.cover, skia.kJPEG, 92)
        print("[anh bia]", a.cover)
    if a.out:
        bad = [m for lv, m in issues if lv == "LOI"]
        if bad and not a.preview and not a.force:
            raise SystemExit("[chan] con [LOI] o tren - sua kich ban truoc khi xuat ban that (hoac --force neu Giang da duyet)")
        render_video(a, sc, brand, plan, a.out, a.preview)


if __name__ == "__main__":
    main()
