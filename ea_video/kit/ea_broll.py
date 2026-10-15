#!/usr/bin/env python3
"""Canh phu (B-roll) tu dung cho video EA vang - khong can footage.

visual:
  "chart"  : bieu do nen XAUUSD dong, duong EMA vang. "mode": "trend" | "range" | "sl" (diem vao + SL cung + TP) | "drop" (sap manh)
  "mtf"    : 3 khung H4 / H1 / M15 xep doc, lan luot sang: xu huong -> vung hoi -> tin hieu
  "clock"  : dong ho 24 gio voi 3 phien A / Au / My, chu 24/7 o giua
  "video"  : file video that (stock vidIQ/Pexels, quay man hinh MT5...) -> cat khung 9:16, phu mau toi
Moi canh co the them "blur": 0..1 (lam mo de chu noi bat), "dim": 0..1.
"""
import math, random, subprocess, os
import numpy as np
import skia
import ea_style as S
from ea_style import paint, lin, rad, rrect, col

BULL = (38, 200, 140)
BEAR = (224, 64, 47)


def gold_series(n, seed=11, mode="trend", start=2400.0):
    rnd = np.random.default_rng(seed)
    drift = {"trend": 0.9, "range": 0.0, "sl": 0.6, "drop": -0.3}.get(mode, 0.5)
    o, h, l, c = [], [], [], []
    p = start
    for i in range(n):
        d = drift + rnd.normal(0, 4.2)
        if mode == "range":
            d += (start - p) * 0.08
        if mode == "drop" and i > n * 0.7:
            d -= 9
        if mode == "trend" and n * 0.55 < i < n * 0.7:
            d -= 2.2                                           # nhip hoi
        op = p; cl = p + d
        hi = max(op, cl) + abs(rnd.normal(0, 2.8)); lo = min(op, cl) - abs(rnd.normal(0, 2.8))
        o.append(op); h.append(hi); l.append(lo); c.append(cl); p = cl
    return np.array(o), np.array(h), np.array(l), np.array(c)


def ema(x, n=12):
    out = np.zeros_like(x); a = 2 / (n + 1); out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = out[i - 1] + a * (x[i] - out[i - 1])
    return out


