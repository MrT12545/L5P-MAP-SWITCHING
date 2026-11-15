import sys,csv,os,struct,math,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import olscsv as O
csv.field_size_limit(1<<30)
D=sys.argv[1]
M={r['IdName']:r for r in csv.DictReader(open(D+'sotf44/WinOLS_L5P_9844_MapList_Named.csv',newline='',encoding='latin1'),delimiter=';')}
src=open(D+'clean1110_in/clean_1110.bin','rb').read(); b=bytearray(src); log=[]; out={}
def interp(x,xs,ys):
    if x<=xs[0]: return ys[0]
    for i in range(len(xs)-1):
        if x<=xs[i+1]: return ys[i]+(ys[i+1]-ys[i])*(x-xs[i])/(xs[i+1]-xs[i])
    return ys[-1]
# ---- Park/Neutral: rolling-neutral request from the 11-10 pedal maps (mildest of A/B/C, tunes 0-5); only >=2500 rpm and >=8% pedal, only raised
t=M['KtDTRC_M_EngTrqReqForRPM']; C,R,_=O.decode_map(src,t)
rpm=[float(x) for x in O.axis(src,t,'X',C)]; ped=[float(y) for y in O.axis(src,t,'Y',R)]
maps=[]
for tn in range(6):
    for mp in 'ABC':
        pa=M[f'KtDTRC_P_M_PedProgReq{mp}'] if tn==0 else M[f'KtDTRC_P_M_PedProgReq{mp}_SOTF_T{tn}']
        PC,PR,pv=O.decode_map(src,pa); maps.append((PC,PR,pv,[float(x) for x in O.axis(src,pa,'X',PC)],[float(y) for y in O.axis(src,pa,'Y',PR)]))
def roll(pd,n): return min(interp(pd,py,[interp(n,px,pv[j*PC:(j+1)*PC]) for j in range(PR)])*60000/(2*math.pi*n) for PC,PR,pv,px,py in maps)
addr=int(t['Fieldvalues.StartAddr'][1:],16); fac=float(t['Fieldvalues.Factor'])
stock=list(struct.unpack('>81h',src[addr:addr+162])); new=list(stock)
for r in range(R):
    for c in range(C):
        if ped[r]<8 or rpm[c]<2500: continue
        v=roll(ped[r],rpm[c])
        if v>stock[r*C+c]*fac: new[r*C+c]=min(round(v/fac),32767)
struct.pack_into('>81h',b,addr,*new); log.append(('Park/Neutral Pedal Torque Request',sum(x!=y for x,y in zip(stock,new))))
out['pn']=dict(rpm=rpm,ped=ped,stock=stock,new=new)
# ---- idle vanes: hiss T1-T3 = tune 3's own idle corner (load 0-30, 600/800 rpm); rumble T4-T5 = vanes open (0 %) at load 0-10, 600/800 rpm
out['vane']={}
for tb in ('KtAICC_Pct_VGT_FdFwd_SeaBC1','KtAICC_Pct_VGT_FdFwd_MidBC1','KtAICC_Pct_VGT_FdFwd_LoBC1','KtAICC_Pct_VGT_Max_SeaBC','KtAICC_Pct_VGT_Max_MidBC','KtAICC_Pct_VGT_Max_LoBC'):
    r3=M[f'{tb}_SOTF_T3']; Cc,Rr,_=O.decode_map(src,r3)
    xs=[float(x) for x in O.axis(src,r3,'X',Cc)]; ys=[float(y) for y in O.axis(src,r3,'Y',Rr)]; f=float(r3['Fieldvalues.Factor'])
    cols=[i for i,x in enumerate(xs) if 600<=x<=800]; rows30=[j for j,y in enumerate(ys) if y<=30]
    a3=int(r3['Fieldvalues.StartAddr'][1:],16); hiss={(j,i):src[a3+j*Cc+i] for j in rows30 for i in cols}
    out['vane'][tb]=dict(rows=[ys[j] for j in rows30],cols=[xs[i] for i in cols],before={},after={})
    for tn in range(1,6):
        a=int(M[f'{tb}_SOTF_T{tn}']['Fieldvalues.StartAddr'][1:],16)
        out['vane'][tb]['before'][tn]=[[src[a+j*Cc+i]*f for i in cols] for j in rows30]
        if tn<=3: target=hiss
        else: target={(j,i):0 for j in rows30 for i in cols if ys[j]<=10}
        ch=0
        for (j,i),v in target.items():
            if b[a+j*Cc+i]!=v: b[a+j*Cc+i]=v; ch+=1
        out['vane'][tb]['after'][tn]=[[b[a+j*Cc+i]*f for i in cols] for j in rows30]
        if ch: log.append((f'Tune {tn} {tb}',ch))
os.makedirs(D+'deliver4',exist_ok=True)
open(D+'deliver4/Nelly_11-10-26_V2_PN-FreeRev_Hiss-T1-3_Rumble-T4-5.bin','wb').write(b)
json.dump(out,open(D+'deliver4/edit_data_1110.json','w'))
for x in log: print(' ',x)
