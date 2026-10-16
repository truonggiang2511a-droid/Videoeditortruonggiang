import cv2, numpy as np, json
W,H=540,960
al=np.fromfile("../work/alpha.raw",np.uint8).reshape(-1,H,W)
cap=cv2.VideoCapture("assets/source.mp4"); fr=[]
while True:
    ok,f=cap.read()
    if not ok: break
    fr.append(cv2.resize(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY),(W,H)))
n=min(len(fr),len(al)); print("frames",len(fr),len(al))
Hc=[np.eye(3)]
for i in range(n-1):
    m=((al[i]<20)&(al[i+1]<20)).astype(np.uint8)*255
    m=cv2.erode(m,np.ones((25,25),np.uint8))
    p0=cv2.goodFeaturesToTrack(fr[i],1200,0.01,7,mask=m)
    p1,st,_=cv2.calcOpticalFlowPyrLK(fr[i],fr[i+1],p0,None,winSize=(21,21),maxLevel=3)
    ok=st.ravel()==1
    h,_=cv2.findHomography(p0[ok],p1[ok],cv2.RANSAC,1.5)
    Hc.append(h@Hc[-1])
S=np.diag([2,2,1.]); Si=np.diag([.5,.5,1.])
out=[]
for h in Hc:
    hf=S@h@Si; hf/=hf[2,2]; out.append([round(float(v),7) for v in hf.T.ravel()])
json.dump(out,open("assets/bg_h.json","w"))
c=np.float32([[[540,800]]])
for i in (0,60,120,170,200,260): 
    if i<len(Hc): print(i, cv2.perspectiveTransform(c,S@Hc[i]@Si)[0,0])
