import csv, struct, math
csv.field_size_limit(1<<30)
FMT={'eByte':(1,'B','b'),'eHiLo':(2,'H','h'),'eHiLoHiLo':(4,'I','i'),'eFloatHiLo':(4,None,None)}
def load(path):
    rows=list(csv.DictReader(open(path,newline='',encoding='latin1'),delimiter=';'))
    uniq={}
    for r in rows:
        k=(r['Fieldvalues.StartAddr'],r['Name'])
        if k in uniq:
            if r['FolderName'].startswith('"NEW'): continue
        uniq[k]=r
    return list(uniq.values())
def num(s,d=0.0):
    try: return float(s)
    except: return d
def read_vals(b,addr,org,n,signed,stride=None):
    size,u,s=FMT[org]; stride=stride or size
    out=[]
    for i in range(n):
        o=addr+i*stride
        if org=='eFloatHiLo': out.append(struct.unpack('>f',b[o:o+4])[0])
        else: out.append(struct.unpack('>'+(s if signed else u),b[o:o+size])[0])
    return out
def decode_map(b,r):
    org=r['DataOrg']; C=int(r['Columns']); R=int(r['Rows'])
    addr=int(r['Fieldvalues.StartAddr'][1:],16)
    raw=read_vals(b,addr,org,C*R,r['bSigned']=='1')
    f=num(r['Fieldvalues.Factor'],1); off=num(r['Fieldvalues.Offset'])
    vals=[x*f+off for x in raw]
    if r['bReciprocal']=='1': vals=[(1/v if v else float('inf')) for v in vals]
    return C,R,vals
def axis(b,r,ax,n):
    src=r[f'Axis{ax}.DataSrc']
    if src=='eRom':
        a=int(r[f'Axis{ax}.DataAddr'][1:],16); org=r[f'Axis{ax}.DataOrg']
        raw=read_vals(b,a,org,n,r[f'Axis{ax}.bSigned']=='1')
        f=num(r[f'Axis{ax}.Factor'],1); off=num(r[f'Axis{ax}.Offset'])
        return [x*f+off for x in raw]
    if src in ('eUserdefString','eUserdef'):
        v=r[f'Axis{ax}.Values']
        return v.split(';') if ';' in v else v.split()
    return list(range(n))
