#!/usr/bin/env python3
"""Giong doc + moc thoi gian cho video EA.

Ba nguon giong (khoa "voice" cua kich ban):
  {"engine": "offline", "speed": 1.0}            giong tieng Viet chay tai cho (piper vais1000 qua sherpa-onnx; lan dau tai ~65MB tu GitHub)
  {"engine": "files"}                            moi canh mot file: scene["voice_file"] (Giang tu thu tung cau, hoac mp3 tu vidIQ/ElevenLabs)
  {"engine": "file", "file": "giong.mp3"}        mot file cho ca kich ban -> may nghe zipformer chia canh + moc tung tu (lan dau tai ~256MB)

Ket qua: work/voice.wav (mono 44.1k) + work/timing.json:
  {"scenes": [{"i":0,"t0":..,"t1":..,"words":[{"w":"Bạn","t0":..,"t1":..}, ...]}], "total": ..}
  python3 ea_voice.py kich_ban.json --work work            # chay rieng de nghe thu / xem moc
"""
import json, os, re, subprocess, sys, tarfile, difflib, unicodedata
import numpy as np

KIT = os.path.dirname(os.path.abspath(__file__))
SR = 44100
TTS_MODEL = "vits-piper-vi_VN-vais1000-medium"
TTS_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/" + TTS_MODEL + ".tar.bz2"
ASR_MODEL = "sherpa-onnx-zipformer-vi-2025-04-20"
ASR_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/" + ASR_MODEL + ".tar.bz2"
MODELS = os.environ.get("EA_MODELS", os.path.join(KIT, "models"))

# doc cho may: chu tren phu de -> cach doc. Them cua rieng trong brand_ea.json "doc".
DOC = {
    "24/7": "hai bốn trên bảy", "EA": "i a", "Robot": "rô bốt", "robot": "rô bốt", "bot": "bót", "Bot": "bót",
    "MT5": "em tê năm", "MT4": "em tê bốn", "XAUUSD": "vàng", "SL": "ét lờ", "TP": "tê pê", "VPS": "vê pê ét",
    "H4": "hát bốn", "H1": "hát một", "M15": "em mười lăm", "M5": "em năm", "D1": "đê một", "Zalo": "da lô", "zalo": "da lô",
    "Backtest": "bách tét", "backtest": "bách tét", "demo": "đê mô", "Demo": "đê mô", "lot": "lốt", "Lot": "lốt",
    "%": " phần trăm", "trading": "tre đinh", "Trading": "tre đinh", "chart": "chát", "Chart": "chát", "AI": "ây ai",
    "Gold": "gâu", "gold": "gâu", "Stop Loss": "xtóp lót", "stop loss": "xtóp lót", "trailing": "trây linh", "Trailing": "trây linh",
    "DCA": "đê xê a", "news": "niu", "News": "niu", "Fed": "phét", "FED": "phét", "CPI": "xê pê i", "NFP": "en ép pê",
}

DIG = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]