class Chart:
    def __init__(self, W, H, mode="trend", seed=11, symbol="XAUUSD", tf="M15", n=90):
        self.W, self.H, self.mode, self.symbol, self.tf = W, H, mode, symbol, tf
        self.o, self.h, self.l, self.c = gold_series(n, seed, mode)
        self.e = ema(self.c, 14)
        self.n = n

    def draw(self, cv, t, dur, x0=0, y0=0, w=None, h=None, show_axis=True, alpha=1.0, reveal=1.0):
        W = w or self.W; H = h or self.H
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y0, W, H)); cv.translate(x0, y0)
        cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=lin(0, 0, 0, H, [(5, 14, 20), (10, 28, 36), (4, 9, 12)], [0, 0.55, 1]), a=alpha))
        # luoi
        gp = paint((40, 80, 92), 0.28 * alpha, stroke=1.2)
        for i in range(1, 12):
            cv.drawLine(0, H * i / 12, W, H * i / 12, gp)
        for i in range(1, 7):
            cv.drawLine(W * i / 7, 0, W * i / 7, H, gp)
        # khung nhin: so nen hien, cuon cham
        vis = 34
        prog = S.clamp(t / max(dur, 0.1))
        span = 0.08 if self.mode == "sl" else 0.36
        end = min(self.n, int(self.n * 0.62 + (self.n * span) * prog * reveal) + 1)
        start = max(0, end - vis)
        sl = slice(start, end)
        lo = self.l[sl].min(); hi = self.h[sl].max()
        if self.mode == "sl":
            ie = int(self.n * 0.62) - 6; e_ = self.c[ie]; rg = (hi - lo) * 0.16
            lo = min(lo, e_ - rg); hi = max(hi, e_ + 2 * rg)
        pad = (hi - lo) * 0.1
        lo -= pad; hi += pad
        top, bot = (H * 0.27, H * 0.70) if H > 1000 else (H * 0.18, H * 0.86)
        Y = lambda v: bot - (v - lo) / (hi - lo) * (bot - top)
        cw = (W * 0.86) / vis
        X = lambda i: W * 0.04 + (i - start) * cw + cw / 2
        # nen cuoi dang "nhay" gia
        live = end - 1
        frac = (t * 1.7) % 1.0
        for i in range(start, end):
            o, hh, ll, c = self.o[i], self.h[i], self.l[i], self.c[i]
            if i == live:
                c = o + (c - o) * (0.4 + 0.6 * frac)
            colr = BULL if c >= o else BEAR
            x = X(i)
            cv.drawLine(x, Y(hh), x, Y(ll), paint(colr, 0.9 * alpha, stroke=max(1.5, cw * 0.09)))
            yt, yb = Y(max(o, c)), Y(min(o, c))
            body = skia.Rect.MakeLTRB(x - cw * 0.33, yt, x + cw * 0.33, max(yb, yt + 2))
            cv.drawRect(body, paint(colr, 0.95 * alpha))
            if i == live:
                cv.drawRect(body, paint(colr, 0.5 * alpha, blur=8))
        # EMA vang
        ep = skia.Path()
        for k, i in enumerate(range(start, end)):
            (ep.moveTo if k == 0 else ep.lineTo)(X(i), Y(self.e[i]))
        cv.drawPath(ep, paint("gold", 0.35 * alpha, stroke=10, blur=6))
        cv.drawPath(ep, paint("gold_hi", 0.95 * alpha, stroke=4))
        # duong gia hien tai
        pc = self.o[live] + (self.c[live] - self.o[live]) * (0.4 + 0.6 * frac)
        yp = Y(pc)
        dash = paint("gold_hi", 0.6 * alpha, stroke=2); dash.setPathEffect(skia.DashPathEffect.Make([14, 10], t * 30 % 24))
        cv.drawLine(0, yp, W, yp, dash)
        if show_axis and self.mode != "sl":
            f = S.font("mono_b", max(18, W * 0.026))
            lab = f"{pc:,.2f}"
            tw = f.measureText(lab)
            cv.drawRRect(rrect(W - tw - 34, yp - 22, tw + 26, 44, 8), paint("gold", 0.95 * alpha))
            cv.drawString(lab, W - tw - 21, yp + 9, f, paint((20, 16, 8), alpha))
        if show_axis:
            f2 = S.font("mono_b", max(18, W * 0.03))
            cv.drawString(f"{self.symbol} · {self.tf}", W * 0.05, H * 0.715, f2, paint("ink", 0.45 * alpha))
        if self.mode == "sl":
            self._sl(cv, X, Y, start, end, W, H, t, alpha)
        cv.restore()

    def _sl(self, cv, X, Y, start, end, W, H, t, alpha):
        i = int(self.n * 0.62) - 6
        hi0 = self.h[start:end].max(); lo0 = self.l[start:end].min()
        entry = self.c[i]; sl = entry - (hi0 - lo0) * 0.16
        tp = entry + (entry - sl) * 2.0
        f = S.font("mono_b", 30)
        for v, name, c in ((sl, "SL", BEAR), (tp, "TP", S.C["gold_hi"]), (entry, "VÀO", S.C["ink"])):
            y = Y(v)
            p = paint(c, 0.9 * alpha, stroke=3); p.setPathEffect(skia.DashPathEffect.Make([18, 10], 0))
            cv.drawLine(X(i), y, W * 0.92, y, p)
            cv.drawRRect(rrect(W * 0.92 - 110, y - 24, 104, 48, 10), paint(c, 0.95 * alpha))
            tc = (255, 255, 255) if name == "SL" else (16, 14, 10)
            cv.drawString(name, W * 0.92 - 58 - f.measureText(name) / 2, y + 11, f, paint(tc, alpha))
        # mui ten vao lenh
        x, y = X(i), Y(self.l[i]) + 40
        ar = skia.Path(); ar.moveTo(x, y - 26); ar.lineTo(x - 22, y + 14); ar.lineTo(x + 22, y + 14); ar.close()
        cv.drawPath(ar, paint(BULL, alpha))
        # vung rui ro to nhe
        cv.drawRect(skia.Rect.MakeLTRB(X(i), Y(entry), W * 0.92, Y(sl)), paint(BEAR, 0.10 * alpha))


