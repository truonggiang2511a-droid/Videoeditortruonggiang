import cv2, json, sys
clip, tj, out = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(tj)); cap = cv2.VideoCapture(clip); n = len(d["pts"]); ims = []
for k in range(8):
    i = int(k * (n - 1) / 7); cap.set(1, i); ok, f = cap.read()
    x, y = map(int, d["pts"][i]); cv2.circle(f, (x, y), 22, (0, 0, 255), 6); cv2.putText(f, f"{i/d['fps']:.1f}s", (30, 80), 0, 2.5, (0, 255, 255), 5)
    ims.append(cv2.resize(f, (270, 480)))
cv2.imwrite(out, cv2.hconcat(ims))
