import sys,csv,struct,re,math,collections,pickle,glob,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ez_select as E, olscsv as O
csv.field_size_limit(1<<30)
D=sys.argv[1]; X=0x39FFE0; NM2LBFT=0.737562149
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ez_full2.py')).read().split('# ---------- selection')[0])
U,RES=pickle.load(open(D+'stockos/final_sel.pkl','rb')); U.discard('KtVOSC_M_DeltaVS_ToAxleTrq')  # WinOLS definition reads a float curve as 17 x int16
HPTAX=pickle.load(open(D+'stockos/hptaxes44.pkl','rb'))
LOSERS={t:pickle.load(open(D+f'stockos/overlap_losers_{t}.pkl','rb')) for t in ('43','44')}
REVIEW={'43':{r['Name']:r for r in csv.DictReader(open(D+'sotf/relocation_review.csv'))}}
H=['Unique ID','Address','NAME','DESC','UNITS','Type','Elements','Size','Endian','Signed','Math','Adder','Precision','MIN','MAX','LEVEL','AXIS','CATEGORY 1','CATEGORY 2','CATEGORY 3','MANUAL DATA']
def row(*v): v=list(v); return v+['']*(len(H)-len(v))
clean=lambda s: re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s.replace('Mapa:',''))).replace(',',' -').replace('"',"'").replace(';',' -').strip()
fmtn=lambda v: '%.12g'%v
def fmtv(v,p=3):
    t='%.*f'%(p,v); return (t.rstrip('0').rstrip('.') if '.' in t else t) or '0'
SZ={'eByte':('1',1,'B','b'),'eHiLo':('2',2,'H','h'),'eHiLoHiLo':('4',4,'I','i'),'eFloatHiLo':('F',4,'f','f')}
UNITGUESS=(('_Pct_','%'),('_phi_','deg'),('_T_','deg C'),('_n_','rpm'),('_v_','kph'),('_p_','kPa'),('_K_','factor'),('_k_','factor'),('_r_','ratio'),('_b_','on/off'),('_e_','enum'),('_Cnt_','count'),('_V_','mm^3'),('_M_','Nm'),('_t_','s'))
def unit_of(u,name):
    if u: return u
    for k,v in UNITGUESS:
        if k in name: return v
    return '-'
def scaling(fac,off,unit):
    if unit in ('Nm','Nm/s'): return fac*NM2LBFT,off*NM2LBFT,unit.replace('Nm','lb-ft'),True
    return fac,off,unit,False
def rng(org,signed,fac,off):
    if org=='eFloatHiLo': return (-999999*abs(fac)+off,999999*abs(fac)+off)
    bits={'eByte':8,'eHiLo':16,'eHiLoHiLo':32}[org]; lo,hi=(-(1<<(bits-1)),(1<<(bits-1))-1) if signed else (0,(1<<bits)-1)
    a,c=lo*fac+off,hi*fac+off; return (min(a,c),max(a,c))
def prec(p,default=2):
    return int(p) if p.lstrip('-').isdigit() and int(p)>=0 else default
