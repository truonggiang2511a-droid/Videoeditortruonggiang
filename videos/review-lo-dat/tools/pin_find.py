import cv2, numpy as np, sys, json
p=sys.argv[1]; cap=cv2.VideoCapture(p); fps=cap.get(5); out=[]; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    if i%6==0:
        h=cv2.cvtColor(f,cv2.COLOR_BGR2HSV)
        m=((h[...,0]<8)|(h[...,0]>172))&(h[...,1]>150)&(h[...,2]>120)
        m=m.astype(np.uint8)
        n,lab,st,cen=cv2.connectedComponentsWithStats(m)
        best=None
        for k in range(1,n):
            x,y,w,hh,a=st[k]
            if 150<a<6000 and 0.5<hh/max(w,1)<2.5 and (best is None or a>best[4]): best=(x,y,w,hh,a)
        out.append([round(i/fps,2)]+([int(best[0]+best[2]/2),int(best[1]+best[3]),int(best[4])] if best else [None]))
    i+=1
print(json.dumps(out))
