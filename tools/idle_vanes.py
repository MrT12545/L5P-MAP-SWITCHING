import sys,csv,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import olscsv as O
csv.field_size_limit(1<<30)
TABLES=['KtAICC_Pct_VGT_FdFwd_LoBC1','KtAICC_Pct_VGT_FdFwd_MidBC1','KtAICC_Pct_VGT_FdFwd_SeaBC1','KtAICC_Pct_VGT_Max_LoBC','KtAICC_Pct_VGT_Max_MidBC','KtAICC_Pct_VGT_Max_SeaBC']
def load(maplist):
    return {r['IdName']:r for r in csv.DictReader(open(maplist,newline='',encoding='latin1'),delimiter=';')}
def grid(b,r):
    C,R,v=O.decode_map(b,r); xs=O.axis(b,r,'X',C); ys=O.axis(b,r,'Y',R)
    return C,R,v,[float(x) for x in xs],[float(y) for y in ys]
if __name__=='__main__':
    for tag,ml,bp in (('9843','sotf/WinOLS_L5P_9843_MapList_Named.csv','sotf/sotf.bin'),('9844','sotf44/WinOLS_L5P_9844_MapList_Named.csv','sotf44/sotf44.bin')):
        M=load(sys.argv[1]+ml); b=open(sys.argv[1]+bp,'rb').read()
        print('=====',tag)
        for t in TABLES:
            r=M[t+'_SOTF_T1']; C,R,v,xs,ys=grid(b,r)
            cols=[i for i,x in enumerate(xs) if x<=800]; rows=[j for j,y in enumerate(ys) if y<=30]
            print(f'{t}  {R}x{C}  X(rpm)={xs[:4]}..  Y(load)={ys[:8]}..  factor={r["Fieldvalues.Factor"]} org={r["DataOrg"]}')
            for p in range(0,6):
                rr=M.get(t) if p==0 else M[f'{t}_SOTF_T{p}']
                if rr is None: print('   T0: (base table not in verified list)'); continue
                C2,R2,v2,xs2,ys2=grid(b,rr)
                blk=[[round(v2[j*C2+i],1) for i in cols] for j in rows]
                print(f'   T{p}: '+'  '.join('/'.join(f'{x:g}' for x in rw) for rw in blk), '' if xs2==xs and ys2==ys else ' (axes differ from T1!)')
