#!/usr/bin/env python3
"""Nhan vat avatar "AURUS" - robot dan chuong trinh cho video EA Bot vang.

Ve hoan toan bang vector (skia): vo den graphite vien vang, kinh mat toi, mat LED vang biet chop / nhin / cuoi,
mieng LED 7 vach nhay theo giong noi, an-ten phat sang, ao vest co ve vang, huy hieu nguc.

  python3 ea_avatar.py --still out.png [--mood smile] [--level 0.6]     # anh tinh de xem
  python3 ea_avatar.py --sheet out.jpg                                   # bang 6 trang thai

Trong bo dung: Bot(cfg).draw(canvas, t, level, bands, look=(dx,dy), mood="neutral")
cfg (avatar trong brand.json): {"name": "AURUS", "eye": "#F6D678", "accent": "#D4AF37", "badge": "A", "chest": "24/7"}
"""
import math, random, argparse
import numpy as np
import skia
import ea_style as S
from ea_style import paint, lin, rad, rrect, col


def rgba_(rgb, a):
    return skia.ColorSetARGB(int(255 * max(0, min(1, a))), *[int(v) for v in rgb])


class Bot:
    def __init__(self, cfg=None, seed=7):
        cfg = cfg or {}
        self.name = cfg.get("name", "AURUS")
        self.eye = S.hex_rgb(cfg["eye"]) if cfg.get("eye") else S.C["gold_hi"]
        self.accent = S.hex_rgb(cfg["accent"]) if cfg.get("accent") else S.C["gold"]
        self.badge = cfg.get("badge", "A")
        self.chest = cfg.get("chest", "24/7")
        rnd = random.Random(seed)
        # lich chop mat: moi 2.4-5.2s mot lan, doi khi chop doi
        self.blinks, t = [], 1.2
        while t < 600:
            self.blinks.append(t)
            if rnd.random() < 0.18:
                self.blinks.append(t + 0.32)
            t += rnd.uniform(2.4, 5.2)

    # ------------------------------------------------------------------ trang thai
    def blink_amt(self, t):
        best = 0.0
        for b in self.blinks:
            d = t - b
            if -0.01 < d < 0.16:
                best = max(best, 1 - abs(d - 0.07) / 0.09)
            if b > t + 1:
                break
        return S.clamp(best)

    # ------------------------------------------------------------------ ve
    def draw(self, cv, cx, cy, s, t, level=0.0, bands=None, look=(0.0, 0.0), mood="neutral", tilt=None, body=True, talk=None, detail=1.0):
        """cx, cy = tam dau; s = ti le (1.0 ~ dau rong 500px). level 0..1 do lon giong; bands 7 dai tan (da lam muot);
        talk 0..1 = dang noi (da lam muot, quyet dinh mieng vach hay mieng cuoi)."""
        self.bands = np.zeros(7) if bands is None else np.clip(np.asarray(bands, float), 0, 1)
        self.talk = S.clamp(level * 6) if talk is None else talk
        breathe = math.sin(t * 2 * math.pi / 3.6)
        bob = math.sin(t * 2 * math.pi / 1.9) * 4 * level + breathe * 3
        if tilt is None:
            tilt = math.sin(t * 0.7) * 1.6 + math.sin(t * 2.3) * 1.2 * level
        if body:
            self._body(cv, cx, cy + 300 * s, s, t, breathe, detail)
        cv.save()
        cv.translate(cx, cy + bob * s)
        # quang sang am sau dau
        cv.drawCircle(0, 0, 330 * s, paint(shader=rad(0, 0, 330 * s, [skia.ColorSetARGB(60, 255, 196, 120), skia.ColorSetARGB(0, 255, 180, 100)])))
        cv.rotate(tilt)
        cv.scale(s, s)
        self._head(cv, t, level, look, mood)
        cv.restore()

    def _body(self, cv, cx, ny, s, t, breathe, detail=1.0):
        """ny = co (tren vai)."""
        cv.save(); cv.translate(cx, ny); cv.scale(s * (1 + 0.004 * breathe), s)
        # co
        cv.drawRRect(rrect(-78, -40, 156, 120, 30), paint(shader=lin(0, -40, 0, 80, [(40, 43, 49), (14, 15, 18)])))
        for i in range(3):
            cv.drawRRect(rrect(-82, -14 + i * 26, 164, 8, 4), paint((60, 63, 70), 0.9))
        # vai + than (ao vest)
        p = skia.Path()
        p.moveTo(-520, 900); p.lineTo(-500, 250)
        p.cubicTo(-490, 120, -400, 60, -250, 50)
        p.lineTo(250, 50)
        p.cubicTo(400, 60, 490, 120, 500, 250)
        p.lineTo(520, 900); p.close()
        cv.drawPath(p, paint(shader=lin(0, 40, 0, 900, [(36, 38, 44), (18, 19, 23), (10, 11, 13)], [0, 0.45, 1])))
        # anh sang vien vai
        rim = skia.Path(); rim.moveTo(-500, 250); rim.cubicTo(-490, 120, -400, 60, -250, 50); rim.lineTo(250, 50); rim.cubicTo(400, 60, 490, 120, 500, 250)
        cv.drawPath(rim, paint(self.accent, 0.55, stroke=5))
        cv.drawPath(rim, paint(self.accent, 0.25, stroke=14, blur=10))
        # ao trong (ngực)
        sh = skia.Path(); sh.moveTo(-150, 52); sh.lineTo(150, 52); sh.lineTo(70, 520); sh.lineTo(-70, 520); sh.close()
        cv.drawPath(sh, paint(shader=lin(0, 50, 0, 520, [(46, 49, 56), (22, 24, 28)])))
        # ve ao (lapel) vang
        for sg in (-1, 1):
            lp = skia.Path(); lp.moveTo(sg * 150, 52); lp.lineTo(sg * 250, 52); lp.lineTo(sg * 130, 420); lp.lineTo(sg * 70, 520); lp.close()
            cv.drawPath(lp, paint(shader=lin(sg * 250, 52, sg * 70, 520, [(28, 30, 35), (16, 17, 20)])))
            ed = skia.Path(); ed.moveTo(sg * 150, 52); ed.lineTo(sg * 70, 520)
            cv.drawPath(ed, paint(self.accent, 0.85 * (0.35 + 0.65 * detail), stroke=4))
            ed2 = skia.Path(); ed2.moveTo(sg * 250, 52); ed2.lineTo(sg * 130, 420)
            cv.drawPath(ed2, paint(self.accent, 0.35 * detail, stroke=2.5))
        if detail < 0.05:
            cv.restore(); return
        cv.saveLayerAlpha(None, int(255 * detail))
        # nut ao
        for y in (300, 400):
            cv.drawCircle(0, y, 9, paint(shader=rad(-3, y - 3, 10, [S.C["gold_hi"], S.C["gold_lo"]])))
        # huy hieu nguc trai (luc giac vang)
        hx, hy = -300, 250
        hexp = skia.Path()
        for i in range(6):
            a = math.pi / 6 + i * math.pi / 3
            (hexp.moveTo if i == 0 else hexp.lineTo)(hx + 46 * math.cos(a), hy + 46 * math.sin(a))
        hexp.close()
        cv.drawPath(hexp, paint(shader=lin(hx - 40, hy - 40, hx + 40, hy + 40, [S.C["gold_hi"], S.C["gold_lo"]])))
        cv.drawPath(hexp, paint((255, 240, 200), 0.6, stroke=2))
        f = S.font("serif_b", 50)
        w = f.measureText(self.badge)
        cv.drawString(self.badge, hx - w / 2, hy + 17, f, paint((26, 20, 8)))
        # den trang thai "24/7" nguc phai
        px, py = 250, 230
        cv.drawRRect(rrect(px - 70, py - 30, 140, 60, 30), paint((8, 9, 11), 0.95))
        cv.drawRRect(rrect(px - 70, py - 30, 140, 60, 30), paint(self.accent, 0.6, stroke=2))
        pulse = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(t * 2 * math.pi / 1.6))
        cv.drawCircle(px - 40, py, 11, paint(S.C["green"], 0.5 * pulse, blur=8))
        cv.drawCircle(px - 40, py, 7, paint(S.C["green"], pulse))
        f2 = S.font("mono_b", 30)
        cv.drawString(self.chest, px - 22, py + 11, f2, paint(S.C["ink"], 0.95))
        cv.restore()
        cv.restore()

    def _head(self, cv, t, level, look, mood):
        W, H, R = 500, 430, 175
        # bong do duoi dau
        cv.drawRRect(rrect(-W / 2 + 10, -H / 2 + 40, W - 20, H, R), paint((0, 0, 0), 0.55, blur=30))
        # an-ten
        cv.drawRRect(rrect(-6, -H / 2 - 74, 12, 80, 6), paint(shader=lin(0, -H / 2 - 74, 0, -H / 2, [(70, 72, 80), (30, 32, 36)])))
        ap = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(t * 2 * math.pi / 1.3))
        cv.drawCircle(0, -H / 2 - 82, 34, paint(self.eye, 0.35 * ap, blur=18))
        cv.drawCircle(0, -H / 2 - 82, 17, paint(shader=rad(-5, -H / 2 - 88, 20, [(255, 248, 220), self.eye, self.accent], [0, 0.45, 1])))
        # tai (2 ben)
        for sg in (-1, 1):
            ex = sg * (W / 2 + 6)
            cv.drawRRect(rrect(ex - 34, -70, 68, 140, 30), paint(shader=lin(ex, -70, ex, 70, [(48, 50, 57), (18, 19, 22)])))
            cv.drawRRect(rrect(ex - 34, -70, 68, 140, 30), paint(self.accent, 0.8, stroke=3))
            cv.drawRRect(rrect(ex - 8, -40, 16, 80, 8), paint(self.eye, 0.25 + 0.5 * level, blur=4))
        # vo dau
        shell = rrect(-W / 2, -H / 2, W, H, R)
        cv.drawRRect(shell, paint(shader=lin(0, -H / 2, 0, H / 2, [(58, 61, 69), (28, 30, 35), (14, 15, 18)], [0, 0.5, 1])))
        cv.drawRRect(shell, paint(shader=rad(-W * 0.22, -H * 0.32, W * 0.55, [skia.ColorSetARGB(70, 255, 255, 255), skia.ColorSetARGB(0, 255, 255, 255)])))
        # vien vang (sang tren, toi duoi)
        rp = paint(stroke=6)
        rp.setShader(lin(0, -H / 2, 0, H / 2, [S.C["gold_hi"], S.C["gold"], S.C["gold_lo"]], [0, 0.5, 1]))
        cv.drawRRect(rrect(-W / 2 + 3, -H / 2 + 3, W - 6, H - 6, R - 3), rp)
        # kinh mat
        VW, VH, VR = 420, 270, 125
        vy = -H / 2 + 62
        visor = rrect(-VW / 2, vy, VW, VH, VR)
        cv.drawRRect(visor, paint(shader=lin(0, vy, 0, vy + VH, [(14, 18, 24), (4, 5, 7)])))
        cv.drawRRect(visor, paint((90, 96, 108), 0.55, stroke=3))
        # mat
        cv.save(); cv.clipRRect(visor, skia.ClipOp.kIntersect, True)
        gx, gy = look[0] * 22, look[1] * 14
        bl = self.blink_amt(t)
        ey = vy + 112 + gy
        for sg in (-1, 1):
            self._eye(cv, sg * 92 + gx, ey, bl, mood, sg)
        # anh sang mat hat len kinh
        cv.drawCircle(gx, ey, 190, paint(shader=rad(gx, ey, 190, [rgba_(self.eye, 0.10), rgba_(self.eye, 0.0)])))
        # mieng: vach LED khi noi, duong cuoi khi im
        my = vy + 212
        n = 7; bw, gap = 15, 11
        x0 = -(n * bw + (n - 1) * gap) / 2 + gx * 0.5
        shape = np.array([0.55, 0.8, 0.95, 1.0, 0.95, 0.8, 0.55])
        talk = self.talk
        if talk > 0.02:
            for i in range(n):
                h = 10 + 58 * self.bands[i] * shape[i]
                x = x0 + i * (bw + gap)
                r = rrect(x, my - h / 2, bw, h, bw / 2)
                cv.drawRRect(r, paint(self.eye, 0.35 * talk, blur=7))
                cv.drawRRect(r, paint(shader=lin(0, my - h / 2, 0, my + h / 2, [(255, 244, 205), self.eye, self.accent], [0, 0.5, 1]), a=talk))
        if talk < 0.98:
            depth = {"smile": 30, "focus": 4}.get(mood, 14)
            hw = (n * bw + (n - 1) * gap) / 2 * (0.9 if mood == "smile" else 0.72)
            cp = skia.Path(); cp.moveTo(-hw + gx * 0.5, my - depth * 0.35); cp.quadTo(gx * 0.5, my + depth, hw + gx * 0.5, my - depth * 0.35)
            cv.drawPath(cp, paint(self.eye, 0.45 * (1 - talk), stroke=16, blur=8))
            cv.drawPath(cp, paint(self.eye, 1 - talk, stroke=9))
        # vet phan chieu kinh
        refl = skia.Path(); refl.moveTo(-VW / 2 + 40, vy + 20); refl.lineTo(-VW / 2 + 150, vy + 20); refl.lineTo(-VW / 2 + 60, vy + VH - 30); refl.lineTo(-VW / 2 + 10, vy + VH - 30); refl.close()
        cv.drawPath(refl, paint((255, 255, 255), 0.045))
        cv.restore()
        # vach trang tri tran + ten
        f = S.font("mono_b", 20)
        nm = " ".join(self.name.upper())
        w = f.measureText(nm)
        cv.drawString(nm, -w / 2, -H / 2 + 44, f, paint(self.accent, 0.75))
        # khe tan nhiet duoi cam
        for i in range(5):
            cv.drawRRect(rrect(-60 + i * 26, H / 2 - 52, 14, 30, 7), paint((6, 7, 9), 0.9))

    def _eye(self, cv, x, y, blink, mood, sg):
        ew, eh = 74, 96
        h = eh * (1 - 0.9 * blink)
        g = paint(self.eye, 0.55, blur=16)
        sh = lin(0, y - h / 2, 0, y + h / 2, [(255, 247, 215), self.eye, self.accent], [0, 0.55, 1])
        if mood == "smile" and blink < 0.5:
            # mat cuoi: hinh vong cung ^
            p = skia.Path()
            p.moveTo(x - ew / 2, y + 16); p.cubicTo(x - ew / 2, y - 46, x + ew / 2, y - 46, x + ew / 2, y + 16)
            p.lineTo(x + ew / 2 - 20, y + 16); p.cubicTo(x + ew / 2 - 22, y - 20, x - ew / 2 + 22, y - 20, x - ew / 2 + 20, y + 16); p.close()
            cv.drawPath(p, g); cv.drawPath(p, paint(shader=sh))
            return
        if mood == "focus" and blink < 0.5:
            # mi tren phang, ha xuong -> nhin nghiem tuc, tap trung
            cut = 18
            cut2 = 18
            p = skia.Path()
            p.moveTo(x - ew / 2, y - h / 2 + cut + 6); p.lineTo(x + ew / 2, y - h / 2 + cut2 + 6)
            p.lineTo(x + ew / 2, y + h / 2 - ew / 2); p.arcTo(skia.Rect.MakeXYWH(x - ew / 2, y + h / 2 - ew, ew, ew), 0, 180, False)
            p.close()
            cv.drawPath(p, g); cv.drawPath(p, paint(shader=sh))
        else:
            r = rrect(x - ew / 2, y - h / 2, ew, h, min(ew, h) / 2)
            cv.drawRRect(r, g)
            cv.drawRRect(r, paint(shader=sh))
        # diem sang
        if blink < 0.6:
            cv.drawCircle(x - ew * 0.18, y - h * 0.22, 9, paint((255, 255, 255), 0.75))


