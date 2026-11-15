import csv,sys,struct,math,collections,re
cfg,binp=sys.argv[1:3]; b=open(binp,'rb').read()
lines=open(cfg,encoding='latin1',newline='').read().split('\r\n')
com=[l for l in lines if l.startswith('#')]; badq=[l for l in lines if l.startswith('"#')]
rows=[r for r in csv.reader([l for l in lines if l and not l.startswith('#')])]
H=rows[0]; body=[r for r in rows[1:] if any(r)]
err=[]
if len(H)!=21: err.append('header cols')
if any(len(r)!=21 for r in body): err.append('row width')
fold={r[17] for r in body if r[5]=='C'}; maps=[r for r in body if r[5]!='C']
ids=[r[0] for r in maps]; dup=[k for k,v in collections.Counter(ids).items() if v>1]
if dup: err.append(f'dup ids {dup[:3]}')
byid={r[0]:r for r in maps}
for r in maps:
    for c in r[17:20]:
        if c and c not in fold: err.append(f'unknown folder {c} in {r[0]}')
    if r[5] in 'NS' and r[6]!='1': err.append(f'N/S elements {r[0]}')
    if r[5] in 'NS' and not (r[18] and r[18]!='0'): err.append(f'N/S needs CAT2 {r[0]}')
    if r[5]=='Z':
        x,y=r[16].split(':'); X_,Y_=byid.get(x),byid.get(y)
        if not X_ or not Y_ or X_[5]!='X' or Y_[5]!='Y' or int(X_[6])*int(Y_[6])!=int(r[6]): err.append(f'Z axis mismatch {r[0]} {r[2]}')
    if r[5]=='Y' and r[16]:
        X_=byid.get(r[16])
        if not X_ or X_[5]!='X' or X_[6]!=r[6]: err.append(f'Y axis mismatch {r[0]} {r[2]}')
    if r[1]=='MANUAL' and len(r[20].split(';'))!=int(r[6]): err.append(f'manual count {r[0]}')
    if '"' in r[2] or ',' in r[2]: err.append('name punct')
# decode every address map
dec={}; insane=[]; ranges=[]
for r in maps:
    if r[1]=='MANUAL': continue
    a=int(r[1],16); n=int(r[6]); size=r[7]; sg=r[9]=='S'
    fmt={'1':'b' if sg else 'B','2':'h' if sg else 'H','4':'i' if sg else 'I','F':'f'}[size]; w=struct.calcsize(fmt)
    if a+w*n>len(b): insane.append((r[0],'past EOF')); continue
    v=[x*float(r[10])+float(r[11]) for x in struct.unpack('>'+fmt*n,b[a:a+w*n])]
    dec[r[0]]=v
    if any(math.isnan(x) or math.isinf(x) for x in v): insane.append((r[0],r[2],'nan'))
    if r[5]!='S' and (min(v)<float(r[13])-1e-6 or max(v)>float(r[14])+1e-6): insane.append((r[0],r[2],'outside MIN/MAX'))
# overlap of address maps
iv=sorted((int(r[1],16),int(r[1],16)+int(r[6])*{'1':1,'2':2,'4':4,'F':4}[r[7]],r[2]) for r in maps if r[1]!='MANUAL')
ov=[(x[2],y[2]) for x,y in zip(iv,iv[1:]) if y[0]<x[1]]
print(cfg.split('/')[-1],"| comments",len(com),"quoted#",len(badq),"| folders",len(fold),"| maps",len(maps),"| errors",len(err),err[:5],"| insane",len(insane),insane[:5],"| overlaps",len(ov),ov[:3])
# P/N table check
GMN=lambda r:(re.search(r'GM name: (\S+)',r[3]).group(1)+('_SOTF_T'+r[2][5] if r[2].startswith('Tune ') else '')) if re.search(r'GM name: (\S+)',r[3]) else r[2]
pn=[r for r in maps if GMN(r)=='KtDTRC_M_EngTrqReqForRPM']
if pn:
    r=pn[0]; x,y=r[16].split(':'); nx,ny=int(byid[x][6]),int(byid[y][6]); v=dec[r[0]]
    xa=dec.get(x) or byid[x][20].split(';'); ya=dec.get(y) or byid[y][20].split(';')
    print("  P/N X axis (across):",[round(float(q),1) for q in xa]); print("  P/N Y axis (down):",[round(float(q),1) for q in ya])
    print("  P/N last row, read X-across (Y = last):",[round(q,1) for q in v[(ny-1)*nx:ny*nx]], r[4])
inj=[GMN(r) for r in maps if r[1]!='MANUAL' and re.match(r'^KtFULC_(phi_SOI_M_Ptn\d|V_QntyR\d|t_DT_R\d|V_QntyA\d|t_DT_A\d|V_QntyM)',GMN(r))]
print("  injection families present:",collections.Counter(re.sub(r'^(T\d )?KtFULC_','',re.sub(r'_(Lo|Mid|Sea)?[A-Z]C\d.*$|_Ptn\d.*$|_PXL.*$|_CC\d.*$','',n)) for n in inj))
print("  SOTF tune tables:",sum(1 for r in maps if re.match(r'^Tune [1-5] ',r[2]) and r[1]!='MANUAL'))
