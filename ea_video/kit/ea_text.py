#!/usr/bin/env python3
"""Cac kieu chu tren video EA (theo video mau NHK: den - vang - trang, serif + khong chan).

Kieu (khoa "style" cua moi muc "text" trong canh):
  title     : chu serif lon giua man hinh, tung dong hien len.        {"lines": ["[BẬN] RỘN", "CÓ NÊN", "{ĐẦU TƯ VÀNG?}"]}
  headline  : tieu de dam goc trai tren + gach dau dong hien tung y.  {"lines": ["VÀO NHIỀU *LỆNH*", "HIỆU QUẢ *HƠN*"], "bullets": [...]}
  box       : hop lower-third toi vien vang, cac cum thay nhau.        {"items": ["KHÔNG CÓ THỜI GIAN", "*BỎ LỠ CƠ HỘI*"]}
  stack     : nhan nho + chu dam xep chong ben trai.                  {"label": "ÍT LỆNH HƠN", "lines": ["CHẤT", "LƯỢNG", "{HƠN}"]}
  chapter   : so chuong mono + tieu de goc trai tren (tren canh phu). {"num": "01", "label": "XU HƯỚNG", "lines": ["KHUNG *H4*", "XÁC ĐỊNH XU HƯỚNG"]}
  checklist : danh sach co dau tick vang.                            {"title": "AURUS SENTINEL", "items": ["SL cứng mỗi lệnh", ...]}
  stat      : con so lon + nhan.                                      {"value": "24/7", "label": "CHẠY KHÔNG NGHỈ"}
  cta       : hop keu goi hanh dong vang.                             {"lines": ["NHẮN ZALO", "NHẬN BẢN DÙNG THỬ"], "label": "MIỄN PHÍ"}
Danh dau: *chu* nghieng serif vang | {chu} vang | [chu] do.
Thoi diem: "at": giay tu dau canh, hoac "@cụm lời" = luc cum loi do duoc noi. Muc trong "items"/"bullets" co the la
  {"text": "...", "at": "@..."}; khong ghi thi tu chia deu trong canh.
"""
import math, re
import skia
import ea_style as S
from ea_style import paint, lin, rad, rrect, Rich, env, ease_out, back_out, clamp

W0, H0 = 1080, 1920
SAFE = 72
Y_CAP = 0.742          # phu de (duoi chu nhan, tren vung nut cua Reels/TikTok)
Y_DISC = 0.792         # dong canh bao rui ro


def _items(lst):
    out = []
    for it in lst or []:
        out.append(it if isinstance(it, dict) else {"text": it})
    return out


