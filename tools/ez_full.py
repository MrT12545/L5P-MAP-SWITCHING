import sys, csv, struct, re, math, collections
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ez_select as E
csv.field_size_limit(1<<30)
binp, maplist, review, other_review, out, LABEL, TAG = sys.argv[1:8]
b=open(binp,'rb').read()
M={}
for r in csv.DictReader(open(maplist,newline='',encoding='latin1'),delimiter=';'): M.setdefault(r['Name'],r)
RV={r['Name']:r for r in csv.DictReader(open(review))}; RVO={r['Name']:r for r in csv.DictReader(open(other_review))}
U=set()
for rv in (RV,RVO): U|={n for n,r in rv.items() if E.selected(n,r['Data vs stock']=='changed','high')}
NM2LBFT=0.737562149
H=['Unique ID','Address','NAME','DESC','UNITS','Type','Elements','Size','Endian','Signed','Math','Adder','Precision','MIN','MAX','LEVEL','AXIS','CATEGORY 1','CATEGORY 2','CATEGORY 3','MANUAL DATA']
def row(*v): v=list(v); return v+['']*(len(H)-len(v))
clean=lambda s: re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s.replace('Mapa:',''))).replace(',',' -').replace('"',"'").replace(';',' -').strip()
fmtn=lambda v: '%.12g'%v
def fmtv(v,prec):
    t='%.*f'%(max(0,min(prec,4)),v)
    return (t.rstrip('0').rstrip('.') if '.' in t else t) or '0'
SZ={'eByte':('1',1,'B','b'),'eHiLo':('2',2,'H','h'),'eHiLoHiLo':('4',4,'I','i'),'eFloatHiLo':('F',4,'f','f')}
def raw(addr,org,n,signed):
    s,w,u,sg=SZ[org]; return list(struct.unpack('>'+(sg if signed else u)*n,b[addr:addr+w*n]))
def unit_of(u,name):
    if u: return u
    for k,v in (('_Pct_','%'),('_phi_','deg'),('_T_','deg C'),('_n_','rpm'),('_v_','kph'),('_p_','kPa'),('_K_','factor'),('_k_','factor'),('_r_','ratio'),('_b_','on/off'),('_e_','enum'),('_Cnt_','count'),('_V_','mm^3'),('_M_','Nm'),('_t_','s')):
        if k in name: return v
    return '-'
def scaling(fac,off,unit):
    if unit in ('Nm','Nm/s'): return fac*NM2LBFT, off*NM2LBFT, unit.replace('Nm','lb-ft'), True
    return fac, off, unit, False
def rng(org,signed,fac,off):
    if org=='eFloatHiLo': return (-999999*abs(fac)+off, 999999*abs(fac)+off)
    bits={'eByte':8,'eHiLo':16,'eHiLoHiLo':32}[org]
    lo,hi=(-(1<<(bits-1)),(1<<(bits-1))-1) if signed else (0,(1<<bits)-1)
    a,c=lo*fac+off,hi*fac+off; return (min(a,c),max(a,c))
# ---------------- folders
folders=[]; fid=[0]; F={}
def folder(path):
    if path in F: return F[path]
    fid[0]+=1; F[path]=f'F{fid[0]}'; folders.append(row('FFFF','0x0000',path[-1],'','0','C','0','0','0','0','0','0','0','0','0','0','0',F[path],'0','0')); return F[path]
for g in E.GROUPS: folder((g,))
SOTF_TOP='SOTF Switch Positions 1-5 (HPT steering wheel tunes)'; folder((SOTF_TOP,))
# ---------------- map entries
maps=[]; nid=[0]; used=[]  # used: (start,end,id,name)
def newid(): i=nid[0]; nid[0]+=1; return 'C%03d'%i
axis_cache={}; manual_cache={}
def manual_axis(vals,ez,unit,label,cats):
    key=(tuple(vals),ez,cats[0])
    if key in manual_cache: return manual_cache[key]
    cid=newid(); manual_cache[key]=cid
    maps.append(row(cid,'MANUAL',label,'Read-only axis labels.',unit or '-',ez,str(len(vals)),'0','0','0','0','0','0','0','0','0','',*cats,';'.join(vals)))
    return cid
