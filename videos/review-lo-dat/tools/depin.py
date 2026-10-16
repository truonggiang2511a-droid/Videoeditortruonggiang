import cv2, numpy as np, sys, subprocess
src, out = sys.argv[1], sys.argv[2]
cap = cv2.VideoCapture(src); fps = cap.get(5); W = int(cap.get(3)); H = int(cap.get(4))
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                      "-c:v", "libx264", "-crf", "14", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
n = k = 0
while True:
    ok, f = cap.read()
    if not ok: break
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    m = (((hsv[..., 0] < 8) | (hsv[..., 0] > 172)) & (hsv[..., 1] > 140) & (hsv[..., 2] > 110)).astype(np.uint8)
    nl, lab, st, _ = cv2.connectedComponentsWithStats(m)
    mask = np.zeros_like(m)
    for i in range(1, nl):
        x, y, w, h, a = st[i]
        if 600 < a < 8000 and 0.6 < h / max(w, 1) < 2.2:        # the map pin (teardrop + white dot inside)
            mask[max(0, y - 8):y + h + 8, max(0, x - 8):x + w + 8] = 255
    if mask.any():
        k += 1; f = cv2.inpaint(f, mask, 9, cv2.INPAINT_TELEA)
    p.stdin.write(f.tobytes()); n += 1
p.stdin.close(); p.wait(); print(out, n, "frames,", k, "da xoa ghim")
