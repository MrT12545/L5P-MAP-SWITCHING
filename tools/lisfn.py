import bisect
def lis_pairs(pairs):
    """pairs: list of (x, y, *rest) sorted by x; keep longest chain strictly increasing in y."""
    pairs=sorted(pairs); ys=[p[1] for p in pairs]; tails=[]; tidx=[]; prev=[-1]*len(ys)
    for i,y in enumerate(ys):
        k=bisect.bisect_left(tails,y)
        if k==len(tails): tails.append(y); tidx.append(i)
        else: tails[k]=y; tidx[k]=i
        prev[i]=tidx[k-1] if k>0 else -1
    out=[]; i=tidx[-1] if tidx else -1
    while i!=-1: out.append(pairs[i]); i=prev[i]
    return out[::-1]
