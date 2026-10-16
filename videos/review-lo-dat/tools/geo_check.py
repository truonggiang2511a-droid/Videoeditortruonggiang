import cv2, json, numpy as np, sys
cfg=json.load(open("geo_cfg.json"))[sys.argv[1]]; d=json.load(open(cfg["H"])); Hs=d["H"]; n=len(Hs)
cap=cv2.VideoCapture(cfg["clip"]); ims=[]
for k in range(8):
    i=int(k*(n-1)/7); cap.set(1,i); ok,f=cap.read(); H=np.array(Hs[i]).reshape(3,3)
    r=cv2.perspectiveTransform(np.float32([cfg["road"]]),H)[0].astype(int)
    cv2.polylines(f,[r],False,(255,255,0),10)
    p=cv2.perspectiveTransform(np.float32([[cfg["lot"]]]),H)[0,0]
    cv2.circle(f,(int(p[0]),int(p[1])),26,(0,0,255),8); cv2.putText(f,f"{i/d['fps']:.1f}s",(30,90),0,3,(0,255,255),6)
    ims.append(cv2.resize(f,(270,480)))
cv2.imwrite(sys.argv[2],cv2.hconcat(ims))
