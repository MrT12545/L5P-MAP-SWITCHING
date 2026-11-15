# keep anchors consistent with forced points: inside each forced interval keep LIS of anchors whose y lies inside the interval's y-range
import sys, pickle
sys.path.insert(0,__import__('os').path.dirname(__file__)); from lisfn import lis_pairs
anch=pickle.load(open(sys.argv[1],'rb')); forced=sorted(pickle.load(open(sys.argv[2],'rb'))); out=sys.argv[3]
bounds=[(-1,-1)]+forced+[(10**9,10**9)]
keep=list(forced)
for (x0,y0),(x1,y1) in zip(bounds,bounds[1:]):
    seg=[(x,y) for x,y in anch if x0<x<x1 and y0<y<y1]
    keep+=lis_pairs(seg) if seg else []
keep=sorted(set(keep)); pickle.dump(keep,open(out,'wb'))
print(f"forced {len(forced)}; anchors kept {len(keep)} of {len(anch)}")