def say_int(n):
    n = int(n)
    if n < 10:
        return DIG[n]
    if n < 20:
        return "mười" + ("" if n == 10 else " " + ("lăm" if n % 10 == 5 else DIG[n % 10]))
    if n < 100:
        u = n % 10
        return DIG[n // 10] + " mươi" + ("" if not u else " " + {1: "mốt", 5: "lăm", 4: "tư"}.get(u, DIG[u]))
    if n < 1000:
        r = n % 100
        return DIG[n // 100] + " trăm" + ("" if not r else (" lẻ " + DIG[r] if r < 10 else " " + say_int(r)))
    for big, name in ((10 ** 9, "tỷ"), (10 ** 6, "triệu"), (1000, "nghìn")):
        if n >= big:
            r = n % big
            return say_int(n // big) + " " + name + ("" if not r else " " + say_int(r))
    return str(n)


def to_spoken(text, extra=None):
    """Chu hien thi -> chu cho may doc: thay tu viet tat, doc so."""
    s = unicodedata.normalize("NFC", text)
    d = dict(DOC); d.update(extra or {})
    for k in sorted(d, key=len, reverse=True):
        if re.match(r"^\w", k):
            s = re.sub(r"(?<![\w/])" + re.escape(k) + r"(?![\w/])", d[k], s)
        else:
            s = s.replace(k, d[k])
    s = re.sub(r"(\d+)[.,](\d+)", lambda m: say_int(m.group(1)) + " phẩy " + " ".join(DIG[int(c)] for c in m.group(2)), s)
    s = re.sub(r"\d+", lambda m: say_int(m.group(0)), s)
    s = re.sub(r"[*{}\[\]\"“”]", "", s)
    s = s.replace("–", ",").replace("—", ",").replace("...", ",").replace("…", ",")
    return re.sub(r"\s+", " ", s).strip()


def syl_count(w):
    return max(1, len(re.findall(r"\w+", w)))


# ------------------------------------------------------------------ tai model
def _fetch(url, name, minsize):
    d = os.path.join(MODELS, name)
    if os.path.isdir(d) and os.listdir(d):
        return d
    os.makedirs(MODELS, exist_ok=True)
    tar = os.path.join(MODELS, name + ".tar.bz2")
    print(f"[giong] tai {name} tu GitHub releases (lan dau trong phien)...", flush=True)
    r = subprocess.run(["curl", "-sL", "--fail", "-o", tar, url])
    if r.returncode != 0 or os.path.getsize(tar) < minsize:
        raise SystemExit(f"[giong] khong tai duoc {name}. Dung giong file (Giang tu thu / vidIQ) hoac thu lai.")
    with tarfile.open(tar) as t:
        t.extractall(MODELS)
    os.remove(tar)
    return d


def ensure_sherpa():
    try:
        import sherpa_onnx  # noqa
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "-q", "sherpa-onnx", "soundfile"], check=True)


_TTS = None


def tts_engine():
    global _TTS
    if _TTS is None:
        ensure_sherpa()
        import sherpa_onnx
        d = _fetch(TTS_URL, TTS_MODEL, 3e7)
        cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=f"{d}/vi_VN-vais1000-medium.onnx", tokens=f"{d}/tokens.txt", data_dir=f"{d}/espeak-ng-data"),
            num_threads=2))
        _TTS = sherpa_onnx.OfflineTts(cfg)
    return _TTS


def synth(text, speed=1.0):
    """-> mang float32 o SR (44.1k)."""
    tts = tts_engine()
    a = tts.generate(text, sid=0, speed=speed)
    x = np.asarray(a.samples, np.float32)
    return resample(x, a.sample_rate, SR)


def resample(x, sr0, sr1):
    if sr0 == sr1 or x.size == 0:
        return x
    n = int(round(len(x) * sr1 / sr0))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def load_audio(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True).stdout
    if not raw:
        raise SystemExit(f"[giong] khong doc duoc am thanh: {path}")
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def trim(x, thr_db=-42, pad=0.03):
    if x.size == 0:
        return x
    hop = int(SR * 0.01)
    e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-12) for i in range(0, len(x), hop)])
    db = 20 * np.log10(e + 1e-9); on = np.where(db > max(thr_db, db.max() - 45))[0]
    if on.size == 0:
        return x
    a = max(0, on[0] * hop - int(pad * SR)); b = min(len(x), (on[-1] + 1) * hop + int(pad * SR))
    return x[a:b]


def gaps(x, min_gap=0.11, thr_rel=-30):
    """Khoang lang trong mot cau (giay) -> [(a, b)]."""
    hop = int(SR * 0.01)
    e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-12) for i in range(0, len(x), hop)])
    db = 20 * np.log10(e + 1e-9); thr = db.max() + thr_rel
    out, s = [], None
    for i, v in enumerate(db < thr):
        if v and s is None:
            s = i
        if not v and s is not None:
            if (i - s) * 0.01 >= min_gap and s > 3:
                out.append((s * 0.01, i * 0.01))
            s = None
    return out


