import sys, struct, math, json
b=open(sys.argv[1],"rb").read()
lo,hi=0x40000,0x160000
n=(hi-lo)//4
f=struct.unpack(f">{n}f",b[lo:hi])
def ok(x): return math.isfinite(x) and abs(x)<1e6 and (x==0 or abs(x)>1e-5)
# runs of plausible floats
runs=[];i=0
while i<n:
    if not ok(f[i]): i+=1; continue
    j=i
    while j<n and ok(f[j]): j+=1
    if j-i>=64: runs.append((i,j))
    i=j
def is_axis(seg): return all(seg[k+1]>seg[k] for k in range(len(seg)-1))
cands=[]
for (s,e) in runs:
    v=f[s:e]
    # skip axis pools (mostly monotonic chunks)
    for W in range(6,33):
        # sliding windows of whole-table candidates: try rows R from 4..32 starting at s
        pass
    # simpler: evaluate best width over the whole run
    best=None
    for W in range(6,33):
        R=(e-s)//W
        if R<4: continue
        rng=max(v)-min(v)
        if rng==0: continue
        h=sum(abs(v[r*W+c+1]-v[r*W+c]) for r in range(R) for c in range(W-1))/(R*(W-1))
        vv=sum(abs(v[(r+1)*W+c]-v[r*W+c]) for r in range(R-1) for c in range(W))/((R-1)*W)
        score=(h+vv)/rng
        if best is None or score<best[0]: best=(score,W,R,h/rng,vv/rng)
    if best and best[0]<0.12:
        distinct=len(set(round(x,4) for x in v))
        if distinct>12: cands.append(dict(off=lo+4*s,n=e-s,W=best[1],R=best[2],score=round(best[0],4),mn=min(v),mx=max(v),distinct=distinct))
cands.sort(key=lambda c:c["score"])
json.dump(cands,open(sys.argv[2],"w"))
print(len(runs),"plausible-float runs >=64;",len(cands),"smooth 2D candidates")
for c in cands[:30]:
    print(f"  @{c['off']:#08x} {c['n']:5d} floats  best width {c['W']:2d} x {c['R']:3d} rows  score {c['score']}  range {c['mn']:.4g}..{c['mx']:.4g}")