# ------------------------------------------------------------------ phong nen studio
def studio(W, H, seed=3, accent=None):
    """Phong nen: vach go doc toi, den am sau dau, dai LED xanh bên trai, bokeh, vignette. Tra ve skia.Image."""
    rnd = random.Random(seed)
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    cv.clear(col((14, 11, 9)))
    sw = W / 15
    for i in range(16):
        x = i * sw
        tone = rnd.uniform(0.85, 1.1)
        cv.drawRect(skia.Rect.MakeXYWH(x, 0, sw * 0.82, H), paint(shader=lin(0, 0, 0, H, [tuple(int(v * tone) for v in (40, 29, 21)), tuple(int(v * tone) for v in (26, 19, 14)), (12, 9, 8)], [0, 0.5, 1])))
        cv.drawRect(skia.Rect.MakeXYWH(x + sw * 0.82, 0, sw * 0.18, H), paint((6, 5, 4), 0.95))
        cv.drawRect(skia.Rect.MakeXYWH(x, 0, 3, H), paint((150, 110, 70), 0.12))
    # den am sau dau
    cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=rad(W * 0.5, H * 0.3, W * 0.75, [skia.ColorSetARGB(95, 255, 186, 110), skia.ColorSetARGB(0, 255, 170, 90)])))
    # dai LED xanh ben trai + bokeh
    cv.drawRRect(rrect(-30, H * 0.11, W * 0.09, 44, 22), paint(S.C["teal"], 0.9))
    cv.drawRRect(rrect(-30, H * 0.11 - 20, W * 0.12, 84, 42), paint(S.C["teal"], 0.35, blur=26))
    for _ in range(14):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H * 0.55), rnd.uniform(14, 46)
        c = rnd.choice([(255, 210, 140), (255, 190, 110), (120, 220, 230)])
        cv.drawCircle(x, y, r, paint(c, rnd.uniform(0.05, 0.14), blur=r * 0.35))
    # vignette + toi dan xuong duoi
    cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=rad(W * 0.5, H * 0.42, H * 0.75, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(235, 0, 0, 0)], [0.35, 1])))
    cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=lin(0, H * 0.55, 0, H, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(170, 0, 0, 0)])))
    return surf.makeImageSnapshot()


