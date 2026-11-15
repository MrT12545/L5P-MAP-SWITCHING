import sys,csv,collections,pickle,re,bisect,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import olscsv as O, ez_select as E
D=sys.argv[1]
def L(p):
    d={}
    for r in O.load(p): d.setdefault(r['Name'],r)
    return d
M44=L(D+'sotf44/WinOLS_maplist_SOTF_9844.csv'); M43=L(D+'sotf/WinOLS_maplist_SOTF_9843.csv')
R44={r['Name']:r for r in csv.DictReader(open(D+'sotf44/relocation_review_9844.csv'))}; R43={r['Name']:r for r in csv.DictReader(open(D+'sotf/relocation_review.csv'))}
fix43,drop43=pickle.load(open(D+'sotf/ez_fix.pkl','rb'))
mp=pickle.load(open(D+'sotf44/codemap43to44.pkl','rb')); h=lambda s:int(s.lstrip('$'),16); X=0x39FFE0
b44=open(D+'sotf44/sotf44.bin','rb').read(); b43=open(D+'sotf/sotf.bin','rb').read()
W={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}; CAL0=0x3FFFE0
def a43(n): return fix43.get(n,h(M43[n]['Fieldvalues.StartAddr']))
def size(n): m=M43[n]; return int(m['Columns'])*int(m['Rows'])*W.get(m['DataOrg'],1)
good43=[n for n in M43 if n in M44 and R43.get(n,{}).get('Confidence') in('high','medium') and n not in drop43 and M43[n]['DataOrg'] in W and M43[n]['Fieldvalues.StartAddr'].startswith('$') and h(M43[n]['Fieldvalues.StartAddr'])>=CAL0]
# ---- anchors
A={}
# 1 code refs confirmed by 4-byte content equality
for c3,c4 in mp.items():
    f3,f4=c3+X,c4+X
    if b43[f3:f3+4]==b44[f4:f4+4]: A[f3]=(f4,'code')
# 2 unique non-trivial content
cal44=b44[CAL0:]
for n in good43:
    a=a43(n); sz=size(n); d=b43[a:a+sz]
    if sz<12 or len(set(d))<5: continue
    i=cal44.find(d)
    if i<0 or cal44.find(d,i+1)>=0: continue
    A[a]=(i+CAL0,'content')
# 3 OS truth
for n,r in R44.items():
    if r['Placement'].startswith('SOTF OS') and n in M43: A[a43(n)]=(h(M44[n]['Fieldvalues.StartAddr']),'os')
pts=sorted((k,v[0]-k,v[1]) for k,v in A.items())
# local agreement filter: keep anchor if its delta equals delta of a neighbour within 3 positions (or it's os)
keep=[]
for i,(k,d,s) in enumerate(pts):
    nb=[pts[j][1] for j in range(max(0,i-3),min(len(pts),i+4)) if j!=i]
    if s=='os' or nb.count(d)>=1: keep.append((k,d,s))
print("anchors:",len(pts),"after local filter:",len(keep),collections.Counter(s for *_,s in keep))
ks=[k for k,*_ in keep]
def place(n):
    a=a43(n); sz=size(n); ref=b43[a:a+sz]
    if a in A and A[a][1]=='os': return A[a][0],'os'
    i=bisect.bisect_right(ks,a)-1
    lo=keep[i] if i>=0 else None
    j=bisect.bisect_left(ks,a+1); hi=keep[j] if j<len(keep) else None
    if lo and lo[0]==a: return a+lo[1],'anchor-'+lo[2]
    if lo and hi and lo[1]==hi[1]: return a+lo[1],'bracketed'
    cands=[x[1] for x in (lo,hi) if x]
    m=[d for d in cands if b44[a+d:a+d+sz]==ref]
    if len(set(m))==1: return a+m[0],'content-resolved'
    return None,'unresolved (layout changes between 9843 and 9844 here)'
if __name__=='__main__':
    U=set()
    for rv in (R43,R44): U|={n for n,r in rv.items() if E.selected(n,r['Data vs stock']=='changed','high')}
    out={}; st=collections.Counter(); cmp=collections.Counter()
    for n in sorted(U):
        if n not in good43: out[n]=(None,'not placed in 9843 either'); st['no 9843']+=1; continue
        a4,how=place(n); out[n]=(a4,how); st[how]+=1
        old=h(M44[n]['Fieldvalues.StartAddr'])
        if a4 is not None: cmp[('same as old' if a4==old else 'DIFFERENT from old', R44[n]['Placement'])]+=1
    pickle.dump(out,open(D+'sotf44/place44_selected.pkl','wb'))
    print(st); print(cmp)
    print("injection unresolved:",[n for n,(a,h_) in out.items() if a is None and E.group(n).startswith('Injection')])
