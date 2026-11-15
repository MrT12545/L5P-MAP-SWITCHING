import sys,os,pickle,collections,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import calrefs as C
D=sys.argv[1]
recs,names=pickle.load(open(D+'sotf44/recs2.pkl','rb'))
ins=pickle.load(open(D+'sotf44/ins.pkl','rb'))
_,R=C.refs(D+'sotf44/ins.pkl')
BASE={13:0x40058000,14:0x40008000,15:0x40018000,16:0x40028000}
# RAM slot per switched map (one slot per map; same for all tunes?)
slot=collections.defaultdict(set)
for r in recs: slot[names[r['orig']]].add(r['ram'])
# index every memory access through base registers and lis-pairs to RAM
acc=collections.defaultdict(list)
lis={}
for k,(pc,n,t,info) in enumerate(ins):
    if not info: continue
    if info[0]=='e_lis': lis[info[1]]=(info[2],k)
    if info[0]=='mem':
        ra,d=info[1],info[2]
        if ra in BASE: acc[BASE[ra]+d].append((pc,t))
        elif ra in lis and k-lis[ra][1]<12 and lis[ra][0] in (0x4005,0x4006): acc[(lis[ra][0]<<16)+d].append((pc,t))
calsite=collections.defaultdict(list)
for pc,j,k,a in R: calsite[a].append(pc)
rows=[]
for orig,name in sorted(names.items(),key=lambda x:x[1]):
    sl=sorted(slot[name]); base_sites=sorted(set(calsite.get(orig,[])))
    loads=[(pc,t) for s in sl for pc,t in acc.get(s,[]) if re.match(r'(e_|se_)?lw',t)]
    stores=[(pc,t) for s in sl for pc,t in acc.get(s,[]) if re.match(r'(e_|se_)?stw',t)]
    rows.append((name,orig,sl,base_sites,loads,stores))
pickle.dump(rows,open(D+'sotf44/sotf_sites.pkl','wb'))
PATCH=0x464910
for name,orig,sl,bs,ld,st in rows:
    gm=[hex(p) for p in bs if p<PATCH]; hp=[hex(p) for p in bs if p>=PATCH]
    print(f'{name:34s} base CPU {orig:#08x} slot {",".join(hex(s) for s in sl)} | slot read at {len(ld)} code site(s): {[hex(p) for p,_ in ld][:4]} | base read directly by GM code at {len(gm)}: {gm[:4]} | by HPT patch: {len(hp)}')
