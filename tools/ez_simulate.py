import csv,struct,sys
def load(p):
    rows=[r for r in csv.reader(l for l in open(p,encoding='latin1',newline='').read().splitlines() if l and not l.startswith('#'))][1:]
    return {r[0]:r for r in rows if r and r[0].startswith('C')}
def vals(b,r):
    if r[1]=='MANUAL': return [float(x) for x in r[20].split(';')]
    n=int(r[6]); a=int(r[1],16); fmt={'1':'B','2':'h' if r[9]=='S' else 'H','F':'f'}[r[7]]; w={'B':1,'h':2,'H':2,'f':4}[fmt]
    return [x*float(r[10])+float(r[11]) for x in struct.unpack('>'+fmt*n,b[a:a+w*n])]
def show(p,binp,zid,maxr=9,maxc=9):
    b=open(binp,'rb').read(); by=load(p); z=by[zid]; x,y=z[16].split(':')
    xa,ya,v=vals(b,by[x]),vals(b,by[y]),vals(b,z); nx=len(xa)
    print(f'  {z[2]}   [across: {by[x][2]} | down: {by[y][2]}]')
    print('   %8s '%'' + ' '.join(f'{q:7g}' for q in xa[:maxc]))
    for j,yy in enumerate(ya[:maxr]): print('   %8g '%yy + ' '.join(f'{q:7.1f}' for q in v[j*nx:j*nx+maxc]))
if __name__=='__main__':
    show(*sys.argv[1:4])
