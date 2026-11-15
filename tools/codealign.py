import pickle,re,collections,sys,bisect,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import calrefs as C, lisfn
D=sys.argv[1]
I3,R3=C.refs(D+'sotf/ins.pkl'); I4,R4=C.refs(D+'sotf44/ins.pkl')
T3=[C.MASK.sub('#',x[2]) for x in I3]; T4=[C.MASK.sub('#',x[2]) for x in I4]
K=12
def grams(T):
    c=collections.Counter(); pos={}
    for i in range(len(T)-K):
        g=hash(tuple(T[i:i+K])); c[g]+=1; pos[g]=i
    return c,pos
c3,p3=grams(T3); c4,p4=grams(T4)
anch=sorted((p3[g],p4[g]) for g in c3 if c3[g]==1 and c4.get(g)==1 and 'illegal' not in T3[p3[g]])
print("raw anchors:",len(anch))
keep=lisfn.lis_pairs(anch) if hasattr(lisfn,'lis_pairs') else anch
print("LIS anchors:",len(keep))
k3=[a for a,_ in keep]
R4i={k:a for pc,j,k,a in R4 for _ in [0]}
R4j={(k,j):a for pc,j,k,a in R4}
votes=collections.defaultdict(collections.Counter)
for pc,j,k,a in R3:
    i=bisect.bisect_right(k3,k)-1
    if i<0: continue
    d=keep[i][1]-keep[i][0]; k4=k+d; j4=j+d
    if 0<=k4<len(T4) and T3[k:j+1]==T4[k4:j4+1] and (k4,j4) in R4j:
        votes[a][R4j[(k4,j4)]]+=1
mp={a:v.most_common(1)[0][0] for a,v in votes.items() if len(v)==1 or v.most_common(2)[0][1]>=3*v.most_common(2)[1][1]}
amb=sum(1 for a,v in votes.items() if a not in mp)
pickle.dump(mp,open(D+'sotf44/codemap43to44.pkl','wb'))
print("cal addresses mapped:",len(mp),"ambiguous:",amb,"of",len({a for *_,a in R3}))
