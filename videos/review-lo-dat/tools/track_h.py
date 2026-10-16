# Per-frame ground-plane homographies H_t mapping anchor-frame pixels -> frame t pixels (1080x1920).
import cv2, numpy as np, sys, json
clip, t_anchor, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
S = 0.5; cap = cv2.VideoCapture(clip); fps = cap.get(5); fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    fr.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), None, fx=S, fy=S))
n = len(fr); a = min(n - 1, round(t_anchor * fps))
sky = np.zeros_like(fr[0]); sky[int(0.12 * sky.shape[0]):] = 255   # ignore the sky/horizon band
def hom(g0, g1):
    p0 = cv2.goodFeaturesToTrack(g0, 2000, 0.01, 8, mask=sky)
    p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None, winSize=(21, 21), maxLevel=4)
    ok = st.ravel() == 1
    H, _ = cv2.findHomography(p0[ok], p1[ok], cv2.RANSAC, 2.0); return H
Hs = [None] * n; Hs[a] = np.eye(3)
for i in range(a, n - 1): Hs[i + 1] = hom(fr[i], fr[i + 1]) @ Hs[i]
for i in range(a, 0, -1): Hs[i - 1] = hom(fr[i], fr[i - 1]) @ Hs[i]
Sm = np.diag([1 / S, 1 / S, 1.]); Si = np.diag([S, S, 1.])
res = []
for H in Hs:
    F = Sm @ H @ Si; F /= F[2, 2]; res.append([round(float(v), 8) for v in F.ravel()])
json.dump({"fps": fps, "anchor": a, "H": res}, open(out, "w"))
print(clip, n, "frames, anchor", a)