# ------------------------------------------------------------------ moc tung tu
def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", unicodedata.normalize("NFC", text.strip()))
    return [p for p in parts if p.strip()]


def word_times(display, dur, gap_list=()):
    """Chia moc thoi gian cho tung chu hien thi theo so am tiet, khop dau phay voi khoang lang do duoc."""
    words = display.split()
    if not words:
        return []
    clauses, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[,;:]$", w):
            clauses.append(cur); cur = []
    if cur:
        clauses.append(cur)
    # ranh gioi menh de theo khoang lang (neu so khoang lang >= so dau phay)
    gl = sorted(gap_list, key=lambda g: g[1] - g[0], reverse=True)[:len(clauses) - 1]
    gl = sorted(gl)
    bounds = []
    if len(gl) == len(clauses) - 1:
        t = 0.0
        for g in gl:
            bounds.append((t, g[0])); t = g[1]
        bounds.append((t, dur))
    else:
        tot = sum(sum(syl_count(w) for w in c) + 0.8 for c in clauses)
        t = 0.0
        for c in clauses:
            d = dur * (sum(syl_count(w) for w in c) + 0.8) / tot
            bounds.append((t, t + d - (0.12 if c is not clauses[-1] else 0))); t += d
    out = []
    for c, (a, b) in zip(clauses, bounds):
        n = sum(syl_count(w) for w in c); t = a
        for w in c:
            d = (b - a) * syl_count(w) / n
            out.append({"w": w, "t0": round(t, 3), "t1": round(t + d, 3)}); t += d
    return out


