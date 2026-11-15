import sys,csv,math,collections,re,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import olscsv as O
csv.field_size_limit(1<<30)
new,old,binp,ez=sys.argv[1:5]; b=open(binp,'rb').read()
raw=open(new,encoding='latin1',newline='').read().split('\r\n')
hdr=raw[0].split(';'); rows=list(csv.DictReader(open(new,newline='',encoding='latin1'),delimiter=';'))
badw=sum(1 for r in rows if None in r or len(r)!=len(hdr))
W={'eByte':1,'eHiLo':2,'eHiLoHiLo':4,'eFloatHiLo':4}
insane=[];nonmono=[]
for r in rows:
    C,R,v=O.decode_map(b,r)
    if r['DataOrg']=='eFloatHiLo' and any(not math.isfinite(x) for x in v): insane.append(r['Name'])
    for w in 'XY':
        if r[f'Axis{w}.DataSrc']=='eRom':
            n=C if w=='X' else R; a=O.axis(b,r,w,n); d=[y-x for x,y in zip(a,a[1:])]
            if n>1 and not(all(x>=0 for x in d) or all(x<=0 for x in d)): nonmono.append((r['Name'],w))
iv=sorted((int(r['Fieldvalues.StartAddr'][1:],16),int(r['Fieldvalues.StartAddr'][1:],16)+int(r['Columns'])*int(r['Rows'])*W[r['DataOrg']],r['Name']) for r in rows)
ov=[(x[2],y[2]) for x,y in zip(iv,iv[1:]) if y[0]<x[1]]
names=collections.Counter(r['Name'] for r in rows)
OLD={}
for r in O.load(old): OLD.setdefault(r['Name'],r)
moved=sum(1 for r in rows if r['Name'] in OLD and OLD[r['Name']]['Fieldvalues.StartAddr']!=r['Fieldvalues.StartAddr'])
# consistency with EZ config
ezr=[x for x in csv.reader(l for l in open(ez,encoding='latin1',newline='').read().split('\r\n') if l and not l.startswith('#'))][1:]
ezA={x[2]:x[1] for x in ezr if x and x[0].startswith('C') and x[1]!='MANUAL'}
NA={r['Name']:'0x'+r['Fieldvalues.StartAddr'][1:].upper() for r in rows}
miss=[n for n in ezA if not n.endswith(' axis') and re.sub(r'^T\d ','',n) not in NA]
mism=[n for n in ezA if not n.endswith(' axis') and re.sub(r'^T\d ','',n) in NA and NA[re.sub(r'^T\d ','',n)]!=ezA[n]]
print(os.path.basename(new),"| rows",len(rows),"| bad width",badw,"| dup names",sum(1 for v in names.values() if v>1),"| float NaN",len(insane),"| non-monotonic axes",len(nonmono),nonmono[:3],"| data overlaps",len(ov),ov[:3])
print("   moved vs previous list:",moved,"of",sum(1 for r in rows if r['Name'] in OLD),"| EZ config maps missing from list:",len(miss),miss[:3],"| address mismatches with EZ:",len(mism),mism[:3])
