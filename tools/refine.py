import sys, pickle, difflib, bisect, collections
stock=open(sys.argv[1],'rb').read(); sotf=open(sys.argv[2],'rb').read()
CAL0=0x60000
cs=stock[CAL0-0x20000:0x200000-0x20000]; cn=sotf[CAL0+0x39FFE0:0x1FFFF0+0x39FFE0]
good=pickle.load(open(sys.argv[3],'rb'))
K=16
blocks=[(a,b,K) for a,b in good]
gaps=0; added=0
for (a1,b1),(a2,b2) in zip(good,good[1:]):
    d1=b1-a1; d2=b2-a2
    s0,s1=a1+K,a2; n0,n1=b1+K,b2
    if s1<=s0 or n1<=n0: continue
    if d1==d2 and cs[s0:s1]==cn[n0:n1]: continue
    if (s1-s0)>200000 or (n1-n0)>200000: continue
    gaps+=1
    sm=difflib.SequenceMatcher(None,cs[s0:s1],cn[n0:n1],autojunk=False)
    for m in sm.get_matching_blocks():
        if m.size>=4:
            blocks.append((s0+m.a,n0+m.b,m.size)); added+=1
blocks.sort()
# build a dense per-byte delta lookup from matching blocks (stock index -> sotf index)
pickle.dump(blocks,open(sys.argv[4],'wb'))
cov=sum(sz for _,_,sz in blocks)
print(f"refined {gaps} gaps, +{added} matching blocks; byte coverage of stock cal by matches: {cov/len(cs)*100:.1f}%")
