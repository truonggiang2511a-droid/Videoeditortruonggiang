import json,math
V="../vi-tri-phuoc-ly/vitri/"
m=json.load(open(V+"mosaics.json")); r=json.load(open(V+"routes.json")); roads=json.load(open(V+"roads.json"))
W=m["wide"]
def px(lat,lon,mm=W):
    z=mm["z"];n=2**z;x=(lon+180)/360*n;y=(1-math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/math.pi)/2*n
    s=2**(16-z)
    return round((x-mm["tx0"])*256*s - 0,1) if False else round(((x*256)*s - W["tx0"]*256),1), round(((y*256)*s - W["ty0"]*256),1)
H=r["home"]
def place(mm):
    s=2**(16-mm["z"]); return {"x":mm["tx0"]*256*s-W["tx0"]*256,"y":mm["ty0"]*256*s-W["ty0"]*256,"w":mm["w"]*s,"h":mm["h"]*s}
D={"size":[W["w"],W["h"]],"home":px(*H),"detail":place(m["detail"]),"far":place(m["far"])}
def samples(P,n=160):
    L=[0]
    for i in range(1,len(P)): L.append(L[-1]+math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]))
    out=[];j=0
    for k in range(n+1):
        t=L[-1]*k/n
        while j<len(L)-2 and L[j+1]<t: j+=1
        seg=L[j+1]-L[j] or 1; f=(t-L[j])/seg
        out.append([round(P[j][0]+(P[j+1][0]-P[j][0])*f,1),round(P[j][1]+(P[j+1][1]-P[j][1])*f,1)])
    return out
routes={}
for k,v in r["pts"].items():
    P=[px(la,lo) for lo,la in v["geom"]]
    routes[k]={"d":"M"+" L".join(f"{x},{y}" for x,y in P),"end":px(*v["at"]),"m":v["m"],"s":v["s"],"S":samples(P)}
D["routes"]=routes
def line_d(lines): return " ".join("M"+" L".join(f"{px(la,lo)[0]},{px(la,lo)[1]}" for lo,la in l) for l in lines)
D["roads"]={"ql1":line_d(roads["ql1"]+roads["ql1b"]),"tl835b":line_d(roads["tl835b"]),"caotoc":line_d(roads["cao_toc"]+roads["ct_tl"])}
old=json.load(open("src/data.json")); D["labels"]=old["labels"]
json.dump(D,open("src/data2.json","w"),ensure_ascii=False)
for k,v in routes.items(): print(k,v["end"],v["m"],v["s"])
print(D["far"],D["detail"])
