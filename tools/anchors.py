import sys, collections, pickle
s=open(sys.argv[1],'rb').read(); n=open(sys.argv[2],'rb').read()
K=32
idx=collections.defaultdict(list)
for i in range(0,len(n)-K,4):
    w=n[i:i+K]
    if len(set(w))<10: continue
    idx[w].append(i)
pairs=[]
for i in range(0,len(s)-K,16):
    w=s[i:i+K]
    if len(set(w))<10: continue
    hits=idx.get(w)
    if hits and len(hits)==1: pairs.append((i,hits[0]))
pickle.dump(pairs,open(sys.argv[3],'wb'))
# run-length by delta along stock offset
runs=[];cur=None
for so,no in pairs:
    d=no-so
    if cur and d==cur[2] and so-cur[1]<=0x2000: cur[1]=so
    else:
        if cur: runs.append(tuple(cur))
        cur=[so,so,d]
runs.append(tuple(cur))
big=[r for r in runs if r[1]-r[0]>=0x800]
print(len(pairs),"unique anchors;",len(big),"runs >=2KB")
for a,b,d in big: print(f"  stock {a:#08x}-{b+K:#08x} ({(b+K-a)//1024:5d}K)  -> sotf {a+d:#08x}  delta {d:+#x}")
