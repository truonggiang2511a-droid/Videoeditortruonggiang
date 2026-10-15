import sys, json, os, wave
sys.path.insert(0, "/home/user/Videoeditortruonggiang/ea_video/kit")
import numpy as np, ea_voice as V
proj = os.path.dirname(os.path.abspath(__file__))
lines = json.load(open(f"{proj}/narration.json", encoding="utf-8"))
speed = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
extra = {"EA":"i a","MT5":"em tê năm","DCA":"đê xê a","AI":"ây ai","Expert Advisor":"ếch pớt át vai dờ","Robot":"rô bốt","bot":"bốt","demo":"đe mô","test":"tét","comment":"com mần","Comment":"com mần","lot":"lốt","Lot":"lốt"}
os.makedirs(f"{proj}/assets/voice", exist_ok=True)
voices = []; tot = 0
for i, text in enumerate(lines, 1):
    pieces = []; words = []; t = 0.0
    sents = V.split_sentences(text)
    for k, s in enumerate(sents):
        x = V.trim(V.synth(V.to_spoken(s, extra), speed=speed))
        ws = V.word_times(s, len(x)/V.SR, V.gaps(x))
        for w in ws:
            words.append({"id": len(words), "text": w["w"], "start": round(w["t0"]+t,3), "end": round(w["t1"]+t,3)})
        pieces.append(x); t += len(x)/V.SR
        if k < len(sents)-1:
            pieces.append(np.zeros(int(0.22*V.SR), np.float32)); t += 0.22
    x = np.concatenate(pieces); x = x/(np.max(np.abs(x))+1e-9)*0.89
    p = f"assets/voice/{i:02d}.wav"; V.write_wav(f"{proj}/{p}", x)
    voices.append({"frame": i, "path": p, "duration_s": round(t,3), "words": words}); tot += t
    print(i, round(t,1), len(text.split()))
json.dump({"voices": voices}, open(f"{proj}/voices_raw.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("total", round(tot,1))
