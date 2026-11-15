import sys, pickle, re
ins=pickle.load(open(sys.argv[1],'rb')); targets=[int(x,16) for x in sys.argv[2:]]
# track e_lis / e_add16i / e_or2i register constants within a sliding window (reset at blr / unconditional branch)
regs={}; hits={t:[] for t in targets}
for a,n,t,info in ins:
    m=re.match(r'e_lis r(\d+), (0x[0-9a-f]+)',t)
    if m: regs[int(m.group(1))]=int(m.group(2),16)<<16; continue
    m=re.match(r'e_add16i r(\d+), r(\d+), (-?0x[0-9a-f]+)',t)
    if m and int(m.group(2)) in regs:
        v=(regs[int(m.group(2))]+int(m.group(3),16))&0xFFFFFFFF; regs[int(m.group(1))]=v
        for tg in targets:
            if v==tg: hits[tg].append((a,'addr',t))
        continue
    m=re.match(r'e_or2i r(\d+), (0x[0-9a-f]+)',t)
    if m and int(m.group(1)) in regs:
        v=regs[int(m.group(1))]|int(m.group(2),16); regs[int(m.group(1))]=v
        for tg in targets:
            if v==tg: hits[tg].append((a,'addr',t))
        continue
    if info and info[0]=='mem':
        ra,disp=info[1],info[2]
        if ra in regs:
            v=(regs[ra]+disp)&0xFFFFFFFF
            for tg in targets:
                if v==tg: hits[tg].append((a,t.split()[0],t))
    if t.startswith(('se_blr','se_b ','e_b ')): regs={}
for tg in targets:
    print(f"\n{tg:#x}: {len(hits[tg])} refs")
    for a,k,t in hits[tg][:25]: print(f"   {a:#08x}  {t}")
