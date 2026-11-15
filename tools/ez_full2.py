import sys,csv,struct,re,math,collections,pickle,glob,os,bisect
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ez_select as E, olscsv as O
csv.field_size_limit(1<<30)
D=sys.argv[1]; X=0x39FFE0
SB=open(D+'ols_extract/E41_L5P_original.bin','rb').read(); sfile=lambda c:c-0x20000
ST={}
for r in O.load(glob.glob('/root/.claude/uploads/*/1b5de558-*.csv')[0]):
    if r['Name'] in ST and not ST[r['Name']]['FolderName'].startswith('"NEW'): continue
    ST[r['Name']]=r
P43,P44=pickle.load(open(D+'stockos/placements.pkl','rb')); G=pickle.load(open(D+'stockos/gap_43_44.pkl','rb'))
B43=open(D+'sotf/sotf.bin','rb').read(); B44=open(D+'sotf44/sotf44.bin','rb').read()
W={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}; h=lambda s:int(s.lstrip('$'),16)
STRONG={'os','code+relocation agree','code+neighbours agree','code+content','relocation+neighbours agree','neighbours+content','relocation+content','neighbours','code','content','relocation (one-side neighbour)'}
def dec43(s,sz,how_t):
    t,how=how_t
    return (t,how) if t is not None and how in STRONG else (None,how)
import bisect as _bs
_ga=sorted((a,b-a) for a,b in G.items())
_ga=[x for i,x in enumerate(_ga) if any(_ga[j][1]==x[1] for j in range(max(0,i-3),min(len(_ga),i+4)) if j!=i)]
_gk=[x[0] for x in _ga]
def via43(t43,sz):
    ref=B43[t43+X:t43+X+sz]; i=_bs.bisect_right(_gk,t43-1)-1; j=_bs.bisect_left(_gk,t43+sz)
    lo=_ga[i] if i>=0 else None; hi=_ga[j] if j<len(_ga) else None
    if lo and hi and lo[1]==hi[1] and all(x[1]==lo[1] for x in _ga[i+1:j]): return t43+lo[1],'between two code-verified tables (9843 layout)'
    m={d for d in {x[1] for x in (lo,hi) if x} if B44[t43+d+X:t43+d+X+sz]==ref}
    if len(m)==1 and len(set(ref))>=3: return t43+m.pop(),'neighbouring tables + contents (9843 layout)'
    return None,None
def _strong43(t43,sz,a):
    ref=B43[t43+X:t43+X+sz]; return sz>=8 and len(set(ref))>=4 and B44[a+X:a+X+sz]==ref
def dec44(n,s,sz,how_t,t43,b43ref):
    t,how=how_t
    if t is None and t43 is not None and t43 in G: t,how=G[t43],'code alignment via 9843'
    if t is not None and (how in STRONG or how=='code alignment via 9843'):
        if t43 is not None and sz>=32 and how!='os':
            a,hw=via43(t43,sz)
            if a is not None and a!=t and _strong43(t43,sz,a) and not _strong43(t43,sz,t): return None,'conflicting evidence (contents match a different spot)',False
        return t,how,True
    if t43 is not None and how in ('unresolved','conflict relocation vs neighbours'):
        a,hw=via43(t43,sz)
        if a is not None and _strong43(t43,sz,a): return a,hw,True
    # content fallback (axes): 9843 bytes found in 9844
    if b43ref is not None and len(set(b43ref))>=3:
        cal=B44[0x3FFFE0:]; i=cal.find(b43ref); 
        if i>=0:
            j=cal.find(b43ref,i+1)
            return i+0x3FFFE0-X,'axis values matched in 9844'+('' if j<0 else ' (several copies - read-only)'),j<0
    return None,how,False
def resolve(tag,n):
    r=ST[n]; P=P43 if tag=='43' else P44; v=P[n]; out={}
    s=v['s']; sz=v['sz']
    if tag=='43':
        t,how=dec43(s,sz,(v['t'],v['how'])); ed=True
    else:
        t,how,ed=dec44(n,s,sz,(v['t'],v['how']),P43[n]['t'] if P43[n]['how'] in STRONG else None,None)
    if t is None: return None,how
    out['data']=(t,how)
    for w,(ta,ha) in v['ax'].items():
        n_=int(r['Columns'] if w=='X' else r['Rows']); asz=n_*W[r[f'Axis{w}.DataOrg']]; sa=h(r[f'Axis{w}.DataAddr.Cpu'])
        if tag=='43': a,ah=dec43(sa,asz,(ta,ha)); edit=a is not None
        else:
            a43=P43[n]['ax'].get(w,(None,''))
            ref=B43[a43[0]+X:a43[0]+X+asz] if a43[0] is not None and a43[1] in STRONG else None
            a,ah,edit=dec44(n,sa,asz,(ta,ha),a43[0] if a43[1] in STRONG else None,ref)
        if a is None: return None,f'axis {w} unresolved'
        out[w]=(a,ah,edit)
    return out,'ok'
# ---------- selection
def changed(tag,n,res):
    if res is None: return False
    v=(P43 if tag=='43' else P44)[n]; TB=B43 if tag=='43' else B44; t=res['data'][0]
    return SB[sfile(v['s']):sfile(v['s'])+v['sz']]!=TB[t+X:t+X+v['sz']]
RES={'43':{},'44':{}}
for tag in ('43','44'):
    for n in ST:
        if n in P43 and n in P44 and (E.module(n) in E.WHITE or n in E.KEY): RES[tag][n]=resolve(tag,n)
U=set()
for tag in ('43','44'):
    for n,(res,why) in RES[tag].items():
        if res and E.selected(n,changed(tag,n,res),'high'): U.add(n)
# also INJ base tables & keys even when unresolved somewhere
U|={n for n in RES['43'] if E.INJ.match(n) or n in E.KEY}
pickle.dump((U,RES),open(D+'stockos/final_sel.pkl','wb'))
print("selected union:",len(U))
for tag in ('43','44'):
    ok=[n for n in U if RES[tag].get(n,(None,))[0]]
    print(tag,"resolved",len(ok),"of",len(U)," by group:",{g:f"{sum(E.group(n)==g for n in ok)}/{sum(E.group(n)==g for n in U)}" for g in E.GROUPS})
