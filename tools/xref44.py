import sys, struct, collections, pickle
sys.path.insert(0,sys.argv[1]); import vle
d=open(sys.argv[2],'rb').read()
BASE=0x200000; END=0x466800
# linear sweep once, keep instruction list
ins=[]; i=0
while i<END-BASE:
    n,(t,info)=vle.dis(d,i,BASE+i); ins.append((BASE+i,n,t,info)); i+=n
pickle.dump(ins,open(sys.argv[3],'wb'))
print("instructions:",len(ins))
