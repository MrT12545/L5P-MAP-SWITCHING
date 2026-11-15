# Relocate items placed in cal A (9843) into cal B (9844). Items keyed like items5 (stock_cpu, L) with 'y' = position in A (cal-relative)
import sys, pickle, bisect, collections, struct, math
A=open(sys.argv[1],'rb').read(); Bb=open(sys.argv[2],'rb').read()
itemsA=pickle.load(open(sys.argv[3],'rb')); anch=pickle.load(open(sys.argv[4],'rb')); out=sys.argv[5]
O=0x3FFFE0; END=0x59FFD0; ca=A[O:END]; cb=Bb[O:END]
W=0x800
items={}
for k,it in itemsA.items():
    if it.get('y') is None: continue
    items[k]=dict(x=it['y'],L=it['L'],esz=it['esz'],confA=it['conf'])
# exact matches near anchor-predicted spot
ax0=[x for x,_ in anch]; ad0=[y-x for x,y in anch]
def pred(x):
    k=bisect.bisect_right(ax0,x)-1; return x+(ad0[k] if k>=0 else ad0[0])
for it in items.values():
    x,L=it['x'],it['L']; data=ca[x:x+L]; y0=pred(x); it['y']=None; it['how']=None
    if L>=8 and len(set(data))>2:
        best=None; i=cb.find(data,max(0,y0-W),y0+W+L)
        while i!=-1:
            if best is None or abs(i-y0)<abs(best-y0): best=i
            i=cb.find(data,i+1,y0+W+L)
        if best is not None: it['y']=best; it['how']='exact'
pts={x:(y-x,16) for x,y in anch}
for it in items.values():
    if it['how']=='exact': pts[it['x']]=(it['y']-it['x'],it['L'])
TAIL=0x1FFA00-0x60000
sys.path.insert(0,__import__('os').path.dirname(__file__)); from lisfn import lis_pairs
an=[(x,x+d,L) for x,(d,L) in pts.items() if x<TAIL]; an=[(x,y-x,L) for x,y,L in lis_pairs(an)]; dl=[d for _,d,_ in an]
an=[an[k] for k in range(len(an)) if (k>0 and dl[k-1]==dl[k]) or (k+1<len(an) and dl[k+1]==dl[k])]+[(TAIL,0,16),(len(ca)-16,0,16)]
ax=[a for a,_,_ in an]; ad=[d for _,d,_ in an]
cache={}
def bp(q):
    if q in cache: return cache[q]
    x1,d1,L1=an[q]; x2,d2,_=an[q+1]; s0,s1=x1+L1,x2
    if s1<=s0: cache[q]=x2; return x2
    c1=0; c2=sum(1 for x in range(s0,s1) if 0<=x+d2<len(cb) and ca[x]==cb[x+d2]); best=(c1+c2,s0)
    for x in range(s0,s1):
        if 0<=x+d1<len(cb) and ca[x]==cb[x+d1]: c1+=1
        if 0<=x+d2<len(cb) and ca[x]==cb[x+d2]: c2-=1
        if c1+c2>best[0]: best=(c1+c2,x+1)
    cache[q]=best[1]; return best[1]
def hb(x,y,L,esz):
    a=ca[x:x+L]; b=cb[y:y+L]
    if y<0 or len(b)<L: return -1
    n=max(1,L//esz); return sum(1 for i in range(L//esz) if abs(a[i*esz]-b[i*esz])<=1)/n
for it in items.values():
    if it['how']=='exact': it['same']=True; continue
    x,L=it['x'],it['L']; k=bisect.bisect_right(ax,x)-1; j=bisect.bisect_left(ax,x+L)
    if k<0 or j>=len(ax): d=ad[max(k,0)]; it['how']='edge'
    elif ad[k]==ad[j]: d=ad[k]; it['how']='aligned'
    else:
        d=ad[k]
        for q in range(k,j):
            if ad[q]!=ad[q+1]:
                t=bp(q)
                if x>=t: d=ad[q+1]
                elif x+L>t: d=max((ad[q],ad[q+1]),key=lambda dd: hb(x,x+dd,L,it['esz']))
        it['how']='shift-resolved'
    it['y']=x+d; it['same']=cb[it['y']:it['y']+L]==ca[x:x+L]
# neighbour upgrade (same rule as before)
for it in items.values(): it['conf']='high' if it['how']=='exact' or it['same'] else ('medium' if it['how'] in ('aligned','edge') else 'low')
for rnd in range(4):
    lst=sorted((it['x'],k) for k,it in items.items())
    hi=[(items[k]['x'],items[k]['y']-items[k]['x'],items[k]['L']) for _,k in lst if items[k]['conf']=='high']; hx=[h[0] for h in hi]; up=0
    for x,k in lst:
        it=items[k]
        if it['conf']=='high': continue
        i=bisect.bisect_left(hx,x)-1; j=bisect.bisect_right(hx,x)
        while i>=0 and hi[i][0]+hi[i][2]>x: i-=1
        while j<len(hi) and hi[j][0]<x+it['L']: j+=1
        if i<0 or j>=len(hi) or hi[i][1]!=hi[j][1]: continue
        if x-(hi[i][0]+hi[i][2])>0x40 or hi[j][0]-(x+it['L'])>0x40: continue
        it['y']=x+hi[i][1]; it['conf']='high'; it['how']+='+neighbours'; up+=1
    if not up: break
pickle.dump(items,open(out,'wb'))
print("A->B anchors:",len(an)," placement:",collections.Counter(it['how'].split('+')[0] for it in items.values()),
      " conf:",collections.Counter(it['conf'] for it in items.values()))
