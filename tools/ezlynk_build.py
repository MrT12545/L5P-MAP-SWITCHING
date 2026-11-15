import sys, csv, struct
csv.field_size_limit(1<<30)
binp, defs, out = sys.argv[1:4]; LABEL=sys.argv[4] if len(sys.argv)>4 else 'HP Tuners SOTF OS 69709843 - cal E2015G5138011_P2B'
b=open(binp,'rb').read()
rows={}; [rows.setdefault(r['Name'],r) for r in csv.DictReader(open(defs,newline='',encoding='latin1'),delimiter=';')]
H=['Unique ID','Address','NAME','DESC','UNITS','Type','Elements','Size','Endian','Signed','Math','Adder','Precision','MIN','MAX','LEVEL','AXIS','CATEGORY 1','CATEGORY 2','CATEGORY 3','MANUAL DATA']
def row(*v): v=list(v); return v+['']*(len(H)-len(v))
def folder(name,f): return row('FFFF','0x0000',name,'','0','C','0','0','0','0','0','0','0','0','0','0','0',f,'0','0')
hx=lambda s: '0x'+s.lstrip('$').upper()
NM2LBFT=0.737562149
comments=[
 '# EZ LYNK custom configuration - GM E41 L5P - '+LABEL,
 '# Addresses are byte offsets in the exported SOTF .bin. ECU CPU addresses are given in DESC. All data is big-endian (MSB).',
 '# Section A - Park/Neutral pedal torque table (KtDTRC_M_EngTrqReqForRPM) shown in lb-ft.',
 '# Section B - HP Tuners SOTF switch positions 1 to 5: VGT feed-forward / VGT max limit / boost set-point at Lo / Mid / Sea baro (45 tables).',
 '# Position 0 (switch off) uses the base calibration tables - not included here.',
 '# VGT % : higher = vanes more closed (more boost and drive pressure). Boost set-point is ABSOLUTE pressure in kPa.',
 '# Section B axes are read-only MANUAL axes (shared by all positions in the binary - edit them only in the base tune tool).',
 '# Layout assumption: table rows = X axis (slow index in memory) and columns = Y axis (fast index). Check: Park/Neutral 100% pedal row must read 1408.6 563.3 328.6 211.1 140.7 93.9 60.3 26.4 2.2 left to right. If it is transposed swap the X and Y Type letters on every axis row.',
]
pn=rows['KtDTRC_M_EngTrqReqForRPM']; tcpu=int(pn['Fieldvalues.StartAddr.Cpu'][1:],16); pcpu=int(pn['AxisY.DataAddr.Cpu'][1:],16); rcpu=int(pn['AxisX.DataAddr.Cpu'][1:],16)
f2=lambda c: '0x%X'%(c+0x39FFE0)
data=[H,
 folder('ECM maps','F1'), folder('Driver Demand','F2'), folder('Driver Demand Axes','F3'),
 folder('SOTF Turbo Vanes and Boost','F10'),
 *[folder(f'Switch Position {p}',f'F1{p}') for p in range(1,6)],
 folder('SOTF Vane and Boost Axes','F16'),
 row(),
 # ---- Section A
 row('C000',f2(tcpu),'Park/Neutral Pedal Torque Request',
     f'KtDTRC_M_EngTrqReqForRPM (CPU 0x{tcpu:X}).'+' Engine torque request vs pedal and RPM used at 0 kph (Park/Neutral and launch); blends to the normal pedal maps by 15 kph (KeDTRC_v_MinARM). Raise the 2500+ RPM columns to allow free rev to the fuel cut when stationary.',
     'lb-ft','Z','81','2','MSB','S',f'{0.25*NM2LBFT:.10f}','0','1','-200','1500','1','C001:C002','F1','F2',''),
 row('C001',f2(pcpu),'Park/Neutral Pedal Torque - Pedal axis',f'KnDTRC_Pct_EngReqForPPSAxis (CPU 0x{pcpu:X}). Accelerator pedal position breakpoints.','%','X','9','F','MSB','U','1','0','1','0','100','1','','F1','F3',''),
 row('C002',f2(rcpu),'Park/Neutral Pedal Torque - RPM axis',f'KnDTRC_n_EngReqForRPMAxis (CPU 0x{rcpu:X}). Engine speed breakpoints.','RPM','Y','9','F','MSB','U','1','0','0','0','8000','1','','F1','F3',''),
 row(),
]
# ---- Section B: shared MANUAL axes
def dec(addr_hex,org,signed,fac,n):
    off=int(addr_hex.lstrip('$'),16); fmt={'eHiLo':'h' if signed else 'H','eByte':'b' if signed else 'B'}[org]
    sz={'eHiLo':2,'eByte':1}[org]
    return [x*fac for x in struct.unpack('>'+fmt*n,b[off:off+sz*n])]