class MTF:
    """3 khung xep doc, lan luot sang theo t: H4 xu huong, H1 vung hoi, M15 tin hieu."""

    def __init__(self, W, H, seed=5, labels=("H4", "H1", "M15"), notes=("XU HƯỚNG", "VÙNG HỒI", "TÍN HIỆU")):
        self.W, self.H = W, H
        self.charts = [Chart(W, H // 3, "trend", seed + k * 7, tf=labels[k], n=70 + k * 10) for k in range(3)]
        self.labels, self.notes = labels, notes

    def draw(self, cv, t, dur):
        W, H = self.W, self.H
        cv.drawRect(skia.Rect.MakeWH(W, H), paint((4, 8, 11)))
        ph = H * 0.15; gap = H * 0.02; y0 = H * 0.215
        for k, ch in enumerate(self.charts):
            on = S.ease_out((t - k * dur / 3.2) / 0.5)
            y = y0 + k * (ph + gap)
            a = 0.25 + 0.75 * on
            ch.draw(cv, t, dur, x0=W * 0.06, y0=y, w=W * 0.88, h=ph, show_axis=False, alpha=a)
            cv.drawRRect(rrect(W * 0.06, y, W * 0.88, ph, 18), paint("gold", (0.25 + 0.6 * on), stroke=3))
            f = S.font("mono_b", 34); f2 = S.font("sans_b", 30)
            cv.drawRRect(rrect(W * 0.06 + 22, y + 20, 120, 52, 10), paint("gold", 0.9 * a))
            cv.drawString(self.labels[k], W * 0.06 + 82 - f.measureText(self.labels[k]) / 2, y + 58, f, paint((18, 14, 6), a))
            cv.drawString(self.notes[k], W * 0.06 + 164, y + 58, f2, paint("ink", 0.9 * a))
            if on > 0.5:
                cv.drawCircle(W * 0.86, y + 46, 16, paint(BULL, on))
                ck = skia.Path(); ck.moveTo(W * 0.86 - 8, y + 46); ck.lineTo(W * 0.86 - 2, y + 53); ck.lineTo(W * 0.86 + 9, y + 39)
                cv.drawPath(ck, paint((8, 30, 20), on, stroke=4))


class Clock:
    """Dong ho 24h, 3 phien giao dich (gio VN), kim quay, 24/7 o giua."""

    def __init__(self, W, H, center_text="24/7", sub="EA KHÔNG NGỦ"):
        self.W, self.H, self.center_text, self.sub = W, H, center_text, sub
        rnd = random.Random(2)
        self.dust = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1, 3.2), rnd.uniform(0.2, 1)) for _ in range(90)]

    def draw(self, cv, t, dur):
        W, H = self.W, self.H
        cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=rad(W / 2, H * 0.44, H * 0.7, [(22, 20, 16), (6, 6, 8)])))
        for x, y, r, sp in self.dust:
            yy = (y - t * 18 * sp) % H
            cv.drawCircle(x, yy, r, paint("gold_hi", 0.18 * sp))
        cx, cy, R = W / 2, H * 0.40, W * 0.29
        sessions = [(7, 16, (64, 214, 220), "Á"), (14, 23, S.C["gold"], "ÂU"), (19, 28, (224, 120, 80), "MỸ")]
        on = S.ease_out(t / 0.8)
        for k, (a, b, c, name) in enumerate(sessions):
            rr = R + 34 + k * 30
            sweep = (b - a) / 24 * 360 * S.ease_out((t - 0.2 - k * 0.25) / 0.9)
            p = paint(c, 0.9, stroke=18)
            cv.drawArc(skia.Rect.MakeXYWH(cx - rr, cy - rr, 2 * rr, 2 * rr), -90 + a / 24 * 360, sweep, False, p)
            if sweep > 20:
                ang = math.radians(-90 + (a + (b - a) * 0.5) / 24 * 360)
                f = S.font("sans_b", 30)
                tx, ty = cx + (rr + 50) * math.cos(ang), cy + (rr + 50) * math.sin(ang)
                cv.drawString(name, tx - f.measureText(name) / 2, ty + 10, f, paint(c, on))
        cv.drawCircle(cx, cy, R, paint((14, 14, 16), 0.95))
        cv.drawCircle(cx, cy, R, paint("gold", 0.9, stroke=5))
        for h in range(24):
            ang = math.radians(-90 + h / 24 * 360)
            l1 = R - (34 if h % 6 == 0 else 18)
            cv.drawLine(cx + l1 * math.cos(ang), cy + l1 * math.sin(ang), cx + (R - 6) * math.cos(ang), cy + (R - 6) * math.sin(ang),
                        paint("gold_hi" if h % 6 == 0 else "muted", 0.9, stroke=5 if h % 6 == 0 else 2.5))
        ang = math.radians(-90 + (t * 50) % 360)
        cv.drawLine(cx, cy, cx + (R - 60) * math.cos(ang), cy + (R - 60) * math.sin(ang), paint("gold_hi", 0.4, stroke=14, blur=8))
        cv.drawLine(cx, cy, cx + (R - 60) * math.cos(ang), cy + (R - 60) * math.sin(ang), paint("gold_hi", 1, stroke=6))
        cv.drawCircle(cx, cy, 14, paint("gold_hi"))
        r = S.Rich("{" + self.center_text + "}", R * 0.42, base_font="serif_b")
        r.draw(cv, cx, cy + R * 0.15 + R * 0.5, align="center", alpha=on, glow="gold")
        f = S.font("mono_b", 34)
        sub = " ".join(self.sub)
        cv.drawString(sub, cx - f.measureText(sub) / 2, cy + R + 150, f, paint("ink", 0.8 * on))


