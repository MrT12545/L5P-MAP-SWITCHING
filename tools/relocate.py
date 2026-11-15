import sys, bisect, collections, pickle
sys.path.insert(0, sys.argv[1]); import olscsv
stock=open(sys.argv[2],'rb').read(); sotf=open(sys.argv[3],'rb').read()
CAL0=0x60000
S_OFF=0x20000            # stock: file = cpu - 0x20000
N_OFF=-0x39FFE0          # sotf cal: file = cpu + 0x39FFE0  -> cpu = file - 0x39FFE0
cs=stock[CAL0-S_OFF:0x200000-S_OFF]             # cal, indexed by cpu-CAL0
cn=sotf[CAL0+0x39FFE0:0x1FFFF0+0x39FFE0]
K=16
def windows(buf,step):
    d=collections.defaultdict(list)
    for i in range(0,len(buf)-K,step):
        w=buf[i:i+K]
        if len(set(w))>=8: d[w].append(i)
    return d
ws=windows(cs,2); wn=windows(cn,2)
anch=sorted((i[0],wn[w][0]) for w,i in ws.items() if len(i)==1 and len(wn.get(w,()))==1)
# keep anchors consistent with neighbours (drop isolated deltas)
dl=[b-a for a,b in anch]
good=[anch[k] for k in range(len(anch)) if (k>0 and dl[k-1]==dl[k]) or (k+1<len(anch) and dl[k+1]==dl[k])]
pos=[a for a,_ in good]; dlt=[b-a for a,b in good]
pickle.dump(good,open(sys.argv[4],'wb'))
print(f"anchors: {len(anch)} unique, {len(good)} neighbour-consistent")
deltas=collections.Counter(dlt); print("distinct deltas:",len(deltas))
def local(x,length):
    k=bisect.bisect_right(pos,x)-1; j=bisect.bisect_left(pos,x+length)
    L=(dlt[k],x-pos[k]) if k>=0 else None
    R=(dlt[j],pos[j]-(x+length)) if j<len(pos) else None
    return L,R
maps=olscsv.load(sys.argv[5])
FMT={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}
def size(r): return FMT[r['DataOrg']]*int(r['Columns'])*int(r['Rows'])
def relocate(cpu,length):
    x=cpu-CAL0
    if not (0<=x<len(cs)): return None,'out-of-cal'
    data=cs[x:x+length]; L,R=local(x,length)
    cand=[]
    if L: cand.append(L[0])
    if R and (not L or R[0]!=L[0]): cand.append(R[0])
    # exact content near expected location
    if length>=8 and len(set(data))>2:
        for d in cand:
            y=x+d
            if 0<=y and cn[y:y+length]==data: return y+CAL0,'exact'
        hits=[]; i=cn.find(data)
        while i!=-1 and len(hits)<3: hits.append(i); i=cn.find(data,i+1)
        if len(hits)==1 and cand and min(abs(hits[0]-x-d) for d in cand)<0x400: return hits[0]+CAL0,'exact'
    if L and R and L[0]==R[0]:
        y=x+L[0]; return y+CAL0, ('same' if cn[y:y+length]==data else 'aligned')
    # ambiguous: prefer the side whose candidate bytes match more of the stock data, else nearest anchor
    best=None
    for d,dist in [c for c in (L,R) if c]:
        y=x+d
        if y<0: continue
        score=sum(1 for p,q in zip(cn[y:y+length],data) if p==q)/max(1,length)
        key=(score,-dist)
        if best is None or key>best[0]: best=(key,y)
    if best is None: return None,'unresolved'
    y=best[1]; return y+CAL0, ('same' if cn[y:y+length]==data else ('between-shifts' if best[0][0]<0.999 else 'same'))
out=[];stat=collections.Counter()
for r in maps:
    cpu=int(r['Fieldvalues.StartAddr.Cpu'][1:],16); L=size(r)
    ncpu,how=relocate(cpu,L)
    axes={}
    for ax in 'XY':
        if r[f'Axis{ax}.DataSrc'].startswith('eRom'):
            acpu=int(r[f'Axis{ax}.DataAddr.Cpu'][1:],16)
            n_ax=int(r['Columns']) if ax=='X' else int(r['Rows'])
            alen=FMT.get(r[f'Axis{ax}.DataOrg'],2)*n_ax
            axes[ax]=relocate(acpu,alen)
    stat[how]+=1
    out.append((r['Name'],cpu,ncpu,how,axes))
pickle.dump(out,open(sys.argv[6],'wb'))
print("map placement:",dict(stat))
axst=collections.Counter(h for _,_,_,_,a in out for (_,h) in a.values()); print("axis placement:",dict(axst))
