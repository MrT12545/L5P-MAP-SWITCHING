import pickle,collections,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ez_select as E
D=sys.argv[1]
P43,P44=pickle.load(open(D+'stockos/placements.pkl','rb'))
def ok(v):
    if v['t'] is None: return False
    return all(a[0] is not None for a in v['ax'].values())
U=set()
for P in (P43,P44):
    U|={n for n,v in P.items() if ok(v) and E.selected(n,bool(v['changed']),'high')}
print("union selected:",len(U))
for tag,P in (('9843',P43),('9844',P44)):
    inc=[n for n in U if n in P and ok(P[n])]
    print(tag,"included",len(inc),"of",len(U))
    gi=collections.Counter(E.group(n) for n in inc); gu=collections.Counter(E.group(n) for n in U)
    print("   ",{g:f"{gi[g]}/{gu[g]}" for g in E.GROUPS})
    miss=[n for n in U if not(n in P and ok(P[n])) and E.INJ.match(n)]
    print("   BC1 injection maps missing:",miss)
pickle.dump(U,open(D+'stockos/selected.pkl','wb'))