fmtv=lambda v: ('%g'%round(v,3))
fams=[('VGT Feed-Forward','KtAICC_Pct_VGT_FdFwd_{}BC1','Pressure controller (VGT) feed-forward base vane position - C1 normal combustion'),
      ('VGT Max Limit','KtAICC_Pct_VGT_Max_{}BC','Maximum boundary on VGT feed-forward / vane position - torque combustion modes EGR closed'),
      ('Boost Set-Point','KtAICC_p_BstSetPt_{}BC1','Boost pressure set-point base value (absolute) - C1 normal combustion')]
baro=[('Lo','Low Baro'),('Mid','Mid Baro'),('Sea','Sea Level')]
axis_ids={}; nid=200
for fname,pat,_ in fams:
    r=rows[pat.format('Sea')+'_SOTF_T1']
    for wx,ez,unit in (('Y','X','Load'),('X','Y','RPM')):   # WinOLS Y (rows, slow) -> EZ X ; WinOLS X (cols, fast) -> EZ Y
        n=int(r['Rows'] if wx=='Y' else r['Columns'])
        key=(r[f'Axis{wx}.DataAddr'],n)
        if key in axis_ids: continue
        vals=dec(r[f'Axis{wx}.DataAddr'],r[f'Axis{wx}.DataOrg'],r[f'Axis{wx}.bSigned']=='1',float(r[f'Axis{wx}.Factor']),n)
        cid=f'C{nid}'; nid+=1; axis_ids[key]=cid
        cpu=int(r[f'Axis{wx}.DataAddr'].lstrip('$'),16)-0x39FFE0
        data.append(row(cid,'MANUAL',f'SOTF {fname} - {unit} axis',f'{r[f"Axis{wx}.Name"]} (SOTF copy at CPU 0x{cpu:X}). Read-only.',unit,ez,str(n),
                        '0','0','0','0','0','0','0','0','0','','F1','F10','F16',';'.join(fmtv(v) for v in vals)))
data.append(row())
nid=100; checks=[]
for p in range(1,6):
    for fname,pat,desc in fams:
        for bk,bname in baro:
            name=pat.format(bk)+f'_SOTF_T{p}'; r=rows[name]
            C,R=int(r['Columns']),int(r['Rows']); org=r['DataOrg']; fac=float(r['Fieldvalues.Factor'])
            ax=axis_ids[(r['AxisY.DataAddr'],R)]; ay=axis_ids[(r['AxisX.DataAddr'],C)]
            off=int(r['Fieldvalues.StartAddr'].lstrip('$'),16); cpu=off-0x39FFE0
            vals=dec(r['Fieldvalues.StartAddr'],org,r['bSigned']=='1',fac,C*R); checks.append((name,min(vals),max(vals)))
            size='1' if org=='eByte' else '2'
            if 'Pct' in name: unit,prec,mn,mx='%','1','0','99.6'
            else: unit,prec,mn,mx='kPa','1','0','450'
            data.append(row(f'C{nid}',hx(r['Fieldvalues.StartAddr']),f'P{p} {fname} - {bname}',
                f'{pat.format(bk)} switch position {p} copy (CPU 0x{cpu:X}). {desc} at {bname.lower()}.',
                unit,'Z',str(C*R),size,'MSB','U',repr(fac),'0',prec,mn,mx,'1',f'{ax}:{ay}','F1','F10',f'F1{p}'))
            nid+=1
with open(out,'w',newline='') as f:
    for c in comments: f.write(c+'\r\n')
    w=csv.writer(f,lineterminator='\r\n'); w.writerows(data)
print("tables:",nid-100,"| axes:",len(axis_ids))
bad=[c for c in checks if not ((c[0].startswith('KtAICC_Pct') and 0<=c[1]<=c[2]<=100) or (c[0].startswith('KtAICC_p_') and 50<c[1]<=c[2]<450))]
print("value sanity failures:",bad)
print("ranges sample:",[(n.split('_SOTF_')[0][-14:]+'/T'+n[-1],round(a,1),round(b2,1)) for n,a,b2 in checks[:9]])
