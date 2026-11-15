import sys, pickle, collections
stock=open(sys.argv[1],'rb').read(); sotf=open(sys.argv[2],'rb').read(); items=pickle.load(open(sys.argv[3],'rb'))
CAL0=0x60000
cs=stock[CAL0-0x20000:0x200000-0x20000]; cn=sotf[CAL0+0x39FFE0:0x1FFFF0+0x39FFE0]
for it in items.values(): it['ctx']=it['conf']
for rnd in range(4):
    lst=sorted((it['x'],k) for k,it in items.items() if it.get('y') is not None)
    hi=[(x,items[k]['y']-x,items[k]['L']) for x,k in lst if items[k]['ctx']=='high']
    import bisect
    hx=[x for x,_,_ in hi]
    up=moved=0
    for x,k in lst:
        it=items[k]
        if it['ctx']=='high': continue
        i=bisect.bisect_left(hx,x)-1; j=bisect.bisect_right(hx,x)
        while i>=0 and hi[i][0]+hi[i][2]>x: i-=1          # previous high item ending at/before x
        while j<len(hi) and hi[j][0]<x+it['L']: j+=1      # next high item starting at/after end
        if i<0 or j>=len(hi): continue
        (px,pd,pl),(nx,nd,_)=hi[i],hi[j]
        if pd!=nd: continue
        gap_before=x-(px+pl); gap_after=nx-(x+it['L'])
        if gap_before>0x40 or gap_after>0x40: continue
        if it['y']-x!=pd:
            it['y']=x+pd; moved+=1
        it['ctx']='high'; it['how']=it['how']+'+neighbours'; up+=1
    print(f"round {rnd}: upgraded {up}, re-placed {moved}")
    if up==0: break
for it in items.values(): it['conf']=it['ctx']; it['same']=cn[it['y']:it['y']+it['L']]==cs[it['x']:it['x']+it['L']] if it.get('y') is not None else None
pickle.dump(items,open(sys.argv[4],'wb'))
print("item confidence now:",collections.Counter(it['conf'] for it in items.values()))
