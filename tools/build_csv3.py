import sys,csv,struct,re,math,collections,pickle,glob,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import ez_select as E, olscsv as O, names as N
csv.field_size_limit(1<<30)
D=sys.argv[1]; X=0x39FFE0
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ez_full2.py')).read().split('# ---------- selection')[0])
HPTAX=pickle.load(open(D+'stockos/hptaxes44.pkl','rb'))
BROKEN={'KtVOSC_M_DeltaVS_ToAxleTrq':'definition in the original CSV reads a float curve as 17 x int16 - fix the definition before use'}
src=glob.glob('/root/.claude/uploads/*/1b5de558-*.csv')[0]
fh=open(src,newline='',encoding='latin1'); rd=csv.DictReader(fh,delimiter=';'); fields=rd.fieldnames; rows=list(rd)
hx=lambda x:'$%X'%x
LBL={'os':'confirmed by HP Tuners SOTF record','code+relocation agree':'ECU code reference + table layout','code+neighbours agree':'ECU code reference + neighbouring tables',
     'code+content':'ECU code reference + table contents','relocation+neighbours agree':'table layout + neighbouring tables','neighbours+content':'neighbouring tables + contents',
     'relocation+content':'table layout + contents','neighbours':'between two code-verified tables','code':'ECU code reference','content':'unique table contents',
     'relocation (one-side neighbour)':'table layout + one neighbouring table','code alignment via 9843':'ECU code aligned against the 9843 bin'}
def fmt(vals,prec):
    p=int(prec) if (prec or '').lstrip('-').isdigit() and int(prec)>=0 else 2
    return ' '.join(('%.*f'%(p,v)) if math.isfinite(v) else 'nan' for v in vals)
