import sys, pickle, bisect
anch=sorted(pickle.load(open(sys.argv[1],'rb')))
# longest strictly increasing subsequence on y (x already sorted)
ys=[y for _,y in anch]; tails=[]; tidx=[]; prev=[-1]*len(ys)
for i,y in enumerate(ys):
    k=bisect.bisect_left(tails,y)
    if k==len(tails): tails.append(y); tidx.append(i)
    else: tails[k]=y; tidx[k]=i
    prev[i]=tidx[k-1] if k>0 else -1
seq=[]; i=tidx[-1]
while i!=-1: seq.append(anch[i]); i=prev[i]
seq.reverse()
pickle.dump(seq,open(sys.argv[2],'wb'))
tr=sum(1 for (x1,y1),(x2,y2) in zip(seq,seq[1:]) if y1-x1!=y2-x2)
print(f"anchors in: {len(anch)}  kept (monotonic chain): {len(seq)}  delta transitions: {tr}")
