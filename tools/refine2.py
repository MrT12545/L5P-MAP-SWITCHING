import sys, pickle, collections
stock=open(sys.argv[1],'rb').read(); sotf=open(sys.argv[2],'rb').read()
CAL0=0x60000
cs=stock[CAL0-0x20000:0x200000-0x20000]; cn=sotf[CAL0+0x39FFE0:0x1FFFF0+0x39FFE0]
good=pickle.load(open(sys.argv[3],'rb'))
K=16
# piecewise delta segments: (start_x, delta, kind)
segs=[(0,good[0][1]-good[0][0])]
nbreak=0
for (a1,b1),(a2,b2) in zip(good,good[1:]):
    d1=b1-a1; d2=b2-a2
    if d1==d2: continue
    s0,s1=a1+K,a2
    if s1<s0: s0=s1=a2
    best=None; c1=0
    tot2=sum(1 for x in range(s0,s1) if 0<=x+d2<len(cn) and cs[x]==cn[x+d2])
    c2=tot2
    for t in range(s0,s1+1):
        # bytes [s0,t) use d1, [t,s1) use d2
        sc=c1+c2
        if best is None or sc>best[0]: best=(sc,t)
        if t<s1:
            x=t
            if 0<=x+d1<len(cn) and cs[x]==cn[x+d1]: c1+=1
            if 0<=x+d2<len(cn) and cs[x]==cn[x+d2]: c2-=1
    t=best[1]
    # align breakpoint to 2 bytes
    t-=t%2
    segs.append((t,d2)); nbreak+=1
pickle.dump(segs,open(sys.argv[4],'wb'))
print(f"{nbreak} shift points; segments {len(segs)}")
sizes=collections.Counter()
for (x,d),(x2,d2) in zip(segs,segs[1:]): sizes[d2-d]+=1
print("most common insert/delete sizes (bytes):",sizes.most_common(12))