# ------------------------------------------------------------------ dung giong cho kich ban
def build(script, work, brand=None, log=print):
    os.makedirs(work, exist_ok=True)
    v = script.get("voice", {"engine": "offline"})
    eng = v.get("engine", "offline")
    extra = (brand or {}).get("doc", {})
    scenes = script["scenes"]
    lead, gap_s, gap_sc, tail = v.get("lead", 0.35), v.get("sentence_gap", 0.16), v.get("scene_gap", 0.28), v.get("tail", 0.9)
    speed = float(v.get("speed", 1.0))
    timing = {"scenes": []}
    if eng == "file":
        return build_from_file(script, work, v, log)
    pieces, t = [np.zeros(int(lead * SR), np.float32)], lead
    for i, sc in enumerate(scenes):
        say = sc.get("say", "").strip()
        st = {"i": i, "t0": round(t, 3), "words": []}
        if sc.get("visual") == "aroll" and sc.get("file"):
            x = load_audio(sc["file"])
            a_, b_ = float(sc.get("in", 0)), sc.get("out")
            x = x[int(a_ * SR):int(float(b_) * SR) if b_ else None]
            words = word_times(say, len(x) / SR, gaps(x)) if say else []
            for w in words:
                w["t0"] += t; w["t1"] += t
            st["words"] = words; st["aroll_t"] = round(t, 3); pieces.append(x); t += len(x) / SR
        elif eng == "files" and sc.get("voice_file"):
            x = trim(load_audio(sc["voice_file"]))
            words = word_times(say, len(x) / SR, gaps(x))
            for w in words:
                w["t0"] += t; w["t1"] += t
            st["words"] = words; pieces.append(x); t += len(x) / SR
        elif say:
            sents = split_sentences(say)
            for k, sent in enumerate(sents):
                x = trim(synth(to_spoken(sent, extra), speed=speed))
                ws = word_times(sent, len(x) / SR, gaps(x))
                for w in ws:
                    w["t0"] = round(w["t0"] + t, 3); w["t1"] = round(w["t1"] + t, 3)
                st["words"] += ws; pieces.append(x); t += len(x) / SR
                if k < len(sents) - 1:
                    pieces.append(np.zeros(int(gap_s * SR), np.float32)); t += gap_s
        hold = float(sc.get("hold", 0.0))                  # giu canh them (giay) sau loi
        if not say and not sc.get("voice_file") and sc.get("visual") != "aroll":
            hold = max(hold, float(sc.get("dur", 2.0)))
        pad = gap_sc + hold
        pieces.append(np.zeros(int(pad * SR), np.float32)); t += pad
        st["t1"] = round(t, 3)
        st["voice_end"] = round(t - pad, 3)
        timing["scenes"].append(st)
        log(f"[giong] canh {i + 1}: {st['t0']:.2f}-{st['t1']:.2f}s  {say[:60]}")
    pieces.append(np.zeros(int(tail * SR), np.float32)); t += tail
    timing["scenes"][-1]["t1"] = round(t, 3)
    timing["scenes"][0]["t0"] = 0.0
    timing["total"] = round(t, 3)
    x = np.concatenate(pieces)
    peak = np.max(np.abs(x)) + 1e-9
    x = x / peak * 0.89
    write_wav(os.path.join(work, "voice.wav"), x)
    json.dump(timing, open(os.path.join(work, "timing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return timing


def write_wav(path, x, sr=SR):
    import wave
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())


# ------------------------------------------------------------------ mot file giong cho ca kich ban -> nghe, chia canh
def build_from_file(script, work, v, log=print):
    ensure_sherpa()
    import sherpa_onnx
    d = _fetch(ASR_URL, ASR_MODEL, 1e8)
    r = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=f"{d}/encoder-epoch-12-avg-8.onnx", decoder=f"{d}/decoder-epoch-12-avg-8.onnx", joiner=f"{d}/joiner-epoch-12-avg-8.onnx",
        tokens=f"{d}/tokens.txt", num_threads=2, sample_rate=16000, feature_dim=80, decoding_method="greedy_search")
    lead = v.get("lead", 0.2); tail = v.get("tail", 0.9)
    x = trim(load_audio(v["file"]))
    x16 = resample(x, SR, 16000)
    rec = []                                               # [tu, giay]
    step = 20.0; pos = 0.0
    while pos < len(x16) / 16000:
        seg = x16[int(pos * 16000):int((pos + step + 0.5) * 16000)]
        s = r.create_stream(); s.accept_waveform(16000, seg); r.decode_stream(s)
        cur, t0 = "", None
        for tk, tt in zip(s.result.tokens, s.result.timestamps):
            if tk.startswith("▁") or tk.startswith(" "):
                if cur and pos + t0 < pos + step:
                    rec.append([cur.lower(), pos + t0])
                cur, t0 = tk.lstrip("▁ "), tt
            else:
                if t0 is None:
                    t0 = tt
                cur += tk
        if cur and t0 is not None and t0 < step:
            rec.append([cur.lower(), pos + t0])
        pos += step
    # khop chu kich ban voi chu nghe duoc
    disp = []
    for i, sc in enumerate(script["scenes"]):
        for w in sc.get("say", "").split():
            for sy in re.findall(r"\w+", to_spoken(w).lower()) or [w.lower()]:
                disp.append((i, w, sy))
    sm = difflib.SequenceMatcher(None, [d_[2] for d_ in disp], [w for w, _ in rec], autojunk=False)
    tmap = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            tmap[a + k] = rec[b + k][1]
    known = sorted(tmap)
    times = []
    for k in range(len(disp)):
        if k in tmap:
            times.append(tmap[k]); continue
        prv = max([j for j in known if j < k], default=None); nxt = min([j for j in known if j > k], default=None)
        if prv is None and nxt is None:
            times.append(k * 0.25)
        elif prv is None:
            times.append(max(0, tmap[nxt] - 0.25 * (nxt - k)))
        elif nxt is None:
            times.append(tmap[prv] + 0.25 * (k - prv))
        else:
            times.append(tmap[prv] + (tmap[nxt] - tmap[prv]) * (k - prv) / (nxt - prv))
    total = lead + len(x) / SR + tail
    timing = {"scenes": [], "total": round(total, 3), "matched": round(len(tmap) / max(1, len(disp)), 3)}
    for i, sc in enumerate(script["scenes"]):
        idx = [k for k, d_ in enumerate(disp) if d_[0] == i]
        ws, cnt = [], 0
        for wd in sc.get("say", "").split():
            n = len(re.findall(r"\w+", to_spoken(wd).lower())) or 1
            ks = idx[cnt:cnt + n]; cnt += n
            if ks:
                ws.append({"w": wd, "t0": round(lead + times[ks[0]], 3), "t1": round(lead + times[ks[-1]] + 0.22, 3)})
        timing["scenes"].append({"i": i, "words": ws})
    for i, st in enumerate(timing["scenes"]):
        st["t0"] = round((st["words"][0]["t0"] - 0.15) if st["words"] else 0, 3)
    timing["scenes"][0]["t0"] = 0.0
    for i, st in enumerate(timing["scenes"]):
        st["t1"] = timing["scenes"][i + 1]["t0"] if i + 1 < len(timing["scenes"]) else round(total, 3)
        st["voice_end"] = st["words"][-1]["t1"] if st["words"] else st["t1"]
    y = np.concatenate([np.zeros(int(lead * SR), np.float32), x, np.zeros(int(tail * SR), np.float32)])
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.89
    write_wav(os.path.join(work, "voice.wav"), y)
    json.dump(timing, open(os.path.join(work, "timing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"[giong] file {v['file']}: {len(x) / SR:.1f}s, khop chu kich ban {timing['matched']:.0%}"
        + ("  <-- thap: kiem lai kich ban co dung loi da thu khong" if timing["matched"] < 0.6 else ""))
    return timing


# ------------------------------------------------------------------ bao hinh mieng (avatar)
def mouth_tracks(voice_wav, fps, n_frames):
    """-> level[n], bands[n,7], talk[n] (0..1, da lam muot)."""
    x = load_audio(voice_wav, 22050); sr = 22050
    hop = sr / fps; win = 1024
    lv = np.zeros(n_frames); bd = np.zeros((n_frames, 7))
    edges = np.geomspace(160, 4200, 8)
    freqs = np.fft.rfftfreq(win, 1 / sr)
    hann = np.hanning(win)
    for f in range(n_frames):
        c = int(f * hop)
        seg = x[max(0, c - win // 2):c + win // 2]
        if seg.size < win:
            seg = np.pad(seg, (0, win - seg.size))
        lv[f] = np.sqrt(np.mean(seg ** 2))
        sp = np.abs(np.fft.rfft(seg * hann))
        for b in range(7):
            m = (freqs >= edges[b]) & (freqs < edges[b + 1])
            bd[f, b] = sp[m].mean() if m.any() else 0
    ref = np.percentile(lv[lv > 1e-4], 95) if (lv > 1e-4).any() else 1
    lv = np.clip(lv / (ref + 1e-9), 0, 1.2)
    for b in range(7):
        col = bd[:, b]; r = np.percentile(col[col > 1e-6], 92) if (col > 1e-6).any() else 1
        bd[:, b] = np.clip(col / (r + 1e-9), 0, 1)
    bd = bd * np.clip(lv[:, None] * 1.4, 0, 1)
    # lam muot: len nhanh, xuong cham
    out_b = np.zeros_like(bd); out_l = np.zeros_like(lv); talk = np.zeros_like(lv)
    pb = np.zeros(7); pl = 0.0; pt = 0.0
    for f in range(n_frames):
        pb = np.where(bd[f] > pb, pb * 0.25 + bd[f] * 0.75, pb * 0.55 + bd[f] * 0.45)
        pl = pl * 0.4 + lv[f] * 0.6 if lv[f] > pl else pl * 0.7 + lv[f] * 0.3
        on = 1.0 if lv[f] > 0.08 else 0.0
        pt = pt * 0.55 + on * 0.45 if on > pt else pt * 0.86 + on * 0.14
        out_b[f] = pb; out_l[f] = pl; talk[f] = pt
    return out_l, out_b, talk


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("--work", default="work")
    a = ap.parse_args()
    sc = json.load(open(a.script, encoding="utf-8"))
    tm = build(sc, a.work)
    print(f"[xong] {a.work}/voice.wav  {tm['total']:.1f}s")
