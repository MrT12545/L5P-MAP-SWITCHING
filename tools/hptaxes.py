# For HPT-switched tables: find the GM axis in the bin whose values match HPT's own axis copy (descriptor of tune 1).
import pickle,struct,sys,glob,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import olscsv as O
import numpy as np
D=sys.argv[1]; X=0x39FFE0
ST={}
for r in O.load(glob.glob('/root/.claude/uploads/*/1b5de558-*.csv')[0]):
    if r['Name'] in ST and not ST[r['Name']]['FolderName'].startswith('"NEW'): continue
    ST[r['Name']]=r
def run(binp,recp):
    b=open(binp,'rb').read(); recs,names=pickle.load(open(recp,'rb'))
    cal=np.frombuffer(b[0x3FFFE0:0x59FFD0],dtype=np.uint8)
    F=[np.frombuffer(cal[o:o+((len(cal)-o)//4)*4].tobytes(),dtype='>f4').astype(np.float64) for o in (0,2)]
    out={}
    for r in recs:
        if r['tune']!=1 or r['typ']!=3: continue
        n=names[r['orig']]; d=ST.get(n)
        if not d: continue
        for w,k in (('X','xp'),('Y','yp')):
            cnt,typ,num,den,ptr=struct.unpack('>HHHHI',b[r[k]+X:r[k]+X+12])
            fmt={0x22:'H',0x32:'h',0x21:'B',0x11:'f'}[typ]; sz=struct.calcsize(fmt)
            raw=struct.unpack('>'+fmt*cnt,b[ptr+X:ptr+X+sz*cnt]); vals=np.array([x*den/num if fmt!='f' else x for x in raw])
            if d[f'Axis{w}.DataOrg']!='eFloatHiLo': out[(n,w)]=('not float',None); continue
            tol=max(abs(den/num),1e-6)*1.01
            hits=[]
            for o,f in ((0,F[0]),(2,F[1])):
                c=np.nonzero(np.abs(f[:len(f)-cnt]-vals[0])<=tol)[0]
                for i in c:
                    if np.all(np.abs(f[i:i+cnt]-vals)<=tol): hits.append(0x3FFFE0+o+4*int(i)-X)
            out[(n,w)]=(hits,vals.tolist())
    return out
if __name__=='__main__':
    P43,P44=pickle.load(open(D+'stockos/placements.pkl','rb'))
    o3=run(D+'sotf/sotf.bin',D+'sotf/recs2.pkl'); o4=run(D+'sotf44/sotf44.bin',D+'sotf44/recs2.pkl')
    ok=bad=0
    for (n,w),(hits,_) in o3.items():
        if hits=='not float': continue
        t=P43[n]['ax'][w][0]
        if t in hits: ok+=1
        else: bad+=1; print("43 check fail",n,w,hex(t) if t else t,[hex(x) for x in hits])
    print("9843 verification: decided axis among HPT-value hits:",ok,"/",ok+bad)
    res={}
    for (n,w),(hits,vals) in o4.items():
        if hits=='not float': continue
        res[(n,w)]=(hits,vals)
        print("44",n,w,[hex(x) for x in hits][:4])
    pickle.dump(res,open(D+'stockos/hptaxes44.pkl','wb'))
