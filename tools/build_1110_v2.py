import sys,csv,os,struct,math,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import olscsv as O
csv.field_size_limit(1<<30)
D=sys.argv[1]
M={r['IdName']:r for r in csv.DictReader(open(D+'sotf44/WinOLS_L5P_9844_MapList_Named.csv',newline='',encoding='latin1'),delimiter=';')}
src=open(D+'clean1110_in/clean_1110.bin','rb').read()
prev=open(D+'deliver4/Nelly_11-10-26_V2_PN-FreeRev_Hiss-T1-3_Rumble-T4-5.bin','rb').read()   # hiss/rumble already correct in here
b=bytearray(prev)
def interp(x,xs,ys):
    if x<=xs[0]: return ys[0]
    for i in range(len(xs)-1):
        if x<=xs[i+1]: return ys[i]+(ys[i+1]-ys[i])*(x-xs[i])/(xs[i+1]-xs[i])
    return ys[-1]
nv=O.decode_map(src,M['KeDTRC_r_VTS_NV_Ratio'])[2][0]; en=O.decode_map(src,M['KeDTRC_b_EnblRPM_PedProg'])[2][0]
t=M['KtDTRC_M_EngTrqReqForRPM']; C,R,_=O.decode_map(src,t)
rpm=[float(x) for x in O.axis(src,t,'X',C)]; ped=[float(y) for y in O.axis(src,t,'Y',R)]
maps=[]
for tn in (0,):           # base tune = tunes 4 and 5 (Map A = B = C there)
    for mp in 'A':
        pa=M[f'KtDTRC_P_M_PedProgReq{mp}'] if tn==0 else M[f'KtDTRC_P_M_PedProgReq{mp}_SOTF_T{tn}']
        PC,PR,pv=O.decode_map(src,pa); maps.append((tn,mp,PC,PR,pv,[float(x) for x in O.axis(src,pa,'X',PC)],[float(y) for y in O.axis(src,pa,'Y',PR)]))
VSPD=30.0   # typical rolling-neutral road speed (kph); with ratio 1.0 the lookup sits below the first column anyway
def roll(pd,n):
    out=[]
    for tn,mp,PC,PR,pv,px,py in maps:
        look=VSPD*nv if en else n
        kw=interp(pd,py,[interp(look,px,pv[j*PC:(j+1)*PC]) for j in range(PR)]); out.append((kw*60000/(2*math.pi*n),tn,mp,kw))
    return min(out)
addr=int(t['Fieldvalues.StartAddr'][1:],16); fac=float(t['Fieldvalues.Factor'])
stock=list(struct.unpack('>81h',src[addr:addr+162])); new=list(stock); who={}
for r in range(R):
    for c in range(C):
        if ped[r]<8 or rpm[c]<2500: continue
        v,tn,mp,kw=roll(ped[r],rpm[c])
        if v>stock[r*C+c]*fac: new[r*C+c]=min(round(v/fac),32767); who[(ped[r],rpm[c])]=(tn,mp,round(kw,1))
struct.pack_into('>81h',b,addr,*new)
os.makedirs(D+'deliver5',exist_ok=True)
A=D+'deliver5/Nelly_11-10-26_V2_A_daily_PN-faithful_Hiss1-3_Rumble4-5.bin'; open(A,'wb').write(b)
bb=bytearray(b); ua=int(M['KeDTRC_b_UseBaseProgOnly']['Fieldvalues.StartAddr'][1:],16); assert bb[ua]==0; bb[ua]=1
B=D+'deliver5/Nelly_11-10-26_V2_B_TEST_UseBaseProgOnly-ON.bin'; open(B,'wb').write(bb)
json.dump(dict(rpm=rpm,ped=ped,stock=stock,new=new,nv=nv,en=en),open(D+'deliver5/pn_1110_faithful.json','w'))
print(f'pedal-map lookup: EnblRPM_PedProg={en:g}, n/v ratio={nv:g} -> lookup value {VSPD*nv:g} vs first column {maps[0][5][0]:g}')
print('mildest tune/map at 100% pedal 3000 rpm:',who.get((100.0,3000.0)))
print('NEW Park/Neutral (lb-ft):')
for r in range(R): print('  %4g%% '%ped[r]+' '.join(f'{new[r*C+c]*0.25*0.737562149:7.1f}' for c in range(C)))
print('UseBaseProgOnly file offset',hex(ua))
