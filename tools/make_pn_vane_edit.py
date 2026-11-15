import sys,csv,os,struct,math,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import olscsv as O, names as N
csv.field_size_limit(1<<30)
D=sys.argv[1]; NM2LB=0.737562149
TAB=['KtAICC_Pct_VGT_FdFwd_LoBC1','KtAICC_Pct_VGT_FdFwd_MidBC1','KtAICC_Pct_VGT_FdFwd_SeaBC1','KtAICC_Pct_VGT_Max_LoBC','KtAICC_Pct_VGT_Max_MidBC','KtAICC_Pct_VGT_Max_SeaBC']
PLAN={'9843':dict(ml='sotf/WinOLS_L5P_9843_MapList_Named.csv',bin='sotf/sotf.bin',hiss=1,rumble=5),
      '9844':dict(ml='sotf44/WinOLS_L5P_9844_MapList_Named.csv',bin='sotf44/sotf44.bin',hiss=3,rumble=4)}
out={}
for tag,p in PLAN.items():
    M={r['IdName']:r for r in csv.DictReader(open(D+p['ml'],newline='',encoding='latin1'),delimiter=';')}
    b=bytearray(open(D+p['bin'],'rb').read()); log=[]
    # ---------- Park/Neutral free-rev table (same method as before: rolling-neutral pedal map A @ 20 kph)
    t=M['KtDTRC_M_EngTrqReqForRPM']; C,R,tv=O.decode_map(b,t)
    rpm=[float(x) for x in O.axis(b,t,'X',C)]; ped=[float(y) for y in O.axis(b,t,'Y',R)]
    def interp(x,xs,ys):
        if x<=xs[0]: return ys[0]
        for i in range(len(xs)-1):
            if x<=xs[i+1]: return ys[i]+(ys[i+1]-ys[i])*(x-xs[i])/(xs[i+1]-xs[i])
        return ys[-1]
    maps=[]
    for tn in range(0,6):
      for mp in 'ABC':
        pa=M[f'KtDTRC_P_M_PedProgReq{mp}'] if tn==0 else M[f'KtDTRC_P_M_PedProgReq{mp}_SOTF_T{tn}']
        PC,PR,pv=O.decode_map(b,pa); px=[float(x) for x in O.axis(b,pa,'X',PC)]; py=[float(y) for y in O.axis(b,pa,'Y',PR)]
        maps.append((PC,PR,pv,px,py))   # pedal maps A B C for tunes 0-5 -> mildest is used
    def roll_nm(pd,n):   # rolling-neutral torque request = pedal map A power (kW) at this pedal and RPM -> Nm; mildest of tunes 0-5
        vals=[]
        for PC,PR,pv,px,py in maps:
            kw=interp(pd,py,[interp(n,px,pv[j*PC:(j+1)*PC]) for j in range(PR)]); vals.append(kw*60000/(2*math.pi*n))
        return min(vals)
    addr=int(t['Fieldvalues.StartAddr'][1:],16); fac=float(t['Fieldvalues.Factor'])
    stock_raw=list(struct.unpack('>%dh'%(C*R),b[addr:addr+2*C*R])); new_raw=list(stock_raw)
    for r in range(R):
        for c in range(C):
            if ped[r]<8 or rpm[c]<2500: continue          # keep lift-off (0-1% pedal) and launch area (<2500 rpm) stock
            roll=roll_nm(ped[r],rpm[c])
            if roll>stock_raw[r*C+c]*fac: new_raw[r*C+c]=min(round(roll/fac),32767)
    struct.pack_into('>%dh'%(C*R),b,addr,*new_raw)
    log.append(('Park/Neutral Pedal Torque Request','KtDTRC_M_EngTrqReqForRPM',sum(1 for x,y in zip(stock_raw,new_raw) if x!=y)))
    pn=dict(rpm=rpm,ped=ped,stock=stock_raw,new=new_raw,fac=fac,addr=addr)
    # ---------- idle vanes: rows load<=30, cols 600/800 rpm
    vane={}
    for tb in TAB:
        src=M[f"{tb}_SOTF_T{p['hiss']}"]; Cc,Rr,_=O.decode_map(b,src)
        xs=[float(x) for x in O.axis(b,src,'X',Cc)]; ys=[float(y) for y in O.axis(b,src,'Y',Rr)]
        cols=[i for i,x in enumerate(xs) if 600<=x<=800]; rows=[j for j,y in enumerate(ys) if y<=30]
        def rawblk(tune):
            rr=M[f'{tb}_SOTF_T{tune}']; a=int(rr['Fieldvalues.StartAddr'][1:],16)
            return a,{(j,i):b[a+j*Cc+i] for j in rows for i in cols}
        _,H=rawblk(p['hiss']); _,Ru=rawblk(p['rumble'])
        f=float(src['Fieldvalues.Factor'])
        vane[tb]=dict(rows=[ys[j] for j in rows],cols=[xs[i] for i in cols],fac=f,hiss={},rumble={},before={})
        for tune in range(1,6):
            a,cur=rawblk(tune); target=H if tune<=3 else Ru
            vane[tb]['before'][tune]=[[cur[(j,i)]*f for i in cols] for j in rows]
            ch=0
            for (j,i),v in target.items():
                if b[a+j*Cc+i]!=v: b[a+j*Cc+i]=v; ch+=1
            if ch: log.append((N.readable(f'{tb}_SOTF_T{tune}'),f'{tb}_SOTF_T{tune}',ch))
        vane[tb]['hiss']=[[H[(j,i)]*f for i in cols] for j in rows]; vane[tb]['rumble']=[[Ru[(j,i)]*f for i in cols] for j in rows]
    outbin=D+f'deliver3/L5P_{tag}_PN-FreeRev_Hiss-T1-3_Rumble-T4-5.bin'
    os.makedirs(D+'deliver3',exist_ok=True); open(outbin,'wb').write(b)
    orig=open(D+p['bin'],'rb').read(); nd=sum(1 for x,y in zip(orig,b) if x!=y)
    out[tag]=dict(pn=pn,vane=vane,log=log,bytes_changed=nd)
    print(tag,'bytes changed',nd); [print('   ',x) for x in log]
json.dump(out,open(D+'deliver3/edit_data.json','w'))
