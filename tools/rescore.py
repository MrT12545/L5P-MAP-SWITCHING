import sys, pickle, struct, math, bisect, collections
stock=open(sys.argv[1],'rb').read(); sotf=open(sys.argv[2],'rb').read()
items=pickle.load(open(sys.argv[3],'rb')); a16=pickle.load(open(sys.argv[4],'rb'))
CAL0=0x60000
cs=stock[CAL0-0x20000:0x200000-0x20000]; cn=sotf[CAL0+0x39FFE0:0x1FFFF0+0x39FFE0]
# all anchor deltas by position
pts=sorted([(x,y-x) for x,y in a16]+[(it['x'],it['y']-it['x']) for it in items.values() if it['how']=='exact'])
px=[p for p,_ in pts]
def dec(buf,off,esz,n):
    b=buf[off:off+esz*n]
    if len(b)<esz*n or off<0: return None
    if esz==4: return struct.unpack('>%df'%n,b)
    if esz==2: return struct.unpack('>%dH'%n,b)
    return tuple(b)
def sim(a,b):
    if b is None: return -1
    ok=0
    for x,y in zip(a,b):
        if not (isinstance(y,int) or math.isfinite(y)): continue
        if abs(x-y)<=0.1*max(abs(x),abs(y))+1e-6: ok+=1
    return ok/len(a)
moved=0; checked=0; low=0
for k,it in items.items():
    if it['how'] not in ('shift-resolved','aligned','edge') or it.get('same'): continue
    if it['how']!='shift-resolved':
        it['conf']='medium'; it['score']=None; continue
    n=it['L']//it['esz']
    if n<4: it['conf']='low' if it['how']=='shift-resolved' else 'medium'; continue
    checked+=1
    x=it['x']; a=dec(cs,x,it['esz'],n)
    lo=bisect.bisect_left(px,x-0x2000); hi=bisect.bisect_right(px,x+0x2000)
    deltas={d for _,d in pts[lo:hi]}|{it['y']-x}
    cur=sim(a,dec(cn,it['y'],it['esz'],n))
    best=max(((sim(a,dec(cn,x+d,it['esz'],n)),d) for d in deltas),key=lambda t:(t[0],-abs(x+t[1]-it['y'])))
    if best[0]>=0.5 and best[0]-cur>=0.25:
        it['y']=x+best[1]; it['how']+='+rescored'; moved+=1; it['score']=best[0]
    else: it['score']=cur
    it['conf']='high' if it['score']>=0.5 else ('medium' if it['how'].startswith('aligned') else 'low')
    if it['conf']=='low': low+=1
for it in items.values():
    if 'conf' not in it:
        it['conf']='high' if it['how']=='exact' or it.get('same') else ('medium' if it['how'] in ('aligned','edge') else 'low')
pickle.dump(items,open(sys.argv[5],'wb'))
print(f"re-scored {checked} changed multi-value items, moved {moved}")
print("confidence:",collections.Counter(it['conf'] for it in items.values()))