class VideoClip:
    """Doc video that theo t (giay tu dau canh), cat khung W x H, phu mau toi xanh-vang."""

    def __init__(self, path, W, H, fps, start=0.0, grade=True):
        self.path, self.W, self.H, self.fps, self.start, self.grade = path, W, H, fps, start, grade
        self.proc = None; self.pos = -1; self.last = None

    def _open(self, t):
        if self.proc:
            self.proc.kill()
        vf = f"scale={self.W}:{self.H}:force_original_aspect_ratio=increase,crop={self.W}:{self.H},fps={self.fps}"
        if self.grade:
            vf += ",eq=brightness=-0.06:saturation=0.72:contrast=1.06,colorbalance=bs=0.06:gs=0.02:rh=0.04"
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{self.start + t:.3f}", "-stream_loop", "-1", "-i", self.path, "-vf", vf, "-pix_fmt", "bgra", "-f", "rawvideo", "-"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.pos = int(round(t * self.fps)) - 1

    def frame(self, t):
        k = int(round(t * self.fps))
        if self.proc is None or k < self.pos or k > self.pos + 45:
            self._open(t)
        n = self.W * self.H * 4
        while self.pos < k:
            buf = self.proc.stdout.read(n)
            if len(buf) < n:
                break
            self.last = buf; self.pos += 1
        if self.last is None:
            return None
        arr = np.frombuffer(self.last, np.uint8).reshape(self.H, self.W, 4)
        return skia.Image.fromarray(arr, colorType=skia.ColorType.kBGRA_8888_ColorType)

    def close(self):
        if self.proc:
            self.proc.kill(); self.proc = None


