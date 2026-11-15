import re,sys
LBL={'os':'confirmed by the HP Tuners SOTF record','code+relocation agree':'verified: ECU code reference + table layout agree','code+neighbours agree':'verified: ECU code reference + neighbouring tables agree',
     'code+content':'verified: ECU code reference + table contents','relocation+neighbours agree':'verified: table layout + neighbouring tables agree','neighbours+content':'verified: neighbouring tables + contents',
     'relocation+content':'verified: table layout + contents','neighbours':'verified: between two code-verified tables','code':'verified: ECU code reference','content':'verified: unique table contents',
     'code alignment via 9843':'verified: ECU code aligned against the 9843 bin','from HP Tuners SOTF record':'from the HP Tuners SOTF record'}
for p in sys.argv[1:]:
    t=open(p,encoding='latin1',newline='').read()
    t=t.replace('- address relocation (one-side neighbour))','- address table layout + one neighbouring table)')
    t=re.sub(r'- address ([^)]+\(9843 layout)\)\)',lambda m:'- address verified: '+m.group(1).replace(' (9843 layout','')+' in the 9843 layout)',t)
    t=re.sub(r'- address ([^)]+)\)',lambda m:'- address '+LBL.get(m.group(1),m.group(1))+')',t)
    t=''.join(ch if ord(ch)<128 else '' for ch in t).replace(' O X: ',' X axis: ').replace(' O Y: ',' Y axis: ')
    open(p,'w',encoding='ascii',newline='').write(t)
