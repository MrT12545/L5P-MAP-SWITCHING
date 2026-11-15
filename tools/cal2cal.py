# anchors + shift segments between two SOTF-layout bins (both cal at file 0x3FFFE0, CPU 0x60000)
import sys, pickle, collections
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read()
O=0x3FFFE0; END=0x59FFD0
ca=a[O:END]; cb=b[O:END]; K=16
def windows(buf):
    d=collections.defaultdict(list)
    for i in range(0,len(buf)-K,2):
        w=buf[i:i+K]
        if len(set(w))>=8: d[w].append(i)
    return d
wa=windows(ca); wb=windows(cb)
anch=sorted((i[0],wb[w][0]) for w,i in wa.items() if len(i)==1 and len(wb.get(w,()))==1)
dl=[y-x for x,y in anch]
good=[anch[k] for k in range(len(anch)) if (k>0 and dl[k-1]==dl[k]) or (k+1<len(anch) and dl[k+1]==dl[k])]
pickle.dump(good,open(sys.argv[3],'wb'))
tr=sum(1 for (x1,y1),(x2,y2) in zip(good,good[1:]) if y1-x1!=y2-x2)
same=sum(1 for i in range(min(len(ca),len(cb))) if ca[i]==cb[i])
print(f"anchors {len(good)}, delta transitions {tr}, bytes identical at same offset {same/len(ca)*100:.1f}%")
