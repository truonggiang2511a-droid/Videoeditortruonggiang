# Track a ground point through a flycam clip by chaining frame-to-frame homographies (aerial view ~ planar ground).
import cv2, numpy as np, sys, json
clip, t_anchor, pt, out = sys.argv[1], float(sys.argv[2]), tuple(map(float, sys.argv[3].split(','))), sys.argv[4]
S = 0.5
cap = cv2.VideoCapture(clip); fps = cap.get(5); fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    fr.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), None, fx=S, fy=S))
n = len(fr); a = min(n - 1, round(t_anchor * fps))
def hom(g0, g1):
    p0 = cv2.goodFeaturesToTrack(g0, 1500, 0.01, 8, mask=None)
    p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None, winSize=(21, 21), maxLevel=4)
    ok = st.ravel() == 1
    H, m = cv2.findHomography(p0[ok], p1[ok], cv2.RANSAC, 2.0)
    return H
pos = [None] * n; pos[a] = np.array([pt[0] * S, pt[1] * S])
for rng, step in ((range(a, n - 1), 1), (range(a, 0, -1), -1)):
    for i in rng:
        H = hom(fr[i], fr[i + step])
        p = cv2.perspectiveTransform(np.float32([[pos[i]]]), H)[0, 0]
        pos[i + step] = p
res = [[round(float(p[0]) / S, 1), round(float(p[1]) / S, 1)] for p in pos]
json.dump({"fps": fps, "pts": res}, open(out, "w"))
print(clip, "frames", n, "first", res[0], "last", res[-1])