def axis_entry(r,wx,n,ez,cats,readonly):
    src=r[f'Axis{wx}.DataSrc']; nm=r[f'Axis{wx}.Name'] or 'axis'; un=r[f'Axis{wx}.Unit']
    if src in ('eRom','eRomDataIndex') and r[f'Axis{wx}.DataOrg'] in SZ:
        a=int(r[f'Axis{wx}.DataAddr'].lstrip('$'),16); org=r[f'Axis{wx}.DataOrg']; sg=r[f'Axis{wx}.bSigned']=='1'
        fac=float(r[f'Axis{wx}.Factor'] or 1); off=float(r[f'Axis{wx}.Offset'] or 0)
        fac,off,un2,conv=scaling(fac,off,un or unit_of('',nm))
        vals=[x*fac+off for x in raw(a,org,n,sg)]
        if any(isinstance(v,float) and (math.isnan(v) or math.isinf(v) or abs(v)>1e7) for v in vals): return None,'bad axis'
        if readonly or (a,n,org) in axis_cache and axis_cache[(a,n,org)][1]!=ez:
            prec=int(r[f'Axis{wx}.Precision'] or 2) if (r[f'Axis{wx}.Precision'] or '').lstrip('-').isdigit() else 2
            return manual_axis([fmtv(v,prec) for v in vals],ez,un2,f'{nm} (read-only copy)',cats),None
        if (a,n,org) in axis_cache: return axis_cache[(a,n,org)][0],None
        cid=newid(); axis_cache[(a,n,org)]=(cid,ez)
        s,w,_,_=SZ[org]; lo,hi=rng(org,sg,fac,off); p=r[f'Axis{wx}.Precision']; p=int(p) if p.lstrip('-').isdigit() and int(p)>=0 else 2
        cpu=a-DELTA
        maps.append(row(cid,'0x%X'%a,f'{nm} axis',f'{nm} - breakpoints (CPU 0x{cpu:X}). Shared axis: editing it changes every map that uses it.',un2,ez,str(n),s,'MSB','S' if sg else 'U',fmtn(fac),fmtn(off),str(min(p,4)),fmtn(lo),fmtn(hi),'1','',cats[0],cats[1],cats[2]))
        used.append((a,a+w*n,cid,nm+' axis'))
        return cid,None
    if src in ('eUserdef','eUserdefString'):
        v=r[f'Axis{wx}.Values']; vals=[x for x in (v.split(';') if ';' in v else v.split()) if x!=''][:n]
        vals=[re.sub(r'^C[ei][A-Z]{4}_e_','',x) for x in vals]
        if len(vals)==n: return manual_axis(vals,ez,un,f'{nm} labels',cats),None
    return manual_axis([str(i) for i in range(n)],ez,'index','Index',cats),None
