import sys, pickle, struct, math, collections
sys.path.insert(0, sys.argv[1]); import olscsv
stock=open(sys.argv[2],'rb').read(); sotf=open(sys.argv[3],'rb').read()
items=pickle.load(open(sys.argv[4],'rb')); maps=olscsv.load(sys.argv[5])
CAL0=0x60000
FMT={'eByte':(1,'B','b'),'eHiLo':(2,'H','h'),'eHiLoHiLo':(4,'I','i'),'eFloatHiLo':(4,'f','f')}
def raw(buf,off,org,n,sg):
    sz,u,s=FMT[org]; return list(struct.unpack('>'+(s if sg else u)*n,buf[off:off+sz*n]))
mono=lambda v: all(b>a for a,b in zip(v,v[1:])) or all(b<a for a,b in zip(v,v[1:]))
def ncpu(cpu,L):
    it=items.get((cpu,L)); 
    return (None,None) if not it or it.get('y') is None else (it['y']+CAL0, it['how'])
ESZ={k:v[0] for k,v in FMT.items()}
res=collections.Counter(); axres=collections.Counter(); bad=[]
for r in maps:
    C,R=int(r['Columns']),int(r['Rows']); org=r['DataOrg']; n=C*R; L=ESZ[org]*n
    cpu=int(r['Fieldvalues.StartAddr.Cpu'][1:],16); nc,how=ncpu(cpu,L)
    if nc is None: res[('unplaced',)]+=1; continue
    a=raw(stock,cpu-0x20000,org,n,r['bSigned']=='1'); b=raw(sotf,nc+0x39FFE0,org,n,r['bSigned']=='1')
    same=a==b; ok=True
    if not same and org=='eFloatHiLo':
        if any(not math.isfinite(v) or abs(v)>1e12 for v in b): ok=False
    for axn in 'XY':
        if not r[f'Axis{axn}.DataSrc'].startswith('eRom'): continue
        aorg=r[f'Axis{axn}.DataOrg']; an=C if axn=='X' else R
        if aorg not in FMT or an<3: continue
        acpu=int(r[f'Axis{axn}.DataAddr.Cpu'][1:],16); anc,ahow=ncpu(acpu,ESZ[aorg]*an)
        if anc is None: continue
        sa=raw(stock,acpu-0x20000,aorg,an,r[f'Axis{axn}.bSigned']=='1'); sb=raw(sotf,anc+0x39FFE0,aorg,an,r[f'Axis{axn}.bSigned']=='1')
        if mono(sa):
            m_ok=mono(sb); axres[(ahow,m_ok)]+=1
            if not m_ok: ok=False
    res[(how,'same' if same else 'changed','ok' if ok else 'SUSPECT')]+=1
    if not ok: bad.append((r['Name'],hex(cpu),hex(nc),how))
for k,v in sorted(res.items(),key=lambda kv:-kv[1]): print("  ",k,v)
print("monotonic-axis check:",dict(axres))
pickle.dump(bad,open(sys.argv[6],'wb')); print("suspect maps:",len(bad))
