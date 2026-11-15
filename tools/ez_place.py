# Unified placement: stock P1B definition -> target bin, using ECU code references (primary), HPT OS records, verified content anchors.
import sys,csv,collections,pickle,bisect,os,glob
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import olscsv as O
D=sys.argv[1]
SB=open(D+'ols_extract/E41_L5P_original.bin','rb').read()
W={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}; h=lambda s:int(s.lstrip('$'),16)
ST={}
for r in O.load(glob.glob('/root/.claude/uploads/*/1b5de558-*.csv')[0]):
    if r['Name'] in ST and not ST[r['Name']]['FolderName'].startswith('"NEW'): continue
    ST[r['Name']]=r
sfile=lambda c:c-0x20000
def build(tag,binp,maplist,review,codemap,extra_aligned):
    TB=open(binp,'rb').read(); tfile=lambda c:c+0x39FFE0
    ML={}
    for r in O.load(maplist): ML.setdefault(r['Name'],r)
    RV={r['Name']:r for r in csv.DictReader(open(review))}
    mp=pickle.load(open(codemap,'rb'))
    A={}
    for s,t in mp.items(): A[s]=(t,'code')
    for n,r in RV.items():
        if r['Placement'].startswith('SOTF OS') and n in ST: A[h(ST[n]['Fieldvalues.StartAddr.Cpu'])]=(h(ML[n]['Fieldvalues.StartAddr'])-0x39FFE0,'os')
        elif extra_aligned and r['Placement']=='aligned' and r['Confidence']=='high' and n in ST and r['Stock CPU (P1B)'].startswith('$'):
            A.setdefault(h(r['Stock CPU (P1B)']),(h(r['SOTF CPU']),'aligned'))
    # unique content anchors
    cal=TB[0x3FFFE0:]
    for n,r in ST.items():
        if r['DataOrg'] not in W or not r['Fieldvalues.StartAddr.Cpu'].startswith('$'): continue
        s=h(r['Fieldvalues.StartAddr.Cpu']); sz=int(r['Columns'])*int(r['Rows'])*W[r['DataOrg']]
        if sz<16 or s<0x60000: continue
        d=SB[sfile(s):sfile(s)+sz]
        if len(set(d))<5: continue
        i=cal.find(d)
        if i>=0 and cal.find(d,i+1)<0: A.setdefault(s,(i+0x3FFFE0-0x39FFE0,'content'))
    pts=sorted((s,t-s,k) for s,(t,k) in A.items())
    keep=[]
    for i,(s,d,k) in enumerate(pts):
        nb=[pts[j][1] for j in range(max(0,i-3),min(len(pts),i+4)) if j!=i]
        if k=='os' or d in nb or SB[sfile(s):sfile(s)+4]==TB[tfile(s+d):tfile(s+d)+4]: keep.append((s,d,k))
    ks=[x[0] for x in keep]; KD={x[0]:x for x in keep}
    def place(s,sz,old=None):
        """evidence-based decision; old = previous relocation's target cpu (or None)"""
        ref=SB[sfile(s):sfile(s)+sz]; triv=len(set(ref))<3
        eq=lambda t: t is not None and TB[tfile(t):tfile(t)+sz]==ref
        if s in KD and KD[s][2]=='os': return s+KD[s][1],'os'
        code=s+mp[s] -s if s in mp else None
        if code is not None: code=mp[s]
        i=bisect.bisect_right(ks,s-1)-1; j=bisect.bisect_left(ks,s+sz)
        lo=keep[i] if i>=0 else None; hi=keep[j] if j<len(keep) else None
        br=s+lo[1] if lo and hi and lo[1]==hi[1] else None
        nbd={x[1] for x in (lo,hi) if x}
        if code is not None:
            if old is not None and code==old: return code,'code+relocation agree'
            if br is not None and code==br: return code,'code+neighbours agree'
            if eq(code) and not triv and not eq(old): return code,'code+content'
            if old is None and (code-s) in nbd: return code,'code'
            if eq(old) and not triv and not eq(code): return None,'conflict code vs content'
            if br is not None and old==br: return old,'relocation+neighbours agree'
            return None,'conflict code vs relocation'
        if old is not None and br is not None and old==br: return old,'relocation+neighbours agree'
        if br is not None and old is None: return br,'neighbours'
        if br is not None and old is not None:
            if eq(br) and not eq(old): return br,'neighbours+content'
            if eq(old) and not eq(br) and not triv: return old,'relocation+content'
            return None,'conflict relocation vs neighbours'
        if old is not None and (old-s) in nbd and (eq(old) and not triv): return old,'relocation+content'
        if old is not None and (old-s) in nbd and extra_aligned: return old,'relocation (one-side neighbour)'
        m=[d for d in nbd if eq(s+d)]
        if len(m)==1 and not triv: return s+m[0],'content'
        return None,'unresolved'
    def _unused(s,sz):
        if s in KD: return s+KD[s][1],KD[s][2]
        i=bisect.bisect_right(ks,s)-1; j=bisect.bisect_left(ks,s+sz)
        lo=keep[i] if i>=0 else None; hi=keep[j] if j<len(keep) else None
        inside=keep[i+1:j]
        if lo and hi and lo[1]==hi[1] and all(x[1]==lo[1] for x in inside): return s+lo[1],'bracketed'
        ref=SB[sfile(s):sfile(s)+sz]
        cands={x[1] for x in (lo,hi) if x}|{x[1] for x in inside}
        m=[d for d in cands if TB[tfile(s+d):tfile(s+d)+sz]==ref]
        if len(m)==1: return s+m[0],'content'
        return None,'unresolved'
    res={}
    for n,r in ST.items():
        if r['DataOrg'] not in W or not r['Fieldvalues.StartAddr.Cpu'].startswith('$'): continue
        s=h(r['Fieldvalues.StartAddr.Cpu'])
        if s<0x60000: continue
        sz=int(r['Columns'])*int(r['Rows'])*W[r['DataOrg']]
        old=None
        if n in RV and RV[n]['SOTF CPU'].startswith('$') and RV[n]['Confidence']!='low': old=h(RV[n]['SOTF CPU'])
        t,how=place(s,sz,old)
        ax={}
        for w in 'XY':
            if r[f'Axis{w}.DataSrc'] in('eRom','eRomDataIndex') and r[f'Axis{w}.DataOrg'] in W:
                n_=int(r['Columns'] if w=='X' else r['Rows']); sa=h(r[f'Axis{w}.DataAddr.Cpu'])
                oa=None
                if n in ML and ML[n][f'Axis{w}.DataAddr'].startswith('$') and old is not None: oa=h(ML[n][f'Axis{w}.DataAddr'])-0x39FFE0
                ax[w]=place(sa,n_*W[r[f'Axis{w}.DataOrg']],oa) if sa>=0x60000 else (None,'bad')
        changed=None
        if t is not None: changed = SB[sfile(s):sfile(s)+sz]!=TB[tfile(t):tfile(t)+sz]
        res[n]=dict(t=t,how=how,ax=ax,changed=changed,s=s,sz=sz)
    print(tag,"anchors kept",len(keep),collections.Counter(k for *_,k in keep),"| placements:",collections.Counter(v['how'] for v in res.values()))
    return res
