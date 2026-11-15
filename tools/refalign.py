import pickle,re,collections,sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import calrefs as C
D=sys.argv[1]
I3,R3=C.refs(D+'sotf/ins.pkl'); I4,R4=C.refs(D+'sotf44/ins.pkl')
def tok(I,k,j): return '|'.join(C.MASK.sub('#',I[i][2]) for i in range(k-2,j+3))
R3.sort(); R4.sort()
t3=[tok(I3,k,j) for pc,j,k,a in R3]; t4=[tok(I4,k,j) for pc,j,k,a in R4]
sm=difflib.SequenceMatcher(None,t3,t4,autojunk=False)
votes=collections.defaultdict(collections.Counter)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal' or (tag=='replace' and i2-i1==j2-j1 and i2-i1<=3):
        for x in range(i2-i1): votes[R3[i1+x][3]][R4[j1+x][3]]+=1
old=pickle.load(open(D+'sotf44/codemap43to44.pkl','rb'))
mp={a:v.most_common(1)[0][0] for a,v in votes.items() if len(v)==1 or v.most_common(2)[0][1]>=3*v.most_common(2)[1][1]}
both=sum(1 for a in mp if a in old); agree=sum(1 for a in mp if a in old and old[a]==mp[a])
print("refalign mapped:",len(mp),"| overlap with codealign:",both,"agree:",agree)
for a,v in old.items(): mp.setdefault(a,v)
pickle.dump(mp,open(D+'sotf44/codemap43to44.pkl','wb')); print("combined:",len(mp))
