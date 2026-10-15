#!/usr/bin/env python3
"""Nghe lai giong da dung (work/voice.wav) bang may nghe zipformer, so voi loi kich ban tung canh.

  python3 kit/ea_asr_check.py work
In: [canh N] giong X% | may nghe: ...  -- canh duoi 75% thi xem tu nao may doc sai, them vao "doc" cua brand_ea.json.
Lan dau tai model ~256MB tu GitHub releases (dung chung voi engine "file").
"""
import json, os, re, sys, difflib, unicodedata
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT)
import ea_voice as V


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.findall(r"[a-z0-9]+", s)


def main(work):
    V.ensure_sherpa()
    import sherpa_onnx
    d = V._fetch(V.ASR_URL, V.ASR_MODEL, 1e8)
    r = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=f"{d}/encoder-epoch-12-avg-8.onnx", decoder=f"{d}/decoder-epoch-12-avg-8.onnx", joiner=f"{d}/joiner-epoch-12-avg-8.onnx",
        tokens=f"{d}/tokens.txt", num_threads=2, sample_rate=16000, feature_dim=80, decoding_method="greedy_search")
    x = V.load_audio(os.path.join(work, "voice.wav"), 16000)
    tm = json.load(open(os.path.join(work, "timing.json"), encoding="utf-8"))
    tot = []
    for st in tm["scenes"]:
        if not st.get("words"):
            continue
        a = max(0, st["words"][0]["t0"] - 0.15); b = st["words"][-1]["t1"] + 0.3
        s = r.create_stream(); s.accept_waveform(16000, x[int(a * 16000):int(b * 16000)]); r.decode_stream(s)
        heard = s.result.text.lower()
        ref = " ".join(w["w"] for w in st["words"])
        ratio = difflib.SequenceMatcher(None, norm(V.to_spoken(ref)), norm(heard)).ratio()
        tot.append(ratio)
        flag = "  <-- xem lai" if ratio < 0.75 else ""
        print(f"[canh {st['i'] + 1}] giong {ratio:.0%} | may nghe: {heard}{flag}")
    if tot:
        print(f"[tong] trung binh {sum(tot) / len(tot):.0%} (tu tieng Anh / ten rieng may nghe hay sai, khong phai luc nao cung la loi doc)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "work")
