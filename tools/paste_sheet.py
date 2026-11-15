import json,sys
D=sys.argv[1]; d=json.load(open(D+'deliver3/edit_data.json')); L=[]; LB=0.737562149
def g(v): s='%.1f'%v; return '0.0' if s=='-0.0' else s
NICE={'KtAICC_Pct_VGT_FdFwd_LoBC1':'VGT Vane Position Feed-Forward - Low Baro (Altitude)','KtAICC_Pct_VGT_FdFwd_MidBC1':'VGT Vane Position Feed-Forward - Mid Baro',
      'KtAICC_Pct_VGT_FdFwd_SeaBC1':'VGT Vane Position Feed-Forward - Sea Level','KtAICC_Pct_VGT_Max_LoBC':'VGT Vane Position Max Limit - Low Baro (Altitude)',
      'KtAICC_Pct_VGT_Max_MidBC':'VGT Vane Position Max Limit - Mid Baro','KtAICC_Pct_VGT_Max_SeaBC':'VGT Vane Position Max Limit - Sea Level'}
for tag in ('9843','9844'):
    pn=d[tag]['pn']; rpm,ped=pn['rpm'],pn['ped']; C=len(rpm)
    def blk(vals,conv,trans=False,hdr=True):
        out=[]
        if not trans:
            if hdr: out.append('pedal%\\rpm\t'+'\t'.join('%g'%x for x in rpm))
            for r,p in enumerate(ped): out.append(('%g\t'%p if hdr else '')+'\t'.join(conv(vals[r*C+c]) for c in range(C)))
        else:
            if hdr: out.append('rpm\\pedal%\t'+'\t'.join('%g'%x for x in ped))
            for c,x in enumerate(rpm): out.append(('%g\t'%x if hdr else '')+'\t'.join(conv(vals[r*C+c]) for r in range(len(ped))))
        return out
    lb=lambda raw: g(raw*0.25*LB); nm=lambda raw: '%.2f'%(raw*0.25)
    L+=['='*100,f'{tag} BIN','='*100,'',
        f'PARK/NEUTRAL FREE-REV TABLE - {tag}  (map: Park/Neutral Pedal Torque Request, GM KtDTRC_M_EngTrqReqForRPM)',
        'Layout: rows = accelerator pedal % (0 1 8 12 20 32 50 86 100), columns = RPM (500 1000 1500 2000 2500 3000 3500 4000 6000). Paste the whole 9 x 9 table.',
        'Orientation check before pasting: STOCK 100% pedal / 500 rpm = 1408.6 lb-ft (1909.75 Nm); 0% pedal / 1500 rpm = -46.8 lb-ft (-63.50 Nm).','',
        '--- NEW, lb-ft (EZ LYNK), values only ---']+blk(pn['new'],lb,hdr=False)+['',
        '--- NEW, Nm (HP Tuners / WinOLS), values only ---']+blk(pn['new'],nm,hdr=False)+['',
        '--- NEW, lb-ft, with labels (to check) ---']+blk(pn['new'],lb)+['',
        '--- STOCK now in the file, lb-ft, with labels ---']+blk(pn['stock'],lb)+['',
        '--- STOCK now in the file, Nm, with labels ---']+blk(pn['stock'],nm)+['',
        '--- If your editor shows RPM down the side: NEW lb-ft transposed, values only ---']+blk(pn['new'],lb,trans=True,hdr=False)+['',
        '--- NEW Nm transposed, values only ---']+blk(pn['new'],nm,trans=True,hdr=False)+['','',
        f'IDLE HISS / RUMBLE - {tag}  (hiss = tunes 1-3, rumble = tunes 4-5)',
        'Each block is the idle corner only: rows = load 0 5 10 15 20 25 30, columns = 600 and 800 rpm. Select that 7 x 2 corner and paste.','']
    for tb,info in d[tag]['vane'].items():
        for t in range(1,6):
            want=info['hiss'] if t<=3 else info['rumble']; before=info['before'][str(t)]
            if [[round(x,3) for x in r] for r in before]==[[round(x,3) for x in r] for r in want]: continue
            L+=[f'--- Tune {t} - {NICE[tb]}  (GM {tb}_SOTF_T{t}) -> {"HISS" if t<=3 else "RUMBLE"}, values only ---']
            L+=['\t'.join(g(x) for x in row) for row in want]
            L+=['    before -> after (load: 600 rpm / 800 rpm):']+[f'    load {rl:g}: {g(bf[0])} / {g(bf[1])}  ->  {g(w[0])} / {g(w[1])}' for rl,bf,w in zip(info['rows'],before,want)]+['']
    L+=['']
open(D+'deliver3/PASTE_MAPS_PN_and_Hiss-Rumble.txt','w',newline='\r\n').write('\n'.join(L)+'\n')
print('sheet written',len(L),'lines')
