import csv,bisect,collections,glob,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ez_select as E
csv.field_size_limit(1<<30)
h=lambda s:int(s.lstrip('$'),16)
def run(review,other):
    rv={r['Name']:r for r in csv.DictReader(open(review))}; ro={r['Name']:r for r in csv.DictReader(open(other))}
    U=set()
    for x in (rv,ro): U|={n for n,r in x.items() if E.selected(n,r['Data vs stock']=='changed','high')}
    anchor=sorted((h(r['Stock CPU (P1B)']),h(r['SOTF CPU'])-h(r['Stock CPU (P1B)'])) for r in rv.values()
                  if r['Confidence']=='high' and r['Placement'].startswith(('aligned','agree')) and r['Stock CPU (P1B)'].startswith('$'))
    ks=[p[0] for p in anchor]
    res={}
    for n in U:
        r=rv.get(n)
        if not r or r['Confidence'] not in('high','medium') or not r['Stock CPU (P1B)'].startswith('$'): continue
        s=h(r['Stock CPU (P1B)']); d=h(r['SOTF CPU'])-s
        i=bisect.bisect_left(ks,s); lo=anchor[i-1] if i>0 else None; hi=anchor[i] if i<len(anchor) else None
        ok = (lo and lo[1]==d) or (hi and hi[1]==d) or r['Placement'].startswith(('aligned','agree','SOTF OS','exact'))
        # between two anchors, a delta between their deltas is plausible (insertions)
        if not ok and lo and hi and min(lo[1],hi[1])<=d<=max(lo[1],hi[1]): ok='between'
        res[n]=(ok,r['Placement'],d,lo,hi)
    return res
if __name__=='__main__':
    res=run(sys.argv[1],sys.argv[2])
    c=collections.Counter(('ok' if v[0] is True else v[0] or 'SUSPECT') for v in res.values()); print(c)
    sus=[(n,v) for n,v in res.items() if not v[0]]
    print(collections.Counter(E.group(n) for n,_ in sus))
    for n,v in sorted(sus)[:40]: print(f"  {n[:50]:50s} {v[1]:28s} d={v[2]:+#x} lo={v[3][1] if v[3] else 0:+#x} hi={v[4][1] if v[4] else 0:+#x}")