class Overlay:
    def __init__(self, spec, t_in, t_out, times=None):
        self.s = spec; self.t_in = t_in; self.t_out = t_out
        self.times = times or []                 # moc cho tung muc con (giay, tuong doi canh)
        self.kind = spec.get("style", "title")

    def draw(self, cv, t, W=W0, H=H0):
        fn = getattr(self, "_" + self.kind, None)
        if fn is None:
            raise SystemExit(f"[chu] kieu khong co: {self.kind}")
        if t < self.t_in - 0.01 or t > self.t_out + 0.3:
            return
        fn(cv, t, W, H)

    def presence(self, t):
        """0..1 muc do dang hien (de lam toi nen phia sau)."""
        return clamp((t - self.t_in + 0.3) / 0.3) * clamp((self.t_out + 0.3 - t) / 0.3)

    def _out(self, t):
        return clamp((self.t_out - t) / 0.25) if t > self.t_out - 0.25 else 1.0

    # ------------------------------------------------------------------ title
    def _title(self, cv, t, W, H):
        lines = self.s["lines"]
        big = self.s.get("size", 150)
        sizes = [big] + [big * 0.74] * (len(lines) - 1)
        if self.s.get("sizes"):
            sizes = self.s["sizes"]
        maxw = W - 2 * SAFE
        k = min(1.0, min(maxw / max(1, Rich(l, sz, base_font="serif", accent_font="serif_bi").width) for l, sz in zip(lines, sizes)))
        sizes = [sz * k for sz in sizes]
        gaps = [sz * 1.22 for sz in sizes]
        total = sum(gaps)
        yc = H * self.s.get("y", 0.565)
        y = yc - total / 2
        out = self._out(t)
        for i, (l, sz) in enumerate(zip(lines, sizes)):
            ti = self.t_in + (self.times[i] if i < len(self.times) else i * 0.32)
            a = ease_out((t - ti) / 0.4) * out
            if a <= 0:
                y += gaps[i]; continue
            r = Rich(l, sz, base_font="serif", accent_font="serif_bi")
            rise = (1 - a) * 34
            y += gaps[i]
            r.draw(cv, W / 2, y - sz * 0.2 + rise, align="center", alpha=a, shadow=0.8)
            if i == 0 and len(lines) > 1:
                lw = 130 * ease_out((t - ti - 0.2) / 0.4)
                cv.drawLine(W / 2 - lw / 2, y - sz * 0.07, W / 2 + lw / 2, y - sz * 0.07, paint("gold", a, stroke=4))

    # ------------------------------------------------------------------ headline + bullets
    def _headline(self, cv, t, W, H):
        lines = self.s.get("lines", [])
        sz = self.s.get("size", 112)
        maxw = W - 2 * SAFE
        sz = S.fit_size(lines, maxw, sz, base_font="sans_xb", accent_font="serif_bi") if lines else sz
        out = self._out(t)
        y = H * self.s.get("y", 0.15)
        for i, l in enumerate(lines):
            ti = self.t_in + i * 0.28
            a = ease_out((t - ti) / 0.38) * out
            y += sz * 1.12
            if a <= 0:
                continue
            Rich(l, sz, base_font="sans_xb", accent_font="serif_bi", upper=True).draw(cv, SAFE - (1 - a) * 40, y, alpha=a, shadow=0.8)
        bl = _items(self.s.get("bullets"))
        if not bl:
            return
        bsz = self.s.get("bullet_size", 52)
        y += sz * 0.55
        n = len(bl)
        for i, it in enumerate(bl):
            ti = self.t_in + (self.times[i] if i < len(self.times) else 0.9 + i * 0.55)
            a = ease_out((t - ti) / 0.3) * out
            y += bsz * 1.55
            if a <= 0:
                continue
            x = SAFE + (1 - a) * 30
            cv.drawRect(skia.Rect.MakeXYWH(x, y - bsz * 0.42, bsz * 0.22, bsz * 0.22), paint("gold", a))
            Rich(it["text"], bsz, base_font="sans_md", upper=True).draw(cv, x + bsz * 0.6, y, alpha=a, shadow=0.7)

    # ------------------------------------------------------------------ box (lower third)
    def _box(self, cv, t, W, H):
        items = _items(self.s.get("items"))
        if not items:
            return
        n = len(items)
        starts = [self.t_in + (self.times[i] if i < len(self.times) else i * (self.t_out - self.t_in) / n) for i in range(n)]
        cur = max([i for i in range(n) if t >= starts[i]] or [0])
        t_end = starts[cur + 1] if cur + 1 < n else self.t_out
        a_box = ease_out((t - self.t_in) / 0.3) * self._out(t)
        a_txt = min(ease_out((t - starts[cur]) / 0.25), clamp((t_end - t) / 0.12) if cur + 1 < n else 1.0) * self._out(t)
        txt = items[cur]["text"]
        sz = self.s.get("size", 66)
        bw_max = W - 2 * SAFE - 60
        lines = S.wrap_words(txt, S.font("serif", sz), bw_max - 80)
        sz2 = min(sz, S.fit_size(lines, bw_max - 80, sz, base_font="serif", accent_font="serif_bi"))
        rs = [Rich(l, sz2, base_font="serif", accent_font="serif_bi") for l in lines]
        tw = max(r.width for r in rs)
        bw = max(tw + 130, W * 0.6); bh = sz2 * 1.25 * len(rs) + sz2 * 1.0
        cx, cy = W / 2, H * self.s.get("y", 0.6)
        sc = 0.92 + 0.08 * ease_out((t - self.t_in) / 0.35)
        cv.save(); cv.translate(cx, cy); cv.scale(sc, 1)
        box = rrect(-bw / 2, -bh / 2, bw, bh, 6)
        cv.drawRRect(box, paint((0, 0, 0), 0.45 * a_box, blur=24))
        cv.drawRRect(box, paint((12, 12, 15), 0.82 * a_box))
        cv.drawRRect(box, paint("gold", 0.45 * a_box, stroke=1.6))
        cv.drawRect(skia.Rect.MakeXYWH(-bw / 2, -bh / 2, 7, bh), paint("gold", a_box))
        cv.restore()
        y = cy - bh / 2 + sz2 * 0.45
        for r in rs:
            y += sz2 * 1.25
            r.draw(cv, cx + 4, y - sz2 * 0.12, align="center", alpha=a_txt, shadow=0.4)

    # ------------------------------------------------------------------ stack
    def _stack(self, cv, t, W, H):
        out = self._out(t)
        y = H * self.s.get("y", 0.47)
        lab = self.s.get("label")
        if lab:
            a = ease_out((t - self.t_in) / 0.3) * out
            Rich(lab, 36, base_font="sans_md", tracking=0.06, upper=True).draw(cv, SAFE, y, alpha=a * 0.85, shadow=0.6)
            lw = 300 * ease_out((t - self.t_in - 0.1) / 0.45)
            cv.drawLine(SAFE, y + 30, SAFE + lw, y + 30, paint("gold", a * 0.9, stroke=3))
            y += 40
        lines = self.s.get("lines", [])
        sz = S.fit_size(lines, W * 0.62, self.s.get("size", 138), base_font="sans_xb") if lines else 120
        for i, l in enumerate(lines):
            ti = self.t_in + 0.2 + (self.times[i] if i < len(self.times) else i * 0.22)
            a = ease_out((t - ti) / 0.32) * out
            y += sz * 1.02
            if a <= 0:
                continue
            Rich(l, sz, base_font="sans_xb", upper=True).draw(cv, SAFE, y + (1 - a) * 26, alpha=a, shadow=0.85)

    # ------------------------------------------------------------------ chapter
    def _chapter(self, cv, t, W, H):
        out = self._out(t)
        a0 = ease_out((t - self.t_in) / 0.3) * out
        y = H * self.s.get("y", 0.105)
        num, lab = self.s.get("num", ""), self.s.get("label", "")
        tag = (f"{num} / {lab}" if num else lab).upper()
        if tag:
            Rich(tag, 32, base_font="mono_b", tracking=0.08).draw(cv, SAFE, y, alpha=a0, shadow=0.6)
            ln = 80 * ease_out((t - self.t_in - 0.15) / 0.4)
            cv.drawLine(SAFE, y + 22, SAFE + ln, y + 22, paint("gold", a0, stroke=3))
        lines = self.s.get("lines", [])
        sz = S.fit_size(lines, W - 2 * SAFE, self.s.get("size", 100), base_font="sans_xb", accent_font="serif_bi") if lines else 90
        y += 30
        for i, l in enumerate(lines):
            ti = self.t_in + 0.15 + i * 0.22
            a = ease_out((t - ti) / 0.35) * out
            y += sz * 1.08
            if a <= 0:
                continue
            Rich(l, sz, base_font="sans_xb", accent_font="serif_bi", upper=False).draw(cv, SAFE - (1 - a) * 36, y, alpha=a, shadow=0.85)

    # ------------------------------------------------------------------ checklist
    def _checklist(self, cv, t, W, H):
        out = self._out(t)
        items = _items(self.s.get("items"))
        title = self.s.get("title")
        sz = self.s.get("size", 50)
        x = SAFE + 10
        y = H * self.s.get("y", 0.47)
        rows = len(items) + (1 if title else 0)
        ph = sz * 1.7 * len(items) + (sz * 1.9 if title else 0) + sz * 0.8
        a0 = ease_out((t - self.t_in) / 0.3) * out
        cv.drawRRect(rrect(SAFE - 24, y - sz * 0.2, W - 2 * SAFE + 48, ph, 22), paint((10, 10, 13), 0.92 * a0))
        cv.drawRRect(rrect(SAFE - 24, y - sz * 0.2, W - 2 * SAFE + 48, ph, 22), paint("gold", 0.4 * a0, stroke=1.6))
        if title:
            y += sz * 1.35
            Rich(title, sz * 0.78, base_font="mono_b", tracking=0.06, color="gold_hi").draw(cv, x, y, alpha=a0, shadow=0)
            y += sz * 0.3
        maxw = W - 2 * SAFE - sz * 1.6
        for i, it in enumerate(items):
            ti = self.t_in + (self.times[i] if i < len(self.times) else 0.35 + i * 0.45)
            a = ease_out((t - ti) / 0.3) * out
            y += sz * 1.7
            if a <= 0:
                continue
            cx_, cy_ = x + sz * 0.42, y - sz * 0.36
            pop = back_out((t - ti) / 0.35)
            cv.drawCircle(cx_, cy_, sz * 0.42 * pop, paint("gold", a))
            ck = skia.Path(); ck.moveTo(cx_ - sz * 0.19, cy_); ck.lineTo(cx_ - sz * 0.04, cy_ + sz * 0.15); ck.lineTo(cx_ + sz * 0.21, cy_ - sz * 0.16)
            cv.drawPath(ck, paint((20, 15, 5), a, stroke=sz * 0.09))
            s2 = S.fit_size([it["text"]], maxw, sz, base_font="sans_sb")
            Rich(it["text"], s2, base_font="sans_sb").draw(cv, x + sz * 1.15, y, alpha=a, shadow=0.5)

    # ------------------------------------------------------------------ stat
    def _stat(self, cv, t, W, H):
        out = self._out(t)
        val = str(self.s.get("value", ""))
        a = ease_out((t - self.t_in) / 0.35) * out
        sz = self.s.get("size", 250)
        m = re.fullmatch(r"(\d+)([%x+]|\s.*)?", val)
        shown = val
        if m and self.s.get("count", True):
            k = ease_out((t - self.t_in) / 0.9)
            shown = str(int(round(int(m.group(1)) * k))) + (m.group(2) or "")
        cy = H * self.s.get("y", 0.6)
        sz = min(sz, S.fit_size(["{" + val + "}"], W - 2 * SAFE, sz, base_font="serif_b"))
        sc = 0.85 + 0.15 * back_out((t - self.t_in) / 0.45)
        cv.save(); cv.translate(W / 2, cy); cv.scale(sc, sc)
        Rich("{" + shown + "}", sz, base_font="serif_b").draw(cv, 0, 0, align="center", alpha=a, glow="gold", shadow=0.8)
        cv.restore()
        lab = self.s.get("label")
        if lab:
            a2 = ease_out((t - self.t_in - 0.35) / 0.35) * out
            ls = S.fit_size([lab], W - 2 * SAFE, 50, base_font="sans_b")
            Rich(lab, ls, base_font="sans_b", tracking=0.04, upper=True).draw(cv, W / 2, cy + ls * 1.6, align="center", alpha=a2)

    # ------------------------------------------------------------------ cta
    def _cta(self, cv, t, W, H):
        out = self._out(t)
        lines = self.s.get("lines", ["NHẮN TIN NGAY"])
        a = ease_out((t - self.t_in) / 0.35) * out
        sz = S.fit_size(lines, W - 2 * SAFE - 120, self.s.get("size", 68), base_font="sans_xb")
        bh = sz * 1.25 * len(lines) + sz * 1.0
        bw = max(Rich(l, sz, base_font="sans_xb").width for l in lines) + 130
        cx, cy = W / 2, H * self.s.get("y", 0.6)
        pulse = 1 + 0.025 * math.sin((t - self.t_in) * 2 * math.pi / 1.1) * clamp((t - self.t_in - 0.5) / 0.3)
        sc = (0.8 + 0.2 * back_out((t - self.t_in) / 0.45)) * pulse
        lab = self.s.get("label")
        if lab:
            Rich(lab, 34, base_font="mono_b", tracking=0.1, color="gold_hi").draw(cv, cx, cy - bh / 2 * sc - 30, align="center", alpha=a)
        cv.save(); cv.translate(cx, cy); cv.scale(sc, sc)
        box = rrect(-bw / 2, -bh / 2, bw, bh, 20)
        cv.drawRRect(box, paint("gold", 0.35 * a, blur=30))
        cv.drawRRect(box, paint(shader=lin(-bw / 2, -bh / 2, bw / 2, bh / 2, [S.C["gold_hi"], S.C["gold"], S.C["gold_lo"]], [0, 0.5, 1]), a=a))
        # vet sang quet qua
        cv.save(); cv.clipRRect(box, skia.ClipOp.kIntersect, True)
        ph = ((t - self.t_in) % 2.2) / 2.2
        sx = -bw + ph * bw * 2.4
        sp = skia.Path(); sp.moveTo(sx, -bh); sp.lineTo(sx + 90, -bh); sp.lineTo(sx + 10, bh); sp.lineTo(sx - 80, bh); sp.close()
        cv.drawPath(sp, paint((255, 255, 255), 0.28 * a))
        cv.restore()
        y = -bh / 2 + sz * 0.5
        for l in lines:
            y += sz * 1.25
            Rich(l, sz, base_font="sans_xb", color=(22, 16, 6), upper=True).draw(cv, 0, y - sz * 0.15, align="center", alpha=a, shadow=0)
        cv.restore()


