import math,os,io,sys,urllib.request,concurrent.futures as cf
from PIL import Image
def xy(lat,lon,z):
    n=2**z; x=(lon+180)/360*n; y=(1-math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/math.pi)/2*n; return x,y
def mosaic(z,lat1,lon1,lat2,lon2,out):
    x0,y0=xy(lat1,lon1,z); x1,y1=xy(lat2,lon2,z)
    tx0,tx1=int(min(x0,x1)),int(max(x0,x1)); ty0,ty1=int(min(y0,y1)),int(max(y0,y1))
    W=(tx1-tx0+1)*256; Hh=(ty1-ty0+1)*256; img=Image.new("RGB",(W,Hh),(40,40,40))
    os.makedirs("vitri/cache",exist_ok=True)
    def get(t):
        x,y=t; p=f"vitri/cache/{z}_{x}_{y}.jpg"
        if not os.path.exists(p):
            u=f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            open(p,"wb").write(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read())
        return t,p
    ts=[(x,y) for x in range(tx0,tx1+1) for y in range(ty0,ty1+1)]
    with cf.ThreadPoolExecutor(8) as ex:
        for (x,y),p in ex.map(get,ts):
            try: img.paste(Image.open(p).convert("RGB"),((x-tx0)*256,(y-ty0)*256))
            except Exception as e: print("bad",p,e)
    img.save(out,quality=92); print(out,img.size,"origin tile",tx0,ty0,"z",z,"tiles",len(ts))
    return dict(z=z,tx0=tx0,ty0=ty0,w=W,h=Hh)
import json
m={}
m["wide"]=mosaic(16,10.700,106.540,10.632,106.618,"vitri/wide_z16.jpg")
m["detail"]=mosaic(18,10.6525,106.5650,10.6425,106.5770,"vitri/detail_z18.jpg")
json.dump(m,open("vitri/mosaics.json","w"))
