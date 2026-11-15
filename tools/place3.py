import sys, pickle, bisect, collections
stock=open(sys.argv[1],'rb').read(); sotf=open(sys.argv[2],'rb').read()
items=pickle.load(open(sys.argv[3],'rb')); a16=pickle.load(open(sys.argv[4],'rb'))
CAL0=0x60000
cs=stock[CAL0-0x20000:0x200000-0x20000]; cn=sotf[CAL0+0x39FFE0:0x1FFFF0+0x39FFE0]
pts={}
for x,y in a16: pts[x]=(y-x,16)
for it in items.values():
    if it['how']=='exact': pts[it['x']]=(it['y']-it['x'],it['L'])
pts[0x1FFA00-CAL0]=(0,16)
sys.path.insert(0,__import__('os').path.dirname(__file__)); from lisfn import lis_pairs
anc=[(x,d,L) for x,(d,L) in pts.items()]; anc=[(x,y-x,L) for x,y,L in lis_pairs([(x,x+d,L) for x,d,L in anc])]
dl=[d for _,d,_ in anc]
anc=[anc[k] for k in range(len(anc)) if (k>0 and dl[k-1]==dl[k]) or (k+1<len(anc) and dl[k+1]==dl[k])]
TAIL=0x1FFA00-CAL0
anc=[a for a in anc if a[0]<TAIL]+[(TAIL,0,16),(len(cs)-16,0,16)]
ax=[a for a,_,_ in anc]; ad=[d for _,d,_ in anc]; aL=[L for _,_,L in anc]
print("combined anchors:",len(anc))
bp_cache={}
def breakpoint(k):
    # best shift point t (stock coords) between anchor k and k+1
    if k in bp_cache: return bp_cache[k]
    x1,d1,L1=anc[k]; x2,d2,_=anc[k+1]
    s0,s1=x1+L1,x2
    if s1<=s0: bp_cache[k]=x2; return x2
    eq1=[0]*(s1-s0+1); 
    c1=0; c2=sum(1 for x in range(s0,s1) if 0<=x+d2<len(cn) and cs[x]==cn[x+d2])
    best=(c1+c2,s0)
    for x in range(s0,s1):
        if 0<=x+d1<len(cn) and cs[x]==cn[x+d1]: c1+=1
        if 0<=x+d2<len(cn) and cs[x]==cn[x+d2]: c2-=1
        if c1+c2>best[0]: best=(c1+c2,x+1)
    bp_cache[k]=best[1]; return best[1]
def hb(x,y,L,esz):
    a=cs[x:x+L]; b=cn[y:y+L]
    if y<0 or len(b)<L: return -1
    n=max(1,L//esz); return sum(1 for i in range(L//esz) if abs(a[i*esz]-b[i*esz])<=1)/n
st=collections.Counter()
for it in items.values():
    if it['how'] in ('exact','outside'): st[it['how']]+=1; continue
    x,L=it['x'],it['L']
    k=bisect.bisect_right(ax,x)-1; j=bisect.bisect_left(ax,x+L)
    if k<0 or j>=len(ax):
        d=ad[k] if k>=0 else ad[j]
        it['y']=x+d; it['how']='edge'; it['same']=cn[it['y']:it['y']+L]==cs[x:x+L]; st[('edge',it['same'])]+=1; continue
    if ad[k]==ad[j]:
        it['y']=x+ad[k]; it['how']='aligned'
    else:
        # anchors k..j may have several shifts; walk them
        d=ad[k]
        for q in range(k,j):
            if ad[q]!=ad[q+1]:
                t=breakpoint(q)
                if x>=t: d=ad[q+1]
                elif x+L>t:   # straddles
                    d=max((ad[q],ad[q+1]),key=lambda dd: hb(x,x+dd,L,it['esz'])); it['straddle']=True
        it['y']=x+d; it['how']='shift-resolved'
    it['same']=cn[it['y']:it['y']+L]==cs[x:x+L]
    st[(it['how'],it['same'],it.get('straddle',False))]+=1
pickle.dump(items,open(sys.argv[5],'wb'))
for k,v in sorted(st.items(),key=lambda kv:-kv[1]): print("  ",k,v)