DELTA=0x39FFE0
skipped=[]; dup_addr={}
def add_map(name,r,cats_main,cats_axes,cats_scalar,prefix,readonly_axes,extra_desc):
    org=r['DataOrg']
    if org not in SZ: skipped.append((name,'unsupported data org '+org)); return
    C,R=int(r['Columns']),int(r['Rows']); n=C*R; a=int(r['Fieldvalues.StartAddr'].lstrip('$'),16)
    if a in dup_addr: skipped.append((name,'same address as '+dup_addr[a])); return
    sg=r['bSigned']=='1'; fac=float(r['Fieldvalues.Factor'] or 1); off=float(r['Fieldvalues.Offset'] or 0)
    unit0=unit_of(r['Fieldvalues.Unit'],name); fac,off,unit,conv=scaling(fac,off,unit0)
    vals=[x*fac+off for x in raw(a,org,n,sg)]
    if org=='eFloatHiLo' and any(math.isnan(v) or math.isinf(v) or abs(v)>1e7 for v in vals): skipped.append((name,'float data not sane - placement suspect')); return
    s,w,_,_=SZ[org]; lo,hi=rng(org,sg,fac,off)
    p=r['Precision']; p=int(p) if p.lstrip('-').isdigit() else 2
    if conv: p=min(p,1) if fac>=0.1 else min(max(p,1),2)
    cpu=a-DELTA
    cm=clean(r['Comment'])[:420]
    desc=f'{name} (CPU 0x{cpu:X}).{extra_desc} {cm}'.strip()
    if conv: desc+=' Torque shown in lb-ft (ECU stores Nm).'
    ty=r['Type']
    if ty=='eEinzel' or n==1:
        isw=('_b_' in name and org!='eFloatHiLo' and fac==1 and off==0)
        cats=cats_scalar[1] if isw else cats_scalar[0]
        cid=newid(); dup_addr[a]=name
        if isw: maps.append(row(cid,'0x%X'%a,prefix+name,desc,'on/off','S','1',s,'MSB','S' if sg else 'U','1','0','0','1','0','1','',*cats))
        else: maps.append(row(cid,'0x%X'%a,prefix+name,desc,unit,'N','1',s,'MSB','S' if sg else 'U',fmtn(fac),fmtn(off),str(max(0,min(p,6))),fmtn(lo),fmtn(hi),'1','',*cats))
        used.append((a,a+w,cid,name)); return
    if ty=='eEindim' or R==1 or C==1:
        wx='X' if C>1 or R==1 else 'Y'
        ax,err=axis_entry(r,wx,n,'X',cats_axes,readonly_axes)
        if err: skipped.append((name,err)); return
        cid=newid(); dup_addr[a]=name
        maps.append(row(cid,'0x%X'%a,prefix+name,desc,unit,'Y',str(n),s,'MSB','S' if sg else 'U',fmtn(fac),fmtn(off),str(max(0,min(p,6))),fmtn(lo),fmtn(hi),'1',ax,*cats_main))
        used.append((a,a+w*n,cid,name)); return
    if ty=='eZweiInv': (xw,xn),(yw,yn)=('X',C),('Y',R)
    else: (xw,xn),(yw,yn)=('Y',R),('X',C)
    ax,e1=axis_entry(r,xw,xn,'X',cats_axes,readonly_axes); ay,e2=axis_entry(r,yw,yn,'Y',cats_axes,readonly_axes)
    if e1 or e2: skipped.append((name,e1 or e2)); return
    cid=newid(); dup_addr[a]=name
    maps.append(row(cid,'0x%X'%a,prefix+name,desc,unit,'Z',str(n),s,'MSB','S' if sg else 'U',fmtn(fac),fmtn(off),str(max(0,min(p,6))),fmtn(lo),fmtn(hi),'1',f'{ax}:{ay}',*cats_main))
    used.append((a,a+w*n,cid,name))
# ---- base calibration maps
order=sorted(U,key=lambda n:(E.GROUPS.index(E.group(n)) if E.group(n) in E.GROUPS else 99, E.kind(n), n))
notinc=[]
switched={re.sub(r'_SOTF_T\d$','',n) for n in M if '_SOTF_T' in n}
for n in order:
    rv=RV.get(n)
    if not rv or rv['Confidence'] not in ('high','medium'): notinc.append((n,rv['Confidence'] if rv else 'not found','placement not reliable in this bin')); continue
    if n not in M: notinc.append((n,'-','not in map list')); continue
    g=E.group(n); g=g if g in E.GROUPS else 'Fuel Control - Other'
    ed=' Edited vs stock P1B in this bin: '+('YES' if rv['Data vs stock']=='changed' else 'no')+'.'
    if n in switched: ed+=' This is the switch-position-0 (SOTF off) table - positions 1-5 are in the SOTF folder.'
    if rv['Confidence']=='medium': ed+=' Address confidence: medium - check values look right before editing.'
    k=E.kind(n)
    add_map(n,M[n],(folder((g,))+'' ,folder((g,k)),''),(folder((g,)),folder((g,'Axes')),''),
            ((folder((g,)),folder((g,'Single values')),''),(folder((g,)),folder((g,'Switches')),'')),'',False,ed)
