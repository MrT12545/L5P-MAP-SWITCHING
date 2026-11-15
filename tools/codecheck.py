import sys,csv,collections,pickle,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import olscsv as O, ez_select as E
D=sys.argv[1]
def L(p):
    d={}
    for r in O.load(p): d.setdefault(r['Name'],r)
    return d
M44=L(D+'sotf44/WinOLS_maplist_SOTF_9844.csv'); M43=L(D+'sotf/WinOLS_maplist_SOTF_9843.csv')
R44={r['Name']:r for r in csv.DictReader(open(D+'sotf44/relocation_review_9844.csv'))}; R43={r['Name']:r for r in csv.DictReader(open(D+'sotf/relocation_review.csv'))}
mp=pickle.load(open(D+'sotf44/codemap43to44.pkl','rb')); h=lambda s:int(s.lstrip('$'),16); X=0x39FFE0
st=collections.Counter()
for n,r in R44.items():
    if n not in M43 or n not in M44 or r['Confidence']!='high' or r['Placement']!='agree': continue
    a3=h(M43[n]['Fieldvalues.StartAddr'])-X; a4=h(M44[n]['Fieldvalues.StartAddr'])-X
    if a3 in mp: st['match' if mp[a3]==a4 else 'MISMATCH']+=1
print("validation vs 'agree' placements:",st)
U=set()
for rv in (R43,R44): U|={n for n,r in rv.items() if E.selected(n,r['Data vs stock']=='changed','high')}
st=collections.Counter(); diff=[]
for n in U:
    if n not in M43 or R43.get(n,{}).get('Confidence')=='low': continue
    a3=h(M43[n]['Fieldvalues.StartAddr'])-X; a4=h(M44[n]['Fieldvalues.StartAddr'])-X
    if a3 not in mp: st['not mapped']+=1; continue
    if mp[a3]==a4: st['code agrees']+=1
    else: st['code DISAGREES']+=1; diff.append((n,R44[n]['Placement'],R44[n]['Confidence'],hex(a4),hex(mp[a3])))
print("selected maps:",st)
for d in sorted(diff)[:12]: print(' ',d)
