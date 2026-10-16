import cv2, numpy as np
hd=cv2.VideoCapture("../src_media/huongdan.mp4"); hd.set(cv2.CAP_PROP_POS_MSEC,1500); ok,a=hd.read()
sift=cv2.SIFT_create(8000)
ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); ka,da=sift.detectAndCompute(ga,None)
cap=cv2.VideoCapture("fly/DJI_0316_1080.mp4"); best=None
for t in np.arange(9.0,18.0,0.25):
    cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,b=cap.read()
    gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY); kb,db=sift.detectAndCompute(gb,None)
    ms=cv2.FlannBasedMatcher().knnMatch(da,db,k=2); g=[m for m,n in ms if m.distance<0.7*n.distance]
    A=np.float32([ka[m.queryIdx].pt for m in g]); B=np.float32([kb[m.trainIdx].pt for m in g])
    h,mask=cv2.findHomography(A,B,cv2.RANSAC,4.0); n=int(mask.sum())
    if best is None or n>best[0]: best=(n,t,h,b)
n,t,h,b=best; print("best t",t,"inliers",n)
pts=np.float32([[[150,1206],[260,1136]]])
print(cv2.perspectiveTransform(pts,h))
p=cv2.perspectiveTransform(pts,h)[0]
cv2.circle(b,tuple(int(v) for v in p[0]),20,(0,0,255),5); cv2.circle(b,tuple(int(v) for v in p[1]),20,(255,255,0),5)
cv2.imwrite("hd_mapped.jpg",cv2.resize(b,(540,960)))
