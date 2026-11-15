import sys, csv, pickle, struct, math, collections, re
sys.path.insert(0, sys.argv[1]); import olscsv
csv.field_size_limit(1<<30)
stock=open(sys.argv[2],'rb').read(); sotf=open(sys.argv[3],'rb').read()
items=pickle.load(open(sys.argv[4],'rb')); recs,orignames=pickle.load(open(sys.argv[5],'rb'))
suspects={n for n,*_ in pickle.load(open(sys.argv[6],'rb'))}
src=sys.argv[7]; out_defs=sys.argv[8]; out_review=sys.argv[9]; out_sotf=sys.argv[10]
CAL0=0x60000; F=lambda cpu: cpu+0x39FFE0
ESZ={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}
fh=open(src,newline='',encoding='latin1'); rd=csv.DictReader(fh,delimiter=';'); fields=rd.fieldnames; rows=list(rd)
OS_FIX={}
switched={v:k for k,v in orignames.items()}            # name -> base cpu in SOTF
def h(x): return '$%X'%x
def fmt(vals,prec):
    p=int(prec or 0); return ' '.join(('%.*f'%(p,v)) if math.isfinite(v) else 'nan' for v in vals)
def values_for(r,fileoff):
    rr=dict(r); rr['Fieldvalues.StartAddr']=h(fileoff)
    C,R,v=olscsv.decode_map(sotf,rr)
    if r['Type']=='eZweiInv': v=[v[rw*C+c] for c in range(C) for rw in range(R)]
    return fmt(v,r['Precision'])
def axis_values(r,ax,fileoff,n):
    rr={'DataOrg':r[f'Axis{ax}.DataOrg'],'Columns':str(n),'Rows':'1','Fieldvalues.StartAddr':h(fileoff),'bSigned':r[f'Axis{ax}.bSigned'],
        'Fieldvalues.Factor':r[f'Axis{ax}.Factor'] or '1','Fieldvalues.Offset':r[f'Axis{ax}.Offset'] or '0','bReciprocal':r[f'Axis{ax}.bReciprocal']}
    return fmt(olscsv.decode_map(sotf,rr)[2],r[f'Axis{ax}.Precision'])
def tag(r,text): r['Comment']=(r['Comment']+'<br>' if r['Comment'] else '')+text
out=[]; review=[]; stat=collections.Counter()
for r in rows:
    r=dict(r); C,R=int(r['Columns']),int(r['Rows']); L=ESZ[r['DataOrg']]*C*R
    scpu=int(r['Fieldvalues.StartAddr.Cpu'][1:],16); it=items.get((scpu,L))
    if r['Name'] in switched: ncpu=switched[r['Name']]; conf='confirmed-by-OS'; how='SOTF OS table'
    elif r['Name'] in OS_FIX: ncpu=OS_FIX[r['Name']]; conf='confirmed-by-OS'; how='SOTF OS table'
    elif it and it.get('y') is not None: ncpu=it['y']+CAL0; conf=it['conf']; how=it['how']
    else: ncpu=None; conf='unplaced'; how='-'
    if r['Name'] in suspects and conf not in ('confirmed-by-OS',): conf='low'
    if ncpu is None: stat['unplaced']+=1; continue
    r['Fieldvalues.StartAddr.Cpu']=h(ncpu); r['Fieldvalues.StartAddr']=h(F(ncpu))
    r['Fieldvalues.Values']=values_for(r,F(ncpu))
    axconf=[]
    for ax in 'XY':
        if not r[f'Axis{ax}.DataSrc'].startswith('eRom'): continue
        n=C if ax=='X' else R; acpu=int(r[f'Axis{ax}.DataAddr.Cpu'][1:],16)
        ait=items.get((acpu,ESZ.get(r[f'Axis{ax}.DataOrg'],2)*n))
        if not ait or ait.get('y') is None: axconf.append('low'); continue
        nac=ait['y']+CAL0; r[f'Axis{ax}.DataAddr.Cpu']=h(nac); r[f'Axis{ax}.DataAddr']=h(F(nac)); axconf.append(ait['conf'])
        if r[f'Axis{ax}.DataSrc']=='eRom': r[f'Axis{ax}.Values']=axis_values(r,ax,F(nac),n)
    rank={'confirmed-by-OS':0,'high':1,'medium':2,'low':3}
    worst=max([conf]+axconf,key=lambda c:rank.get(c,3))
    if worst in ('medium','low'): tag(r,f'[SOTF-bin relocation: {worst} confidence - verify]')
    if r['Name'] in switched: tag(r,'[SOTF: base map - switch positions 1-5 use the SOTF_Tune_n copies]')
    out.append(r); stat[worst]+=1
    if not r['FolderName'].startswith('"NEW') and not r['FolderName'].startswith('NEW'):
        same=sotf[F(ncpu):F(ncpu)+L]==stock[scpu-0x20000:scpu-0x20000+L]
        review.append([r['Name'],re.sub(r'^"?(.*?): .*$',r'\1',r['FolderName']),h(scpu),h(ncpu),h(F(ncpu)),how,worst,'same' if same else 'changed'])