def _demo(out, mood="neutral", level=0.0, t=0.5, W=1080, H=1920):
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    cv.drawImage(studio(W, H), 0, 0)
    b = Bot()
    bands = np.clip(np.array([0.5, 0.8, 1.0, 0.9, 0.7, 0.6, 0.4]) * level * 1.4, 0, 1)
    b.draw(cv, W / 2, H * 0.33, 1.0, t, level, bands, mood=mood)
    surf.makeImageSnapshot().save(out, skia.kPNG) if out.endswith(".png") else surf.makeImageSnapshot().save(out, skia.kJPEG, 90)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--still"); ap.add_argument("--sheet")
    ap.add_argument("--mood", default="neutral"); ap.add_argument("--level", type=float, default=0.0)
    a = ap.parse_args()
    if a.still:
        _demo(a.still, a.mood, a.level)
    if a.sheet:
        W, H = 1080, 1920
        sheet = skia.Surface(W * 3 // 2, H)
        sc = sheet.getCanvas(); sc.clear(col((0, 0, 0)))
        bg = studio(W, H); b = Bot()
        states = [("neutral", 0, 0.5), ("neutral", 0.7, 0.6), ("smile", 0, 0.7), ("focus", 0.5, 0.8), ("neutral", 0, 1.27), ("smile", 0.9, 0.9)]
        for k, (m, lv, t) in enumerate(states):
            s = skia.Surface(W, H); cv = s.getCanvas(); cv.drawImage(bg, 0, 0)
            bands = np.clip(np.array([0.5, 0.8, 1.0, 0.9, 0.7, 0.6, 0.4]) * lv * 1.4, 0, 1)
            b.draw(cv, W / 2, H * 0.33, 1.0, t, lv, bands, mood=m, look=((-0.6, 0) if k == 3 else (0, 0)))
            img = s.makeImageSnapshot()
            sc.save(); sc.translate((k % 3) * W / 2, (k // 3) * H / 2); sc.scale(0.5, 0.5); sc.drawImage(img, 0, 0); sc.restore()
        sheet.makeImageSnapshot().save(a.sheet, skia.kJPEG, 88)
        print(a.sheet)