# ---- SOTF per-position copies
sotf=sorted([n for n in M if re.search(r'_SOTF_T[1-5]$',n)],key=lambda n:(int(n[-1]),E.group(n.rsplit('_SOTF_',1)[0]),n))
for n in sotf:
    base=n.rsplit('_SOTF_',1)[0]; p=int(n[-1]); g=E.group(base)
    top=folder((SOTF_TOP,)); pos=folder((SOTF_TOP,f'Position {p}')); sub=folder((SOTF_TOP,f'Position {p}',f'P{p} {g}'))
    axf=folder((SOTF_TOP,'SOTF axes (read-only)'))
    add_map(n,M[n],(top,pos,sub),(top,axf,''),((top,pos,sub),(top,pos,sub)),f'P{p} ',True,
            f' HPT SOTF switch position {p} copy of {base} - used instead of the base table when the steering-wheel tune {p} is selected.')
# ---- overlap check
used.sort(); ov=[(x,y) for x,y in zip(used,used[1:]) if y[0]<x[1]]
# ---- write
comments=[
 '# EZ LYNK custom configuration - GM E41 L5P Duramax - '+LABEL,
 '# Full performance map list: injection timing (main SOI) / pilot (R1 R2) / main quantity and pulse width / post (A1-A4 P1) / rail pressure / boost and VGT / exhaust brake / torque-fuel-smoke limits / torque management / pedal / rev and speed limits / idle.',
 '# Plus the HP Tuners SOTF steering-wheel tune copies for switch positions 1 to 5 (33 tables per position). Position 0 = base tables in the normal folders.',
 '# Addresses are byte offsets in the exported .bin (ECU CPU address = file offset - 0x39FFE0 - shown in each DESC). All data big-endian (MSB).',
 '# Torque maps and axes are shown in lb-ft (ECU stores Nm). Boost/MAP pressures are absolute kPa. VGT % higher = vanes more closed.',
 '# Emissions / aftertreatment maps (EGR DPF SCR DEF NOx LNT catalyst regen combustion modes D S V) and DTC / diagnostic tables are intentionally NOT included.',
 '# Layout: table rows = X axis (slow index in memory) and columns = Y axis. Check: Park/Neutral torque (KtDTRC_M_EngTrqReqForRPM) 100% pedal row must read from high torque at low rpm down to ~0 at high rpm.',
 '# Axes with an address are editable and shared: changing one changes every map that uses it. MANUAL axes are read-only labels.',
]
with open(out,'w',newline='',encoding='latin1') as f:
    for c in comments: f.write(c+'\r\n')
    w=csv.writer(f,lineterminator='\r\n'); w.writerows([H]+folders+[row()]+maps)
base=out.rsplit('.',1)[0]
with open(base+'_NOT_INCLUDED.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['Name','Group','Confidence','Reason']); w.writerows([(n,E.group(n),c,why) for n,c,why in notinc]+[(n,E.group(n.rsplit('_SOTF_',1)[0]),'-',why) for n,why in skipped])
cnt=collections.Counter(x[5] for x in maps)
print(TAG,"rows:",len(maps),"types:",dict(cnt),"folders:",len(folders),"not included:",len(notinc),"skipped:",len(skipped),"overlaps:",len(ov))
for x,y in ov[:15]: print("  overlap",x[3],hex(x[0]),hex(x[1]),"|",y[3],hex(y[0]))
print("skipped sample:",skipped[:8])