def finish(cv, W, H, dim=0.35, vignette=True):
    """Phu toi + vignette cho canh phu de chu doc ro."""
    if dim:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), dim))
    if vignette:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=rad(W / 2, H * 0.45, H * 0.72, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(210, 0, 0, 0)], [0.4, 1])))


# ------------------------------------------------------------------ minh hoa DCA (them 13/10/2026)
def dca_series(n, seed=21, mode="dca", start=2400.0):
    """Chuoi gia minh hoa cho canh DCA. dca: giam dan, bien dong tang, day, hoi len. pause: chay thang mot mach roi hoi."""
    rnd = np.random.default_rng(seed)
    o, h, l, c = [], [], [], []
    p = start
    for i in range(n):
        x = i / n
        if mode == "pause":
            if x < 0.22:
                d, sg = rnd.normal(0.3, 2.0), 1.6
            elif x < 0.55:
                d, sg = -6.5 - abs(rnd.normal(0, 1.6)), 1.0          # mot mach, khong hoi
            elif x < 0.63:
                d, sg = 4.2 + rnd.normal(0, 1.2), 2.2                 # song hoi
            elif x < 0.72:
                d, sg = -1.6 + rnd.normal(0, 1.4), 2.0
            else:
                d, sg = 3.4 + rnd.normal(0, 1.6), 2.2
        else:
            if x < 0.15:
                d, sg = rnd.normal(0.2, 2.0), 1.8
            elif x < 0.55:
                vol = 1.6 + 12 * ((x - 0.15) / 0.4) ** 1.5
                d, sg = -2.0 - vol * 0.25 + rnd.normal(0, vol * 0.5), vol * 0.75
            elif x < 0.68:
                d, sg = rnd.normal(0.4, 3.0), 2.4
            else:
                d, sg = 3.3 + rnd.normal(0, 1.8), 2.0
        op = p; cl = p + d
        hi = max(op, cl) + abs(rnd.normal(0, sg)); lo = min(op, cl) - abs(rnd.normal(0, sg))
        o.append(op); h.append(hi); l.append(lo); c.append(cl); p = cl
    return np.array(o), np.array(h), np.array(l), np.array(c)


