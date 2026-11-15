# usage: gapalign.py ins_a.pkl ins_b.pkl out.pkl  -> {cal_a: cal_b} via ordered refs between code anchors
import pickle,collections,sys,os,bisect,re,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import calrefs as C, lisfn
A,B,out=sys.argv[1:4]
I3,R3=C.refs(A); I4,R4=C.refs(B)
LM=lambda t: re.sub(r'\br\d+\b','r',C.MASK.sub('#',t))
T3=[LM(x[2]) for x in I3]; T4=[LM(x[2]) for x in I4]
K=16
def grams(T):
    c=collections.Counter(); pos={}
    for i in range(len(T)-K):
        g=hash(tuple(T[i:i+K])); c[g]+=1; pos[g]=i
    return c,pos
c3,p3=grams(T3); c4,p4=grams(T4)
anch=lisfn.lis_pairs(sorted((p3[g],p4[g]) for g in c3 if c3[g]==1 and c4.get(g)==1 and 'illegal' not in T3[p3[g]]))
# collapse anchors into a list of (i3,i4) boundaries
a3=[x[0] for x in anch]
R3s=sorted((k,j,a) for pc,j,k,a in R3); R4s=sorted((k,j,a) for pc,j,k,a in R4)
k3=[x[0] for x in R3s]; k4=[x[0] for x in R4s]
votes=collections.defaultdict(collections.Counter); votes2=collections.defaultdict(collections.Counter); gaps=0; okg=0
for g in range(len(anch)-1):
    s3,s4=anch[g]; e3,e4=anch[g+1]
    if e3-s3<=K and e4-s4<=K: continue          # contiguous anchors, nothing between
    i0,i1=bisect.bisect_left(k3,s3),bisect.bisect_left(k3,e3)
    j0,j1=bisect.bisect_left(k4,s4),bisect.bisect_left(k4,e4)
    if i1==i0: continue
    gaps+=1
    if i1-i0==j1-j0 and i1-i0<=200:
        okg+=1
        for x in range(i1-i0):
            r3=R3s[i0+x]; r4=R4s[j0+x]
            if (r3[1]-r3[0])==(r4[1]-r4[0]) and I3[r3[1]][2].split()[0]==I4[r4[1]][2].split()[0]: votes[r3[2]][r4[2]]+=1
    elif i1-i0<=300 and j1-j0<=300:
        tk=lambda I,r:'|'.join(LM(I[q][2]) for q in range(r[0]-1,r[1]+2))
        ta=[tk(I3,R3s[q]) for q in range(i0,i1)]; tb=[tk(I4,R4s[q]) for q in range(j0,j1)]
        for tag,x1,x2,y1,y2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
            if tag=='equal' or (tag=='replace' and x2-x1==y2-y1):
                for q in range(x2-x1): votes2[R3s[i0+x1+q][2]][R4s[j0+y1+q][2]]+=1
mp={a:v.most_common(1)[0][0] for a,v in votes.items() if len(v)==1 or v.most_common(2)[0][1]>=3*v.most_common(2)[1][1]}
n1=len(mp)
for a,v in votes2.items():
    if a in mp: continue
    if len(v)==1 or v.most_common(2)[0][1]>=3*v.most_common(2)[1][1]: mp[a]=v.most_common(1)[0][0]
print("equal-count mapped",n1,"+ difflib gaps",len(mp)-n1)
pickle.dump(mp,open(out,'wb')); print("anchors",len(anch),"gaps with refs",gaps,"equal-count gaps",okg,"mapped",len(mp))
