import sys, pickle, bisect, collections
sys.path.insert(0, sys.argv[1]); import olscsv
stock=open(sys.argv[2],'rb').read(); sotf=open(sys.argv[3],'rb').read()
segs=pickle.load(open(sys.argv[4],'rb')); maps=olscsv.load(sys.argv[5])
CAL0=0x60000
cs=stock[CAL0-0x20000:0x200000-0x20000]; cn=sotf[CAL0+0x39FFE0:0x1FFFF0+0x39FFE0]
starts=[s for s,_ in segs]
def delta(x): return segs[bisect.bisect_right(starts,x)-1][1]
FMT={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}
def place(cpu,length):
    x=cpu-CAL0
    if not (0<=x<len(cs)): return None,'outside-cal'
    d0=delta(x); d1=delta(x+length-1)
    y=x+d0
    if d0!=d1: return y+CAL0,'straddles-shift'
    return y+CAL0, 'identical' if cn[y:y+length]==cs[x:x+length] else 'changed'
res=[]; st=collections.Counter(); axst=collections.Counter()
for r in maps:
    C,R=int(r['Columns']),int(r['Rows'])
    L=FMT[r['DataOrg']]*C*R
    cpu=int(r['Fieldvalues.StartAddr.Cpu'][1:],16)
    ncpu,how=place(cpu,L); st[how]+=1
    ax={}
    for a in 'XY':
        if r[f'Axis{a}.DataSrc'].startswith('eRom'):
            acpu=int(r[f'Axis{a}.DataAddr.Cpu'][1:],16); n=C if a=='X' else R
            ax[a]=place(acpu,FMT.get(r[f'Axis{a}.DataOrg'],2)*n); axst[ax[a][1]]+=1
    res.append(dict(name=r['Name'],folder=r['FolderName'],cpu=cpu,ncpu=ncpu,how=how,axes=ax,size=L,C=C,R=R))
pickle.dump(res,open(sys.argv[6],'wb'))
print("maps:",dict(st)); print("axes:",dict(axst))
# changed maps by kind
ch=[m for m in res if m['how']=='changed']
print("changed maps by dimension:",collections.Counter(('scalar' if m['C']*m['R']==1 else ('curve' if min(m['C'],m['R'])==1 else 'table')) for m in ch))
print("straddling examples:",[(m['name'],hex(m['cpu']),m['size']) for m in res if m['how']=='straddles-shift'][:12])
