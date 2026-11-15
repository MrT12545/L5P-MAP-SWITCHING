import pickle,re,collections,sys
def refs(ins_path):
    ins=pickle.load(open(ins_path,'rb')); out=[]
    for k,(pc,n,t,info) in enumerate(ins):
        if not info or info[0]!='e_lis': continue
        rx,hi=info[1],info[2]
        if not (0x6<=hi<=0x20): continue
        for j in range(k+1,min(k+10,len(ins))):
            pc2,n2,t2,i2=ins[j]
            if i2 and i2[0]=='add16i' and i2[2]==rx: out.append((pc,j,k,(hi<<16)+i2[3])); 
            elif i2 and i2[0]=='mem' and i2[1]==rx: out.append((pc,j,k,(hi<<16)+i2[2]))
            # stop if rx overwritten
            if re.match(r'\S+ r%d,'%rx,t2) and not t2.startswith(('e_stw','e_sth','e_stb','se_stw','se_sth','se_stb','e_cmp','se_cmp')): break
    return ins,out
MASK=re.compile(r'0x[0-9a-f]+|-?\b\d+\b')
def sig(ins,k,w=7):
    return tuple(MASK.sub('#',ins[i][2]) for i in range(max(0,k-w),min(len(ins),k+w+1)))
if __name__=='__main__':
    D=sys.argv[1]
    I3,R3=refs(D+'sotf/ins.pkl'); I4,R4=refs(D+'sotf44/ins.pkl')
    print("refs 9843:",len(R3),"9844:",len(R4))
    S4=collections.defaultdict(list)
    for pc,j,k,a in R4: S4[(sig(I4,k),j-k)].append(a)
    votes=collections.defaultdict(collections.Counter)
    for pc,j,k,a in R3:
        c=S4.get((sig(I3,k),j-k))
        if c and len(set(c))==1: votes[a][c[0]]+=1
    mp={a:v.most_common(1)[0][0] for a,v in votes.items() if len(v)==1 or v.most_common(2)[0][1]>=2*v.most_common(2)[1][1]}
    pickle.dump(mp,open(D+'sotf44/codemap43to44.pkl','wb'))
    print("cal addresses mapped 9843->9844:",len(mp),"of",len({a for *_,a in R3}))
