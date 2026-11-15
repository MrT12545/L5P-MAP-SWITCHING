import csv,sys,os,bisect,pickle
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import neighcheck as N
csv.field_size_limit(1<<30)
review,other,maplist,sotfbin,out=sys.argv[1:6]
stock=open(sys.argv[6] if len(sys.argv)>6 else '/tmp/claude-0/-home-user/6f9e1fc2-7659-5bcc-a119-4e79dd39c9cd/scratchpad/ols_extract/E41_L5P_original.bin','rb').read()
b=open(sotfbin,'rb').read(); h=lambda s:int(s.lstrip('$'),16)
M={}
for r in csv.DictReader(open(maplist,newline='',encoding='latin1'),delimiter=';'): M.setdefault(r['Name'],r)
W={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}
def span(r): return int(r['Columns'])*int(r['Rows'])*W.get(r['DataOrg'],1)
iv=sorted((h(r['Fieldvalues.StartAddr']),h(r['Fieldvalues.StartAddr'])+span(r),n) for n,r in M.items() if r['Fieldvalues.StartAddr'].startswith('$') and h(r['Fieldvalues.StartAddr'])>0)
starts=[x[0] for x in iv]
def overlaps(a,e,me):
    i=bisect.bisect_left(starts,a)
    return [x[2] for x in iv[max(0,i-30):i+30] if x[2]!=me and x[0]<e and a<x[1]]
res=N.run(review,other); fix={}; drop=[]
for n,v in sorted(res.items()):
    if v[0] is True or v[1]=='exact': continue
    r=M[n]; sz=span(r); s=v[2]; st_cpu=None
    rv={x['Name']:x for x in csv.DictReader(open(review))}[n]; sc=h(rv['Stock CPU (P1B)'])
    sd=stock[sc-0x20000:sc-0x20000+sz]
    def score(d):
        a=sc+d+0x39FFE0; return sum(x==y for x,y in zip(sd,b[a:a+sz]))/sz, overlaps(a,a+sz,n)
    cur=score(v[2]); cands=[(d,)+score(d) for d in {x[1] for x in (v[3],v[4]) if x} if d!=v[2]]
    if not cands: drop.append(n); continue
    if not cur[1] and (cur[0]>=0.5 or v[0]=='between' and cur[0]>=0.3):
        print(f"{n[:46]:46s} keep d={v[2]:+#x} eq={cur[0]:.2f}"); continue
    if not cands: drop.append(n); continue
    best=max(cands,key=lambda c:(not c[2],c[1]))
    print(f"{n[:46]:46s} cur d={v[2]:+#x} eq={cur[0]:.2f} ov={cur[1][:2]} | best d={best[0]:+#x} eq={best[1]:.2f} ov={best[2][:2]}")
    if not best[2] and (best[1]>=max(0.5,cur[0]-0.05) or (cur[1] and best[1]>=0.3)): fix[n]=sc+best[0]+0x39FFE0
    else: drop.append(n)
pickle.dump((fix,drop),open(out,'wb')); print("fix:",len(fix),"drop:",drop)
