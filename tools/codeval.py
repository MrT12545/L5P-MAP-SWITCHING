import sys,csv,collections,pickle,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ez_select as E
D,review,other,mpp,fixp=sys.argv[1:6]
h=lambda s:int(s.lstrip('$'),16)
RV={r['Name']:r for r in csv.DictReader(open(D+review))}; RO={r['Name']:r for r in csv.DictReader(open(D+other))}
mp=pickle.load(open(D+mpp,'rb')); fix,drop=pickle.load(open(D+fixp,'rb'))
U=set()
for rv in (RV,RO): U|={n for n,r in rv.items() if E.selected(n,r['Data vs stock']=='changed','high')}
st=collections.Counter(); dis=[]
allst=collections.Counter()
for n,r in RV.items():
    if not r['Stock CPU (P1B)'].startswith('$') or r['Confidence']=='low': continue
    s=h(r['Stock CPU (P1B)']); t=h(r['SOTF CPU'])
    if s in mp: allst[(r['Placement'].split('+')[0],'agree' if mp[s]==t else 'DIS')]+=1
for n in U:
    r=RV.get(n)
    if not r or r['Confidence']=='low' or n in drop: continue
    s=h(r['Stock CPU (P1B)']); t=fix.get(n,h(r['SOTF CPU'])+0x39FFE0)-0x39FFE0
    if s not in mp: st['not code-mapped']+=1; continue
    if mp[s]==t: st['code agrees']+=1
    else: st['code DISAGREES']+=1; dis.append((n,r['Placement'],hex(t),hex(mp[s])))
print("all maps:",sorted(allst.items()))
print("selected:",st)
for d in sorted(dis)[:25]: print(' ',d)
pickle.dump(dis,open(D+mpp.replace('.pkl','_dis.pkl'),'wb'))
