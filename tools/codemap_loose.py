# usage: codemap.py ins_src.pkl ins_dst.pkl out.pkl  -> {src_cal_cpu: dst_cal_cpu}
import pickle,collections,sys,os,difflib,bisect,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import calrefs as C, lisfn
src,dst,out=sys.argv[1:4]
LM=lambda t: re.sub(r'\br\d+\b','r',C.MASK.sub('#',t))
I3,R3=C.refs(src); I4,R4=C.refs(dst)
T3=[LM(x[2]) for x in I3]; T4=[LM(x[2]) for x in I4]
votes=collections.defaultdict(collections.Counter)
# A: k-gram anchored instruction alignment
K=12
def grams(T):
    c=collections.Counter(); pos={}
    for i in range(len(T)-K):
        g=hash(tuple(T[i:i+K])); c[g]+=1; pos[g]=i
    return c,pos
c3,p3=grams(T3); c4,p4=grams(T4)
keep=lisfn.lis_pairs(sorted((p3[g],p4[g]) for g in c3 if c3[g]==1 and c4.get(g)==1 and 'illegal' not in T3[p3[g]]))
k3=[a for a,_ in keep]; R4j={(k,j):a for pc,j,k,a in R4}
for pc,j,k,a in R3:
    i=bisect.bisect_right(k3,k)-1
    if i<0: continue
    d=keep[i][1]-keep[i][0]
    if T3[k:j+1]==T4[k+d:j+d+1] and (k+d,j+d) in R4j: votes[a][R4j[(k+d,j+d)]]+=1
# B: ordered reference-site alignment
def tok(I,k,j): return '|'.join(LM(I[i][2]) for i in range(k-2,j+3))
R3s=sorted(R3); R4s=sorted(R4)
sm=difflib.SequenceMatcher(None,[tok(I3,k,j) for pc,j,k,a in R3s],[tok(I4,k,j) for pc,j,k,a in R4s],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal' or (tag=='replace' and i2-i1==j2-j1 and i2-i1<=3):
        for x in range(i2-i1): votes[R3s[i1+x][3]][R4s[j1+x][3]]+=1
mp={a:v.most_common(1)[0][0] for a,v in votes.items() if len(v)==1 or v.most_common(2)[0][1]>=3*v.most_common(2)[1][1]}
pickle.dump(mp,open(out,'wb')); print(os.path.basename(out),"mapped",len(mp),"of",len({a for *_,a in R3}),"anchors",len(keep))
