import json
D=json.load(open("src/data.json"))
R=D["routes"]
def km(m): return f"{m} m" if m<1000 else f"{m/1000:.1f}".replace(".",",")+" km"
def mins(s): return f"~{max(1,round(s/60))} phút"
POIS=[ # key, label, show-time, place (card above 'u' or below 'd')
 ("TL835B","TL835B",12.0,"u"),
 ("NÚT GIAO BÌNH CHÁNH","NÚT GIAO QL1A",22.4,"u"),
 ("CHỢ BÌNH CHÁNH","CHỢ BÌNH CHÁNH",29.4,"u"),
 ("TIỂU HỌC BÌNH CHÁNH","TIỂU HỌC BÌNH CHÁNH",35.0,"u"),
 ("UBND XÃ BÌNH CHÁNH","UBND XÃ BÌNH CHÁNH",36.6,"d"),
 ("BỆNH VIỆN ĐK BÌNH CHÁNH","BV ĐA KHOA BÌNH CHÁNH",45.6,"u"),
 ("CHỢ HƯNG LONG","CHỢ HƯNG LONG",48.6,"u"),
]
DRAW={"TL835B":(9.8,2.2),"NÚT GIAO BÌNH CHÁNH":(19.0,3.4),"CHỢ BÌNH CHÁNH":(26.4,3.0),"TIỂU HỌC BÌNH CHÁNH":(33.6,1.4),"UBND XÃ BÌNH CHÁNH":(35.2,1.4),"BỆNH VIỆN ĐK BÌNH CHÁNH":(42.6,3.0),"CHỢ HƯNG LONG":(45.8,2.8)}
HUD=[ # t0,t1, title, dist, time
 (12.2,16.2,"TL835B",km(R["TL835B"]["m"]),mins(R["TL835B"]["s"])),
 (22.6,26.2,"NÚT GIAO QL1A",km(R["NÚT GIAO BÌNH CHÁNH"]["m"]),mins(R["NÚT GIAO BÌNH CHÁNH"]["s"])),
 (29.6,33.4,"CHỢ BÌNH CHÁNH",km(R["CHỢ BÌNH CHÁNH"]["m"]),mins(R["CHỢ BÌNH CHÁNH"]["s"])),
 (45.8,48.4,"BV ĐA KHOA BÌNH CHÁNH",km(R["BỆNH VIỆN ĐK BÌNH CHÁNH"]["m"]),mins(R["BỆNH VIỆN ĐK BÌNH CHÁNH"]["s"])),
 (48.8,51.2,"CHỢ HƯNG LONG",km(R["CHỢ HƯNG LONG"]["m"]),mins(R["CHỢ HƯNG LONG"]["s"])),
]
W,Hh=D["size"]; hx,hy=D["home"]; det=D["detail"]; L=D["labels"]
paths=[]; pois=[]; hud=[]
for i,(k,(t0,dur)) in enumerate(DRAW.items()):
    paths.append(f'<path id="r{i}" class="route glow" d="{R[k]["d"]}" pathLength="1"/><path id="rc{i}" class="route core" d="{R[k]["d"]}" pathLength="1"/>')
for i,(k,lab,t,pl) in enumerate(POIS):
    x,y=R[k]["end"]
    pois.append(f'''<div class="poi {pl}" id="p{i}" style="left:{x}px;top:{y}px"><div class="pin"></div><div class="card"><b>{lab}</b><span>{km(R[k]["m"])} · {mins(R[k]["s"])}</span></div></div>''')
for i,(t0,t1,ti,d,tm) in enumerate(HUD):
    hud.append(f'<div class="hud" id="h{i}"><div class="hk">TỪ CĂN NHÀ ĐẾN</div><div class="ht">{ti}</div><div class="hr"><span class="hd">{d}</span><span class="hm">{tm}</span></div></div>')
def rt(lid,text,cls,size):
    a=L[lid]; return f'<div class="roadtxt {cls}" id="t_{lid}" style="left:{a["x"]}px;top:{a["y"]}px;font-size:{size}px;--a:{a["a"]}deg"><span class="rti" id="t_{lid}_i">{text}</span></div>'
summary_rows="".join(f'<div class="srow"><span>{n}</span><b>{km(R[k]["m"])}</b><i>{mins(R[k]["s"])}</i></div>' for n,k in [("TL835B","TL835B"),("Nút giao QL1A","NÚT GIAO BÌNH CHÁNH"),("Chợ Bình Chánh","CHỢ BÌNH CHÁNH"),("BV Đa khoa Bình Chánh","BỆNH VIỆN ĐK BÌNH CHÁNH")])
html=open("src/template.tpl",encoding="utf-8").read()
html=(html.replace("%W%",str(W)).replace("%H%",str(Hh)).replace("%HX%",str(hx)).replace("%HY%",str(hy))
 .replace("%DX%",str(det["x"])).replace("%DY%",str(det["y"])).replace("%DW%",str(det["w"])).replace("%DH%",str(det["h"]))
 .replace("%ROADS%",f'<path id="rd_ql1" class="road ql1" d="{D["roads"]["ql1"]}" pathLength="1"/><path id="rd_ct" class="road ct" d="{D["roads"]["caotoc"]}" pathLength="1"/><path id="rd_835" class="road tl" d="{D["roads"]["tl835b"]}" pathLength="1"/>')
 .replace("%ROUTES%","".join(paths)).replace("%POIS%","".join(pois)).replace("%HUD%","".join(hud))
 .replace("%ROADTXT%",rt("ql1","QUỐC LỘ 1A","y",118)+rt("tl835b","TL835B","c",72)+rt("caotoc","CAO TỐC","w",80))
 .replace("%SUMMARY%",summary_rows)
 .replace("%DRAW%",json.dumps({f"r{i}":v for i,v in enumerate(DRAW.values())}))
 .replace("%POIT%",json.dumps([p[2] for p in POIS])).replace("%HUDT%",json.dumps([[h[0],h[1]] for h in HUD])))
open("index.html","w",encoding="utf-8").write(html); print("built")
