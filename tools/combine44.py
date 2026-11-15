import sys, pickle, struct, math, collections
st=open(sys.argv[1],'rb').read(); a43=open(sys.argv[2],'rb').read(); b44=open(sys.argv[3],'rb').read()
direct=pickle.load(open(sys.argv[4],'rb')); via=pickle.load(open(sys.argv[5],'rb')); it43=pickle.load(open(sys.argv[6],'rb')); out=sys.argv[7]
CAL0=0x60000; cs=st[CAL0-0x20000:0x200000-0x20000]; O=0x3FFFE0; c43=a43[O:0x59FFD0]; c44=b44[O:0x59FFD0]
def elems(buf,y,L,esz):
    if y is None or y<0 or y+L>len(buf): return None
    n=L//esz; raw=buf[y:y+L]
    if esz==4: return [list(struct.unpack('>%df'%n,raw)),list(struct.unpack('>%di'%n,raw))]
    if esz==2: return [list(struct.unpack('>%dH'%n,raw)),list(struct.unpack('>%dh'%n,raw))]
    return [list(raw),list(struct.unpack('>%db'%n,raw))]
def mono(seq): return all(b>a for a,b in zip(seq,seq[1:])) or all(b<a for a,b in zip(seq,seq[1:]))
def ok_mono(src,cand):
    if src is None or cand is None or len(src[0])<3: return None
    if not any(mono(s) for s in src if all(isinstance(v,int) or math.isfinite(v) for v in s)): return None
    return any(mono(c) for c in cand if all(isinstance(v,int) or math.isfinite(v) for v in c))
def score(k,y):
    it=direct[k]; L=it['L']; esz=it['esz']; x=it['x']
    if y is None or y<0 or y+L>len(c44): return -9
    s=0
    if c44[y:y+L]==cs[x:x+L]: s+=4
    y43=it43[k].get('y') if k in it43 else None
    if y43 is not None and c44[y:y+L]==c43[y43:y43+L]: s+=4
    m=ok_mono(elems(cs,x,L,esz),elems(c44,y,L,esz))
    if m is True: s+=2
    if m is False: s-=6
    if esz==4:
        f=elems(c44,y,L,4)[0]
        if any((not math.isfinite(v)) or abs(v)>1e12 for v in f): s-=4
    return s
final={}; stat=collections.Counter()
for k,d in direct.items():
    yd=d.get('y'); v=via.get(k); yv=v.get('y') if v else None
    cd=d.get('conf','low'); cv=v.get('conf','low') if v else 'low'
    if v and v.get('confA')=='low' and cv=='high' and not v.get('same'): cv='medium'   # carried an uncertain 9843 guess
    if yd==yv and yd is not None:
        y=yd; conf='high' if 'high' in (cd,cv) else ('medium' if 'medium' in (cd,cv) else 'low'); how='agree'
    else:
        sd,sv=score(k,yd),score(k,yv)
        rank={'high':2,'medium':1,'low':0}
        if (sv,rank[cv])>(sd,rank[cd]): y,conf,how=yv,cv,'via9843'
        else: y,conf,how=yd,cd,'direct'
        if max(sd,sv)>=4 and conf!='high': conf='high'
    final[k]=dict(d); final[k].update(y=y,conf=conf,how=how,same=(y is not None and c44[y:y+d['L']]==cs[d['x']:d['x']+d['L']]))
    stat[(how,conf)]+=1
pickle.dump(final,open(out,'wb'))
for k,v in sorted(stat.items(),key=lambda kv:-kv[1]): print("  ",k,v)
