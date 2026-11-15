import sys, struct, pickle, collections
sys.path.insert(0, sys.argv[1]); import olscsv
sotf=open(sys.argv[2],'rb').read(); items=pickle.load(open(sys.argv[3],'rb')); maps=olscsv.load(sys.argv[4])
F=lambda c: c+0x39FFE0; CAL0=0x60000
ESZ={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}
# SOTF cpu -> definitions
at=collections.defaultdict(list); axat=collections.defaultdict(list)
for r in maps:
    C,R=int(r['Columns']),int(r['Rows']); cpu=int(r['Fieldvalues.StartAddr.Cpu'][1:],16)
    it=items.get((cpu,ESZ[r['DataOrg']]*C*R))
    if it and it.get('y') is not None: at[it['y']+CAL0].append(r)
recs=[]; p=0x1504F8
while True:
    a,b,c,d=struct.unpack('>4I',sotf[F(p):F(p)+16])
    if not (0x60000<=b<0x1A0000 and 0x1504F8<=c<0x1A0000 and 0x40000000<=d<0x40100000): break
    w0,w1,xp,yp,dp=struct.unpack('>5I',sotf[F(c):F(c)+20])
    recs.append(dict(rec=p,tune=a>>24,typ=(a>>16)&0xff,orig=b,desc=c,ram=d,w0=w0,w1=w1,xp=xp,yp=yp,dp=dp)); p+=16
pickle.dump(recs,open(sys.argv[5],'wb'))
byorig=collections.OrderedDict()
for r in recs: byorig.setdefault(r['orig'],[]).append(r)
print(f"{len(recs)} records, {len(byorig)} switched maps\n")
for orig,rs in byorig.items():
    r0=rs[0]; xd=r0['w0']>>24; yd=(r0['w0']>>16)&0xff; fl=r0['w0']&0xffff
    names=[m['Name'] for m in at.get(orig,[])]
    dm=at.get(orig,[None])[0]
    dd=f"{dm['Columns']}x{dm['Rows']} {dm['DataOrg']}" if dm else '?'
    tunes=sorted(x['tune'] for x in rs)
    print(f"{orig:#08x} desc {xd}x{yd} fl={fl:#06x} w1={r0['w1']:#010x} type={r0['typ']} tunes={tunes} | def: {names[0] if names else 'NO DEFINITION AT THIS ADDRESS'} [{dd}]")
