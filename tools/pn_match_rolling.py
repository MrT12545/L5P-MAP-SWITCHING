import sys, struct, math, re
sys.path.insert(0, sys.argv[1]); import olscsv
binpath, csvpath, outbin, outcsv = sys.argv[2:6]
VREF = float(sys.argv[6]) if len(sys.argv) > 6 else 20.0   # rolling-neutral reference speed, kph
b = bytearray(open(binpath,'rb').read())
maps = olscsv.load(csvpath); by = {r['Name']: r for r in maps}
def interp(x, xs, ys):
    if x <= xs[0]: return ys[0]
    for i in range(len(xs)-1):
        if x <= xs[i+1]: return ys[i] + (ys[i+1]-ys[i])*(x-xs[i])/(xs[i+1]-xs[i])
    return ys[-1]
# rolling-neutral power request (kW) vs pedal at VREF
pa = by['KtDTRC_P_M_PedProgReqA']; PC, PR, pv = olscsv.decode_map(b, pa)
pv_x = [float(x) for x in olscsv.axis(b, pa, 'X', PC)]; pv_y = [float(y) for y in olscsv.axis(b, pa, 'Y', PR)]
def P_roll(ped):
    col = [interp(VREF, pv_x, pv[r*PC:(r+1)*PC]) for r in range(PR)]
    return interp(ped, pv_y, col)
# P/N table
t = by['KtDTRC_M_EngTrqReqForRPM']; C, R, tv = olscsv.decode_map(b, t)
rpm = [float(x) for x in olscsv.axis(b, t, 'X', C)]; ped = [float(y) for y in olscsv.axis(b, t, 'Y', R)]
addr = int(t['Fieldvalues.StartAddr'][1:], 16); fac = float(t['Fieldvalues.Factor']); signed = t['bSigned'] == '1'
new = list(tv); changed = []
for r in range(R):
    for c in range(C):
        stock = tv[r*C+c]
        roll = P_roll(ped[r]) * 60000 / (2*math.pi*max(rpm[c], 300))
        eligible = rpm[c] >= 2500 or (rpm[c] >= 2000 and stock <= 0)   # stay out of the in-gear launch area
        if eligible and roll > stock:
            raw = round(roll / fac); raw = min(raw, 32767 if signed else 65535)
            new[r*C+c] = raw * fac; changed.append((ped[r], rpm[c], stock, new[r*C+c]))
            struct.pack_into('>h' if signed else '>H', b, addr + 2*(r*C+c), raw)
open(outbin, 'wb').write(b)
with open(outcsv, 'w') as f:
    f.write('pedal% \\ rpm;' + ';'.join(f'{x:g}' for x in rpm) + '\n')
    for r in range(R): f.write(f'{ped[r]:g};' + ';'.join(f'{new[r*C+c]:.2f}' for c in range(C)) + '\n')
def show(title, v):
    print(title); print('pedal\\rpm ' + ' '.join(f'{x:7.0f}' for x in rpm))
    for r in range(R): print(f'{ped[r]:8.0f}  ' + ' '.join(f'{v[r*C+c]:7.1f}' for c in range(C)))
print(f'map @ file ${addr:X}, signed={signed}, factor={fac}, ref speed={VREF} kph')
print('rolling-neutral power request at that speed (kW):', {p: round(P_roll(p),1) for p in ped})
show('\nSTOCK', tv); show('\nNEW', new)
print(f'\n{len(changed)} cells changed')