# ---- SOTF copies
DT={0x11:('eFloatHiLo','1'),0x21:('eByte','0'),0x31:('eByte','1'),0x22:('eHiLo','0'),0x32:('eHiLo','1')}
base_rows={}
for r in out:
    if r['Name'] in switched and not r['FolderName'].startswith('"NEW') and not r['FolderName'].startswith('NEW'): base_rows.setdefault(r['Name'],r)
sotf_summary=[]
for rc in sorted(recs,key=lambda x:(x['tune'],x['rec'])):
    name=orignames[rc['orig']]; b=dict(base_rows[name]); t=rc['tune']
    if rc['typ']==3: dtype=rc['w0']&0xffff
    else: dtype=rc['w0']&0xffff
    org,sg=DT[dtype]
    if org!=b['DataOrg']: b['Fieldvalues.Factor']='1' if org=='eFloatHiLo' else str((rc['w1']&0xffff)/(rc['w1']>>16)); b['Fieldvalues.Offset']='0'
    b['DataOrg']=org; b['bSigned']=sg
    b['Name']=f"{name}_SOTF_T{t}"; b['IdName']=b['Name']; b['FolderName']=f'SOTF_Tune_{t}: " "'
    b['Fieldvalues.StartAddr.Cpu']=h(rc['dp']); b['Fieldvalues.StartAddr']=h(F(rc['dp']))
    axes=[('X',rc['xp'])]+([('Y',rc['yp'])] if rc['typ']==3 and rc['yp'] else [])
    for ax,dptr in axes:
        cnt,typ,sn,sd,ptr=struct.unpack('>HHHHI',sotf[F(dptr):F(dptr)+12])
        aorg,asg=DT[typ]
        b[f'Axis{ax}.DataSrc']='eRom'; b[f'Axis{ax}.DataAddr.Cpu']=h(ptr); b[f'Axis{ax}.DataAddr']=h(F(ptr))
        b[f'Axis{ax}.DataOrg']=aorg; b[f'Axis{ax}.bSigned']=asg; b[f'Axis{ax}.Factor']=repr(sd/sn); b[f'Axis{ax}.Offset']='0'
        b[f'Axis{ax}.Values']=axis_values(b,ax,F(ptr),cnt)
    b['Comment']=f"SOTF switch position {t} copy of {name} (base at cpu {h(rc['orig'])}); selected via RAM slot {h(rc['ram'])}<br>"+b['Comment'].split('<br>[SOTF')[0]
    b['Fieldvalues.Values']=values_for(b,F(rc['dp']))
    out.append(b); stat['sotf-copy']+=1
    sotf_summary.append([t,name,h(rc['orig']),h(rc['dp']),h(F(rc['dp'])),f"{b['Columns']}x{b['Rows']}",org,b['Fieldvalues.Unit'],
                         b['AxisX.DataAddr.Cpu'], b['AxisY.DataAddr.Cpu'] if len(axes)>1 else '-'])
with open(out_defs,'w',newline='',encoding='latin1') as f:
    w=csv.DictWriter(f,fieldnames=fields,delimiter=';',lineterminator='\r\n'); w.writeheader(); w.writerows(out)
with open(out_review,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['Name','Folder','Stock CPU (P1B)','SOTF CPU','SOTF bin offset','Placement','Confidence','Data vs stock']); w.writerows(review)
with open(out_sotf,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['Tune','Base map','Base CPU','Copy CPU','Copy bin offset','Size','DataOrg','Unit','X axis CPU','Y axis CPU']); w.writerows(sotf_summary)
print("rows written:",len(out)); print(dict(stat))
