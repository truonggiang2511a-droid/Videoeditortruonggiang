#!/usr/bin/env python3
"""Nhac nen + tieng dong + tron am cho video EA.

"music": {"style": "dark_pad" | "pulse" | "none", "volume": 0.16}   nhac tong hop (khong ban quyen)
"music": {"file": "nhac.mp3", "volume": 0.18, "start": 0}          nhac that cua Giang
Nhac tu ha xuong khi co giong (ducking). Tieng dong: whoosh khi doi canh, tick khi hien gach dau dong,
boom khi hien tieu de lon, riser truoc CTA. Ban xuat cuoi chuan -14 LUFS (Reels/TikTok).
"""
import math, subprocess
import numpy as np
import ea_voice as V

SR = V.SR
NOTE = {"A2": 110.0, "F2": 87.31, "C3": 130.81, "G2": 98.0, "D3": 146.83, "E2": 82.41, "A3": 220.0, "C4": 261.63, "E4": 329.63,
        "F3": 174.61, "G3": 196.0, "B3": 246.94, "D4": 293.66, "A4": 440.0, "F4": 349.23, "G4": 392.0, "E3": 164.81}
PROG = [("A2", ["A3", "C4", "E4"]), ("F2", ["F3", "A3", "C4"]), ("C3", ["G3", "C4", "E4"]), ("G2", ["G3", "B3", "D4"])]


def onepole(x, a):
    """Loc thong thap mot cuc (a nho = toi hon)."""
    y = np.empty_like(x); acc = 0.0
    # vectorized via lfilter-free recurrence in chunks
    for i in range(len(x)):
        acc += a * (x[i] - acc); y[i] = acc
    return y


def lp_fft(x, cutoff, sr=SR):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / sr)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x)).astype(np.float32)


def music(dur, style="dark_pad", bpm=84, seed=1):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    if style == "none":
        return out
    bar = 4 * 60 / bpm; chord_len = 2 * bar
    rng = np.random.default_rng(seed)
    for k in range(int(dur / chord_len) + 1):
        root, ch = PROG[k % len(PROG)]
        a = int(k * chord_len * SR); b = min(n, int((k + 1) * chord_len * SR) + int(0.6 * SR))
        if a >= n:
            break
        tt = np.arange(b - a) / SR
        envl = np.minimum(1, tt / 0.9) * np.minimum(1, np.maximum(0, (chord_len + 0.6 - tt) / 0.9))
        pad = np.zeros(b - a)
        for nm in ch:
            f = NOTE[nm]
            for det in (-0.12, 0.0, 0.11):
                ph = rng.uniform(0, 2 * np.pi)
                fr = f * (2 ** (det / 12))
                pad += (2 * ((tt * fr + ph / 6.283) % 1) - 1) * 0.06      # saw
        pad = lp_fft(pad.astype(np.float32), 900 + 300 * math.sin(k))
        sub = np.sin(2 * np.pi * NOTE[root] * tt) * 0.22
        out[a:b] += ((pad + sub) * envl).astype(np.float32)
    if style == "pulse":
        beat = 60 / bpm
        for i in range(int(dur / beat * 2)):
            s0 = int(i * beat / 2 * SR)
            if s0 >= n:
                break
            L = min(int(0.05 * SR), n - s0)
            hat = rng.normal(0, 1, L) * np.exp(-np.arange(L) / (0.008 * SR)) * (0.05 if i % 2 else 0.03)
            out[s0:s0 + L] += lp_fft(hat.astype(np.float32), 9000) - lp_fft(hat.astype(np.float32), 5000)
            if i % 4 == 0:
                L2 = min(int(0.35 * SR), n - s0); tk = np.arange(L2) / SR
                out[s0:s0 + L2] += (np.sin(2 * np.pi * (48 + 60 * np.exp(-tk * 30)) * tk) * np.exp(-tk * 9) * 0.35).astype(np.float32)
    fade = np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 1.8)
    out *= fade.astype(np.float32)
    return out / (np.max(np.abs(out)) + 1e-9) * 0.7