# ------------------------------------------------------------------ phu de
def chunk_words(words, max_syl=4):
    """[{w,t0,t1}] -> [(text, t0, t1, ws)]: ngat o dau cau truoc, moi cum <= max_syl+1 tieng, chia deu."""
    clauses, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[,.;:!?…]$", w["w"]):
            clauses.append(cur); cur = []
    if cur:
        clauses.append(cur)
    out = []
    for c in clauses:
        n = len(c)
        if n <= max_syl + 1:
            out.append(c); continue
        k = math.ceil(n / max_syl); size = math.ceil(n / k)
        for j in range(0, n, size):
            out.append(c[j:j + size])
    res = []
    for c in out:
        txt = re.sub(r"[,.;:]$", "", " ".join(x["w"] for x in c))
        res.append((txt, c[0]["t0"], c[-1]["t1"], c))
    return res


def draw_caption(cv, t, chunks, W=W0, H=H0, size=56, karaoke=True, y=Y_CAP):
    cur = None
    for i, (txt, a, b, ws) in enumerate(chunks):
        nxt = chunks[i + 1][1] if i + 1 < len(chunks) else b + 0.4
        if a - 0.05 <= t < min(nxt, b + 0.45):
            cur = (txt, a, b, ws); break
    if not cur:
        return
    txt, a, b, ws = cur
    f = S.font("sans_b", size)
    k = clamp((t - a + 0.05) / 0.12)
    words = [S.strip_marks(w["w"]).rstrip(",.;:") for w in ws]
    widths = [f.measureText(w) for w in words]
    sp = f.measureText(" ")
    total = sum(widths) + sp * (len(words) - 1)
    scale = min(1.0, (W - 2 * SAFE) / max(1, total))
    if scale < 1:
        f = S.font("sans_b", size * scale); widths = [f.measureText(w) for w in words]; sp = f.measureText(" "); total = sum(widths) + sp * (len(words) - 1)
    x = W / 2 - total / 2
    yy = H * y + (1 - ease_out(k)) * 10
    stroke = paint((0, 0, 0), 0.9 * k, stroke=size * 0.16)
    shadow = paint((0, 0, 0), 0.55 * k, blur=size * 0.12)
    for w, wd, wt in zip(words, widths, ws):
        cv.drawString(w, x + 2, yy + 4, f, shadow)
        cv.drawString(w, x, yy, f, stroke)
        hot = karaoke and wt["t0"] - 0.02 <= t <= wt["t1"] + 0.02
        cv.drawString(w, x, yy, f, paint("gold_hi" if hot else "ink", k))
        x += wd + sp


def draw_disclaimer(cv, text, W=W0, H=H0, alpha=0.62, y=Y_DISC):
    t = S.nfc(text).upper()
    sz = 25
    while sz > 14:
        r = Rich(t, sz, base_font="mono", tracking=0.05)
        if r.width <= W - 2 * SAFE:
            break
        sz -= 1
    r.draw(cv, W / 2, H * y, align="center", alpha=alpha, shadow=0.9)


def draw_watermark(cv, text, W=W0, H=H0, alpha=0.75):
    r = Rich(text, 26, base_font="mono_b", tracking=0.12, color="gold_hi")
    cv.drawRect(skia.Rect.MakeXYWH(SAFE, H * 0.088 - 30, 4, 38), paint("gold", alpha))
    r.draw(cv, SAFE + 18, H * 0.088, alpha=alpha, shadow=0.7)