P43=build('9843',D+'sotf/sotf.bin',D+'sotf/WinOLS_maplist_SOTF_9843.csv',D+'sotf/relocation_review.csv',D+'stockos/map_stock_43.pkl',True)
P44=build('9844',D+'sotf44/sotf44.bin',D+'sotf44/WinOLS_maplist_SOTF_9844.csv',D+'sotf44/relocation_review_9844.csv',D+'stockos/map_stock_44_final.pkl',False)
pickle.dump((P43,P44),open(D+'stockos/placements.pkl','wb'))
# compare with old placements
for tag,P,rv in (('9843',P43,'sotf/relocation_review.csv'),('9844',P44,'sotf44/relocation_review_9844.csv')):
    R={r['Name']:r for r in csv.DictReader(open(D+rv))}; c=collections.Counter()
    for n,v in P.items():
        if n in R and v['t'] is not None and R[n]['SOTF CPU'].startswith('$'): c[(R[n]['Confidence'],'same' if h(R[n]['SOTF CPU'])==v['t'] else 'diff')]+=1
    print(tag,"vs old:",sorted(c.items()))
print("P/N 43:",hex(P43['KtDTRC_M_EngTrqReqForRPM']['t']+0x39FFE0),P43['KtDTRC_M_EngTrqReqForRPM']['how']," 44:",hex(P44['KtDTRC_M_EngTrqReqForRPM']['t']+0x39FFE0) if P44['KtDTRC_M_EngTrqReqForRPM']['t'] else None,P44['KtDTRC_M_EngTrqReqForRPM']['how'])