# ------------------------------------------------------------------ tieng dong
def sfx(kind):
    rng = np.random.default_rng(len(kind))
    if kind == "whoosh":
        L = int(0.42 * SR); tt = np.arange(L) / SR
        nz = rng.normal(0, 1, L).astype(np.float32)
        lo = lp_fft(nz, 2600); lo2 = lp_fft(nz, 500)
        bp = lo - lo2
        envl = np.sin(np.pi * np.minimum(1, tt / 0.42)) ** 2
        return (bp * envl * 0.5).astype(np.float32)
    if kind == "tick":
        L = int(0.06 * SR); tt = np.arange(L) / SR
        return (np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 70) * 0.35).astype(np.float32)
    if kind == "boom":
        L = int(1.1 * SR); tt = np.arange(L) / SR
        b = np.sin(2 * np.pi * (38 + 40 * np.exp(-tt * 8)) * tt) * np.exp(-tt * 3.2)
        nz = lp_fft(rng.normal(0, 1, L).astype(np.float32), 1200) * np.exp(-tt * 18) * 0.4
        return ((b + nz) * 0.7).astype(np.float32)
    if kind == "riser":
        L = int(1.3 * SR); tt = np.arange(L) / SR
        f = 220 + 900 * (tt / 1.3) ** 2
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.12
        nz = (lp_fft(rng.normal(0, 1, L).astype(np.float32), 6000) - lp_fft(rng.normal(0, 1, L).astype(np.float32), 1500)) * 0.25
        return ((tone + nz) * (tt / 1.3) ** 1.6).astype(np.float32)
    if kind == "shine":
        L = int(1.2 * SR); tt = np.arange(L) / SR
        s = sum(np.sin(2 * np.pi * f * tt) for f in (1318.5, 1760, 2637)) * np.exp(-tt * 4) * 0.08
        return s.astype(np.float32)
    return np.zeros(1, np.float32)


def mix(voice_wav, events, dur, music_cfg, out_wav, log=print):
    """events: [(giay, kind, vol)]. Tra ve duong dan wav stereo da tron (chua chuan loudness)."""
    v = V.load_audio(voice_wav)
    n = int(dur * SR)
    v = np.pad(v, (0, max(0, n - len(v))))[:n]
    mcfg = music_cfg or {}
    vol = float(mcfg.get("volume", 0.16))
    if mcfg.get("file"):
        m = V.load_audio(mcfg["file"])
        st = int(float(mcfg.get("start", 0)) * SR)
        m = m[st:]
        if len(m) < n:
            m = np.tile(m, int(n / max(1, len(m))) + 1)
        m = m[:n]
        fade = np.minimum(1, np.arange(n) / (1.0 * SR)) * np.minimum(1, (n - np.arange(n)) / (1.8 * SR))
        m = m * fade / (np.max(np.abs(m)) + 1e-9) * 0.7
    else:
        m = music(dur, mcfg.get("style", "dark_pad"))
    # ducking theo giong
    hop = int(0.02 * SR)
    e = np.sqrt(np.convolve(v ** 2, np.ones(hop * 3) / (hop * 3), mode="same"))
    envd = np.clip(e / (np.percentile(e[e > 1e-4], 80) + 1e-9 if (e > 1e-4).any() else 1), 0, 1)
    sm = np.zeros_like(envd); acc = 0.0
    step = 64
    for i in range(0, n, step):
        tgt = envd[i]
        acc = acc + (tgt - acc) * (0.5 if tgt > acc else 0.02)
        sm[i:i + step] = acc
    g = vol * (1 - 0.6 * sm)
    fx = np.zeros(n, np.float32)
    for t, kind, vv in events:
        s = sfx(kind); a = int(t * SR)
        if kind == "riser":
            a -= len(s)
        if a < 0:
            s = s[-a:]; a = 0
        b = min(n, a + len(s))
        if b > a:
            fx[a:b] += s[:b - a] * vv
    mono = v * 1.0 + m * g + fx
    left = mono + m * g * 0.08; right = mono - m * g * 0.08
    st = np.stack([left, right], 1)
    st = st / max(1.0, np.max(np.abs(st)) / 0.95)
    import wave
    y = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
    return out_wav