def build(tag,binp,old_maplist,out,notinc_out):
    TB=open(binp,'rb').read(); P=P43 if tag=='43' else P44
    OLD={}
    for r in O.load(old_maplist): OLD.setdefault(r['Name'],r)
    out_rows=[]; notinc=[]; stat=collections.Counter(); done=set(); HOW={}
    switched={re.sub(r'_SOTF_T\d$','',n) for n in OLD if '_SOTF_T' in n}
    for r0 in rows:
        n=r0['Name']
        if n in done: continue
        if n not in ST or r0['Fieldvalues.StartAddr.Cpu']!=ST[n]['Fieldvalues.StartAddr.Cpu']: continue   # duplicate definition rows
        done.add(n)
        if n in BROKEN: notinc.append((n,r0['FolderName'],BROKEN[n])); continue
        if n not in P43 or n not in P44: notinc.append((n,r0['FolderName'],'outside the calibration area or unsupported data type')); continue
        res,why=resolve(tag,n)
        if res is None and tag=='44' and why.startswith('axis'):
            v=P44[n]; t=v['t'] if v['how'] in STRONG else None
            if t is None and P43[n]['how'] in STRONG and P43[n]['t'] in G: t=G[P43[n]['t']]
            if t is not None:
                axpl={}
                for w,(ta,ha) in v['ax'].items():
                    if ta is not None and ha in STRONG: axpl[w]=(ta,ha,True)
                    elif (n,w) in HPTAX and HPTAX[(n,w)][0]: axpl[w]=('manual',HPTAX[(n,w)][1])
                if len(axpl)==len(v['ax']): res={'data':(t,v['how'] if v['how'] in STRONG else 'code alignment via 9843'),**axpl}
        if res is None:
            why=why.replace('unresolved','address could not be verified').replace('conflict code vs relocation','ECU code and table-layout evidence disagree').replace('conflict relocation vs neighbours','layout evidence disagrees').replace('conflict code vs content','ECU code and table contents disagree')
            notinc.append((n,r0['FolderName'],why)); stat['not verified']+=1; continue
        r=dict(r0); t,how=res['data']
        r['Fieldvalues.StartAddr.Cpu']=hx(t); r['Fieldvalues.StartAddr']=hx(t+X)
        C,Rr,vals=O.decode_map(TB,r)
        if r['DataOrg']=='eFloatHiLo' and any(not math.isfinite(x) or abs(x)>1e7 for x in vals):
            notinc.append((n,r0['FolderName'],'data not sane at resolved address')); stat['not verified']+=1; continue
        if r['Type']=='eZweiInv': vals=[vals[rw*C+c] for c in range(C) for rw in range(Rr)]
        r['Fieldvalues.Values']=fmt(vals,r['Precision'])
        notes=[f'[Address verified: {LBL.get(how,how)}]']
        bad_axis=False
        for w in ('X','Y'):
            if w not in res: continue
            nax=C if w=='X' else Rr
            if res[w][0]=='manual':
                vv=res[w][1]; r[f'Axis{w}.DataSrc']='eUserdef'; r[f'Axis{w}.DataAddr.Cpu']='$20000'; r[f'Axis{w}.DataAddr']='$0'
                r[f'Axis{w}.Values']=fmt(vv,r[f'Axis{w}.Precision']); notes.append(f'[{w} axis shown as fixed values from the HP Tuners table definition]'); continue
            a,ah,edit=res[w]
            if not edit:
                rr={'DataOrg':r[f'Axis{w}.DataOrg'],'Columns':str(nax),'Rows':'1','Fieldvalues.StartAddr':hx(a+X),'bSigned':r[f'Axis{w}.bSigned'],'Fieldvalues.Factor':r[f'Axis{w}.Factor'] or '1','Fieldvalues.Offset':r[f'Axis{w}.Offset'] or '0','bReciprocal':r[f'Axis{w}.bReciprocal']}
                vv=O.decode_map(TB,rr)[2]
                r[f'Axis{w}.DataSrc']='eUserdef'; r[f'Axis{w}.DataAddr.Cpu']='$20000'; r[f'Axis{w}.DataAddr']='$0'; r[f'Axis{w}.Values']=fmt(vv,r[f'Axis{w}.Precision'])
                notes.append(f'[{w} axis shown as fixed values - several identical copies in this bin]'); continue
            r[f'Axis{w}.DataAddr.Cpu']=hx(a); r[f'Axis{w}.DataAddr']=hx(a+X)
            rr={'DataOrg':r[f'Axis{w}.DataOrg'],'Columns':str(nax),'Rows':'1','Fieldvalues.StartAddr':hx(a+X),'bSigned':r[f'Axis{w}.bSigned'],'Fieldvalues.Factor':r[f'Axis{w}.Factor'] or '1','Fieldvalues.Offset':r[f'Axis{w}.Offset'] or '0','bReciprocal':r[f'Axis{w}.bReciprocal']}
            vv=O.decode_map(TB,rr)[2]
            if any(not math.isfinite(x) or abs(x)>1e7 for x in vv): bad_axis=True
            d=[y-x for x,y in zip(vv,vv[1:])]
            if nax>1 and not (all(x>=0 for x in d) or all(x<=0 for x in d)): bad_axis=True
            if r[f'Axis{w}.DataSrc']=='eRom': r[f'Axis{w}.Values']=fmt(vv,r[f'Axis{w}.Precision'])
        if bad_axis: notinc.append((n,r0['FolderName'],'axis values not sane at resolved address')); stat['not verified']+=1; continue
        if n in switched: notes.append('[SOTF: base table = steering-wheel tune 0 - tunes 1-5 use the _SOTF_Tn copies]')
        r['Comment']=' '.join(notes)+('<br>'+r['Comment'] if r['Comment'] else '')
        out_rows.append(r); stat['verified']+=1; HOW[n]=how
    # data overlap check
    W={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}
    def rank(h):
        if h=='os': return 0
        if h in ('code+relocation agree','code+neighbours agree','code+content'): return 1
        if h in ('code alignment via 9843','code'): return 2
        if h in ('relocation+neighbours agree','neighbours+content','relocation+content'): return 3
        return 4
    iv=sorted((int(r['Fieldvalues.StartAddr'][1:],16),int(r['Fieldvalues.StartAddr'][1:],16)+int(r['Columns'])*int(r['Rows'])*W[r['DataOrg']],r['Name']) for r in out_rows)
    drop=set()
    for i,x in enumerate(iv):
        for y in iv[i+1:i+40]:
            if y[0]>=x[1]: break
            if x[2] in drop or y[2] in drop: continue
            sx,sy=P[x[2]]['s'],P[y[2]]['s']
            if (y[0]-x[0])==(sy-sx): continue          # same overlap already exists in the stock definitions - keep both
            rx,ry=rank(HOW[x[2]]),rank(HOW[y[2]])
            losers=[y[2]] if rx<ry else [x[2]] if ry<rx else [x[2],y[2]]
            for l in losers:
                other=y[2] if l==x[2] else x[2]
                drop.add(l); notinc.append((l,ST[l]['FolderName'],f'overlaps {other} which has stronger address evidence - left out' if len(losers)==1 else f'overlaps {other} with equal evidence - both left out'))
    pickle.dump(drop,open(D+f'stockos/overlap_losers_named_{tag}.pkl','wb'))
    out_rows=[r for r in out_rows if r['Name'] not in drop]; stat['verified']-=len(drop); stat['not verified']+=len(drop)
    # SOTF copies from the HP Tuners records (unchanged from before)
    sot=[OLD[n] for n in OLD if re.search(r'_SOTF_T[1-5]$',n)]
    out_rows+=sot; stat['SOTF tune copies']=len(sot)
    # ---- descriptive names, folders, detailed descriptions
    NAME=N.unique_names([(r['Name'],N.readable(r['Name'])) for r in out_rows])
    QUNIT={'phi':'deg','T':'deg C','n':'rpm','v':'kph','p':'kPa','Pct':'%','pct':'%','V':'mm^3','M':'Nm','t':'s','K':'factor','k':'factor','r':'ratio','b':'on/off','e':'enum','Cnt':'count','P':'kW','m':'mg','U':'V','I':'A','dm':'g/s'}
    def uguess(u,nm):
        if u and u!='-': return u
        q=N.parse(re.sub(r'_SOTF_T\d$','',nm or '')); return QUNIT.get(q[2],'') if q and q[2] else ''
    for r in out_rows:
        gm=r['Name']; base=re.sub(r'_SOTF_T\d$','',gm); tm=re.search(r'_SOTF_T(\d)$',gm)
        defrow=ST.get(base,r); mod=E.module(base); perf=mod in E.WHITE; aft=bool(E.AFT.search(base) or E.EXCL.search(base))
        C,Rr,vals=O.decode_map(TB,r); cpu=int(r['Fieldvalues.StartAddr'][1:],16)-X
        axes={}
        for w in 'XY':
            src=r[f'Axis{w}.DataSrc']; nax=C if w=='X' else Rr
            if nax<=1 and not (C*Rr>1 and src!='eDataSrcNone'): continue
            if src in ('eRom','eRomDataIndex'):
                try: av=O.axis(TB,r,w,nax); axes[w]=(r[f'Axis{w}.Name'],uguess(r[f'Axis{w}.Unit'],r[f'Axis{w}.Name']),av[0],av[-1],nax)
                except Exception: pass
            elif src in ('eUserdef','eUserdefString'):
                v=[x for x in re.split(r'[; ]+',r[f'Axis{w}.Values']) if x]
                try: axes[w]=(r[f'Axis{w}.Name'],uguess(r[f'Axis{w}.Unit'],r[f'Axis{w}.Name']),float(v[0]),float(v[-1]),nax)
                except Exception: axes[w]=(r[f'Axis{w}.Name'],'',None,None,nax)
        if tm:
            g=E.group(base); folder=f'14 SOTF Steering-Wheel Tune {tm.group(1)} - {N.PERF_TITLE.get(g,g)}'
            ctx=dict(unit=uguess(r['Fieldvalues.Unit'],gm),vmin=min(vals),vmax=max(vals),how='HP Tuners SOTF record',cpu=cpu,axes=axes,perf=True,comment=defrow['Comment'],tune=int(tm.group(1)))
        else:
            cat=N.category(gm,E.group(base) if perf else None,perf,aft)
            if perf and not aft and cat[:2]<='13':
                sub='Single Values' if (r['Type']=='eEinzel' or C*Rr==1) else (N.subfolder(gm) or 'Tables and Curves')
                folder=f'{cat} - {sub}'
            else: folder=cat
            v=P[gm]; ed=SB[sfile(v['s']):sfile(v['s'])+v['sz']]!=TB[cpu+X:cpu+X+v['sz']]
            ctx=dict(unit=uguess(r['Fieldvalues.Unit'],gm),vmin=min(vals) if vals else None,vmax=max(vals) if vals else None,how=N.HOW.get(HOW.get(gm,''),HOW.get(gm,'')),cpu=cpu,axes=axes,
                     perf=perf and not aft,comment=defrow['Comment'],switched=gm in switched,edited=ed)
        r['Comment']=N.describe(gm,defrow,ctx,'<br>')
        r['IdName']=gm; r['Name']=NAME[gm]; r['FolderName']=f'{folder}: " "'
    out_rows.sort(key=lambda r:(r['FolderName'],r['Name']))
    with open(out,'w',newline='',encoding='latin1') as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter=';',lineterminator='\r\n'); w.writeheader(); w.writerows(out_rows)
    with open(notinc_out,'w',newline='') as f:
        w=csv.writer(f); w.writerow(['Map','WinOLS folder','Why it is not in the map list'])
        for n,fo,why in sorted(set(notinc)): w.writerow([n,re.sub(r'^"?(.*?): .*$',r'\1',fo),why])
    print(tag,dict(stat),"rows written",len(out_rows))
    return out_rows
build('43',D+'sotf/sotf.bin',D+'sotf/WinOLS_maplist_SOTF_9843.csv',D+'sotf/WinOLS_L5P_9843_MapList_Named.csv',D+'sotf/WinOLS_L5P_9843_MapList_NOT_INCLUDED.csv')
build('44',D+'sotf44/sotf44.bin',D+'sotf44/WinOLS_maplist_SOTF_9844.csv',D+'sotf44/WinOLS_L5P_9844_MapList_Named.csv',D+'sotf44/WinOLS_L5P_9844_MapList_NOT_INCLUDED.csv')
