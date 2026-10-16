#!/usr/bin/env python3
"""Slim the presenter a little: horizontal liquify around the body, driven by the face track in work/scan.json.
    python3 tools/slim.py in.mp4 out.mp4 [--body 0.08] [--face 0.04]
Body narrower by ~body*100 %, face by ~face*100 %; the warp fades out with distance so the background barely moves."""
import argparse, json, subprocess, numpy as np, cv2
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--scan", default="work/scan.json"); ap.add_argument("--body", type=float, default=0.08); ap.add_argument("--face", type=float, default=0.04)
ap.add_argument("--t0", type=float, default=0.0)
a = ap.parse_args()
sc = json.load(open(a.scan)); F = np.array([f[:5] for f in sc["faces"] if f[5] > 0.5])
cap = cv2.VideoCapture(a.src); fps = cap.get(5); W = int(cap.get(3)); H = int(cap.get(4))
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                        "-ss", str(a.t0), "-i", a.src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "12", "-preset", "medium",
                        "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", a.out], stdin=subprocess.PIPE)
xs = np.arange(W, dtype=np.float32)[None, :].repeat(H, 0); ys = np.arange(H, dtype=np.float32)[:, None].repeat(W, 1)
def face_at(t):
    i = np.searchsorted(F[:, 0], t)
    if i <= 0: return F[0, 1:]
    if i >= len(F): return F[-1, 1:]
    f0, f1 = F[i - 1], F[i]
    if f1[0] - f0[0] > 1.0: return f0[1:] if t - f0[0] < f1[0] - t else f1[1:]
    r = (t - f0[0]) / (f1[0] - f0[0]); return f0[1:] * (1 - r) + f1[1:] * r
n = 0; prev = None
while True:
    ok, fr = cap.read()
    if not ok: break
    t = a.t0 + n / fps
    cx, cy, fw, fh = face_at(t)
    st = np.array([cx * W, cy * H, fw * W, fh * H])
    prev = st if prev is None else prev * 0.6 + st * 0.4            # smooth jitter of the face box
    cxp, cyp, fwp, fhp = prev
    top = cyp - 0.9 * fhp; chin = cyp + 0.6 * fhp
    k = np.where(ys < top, 0.0, np.where(ys < chin, a.face, a.body)).astype(np.float32)
    ramp = np.clip((ys - (top - 0.6 * fhp)) / (0.6 * fhp), 0, 1); k *= ramp
    blend = np.clip((ys - chin) / (0.8 * fhp), 0, 1)                   # face -> body transition
    k = np.where(ys >= chin, a.face + (a.body - a.face) * blend, k)
    sig = np.where(ys < chin, 1.25 * fwp, 2.4 * fwp).astype(np.float32)
    u = xs - cxp
    mx = (cxp + u * (1 + k * np.exp(-(u / sig) ** 2))).astype(np.float32)
    out = cv2.remap(fr, mx, ys, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    enc.stdin.write(out.tobytes()); n += 1
enc.stdin.close(); enc.wait(); print(a.out, n, "frames")
