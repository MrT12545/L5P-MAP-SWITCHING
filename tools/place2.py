import sys, pickle, bisect, collections
sys.path.insert(0, sys.argv[1]); import olscsv
stock=open(sys.argv[2],'rb').read(); sotf=open(sys.argv[3],'rb').read()
segs=pickle.load(open(sys.argv[4],'rb')); maps=olscsv.load(sys.argv[5])
CAL0=0x60000
cs=stock[CAL0-0x20000:0x200000-0x20000]; cn=sotf[CAL0+0x39FFE0:0x1FFFF0+0x39FFE0]
starts=[s for s,_ in segs]
def segdelta(x): return segs[bisect.bisect_right(starts,x)-1][1]
ESZ={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}
# collect items
items={}
def add(cpu,org,n):
    L=ESZ.get(org,2)*n; k=(cpu,L)
    if k not in items: items[k]=dict(x=cpu-CAL0,L=L,esz=ESZ.get(org,2))
for r in maps:
    C,R=int(r['Columns']),int(r['Rows'])
    add(int(r['Fieldvalues.StartAddr.Cpu'][1:],16),r['DataOrg'],C*R)
    for a in 'XY':
        if r[f'Axis{a}.DataSrc'].startswith('eRom'):
            add(int(r[f'Axis{a}.DataAddr.Cpu'][1:],16),r[f'Axis{a}.DataOrg'],C if a=='X' else R)
W=0x800
# A/B: predicted + exact local
for it in items.values():
    x,L=it['x'],it['L']
    if not (0<=x<len(cs)): it['how']='outside'; it['y']=None; continue
    y0=x+segdelta(x); it['y0']=y0; data=cs[x:x+L]
    if L>=8 and len(set(data))>2:
        lo=max(0,y0-W); best=None; i=cn.find(data,lo,y0+W+L)
        while i!=-1:
            if best is None or abs(i-y0)<abs(best-y0): best=i
            i=cn.find(data,i+1,y0+W+L)
        if best is not None: it['y']=best; it['how']='exact'; continue
    it['y']=None; it['how']=None
# C: anchors from exact items
anc=sorted((it['x'],it['y']-it['x']) for it in items.values() if it['how']=='exact')
ad=[d for _,d in anc]
keep=[anc[k] for k in range(len(anc)) if (k>0 and ad[k-1]==ad[k]) or (k+1<len(anc) and ad[k+1]==ad[k])]
ax=[a for a,_ in keep]; adl=[d for _,d in keep]
def hb_score(x,y,L,esz):
    a=cs[x:x+L]; b=cn[y:y+L]
    if len(b)<L or y<0: return -1
    n=L//esz; return sum(1 for i in range(n) if abs(a[i*esz]-b[i*esz])<=1)/max(1,n)
# D: place the rest
for it in items.values():
    if it['how'] in ('exact','outside'): continue
    x,L=it['x'],it['L']
    k=bisect.bisect_right(ax,x)-1; j=bisect.bisect_left(ax,x+L)
    dp=adl[k] if k>=0 else None; dn=adl[j] if j<len(ax) else None
    if dp is not None and dp==dn:
        y=x+dp; it['how']='aligned'
    else:
        cands=[d for d in (dp,dn) if d is not None]
        y=max((x+d for d in cands),key=lambda yy: hb_score(x,yy,L,it['esz']))
        it['how']='between-shift'
    it['y']=y
    it['same']= cn[y:y+L]==cs[x:x+L]
pickle.dump(items,open(sys.argv[6],'wb'))
c=collections.Counter((it['how'], it.get('same')) for it in items.values()); print("items:",len(items)); [print("  ",k,v) for k,v in sorted(c.items(),key=lambda kv:-kv[1])]
print("anchors:",len(keep))