def build(tag,binp,maplist,out,label):
    TB=open(binp,'rb').read()
    def raw(cpu,org,n,signed):
        s,w,u,sg=SZ[org]; a=cpu+X; return list(struct.unpack('>'+(sg if signed else u)*n,TB[a:a+w*n]))
    ML={}
    for r in O.load(maplist): ML.setdefault(r['Name'],r)
    folders=[]; F={}; fid=[0]
    def folder(path):
        if path in F: return F[path]
        fid[0]+=1; F[path]=f'F{fid[0]}'; folders.append(row('FFFF','0x0000',path[-1],'','0','C','0','0','0','0','0','0','0','0','0','0','0',F[path],'0','0')); return F[path]
    for g in E.GROUPS: folder((g,))
    SOTF_TOP='SOTF Steering-Wheel Tunes 1-5'; folder((SOTF_TOP,))
    maps=[]; nid=[0]; used=[]; notinc=[]; manual_cache={}; axis_cache={}
    def newid(): i=nid[0]; nid[0]+=1; return 'C%03d'%i
    def manual(vals,ez,unit,label,cats):
        key=(tuple(vals),ez,cats[0],cats[1])
        if key in manual_cache: return manual_cache[key]
        cid=newid(); manual_cache[key]=cid
        maps.append(row(cid,'MANUAL',label,'Read-only axis breakpoints.',unit or '-',ez,str(len(vals)),'0','0','0','0','0','0','0','0','0','',*cats,';'.join(vals))); return cid
    def axis(r,w,n,ez,cats,place,readonly,name):
        src=r[f'Axis{w}.DataSrc']; nm=r[f'Axis{w}.Name'] or 'axis'; un=unit_of(r[f'Axis{w}.Unit'],nm)
        if src in ('eRom','eRomDataIndex') and r[f'Axis{w}.DataOrg'] in SZ:
            org=r[f'Axis{w}.DataOrg']; sg=r[f'Axis{w}.bSigned']=='1'
            fac=float(r[f'Axis{w}.Factor'] or 1); off=float(r[f'Axis{w}.Offset'] or 0); fac,off,un2,_=scaling(fac,off,un)
            p=min(prec(r[f'Axis{w}.Precision']),4)
            if place and place[0]=='manual':
                return manual([fmtv(v,p) for v in place[1]],ez,un2,f'{nm} (read-only)',cats),None
            a,how,edit=place
            vals=[x*fac+off for x in raw(a,org,n,sg)]
            if any(math.isnan(v) or math.isinf(v) or abs(v)>1e7 for v in vals): return None,'axis values not sane'
            d=[y-x for x,y in zip(vals,vals[1:])]
            if n>1 and not (all(x>=0 for x in d) or all(x<=0 for x in d)): return None,'axis not monotonic - placement suspect'
            if readonly or not edit or ((a,n,org) in axis_cache and axis_cache[(a,n,org)][1]!=ez):
                return manual([fmtv(v,p) for v in vals],ez,un2,f'{nm} (read-only)',cats),None
            if (a,n,org) in axis_cache: return axis_cache[(a,n,org)][0],None
            cid=newid(); axis_cache[(a,n,org)]=(cid,ez); s,wd,_,_=SZ[org]; lo,hi=rng(org,sg,fac,off)
            maps.append(row(cid,'0x%X'%(a+X),f'{nm} axis',f'{nm} breakpoints (CPU 0x{a:X} - {how}). Shared: changing it changes every map that uses it.',un2,ez,str(n),s,'MSB','S' if sg else 'U',fmtn(fac),fmtn(off),str(p),fmtn(lo),fmtn(hi),'1','',*cats))
            used.append((a,a+wd*n,cid,nm+' axis',True)); return cid,None
        if src in ('eUserdef','eUserdefString'):
            v=r[f'Axis{w}.Values']; vals=[x for x in (v.split(';') if ';' in v else v.split()) if x][:n]
            vals=[re.sub(r'^C[ei][A-Z]{4}_e_','',x) for x in vals]
            if len(vals)==n: return manual(vals,ez,un,f'{nm} labels',cats),None
        return manual([str(i) for i in range(n)],ez,'index','Index',cats),None
    def add(name,r,cpu,how,axpl,cats_main,cats_ax,cats_n,cats_s,prefix,readonly_ax,extra):
        org=r['DataOrg']
        if org not in SZ: notinc.append((name,'unsupported data type')); return
        C,R=int(r['Columns']),int(r['Rows']); n=C*R; sg=r['bSigned']=='1'
        fac=float(r['Fieldvalues.Factor'] or 1); off=float(r['Fieldvalues.Offset'] or 0)
        fac,off,unit,conv=scaling(fac,off,unit_of(r['Fieldvalues.Unit'],name))
        vals=[x*fac+off for x in raw(cpu,org,n,sg)]
        if org=='eFloatHiLo' and any(math.isnan(v) or math.isinf(v) or abs(v)>1e7 for v in vals): notinc.append((name,'data not sane at resolved address')); return
        s,wd,_,_=SZ[org]; lo,hi=rng(org,sg,fac,off); p=prec(r['Precision'])
        if conv: p=1
        desc=f'{name} (CPU 0x{cpu:X} - address {how}).{extra} {clean(r["Comment"])[:400]}'.strip()
        if conv: desc+=' Shown in lb-ft (ECU stores Nm).'
        ty=r['Type']; ids=[]
        if ty=='eEinzel' or n==1:
            isw='_b_' in name and org!='eFloatHiLo' and fac==1 and off==0
            cid=newid()
            if isw: maps.append(row(cid,'0x%X'%(cpu+X),prefix+name,desc,'on/off','S','1',s,'MSB','S' if sg else 'U','1','0','0','1','0','1','',*cats_s))
            else: maps.append(row(cid,'0x%X'%(cpu+X),prefix+name,desc,unit,'N','1',s,'MSB','S' if sg else 'U',fmtn(fac),fmtn(off),str(min(p,6)),fmtn(lo),fmtn(hi),'1','',*cats_n))
            used.append((cpu,cpu+wd,cid,name,False)); return
        mark=len(maps); m0=nid[0]
        if ty=='eEindim' or R==1 or C==1:
            w='X' if (C>1 or R==1) else 'Y'
            ax,err=axis(r,w,n,'X',cats_ax,axpl.get(w),readonly_ax,name)
            if err: del maps[mark:]; notinc.append((name,err)); return
            cid=newid(); maps.append(row(cid,'0x%X'%(cpu+X),prefix+name,desc,unit,'Y',str(n),s,'MSB','S' if sg else 'U',fmtn(fac),fmtn(off),str(min(p,6)),fmtn(lo),fmtn(hi),'1',ax,*cats_main))
            used.append((cpu,cpu+wd*n,cid,name,False)); return
        if ty=='eZweiInv': (xw,xn),(yw,yn)=('X',C),('Y',R)
        else: (xw,xn),(yw,yn)=('Y',R),('X',C)
        ax,e1=axis(r,xw,xn,'X',cats_ax,axpl.get(xw),readonly_ax,name)
        ay,e2=(None,None) if e1 else axis(r,yw,yn,'Y',cats_ax,axpl.get(yw),readonly_ax,name)
        if e1 or e2: notinc.append((name,e1 or e2)); return
        cid=newid(); maps.append(row(cid,'0x%X'%(cpu+X),prefix+name,desc,unit,'Z',str(n),s,'MSB','S' if sg else 'U',fmtn(fac),fmtn(off),str(min(p,6)),fmtn(lo),fmtn(hi),'1',f'{ax}:{ay}',*cats_main))
        used.append((cpu,cpu+wd*n,cid,name,False))
    switched={re.sub(r'_SOTF_T\d$','',n) for n in ML if '_SOTF_T' in n}
    TBK=tag
    order=sorted(U,key=lambda n:(E.GROUPS.index(E.group(n)) if E.group(n) in E.GROUPS else 99,E.kind(n),n))
    for n in order:
        res,why=RES[tag][n]
        if n in LOSERS[tag]: notinc.append((n,'overlaps a table with stronger address evidence')); continue
        if not res:
            # 9844: OS tables whose axes only HPT can confirm
            if tag=='44' and why.startswith('axis') and RES['44'][n][0] is None:
                v=P44[n]; t=v['t'] if v['how'] in STRONG else None
                if t is not None:
                    axpl={}
                    for w,(ta,ha) in v['ax'].items():
                        if ta is not None and ha in STRONG: axpl[w]=(ta,ha,True)
                        elif (n,w) in HPTAX and HPTAX[(n,w)][0]: axpl[w]=('manual',HPTAX[(n,w)][1])
                    if len(axpl)==len(v['ax']): res={'data':(t,v['how']),**axpl}
            if not res: notinc.append((n,why)); continue
        g=E.group(n); g=g if g in E.GROUPS else 'Fuel Control - Other'
        t,how=res['data']; r=ST[n]; v=(P43 if tag=='43' else P44)[n]
        ed=' Edited vs stock P1B: '+('YES' if SB[sfile(v['s']):sfile(v['s'])+v['sz']]!=TB[t+X:t+X+v['sz']] else 'no')+'.'
        if n in switched: ed+=' Base table = steering-wheel tune 0 (SOTF off). Tunes 1-5 are in the SOTF folder.'
        axpl={w:res[w] for w in ('X','Y') if w in res}
        add(n,r,t,how,axpl,(folder((g,)),folder((g,E.kind(n))),''),(folder((g,)),folder((g,'Axes')),''),
            (folder((g,)),folder((g,'Single values')),''),(folder((g,)),folder((g,'Switches')),''),'',False,ed)
    # SOTF copies (HPT OS records; axes are HPT's own copies -> read-only)
    sot=sorted([n for n in ML if re.search(r'_SOTF_T[1-5]$',n)],key=lambda n:(int(n[-1]),E.group(n.rsplit('_SOTF_',1)[0]),n))
    for n in sot:
        base=n.rsplit('_SOTF_',1)[0]; p=int(n[-1]); g=E.group(base); r=ML[n]
        top=folder((SOTF_TOP,)); pos=folder((SOTF_TOP,f'Tune {p}')); sub=folder((SOTF_TOP,f'Tune {p}',f'T{p} {g}')); axf=folder((SOTF_TOP,'Tune axes (read-only)'))
        cpu=int(r['Fieldvalues.StartAddr'].lstrip('$'),16)-X
        axpl={}
        for w in 'XY':
            if r[f'Axis{w}.DataSrc'] in('eRom','eRomDataIndex'): axpl[w]=(int(r[f'Axis{w}.DataAddr'].lstrip('$'),16)-X,'HPT SOTF descriptor',False)
        add(n,r,cpu,'from HP Tuners SOTF record',axpl,(top,pos,sub),(top,axf,''),(top,pos,sub),(top,pos,sub),f'T{p} ',True,
            f' Steering-wheel tune {p} copy of {base} - used instead of the base table when tune {p} is selected.')
    # overlap check
    used.sort(); bad=set()
    for x,y in zip(used,used[1:]):
        if y[0]<x[1]: bad.add(y[2]); notinc.append((y[3],f'overlaps {x[3]} - left out'))
    if bad:
        keepm=[]; 
        for m in maps:
            if m[0] in bad: continue
            if m[16] and any(i in bad for i in m[16].split(':')): notinc.append((m[2],'uses an axis that was left out')); continue
            keepm.append(m)
        maps[:]=keepm
    comments=[
     '# EZ LYNK custom configuration - GM E41 L5P Duramax - '+label,
     '# Performance map list: injection timing (main SOI) / pilot (R1 R2) / main quantity and energizing time / post (A1-A4 P1) / rail pressure / boost and VGT / exhaust brake / torque-fuel-smoke limits / torque management / pedal / rev and speed limits / idle.',
     '# Plus the HP Tuners steering-wheel (SOTF) tune copies for tunes 1 to 5. Tune 0 (SOTF off) = the base tables in the normal folders.',
     '# Every address was checked against the ECU code (where the OS reads the table) and/or the HP Tuners SOTF records - see each DESC. Unverifiable maps are left out (separate NOT_INCLUDED list).',
     '# Addresses are byte offsets in the exported .bin (CPU address = file offset - 0x39FFE0). Big-endian (MSB).',
     '# Torque is shown in lb-ft (ECU stores Nm). Boost / MAP pressures are absolute kPa. VGT % higher = vanes more closed.',
     '# Emissions / aftertreatment maps (EGR DPF SCR DEF NOx LNT catalyst regen and the D S V combustion modes) and DTC / diagnostic tables are intentionally NOT included.',
     '# Layout: table rows = X axis (slow index) and columns = Y axis. Check: Park/Neutral torque (KtDTRC_M_EngTrqReqForRPM) 100% pedal row reads high torque at low rpm falling to ~0 at high rpm.',
     '# Axes with an address are editable and shared. MANUAL axes are read-only labels.',
    ]
    with open(out,'w',newline='',encoding='latin1') as f:
        for c in comments: f.write(c+'\r\n')
        w=csv.writer(f,lineterminator='\r\n'); w.writerows([H]+folders+[row()]+maps)
    with open(out.replace('.csv','_NOT_INCLUDED.csv'),'w',newline='') as f:
        w=csv.writer(f); w.writerow(['Map','Group','Why it is not in the EZ LYNK config'])
        for n,why in sorted(set(notinc)):
            why=why.replace('unresolved','address could not be verified').replace('conflict code vs relocation','ECU code and table-layout evidence disagree').replace('conflict relocation vs neighbours','layout evidence disagrees').replace('conflict code vs content','ECU code and table contents disagree')
            w.writerow([n,E.group(re.sub(r'_SOTF_T\d$','',n)),why])
    cnt=collections.Counter(m[5] for m in maps)
    data=[m for m in maps if m[5] in 'NSZY' or (m[5]=='X' and m[1]!='MANUAL' and not m[2].endswith(' axis'))]
    print(tag,"rows",len(maps),dict(cnt),"| maps (excl axes):",sum(1 for m in maps if not (m[1]=='MANUAL' or m[2].endswith(' axis'))),"| folders",len(folders),"| not included",len(set(notinc)))
    return maps
m43=build('43',D+'sotf/sotf.bin',D+'sotf/WinOLS_maplist_SOTF_9843.csv',D+'sotf/EZLYNK_FULL_MapList_9843.csv','HP Tuners SOTF OS 69709843 - cal E2015G5138011_P2B (9843 bin)')
m44=build('44',D+'sotf44/sotf44.bin',D+'sotf44/WinOLS_maplist_SOTF_9844.csv',D+'sotf44/EZLYNK_FULL_MapList_9844.csv','HP Tuners SOTF OS 69709844 - cal E2015G5141011_P2B (9844 bin)')
