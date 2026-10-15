#!/usr/bin/env python3
"""Bo nhan dien va cong cu ve chung cho video EA Bot vang (skia).

Mau: den than #0B0C0F, vang #D4AF37 / #F2CF6B, trang nga #F4F0E8, do nhan #E0402F.
Chu: Be Vietnam Pro (dam, khong chan), Playfair Display (serif, nghieng vang), IBM Plex Mono (nhan nho, disclaimer).
Danh dau chu trong kich ban:  *chu*  = nghieng serif vang  |  {chu} = vang  |  [chu] = do
"""
import os, re, unicodedata
import skia

KIT = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(KIT, "fonts")

C = {
    "bg": (11, 12, 15), "ink": (244, 240, 232), "gold": (212, 175, 55), "gold_hi": (246, 214, 120),
    "gold_lo": (150, 112, 38), "red": (224, 64, 47), "teal": (64, 214, 220), "muted": (168, 162, 150),
    "panel": (16, 17, 21), "green": (38, 200, 140),
}

FONT_FILES = {
    "sans_md": "BeVietnamPro-Medium.ttf", "sans_sb": "BeVietnamPro-SemiBold.ttf", "sans_b": "BeVietnamPro-Bold.ttf",
    "sans_xb": "BeVietnamPro-ExtraBold.ttf", "sans_bk": "BeVietnamPro-Black.ttf",
    "serif": "PlayfairDisplay-Medium.ttf", "serif_b": "PlayfairDisplay-Bold.ttf",
    "serif_i": "PlayfairDisplay-MediumItalic.ttf", "serif_bi": "PlayfairDisplay-BoldItalic.ttf",
    "mono": "IBMPlexMono-Medium.ttf", "mono_b": "IBMPlexMono-SemiBold.ttf",
}
_TF = {}


def tf(name):
    if name not in _TF:
        p = os.path.join(FONT_DIR, FONT_FILES.get(name, name))
        t = skia.Typeface.MakeFromFile(p)
        if t is None:
            raise SystemExit(f"[font] khong mo duoc {p} - chay lai buoc lay bo cong cu")
        _TF[name] = t
    return _TF[name]


def font(name, size):
    f = skia.Font(tf(name), size)
    f.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
    f.setSubpixel(True)
    return f


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def col(c, a=1.0):
    if isinstance(c, str):
        c = C.get(c) or hex_rgb(c)
    a = max(0.0, min(1.0, a))
    return skia.ColorSetARGB(int(round(255 * a)), int(c[0]), int(c[1]), int(c[2]))


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def paint(c="ink", a=1.0, stroke=0, blur=0, shader=None):
    p = skia.Paint(AntiAlias=True)
    p.setColor(col(c, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(a)
    return p


def lin(x0, y0, x1, y1, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [col(c) if not isinstance(c, int) else c for c in colors], pos)


def rad(cx, cy, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, [col(c) if not isinstance(c, int) else c for c in colors], pos)


def rgba(rgb, a):
    return skia.ColorSetARGB(int(255 * max(0, min(1, a))), *[int(v) for v in rgb])


def rrect(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x); return 3 * x * x - 2 * x * x * x


def back_out(x, k=1.6):
    x = clamp(x); x -= 1; return 1 + x * x * ((k + 1) * x + k)


def env(t, t0, t1, fin=0.35, fout=0.25):
    """0..1: vao trong fin giay sau t0, ra trong fout giay truoc t1."""
    if t < t0 or t > t1:
        return 0.0
    a = ease_out((t - t0) / fin) if fin > 0 else 1.0
    b = ease_out((t1 - t) / fout) if fout > 0 else 1.0
    return min(a, b)


# ------------------------------------------------------------------ chu nhieu kieu
TOKEN = re.compile(r"\*([^*]+)\*|\{([^}]+)\}|\[([^\]]+)\]|([^*{\[]+)")


def parse_rich(s):
    """'VAO NHIEU *LENH*' -> [(text, kind)] kind: base | serif_gold | gold | red."""
    out = []
    for m in TOKEN.finditer(nfc(s)):
        if m.group(1):
            out.append((m.group(1), "serif_gold"))
        elif m.group(2):
            out.append((m.group(2), "gold"))
        elif m.group(3):
            out.append((m.group(3), "red"))
        elif m.group(4):
            out.append((m.group(4), "base"))
    return out


def strip_marks(s):
    return re.sub(r"[*{}\[\]]", "", nfc(s))


class Rich:
    """Mot dong chu nhieu kieu. base_font: ten font cho phan thuong; accent_font: font cho *chu*."""

    def __init__(self, s, size, base_font="sans_xb", accent_font="serif_bi", color="ink", tracking=0.0,
                 accent_scale=1.0, upper=False):
        self.size = size; self.tracking = tracking; self.color = color
        self.parts = []
        for txt, kind in parse_rich(s):
            if upper and kind != "serif_gold":
                txt = txt.upper()
            fn = accent_font if kind == "serif_gold" else base_font
            sz = size * (accent_scale if kind == "serif_gold" else 1.0)
            c = {"serif_gold": "gold_hi", "gold": "gold_hi", "red": "red"}.get(kind, color)
            f = font(fn, sz)
            w = f.measureText(txt) + tracking * size * max(0, len(txt) - 1)
            self.parts.append((txt, f, c, w))
        self.width = sum(p[3] for p in self.parts)
        m = font(base_font, size).getMetrics()
        self.ascent, self.descent = -m.fAscent, m.fDescent

    def draw(self, cv, x, y, align="left", alpha=1.0, shadow=0.55, glow=None):
        """y = duong chan chu (baseline)."""
        if align == "center":
            x -= self.width / 2
        elif align == "right":
            x -= self.width
        if shadow:
            sp = paint("bg", alpha * shadow, blur=self.size * 0.09)
            self._run(cv, x + self.size * 0.02, y + self.size * 0.05, sp, alpha, fixed=True)
        if glow:
            gp = paint(glow, alpha * 0.45, blur=self.size * 0.18)
            self._run(cv, x, y, gp, alpha, fixed=True)
        self._run(cv, x, y, None, alpha)
        return x

    def _run(self, cv, x, y, fixed_paint, alpha, fixed=False):
        cx = x
        for txt, f, c, w in self.parts:
            p = fixed_paint if fixed else paint(c, alpha)
            if self.tracking:
                for ch in txt:
                    cv.drawString(ch, cx, y, f, p)
                    cx += f.measureText(ch) + self.tracking * self.size
            else:
                cv.drawString(txt, cx, y, f, p)
                cx += w


def fit_size(lines, max_w, size, **kw):
    """Giam co chu cho tat ca dong cung vua max_w."""
    while size > 20:
        if all(Rich(l, size, **kw).width <= max_w for l in lines):
            return size
        size *= 0.95
    return size


def wrap_words(s, f, max_w):
    words, lines, cur = nfc(s).split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.measureText(strip_marks(t)) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines
