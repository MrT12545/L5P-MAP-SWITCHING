import sys, pickle, struct, math, collections
sys.path.insert(0, sys.argv[1]); import olscsv
stock=open(sys.argv[2],'rb').read(); sotf=open(sys.argv[3],'rb').read()
placed=pickle.load(open(sys.argv[4],'rb')); maps={r['Name']:r for r in olscsv.load(sys.argv[5])}
def sfile(cpu): return cpu-0x20000
def nfile(cpu): return cpu+0x39FFE0
FMT={'eByte':(1,'B','b'),'eHiLo':(2,'H','h'),'eHiLoHiLo':(4,'I','i'),'eFloatHiLo':(4,'f','f')}
def raw(buf,off,org,n,signed):
    sz,u,s=FMT[org]; c=s if signed else u
    return list(struct.unpack('>'+c*n,buf[off:off+sz*n]))
def mono(v):
    inc=all(b>a for a,b in zip(v,v[1:])); dec=all(b<a for a,b in zip(v,v[1:])); return inc or dec
verdict=collections.Counter(); bad=[]
for m in placed:
    if m['how']!='changed': continue
    r=maps[m['name']]; org=r['DataOrg']; n=m['C']*m['R']; sg=r['bSigned']=='1'
    a=raw(stock,sfile(m['cpu']),org,n,sg); b=raw(sotf,nfile(m['ncpu']),org,n,sg)
    ok=True; why=''
    if org=='eFloatHiLo':
        fin=[x for x in b if math.isfinite(x) and abs(x)<1e9]
        if len(fin)<n: ok=False; why='non-finite/huge floats'
        else:
            # magnitude sanity: new range should not explode vs stock range
            sa=max(abs(x) for x in a) or 1; sb=max(abs(x) for x in b)
            if sb>sa*1000 and sb>1e4: ok=False; why=f'magnitude x{sb/sa:.0f}'
    # axis check
    for ax,(acpu,how) in m['axes'].items():
        if acpu is None: continue
        aorg=r[f'Axis{ax}.DataOrg']; an=m['C'] if ax=='X' else m['R']
        if an<3 or aorg not in FMT: continue
        sa=raw(stock,sfile(int(r[f'Axis{ax}.DataAddr.Cpu'][1:],16)),aorg,an,r[f'Axis{ax}.bSigned']=='1')
        sb=raw(sotf,nfile(acpu),aorg,an,r[f'Axis{ax}.bSigned']=='1')
        if mono(sa) and not mono(sb): ok=False; why+=f' axis{ax} lost monotonicity'
    verdict['plausible' if ok else 'suspect']+=1
    if not ok: bad.append((m['name'],hex(m['cpu']),hex(m['ncpu']),why))
# all axes (including those of identical maps) monotonic check
ax_bad=0; ax_tot=0
for m in placed:
    r=maps[m['name']]
    for ax,(acpu,how) in m['axes'].items():
        if acpu is None or how=='identical': continue
        aorg=r[f'Axis{ax}.DataOrg']; an=m['C'] if ax=='X' else m['R']
        if an<3 or aorg not in FMT: continue
        sa=raw(stock,sfile(int(r[f'Axis{ax}.DataAddr.Cpu'][1:],16)),aorg,an,r[f'Axis{ax}.bSigned']=='1')
        sb=raw(sotf,nfile(acpu),aorg,an,r[f'Axis{ax}.bSigned']=='1')
        if mono(sa): ax_tot+=1; ax_bad+= (not mono(sb))
print("changed maps:",dict(verdict)); print(f"changed monotonic axes still monotonic: {ax_tot-ax_bad}/{ax_tot}")
pickle.dump(bad,open(sys.argv[6],'wb'))
for x in bad[:25]: print("  SUSPECT",x)
