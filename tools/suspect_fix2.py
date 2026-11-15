# 9844: candidates from stock-neighbour deltas AND 9843-neighbour deltas; score vs stock data and vs 9843 data
import csv,sys,os,bisect,pickle,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import neighcheck as N
csv.field_size_limit(1<<30); h=lambda s:int(s.lstrip('$'),16)
D='/tmp/claude-0/-home-user/6f9e1fc2-7659-5bcc-a119-4e79dd39c9cd/scratchpad/'
stock=open(D+'ols_extract/E41_L5P_original.bin','rb').read(); b44=open(D+'sotf44/sotf44.bin','rb').read(); b43=open(D+'sotf/sotf.bin','rb').read()
def L(p):
    d={}
    for r in csv.DictReader(open(p,newline='',encoding='latin1'),delimiter=';'): d.setdefault(r['Name'],r)
    return d
M44=L(D+'sotf44/WinOLS_maplist_SOTF_9844.csv'); M43=L(D+'sotf/WinOLS_maplist_SOTF_9843.csv')
R44={r['Name']:r for r in csv.DictReader(open(D+'sotf44/relocation_review_9844.csv'))}; R43={r['Name']:r for r in csv.DictReader(open(D+'sotf/relocation_review.csv'))}
fix43,drop43=pickle.load(open(D+'sotf/ez_fix.pkl','rb'))
W={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}
span=lambda r:int(r['Columns'])*int(r['Rows'])*W.get(r['DataOrg'],1)
iv=sorted((h(r['Fieldvalues.StartAddr']),h(r['Fieldvalues.StartAddr'])+span(r),n) for n,r in M44.items() if r['Fieldvalues.StartAddr'].startswith('$') and h(r['Fieldvalues.StartAddr'])>0 and n in R44 and R44[n]['Confidence']=='high' and R44[n]['Placement'] in ('agree','SOTF OS table','SOTF OS code reference'))
starts=[x[0] for x in iv]
def overlaps(a,e,me):
    i=bisect.bisect_left(starts,a); return [x[2] for x in iv[max(0,i-40):i+40] if x[2]!=me and x[0]<e and a<x[1]]
# 9843->9844 anchors (file offsets)
A=sorted((h(M43[n]['Fieldvalues.StartAddr']),h(M44[n]['Fieldvalues.StartAddr'])-h(M43[n]['Fieldvalues.StartAddr'])) for n,r in R44.items()
         if r['Placement']=='agree' and r['Confidence']=='high' and n in R43 and R43[n]['Confidence']=='high' and R43[n]['Placement'].startswith('aligned') and n in M43 and n in M44)
ak=[x[0] for x in A]
res=N.run(D+'sotf44/relocation_review_9844.csv',D+'sotf/relocation_review.csv'); fix={}; drop=[]; log=[]
def ok43(n): return n in R43 and R43[n]['Confidence'] in('high','medium') and n not in drop43
for n,v in sorted(res.items()):
    if v[0] is True or v[1]=='exact': continue
    r=M44[n]; sz=span(r); sc=h(R44[n]['Stock CPU (P1B)']); sd=stock[sc-0x20000:sc-0x20000+sz]
    d43=None
    if ok43(n):
        a43=fix43.get(n,h(M43[n]['Fieldvalues.StartAddr'])); d43=b43[a43:a43+sz]
    cands={h(r['Fieldvalues.StartAddr'])}
    for x in (v[3],v[4]):
        if x: cands.add(sc+x[1]+0x39FFE0)
    struct_ok=False
    if d43 is not None:
        i=bisect.bisect_left(ak,a43); nb=[a43+A[j][1] for j in (i-1,i) if 0<=j<len(A)]
        cands|=set(nb)
        cur_a0=h(r['Fieldvalues.StartAddr'])
        struct_ok = len(nb)==2 and nb[0]==nb[1]==cur_a0 and not overlaps(cur_a0,cur_a0+sz,n)
    sc_=[]
    for a in cands:
        cur=b44[a:a+sz]
        es=sum(x==y for x,y in zip(sd,cur))/sz; e3=sum(x==y for x,y in zip(d43,cur))/sz if d43 is not None else 0
        sc_.append((max(es,e3),es,e3,a,overlaps(a,a+sz,n)))
    good=[c for c in sc_ if not c[4]]
    best=max(good,key=lambda c:c[0]) if good else None
    cur_a=h(r['Fieldvalues.StartAddr'])
    if struct_ok: log.append((n,'keep-structural',0,0)); continue
    if best and best[0]>=0.6:
        if best[3]!=cur_a: fix[n]=best[3]
        log.append((n,'keep' if best[3]==cur_a else 'moved',round(best[1],2),round(best[2],2)))
    else: drop.append(n); log.append((n,'drop',best and round(best[1],2),best and round(best[2],2)))
pickle.dump((fix,drop),open(D+'sotf44/ez_fix.pkl','wb'))
print("9843->9844 anchors:",len(A)); print(collections.Counter(x[1] for x in log))
import ez_select as E
print("dropped by group:",collections.Counter(E.group(n) for n in drop))
print("injection drops:",[x for x in log if x[1]=='drop' and E.group(x[0]).startswith('Injection')])
