import numpy as np, os, sys, wave
os.makedirs("assets/sfx", exist_ok=True)
SR=44100
rng=np.random.default_rng(7)
def lp(x,c):
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); X*=1/(1+(f/c)**4); return np.fft.irfft(X,len(x))
def hp(x,c): return x-lp(x,c)
def save(n,x,g=0.9):
    x=np.asarray(x,np.float64); x=x/(np.abs(x).max()+1e-9)*g
    st=np.stack([x,x],1)
    with wave.open(f"assets/sfx/{n}.wav","wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())
def t(d): return np.arange(int(d*SR))/SR
# long cinematic whoosh for camera moves (sweeping band of noise)
d=1.4; tt=t(d); nz=rng.normal(0,1,len(tt))
env=np.sin(np.pi*np.clip(tt/d,0,1))**2.2
sweep=np.zeros_like(tt); 
for i,c in enumerate(np.linspace(400,3200,8)):
    seg=hp(lp(nz,c*1.6),c*0.6); w=np.exp(-((tt/d-i/7)**2)/0.02); sweep+=seg*w
save("whoosh", sweep*env, 0.8)
# short swish for line start
d=0.6; tt=t(d); nz=rng.normal(0,1,len(tt)); save("swish", hp(lp(nz,6000),1500)*np.sin(np.pi*tt/d)**2, 0.6)
# pin pop: pitched blip + click
d=0.35; tt=t(d); f=900*np.exp(-tt*9)+420; s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*14); s[:200]+=rng.normal(0,0.4,200)
save("pop", s, 0.75)
# arrival chime (bell-ish)
d=1.6; tt=t(d); s=sum(a*np.sin(2*np.pi*fr*tt)*np.exp(-tt*k) for a,fr,k in [(1,1046.5,3),(0.6,1568,3.5),(0.35,2093,4.5),(0.2,3136,6)])
save("chime", s, 0.55)
# map draw: soft airy rising shimmer (3s)
d=3.0; tt=t(d); nz=rng.normal(0,1,len(tt)); s=hp(lp(nz,9000),2500)*(0.25+0.75*(tt/d))*np.sin(np.pi*tt/d)**0.6
tone=sum(np.sin(2*np.pi*fr*(1+0.15*tt/d)*tt) for fr in (660,990))*0.06*np.sin(np.pi*tt/d)
save("draw", s*0.5+tone, 0.45)
# title impact
d=1.8; tt=t(d); b=np.sin(2*np.pi*(40+60*np.exp(-tt*7))*tt)*np.exp(-tt*2.6); n2=lp(rng.normal(0,1,len(tt)),1500)*np.exp(-tt*12)*0.5
save("boom", b+n2, 0.9)
# riser into title
d=1.5; tt=t(d); f=200+1200*(tt/d)**2; s=np.sin(2*np.pi*np.cumsum(f)/SR)*0.25+hp(lp(rng.normal(0,1,len(tt)),7000),1800)*0.5
save("riser", s*(tt/d)**1.8, 0.6)
print("ok")

# soft ambient bed (pad chords + gentle pulse), length = argv[1] seconds -> assets/bgm.wav
BG=float(sys.argv[1]) if len(sys.argv)>1 else 0
if BG>0:
    tt=t(BG); x=np.zeros_like(tt)
    chords=[[220.0,277.18,329.63,415.3],[196.0,246.94,293.66,369.99],[174.61,220.0,261.63,329.63],[196.0,246.94,293.66,392.0]]
    bar=60/96*4
    for i in range(int(BG/bar)+1):
        a,b=int(i*bar*SR),int(min(BG,(i+1)*bar+0.6)*SR)
        if a>=len(tt): break
        seg=tt[a:b]-tt[a]; env=np.minimum(1,seg/0.8)*np.exp(-seg/(bar*1.6))
        for f in chords[i%4]: x[a:b]+=0.18*env*(np.sin(2*np.pi*f*seg)+0.3*np.sin(2*np.pi*2*f*seg+0.4))
    beat=60/96
    for k in range(int(BG/beat)):
        a=int(k*beat*SR); n=min(int(0.25*SR),len(tt)-a); s2=np.arange(n)/SR
        x[a:a+n]+=0.5*np.sin(2*np.pi*(55+60*np.exp(-s2*30))*s2)*np.exp(-s2*14)
    fade=np.minimum(1,np.minimum(tt/1.5,(BG-tt)/2.5)); x*=fade
    x=lp(x,5000)
    x=x/(np.abs(x).max()+1e-9)*0.8; st=np.stack([x,x],1)
    with wave.open("assets/bgm.wav","wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())