class DcaChart(Chart):
    """mode "dca": luoi DCA am cach nhau theo ATR (gian khi bien dong manh), chot ca ro khi hoi.
    mode "pause": gia chay mot mach khong hoi -> vung do "DỪNG DCA", co song hoi -> "DCA LẠI KHI HỒI".
    Nen hien dan tu trai sang phai trong canh (khung nhin co dinh)."""

    def __init__(self, W, H, mode="dca", seed=21, symbol="XAUUSD", tf="M15", n=46, k_atr=2.4, labels=None):
        self.W, self.H, self.mode, self.symbol, self.tf, self.n = W, H, mode, symbol, tf, n
        self.o, self.h, self.l, self.c = dca_series(n, seed, mode)
        self.e = ema(self.c, 10)
        tr = self.h - self.l
        self.atr = np.array([tr[max(0, i - 5):i + 1].mean() for i in range(n)])
        self.lab = {"pause": "KHÔNG HỒI · DỪNG DCA", "resume": "DCA LẠI KHI HỒI", "tp": "CHỐT CẢ RỔ", "gap": "ATR"}
        self.lab.update(labels or {})
        self.orders, self.close_i, self.tp = [], None, None
        if mode == "dca":
            i0 = int(n * 0.15); lvl = self.c[i0]; self.orders = [(i0, lvl)]; nxt = lvl - k_atr * self.atr[i0]
            for i in range(i0 + 1, n):
                if len(self.orders) < 5 and self.l[i] <= nxt:
                    self.orders.append((i, nxt)); nxt = nxt - k_atr * self.atr[i]
                avg = np.mean([v for _, v in self.orders]); tp = avg + 0.5 * self.atr[self.orders[-1][0]]
                if i > self.orders[-1][0] + 2 and self.h[i] >= tp and len(self.orders) > 2:
                    self.close_i, self.tp = i, tp; break
        else:
            self.run = (int(n * 0.22), int(n * 0.55))
            i1 = self.run[0] - 1
            self.orders = [(i1, self.c[i1])]
            self.resume_i = int(n * 0.57)
            self.orders.append((self.resume_i, self.l[self.resume_i] + (self.c[self.resume_i] - self.l[self.resume_i]) * 0.3))

    def draw(self, cv, t, dur, x0=0, y0=0, w=None, h=None, show_axis=True, alpha=1.0, reveal=1.0):
        W = w or self.W; H = h or self.H
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(x0, y0, W, H)); cv.translate(x0, y0)
        cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=lin(0, 0, 0, H, [(5, 14, 20), (10, 28, 36), (4, 9, 12)], [0, 0.55, 1]), a=alpha))
        gp = paint((40, 80, 92), 0.28 * alpha, stroke=1.2)
        for i in range(1, 12):
            cv.drawLine(0, H * i / 12, W, H * i / 12, gp)
        for i in range(1, 7):
            cv.drawLine(W * i / 7, 0, W * i / 7, H, gp)
        n = self.n
        prog = S.ease_in_out(S.clamp(t / max(dur * 0.82, 0.1)))
        end = max(4, min(n, int(n * (0.12 + 0.88 * prog)) + 1))
        lo = self.l.min(); hi = self.h.max(); pad = (hi - lo) * 0.08; lo -= pad; hi += pad
        if H > 1000:
            top, bot = (H * 0.34, H * 0.68) if self.mode == "pause" else (H * 0.26, H * 0.71)
        else:
            top, bot = H * 0.18, H * 0.86
        Y = lambda v: bot - (v - lo) / (hi - lo) * (bot - top)
        cw = (W * 0.80) / n
        X = lambda i: W * 0.04 + i * cw + cw / 2
        xr = W * 0.86                                                  # mep phai vung nen
        # vung "mot mach" (pause)
        if self.mode == "pause" and end > self.run[0] + 3:
            a_ = S.ease_out((end - self.run[0] - 3) / 4)
            ra, rb = self.run[0], min(end - 1, self.run[1])
            r = skia.Rect.MakeLTRB(X(ra) - cw / 2, top - 10, X(rb) + cw / 2, bot + 10)
            cv.drawRect(r, paint(BEAR, 0.13 * a_ * alpha))
            cv.drawRect(r, paint(BEAR, 0.55 * a_ * alpha, stroke=2))
            self._pill(cv, self.lab["pause"], (r.left() + r.right()) / 2, top - 46, BEAR, (255, 255, 255), a_ * alpha, icon="pause")
        # nen
        for i in range(end):
            o, hh, ll, c = self.o[i], self.h[i], self.l[i], self.c[i]
            colr = BULL if c >= o else BEAR
            x = X(i)
            cv.drawLine(x, Y(hh), x, Y(ll), paint(colr, 0.9 * alpha, stroke=max(1.5, cw * 0.09)))
            yt, yb = Y(max(o, c)), Y(min(o, c))
            cv.drawRect(skia.Rect.MakeLTRB(x - cw * 0.33, yt, x + cw * 0.33, max(yb, yt + 2)), paint(colr, 0.95 * alpha))
        ep = skia.Path()
        for i in range(end):
            (ep.moveTo if i == 0 else ep.lineTo)(X(i), Y(self.e[i]))
        cv.drawPath(ep, paint("gold_hi", 0.55 * alpha, stroke=3))
        # lenh DCA
        f = S.font("sans_b", 28)
        shown = [(k, i, v) for k, (i, v) in enumerate(self.orders) if i < end]
        closed = self.close_i is not None and end > self.close_i
        x_end = X(self.close_i) if closed else xr
        for k, i, v in shown:
            a_ = S.ease_out((end - i) / 2.5) * alpha * (0.55 if closed else 1.0)
            y = Y(v)
            dp = paint(BULL, 0.85 * a_, stroke=2.5); dp.setPathEffect(skia.DashPathEffect.Make([12, 8], 0))
            cv.drawLine(X(i), y, x_end, y, dp)
            tri = skia.Path(); yy = Y(self.l[i]) + 30
            tri.moveTo(X(i), yy - 22); tri.lineTo(X(i) - 17, yy + 10); tri.lineTo(X(i) + 17, yy + 10); tri.close()
            cv.drawPath(tri, paint(BULL, a_))
            if self.mode == "pause" and k == 1:
                fw = S.font("sans_xb", 30).measureText(self.lab["resume"]) + 40
                self._pill(cv, self.lab["resume"], X(i) + 34 + fw / 2, yy + 4, BULL, (6, 26, 16), a_)
            else:
                lab = f"L{k + 1}"
                cv.drawRRect(rrect(xr + 8, y - 21, 70, 42, 9), paint(BULL, 0.95 * a_))
                cv.drawString(lab, xr + 43 - f.measureText(lab) / 2, y + 10, f, paint((6, 26, 16), a_))
        # khoang cach theo ATR (ngoac giua 2 lenh lien tiep)
        if self.mode == "dca":
            fg = S.font("mono_b", 22)
            for (k1, i1, v1), (k2, i2, v2) in zip(shown[:-1], shown[1:]):
                a_ = S.ease_out((end - i2) / 3) * alpha * (0.4 if closed else 1.0)
                xb = xr - 26; y1, y2 = Y(v1), Y(v2)
                bp = paint("gold_hi", 0.9 * a_, stroke=2.5)
                cv.drawLine(xb, y1 + 4, xb, y2 - 4, bp); cv.drawLine(xb - 9, y1 + 4, xb + 9, y1 + 4, bp); cv.drawLine(xb - 9, y2 - 4, xb + 9, y2 - 4, bp)
                g = self.lab["gap"]; tw = fg.measureText(g)
                cv.drawRRect(rrect(xb - tw - 26, (y1 + y2) / 2 - 17, tw + 16, 34, 7), paint((8, 10, 12), 0.85 * a_))
                cv.drawString(g, xb - tw - 18, (y1 + y2) / 2 + 8, fg, paint("gold_hi", a_))
            if closed:
                a_ = S.ease_out((end - self.close_i) / 2) * alpha
                y = Y(self.tp)
                tp = paint("gold_hi", a_, stroke=3); tp.setPathEffect(skia.DashPathEffect.Make([16, 9], 0))
                cv.drawLine(X(self.orders[0][0]), y, xr, y, tp)
                self._pill(cv, self.lab["tp"], X(self.close_i), y - 46, S.C["gold_hi"], (24, 18, 6), a_)
        if show_axis:
            f2 = S.font("mono_b", max(18, W * 0.03))
            cv.drawString(f"{self.symbol} · {self.tf}", W * 0.05, H * 0.715, f2, paint("ink", 0.45 * alpha))
        cv.restore()

    def _pill(self, cv, text, cx, cy, bg, fg, a, icon=None):
        f = S.font("sans_xb", 30)
        tw = f.measureText(text); iw = 30 if icon else 0
        w = tw + 40 + iw
        x = max(16, min(self.W - w - 16, cx - w / 2))
        cv.drawRRect(rrect(x, cy - 26, w, 52, 26), paint(bg, 0.95 * a))
        if icon == "pause":
            cv.drawRect(skia.Rect.MakeXYWH(x + 20, cy - 12, 7, 24), paint(fg, a)); cv.drawRect(skia.Rect.MakeXYWH(x + 32, cy - 12, 7, 24), paint(fg, a))
        cv.drawString(text, x + 20 + iw, cy + 11, f, paint(fg, a))
