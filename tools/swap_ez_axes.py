import csv,sys,collections
src,dst=sys.argv[1:3]
raw=open(src,encoding='latin1',newline='').read().splitlines()
com=[l for l in raw if l.startswith('#')]; data=[l for l in raw if l and not l.startswith('#')]
rows=list(csv.reader(data))
z=[r for r in rows if len(r)>16 and r[5]=='Z']
xs=collections.Counter(r[16].split(':')[0] for r in z); ys=collections.Counter(r[16].split(':')[1] for r in z)
both=set(xs)&set(ys); assert not both, f'axis used as both X and Y: {both}'
for r in rows:
    if len(r)>16 and r[5]=='Z': a,b=r[16].split(':'); r[16]=f'{b}:{a}'
    elif r and r[0] in xs: r[5]='Y'
    elif r and r[0] in ys: r[5]='X'
fixed=[]
for c in com:
    if c.startswith('# Layout assumption'):
        c='# Layout: X axis = across the top (RPM) and Y axis = down the side (pedal % or load). Check: Park/Neutral table - the 100% pedal row (bottom) reads 1408.6 563.3 328.6 211.1 140.7 93.9 60.3 26.4 2.2 left to right (stock).'
    fixed.append(c)
with open(dst,'w',encoding='latin1',newline='') as f:
    for c in fixed: f.write(c+'\r\n')
    csv.writer(f,lineterminator='\r\n').writerows(rows)
print(dst.split('/')[-1],': swapped',len(z),'tables;',len(xs),'axes now Y,',len(ys),'axes now X')
