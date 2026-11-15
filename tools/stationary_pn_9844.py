"""Build a default-disabled stationary-P/N diagnostic on the pilot prototype.

Research candidate only: internal gear qualification and live request behavior
remain unverified. Neither switch is enabled in the generated file.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import struct

import pilot_sotf_9844 as P
from e41_export_integrity import Export
from verify_pilot_sotf_9844 import verify as verify_pilot

TCM_HOOK = 0x2B9EA2
PN_CALL = 0x283762
TCM_CODE = 0x466D00
PN_CODE = 0x466E00
CONTROL = 0x175500
PN_TABLE = CONTROL + 32
MARKER = b'TSM_PN_DIAG_0001'
PN_BASE = 0x7AA98
# The existing A-build's reviewed table, raw signed words (0.25 Nm/word).
# This table is only substituted under the new guard; the original stays intact.
PN_RAW = (
    0, -191, -254, -38, -76, -127, -109, -95, -63,
    76, 19, 0, -38, -76, -127, -109, -95, -63,
    305, 114, 50, 0, 188, 157, 135, 118, 79,
    611, 152, 76, 38, 283, 236, 202, 177, 118,
    916, 305, 101, 57, 372, 310, 266, 232, 155,
    1833, 763, 407, 152, 998, 831, 713, 624, 416,
    2444, 1069, 611, 381, 1752, 1460, 1251, 1095, 730,
    3819, 1718, 814, 477, 2771, 2309, 1979, 1732, 1155,
    7639, 3055, 1782, 1145, 2962, 2468, 2116, 1851, 1234,
)


def shim(cpu, purpose):
    if purpose not in ('tcm', 'demand'):
        raise ValueError('Unknown purpose')
    out = bytearray()
    fixups = []
    labels = {}

    def emit(word):
        out.extend(P.p32(word))

    def short(word):
        out.extend(struct.pack('>H', word))

    def cond(opcode, label='done'):
        fixups.append((len(out), opcode, label))
        emit(0)

    emit(0x182106E0)
    for reg, offset in [(0, 4), (6, 8), (7, 12)]:
        emit(P.mem(0x54000000, reg, 1, offset))
    emit(0x7C000026)
    emit(P.mem(0x54000000, 0, 1, 16))
    if purpose == 'tcm':
        emit(0x3BCF9DE6)  # original e_lha r30,-0x621a(r15)
        short(0x2A1E)  # se_cmpi r30,1
        cond(0x7A020000)
    else:
        # Do not redirect any unexpected caller/table pointer.
        emit(P.lis(6, (PN_BASE + 0x8000) >> 16))
        emit(P.add16(6, 6, PN_BASE - (((PN_BASE + 0x8000) >> 16) << 16)))
        short(0x0C63)  # se_cmp r3,r6
        cond(0x7A020000)
    emit(P.lis(6, CONTROL >> 16))
    emit(P.mem(0x30000000, 6, 6, (CONTROL & 65535) + (purpose == 'demand')))
    short(0x2A16)  # exact enable=1
    cond(0x7A020000)
    emit(P.mem(0x38000000, 6, 15, -0x4B28))
    short(0x2A06)  # gear==0
    cond(0x7A120000, 'speed')
    short(0x2A96)  # gear==9
    cond(0x7A020000)
    labels['speed'] = len(out)
    emit(P.mem(0x58000000, 7, 15, -0x5D72))
    short(0x2A07)  # VSS raw must be exactly zero
    cond(0x7A020000)
    if purpose == 'tcm':
        short(0x480E)  # se_li r30,0, local arbitration input only
    else:
        emit(P.lis(3, (PN_TABLE + 0x8000) >> 16))
        emit(P.add16(3, 3, PN_TABLE - (((PN_TABLE + 0x8000) >> 16) << 16)))
    labels['done'] = len(out)
    emit(P.mem(0x50000000, 0, 1, 16))
    emit(0x7C0FF120)
    for reg, offset in [(7, 12), (6, 8), (0, 4)]:
        emit(P.mem(0x50000000, reg, 1, offset))
    emit(P.add16(1, 1, 32))
    emit(P.branch(cpu + len(out), TCM_HOOK + 4 if purpose == 'tcm' else P.LOOKUP))
    for at, opcode, label in fixups:
        displacement = labels[label] - at
        if not 0 <= displacement <= 32766 or displacement % 2:
            raise ValueError('Invalid conditional target')
        struct.pack_into('>I', out, at, opcode | displacement)
    if len(out) > 0x100:
        raise ValueError('Shim slot overflow')
    return bytes(out)


def build(source):
    base, pilot_manifest = P.build(source)
    export = Export(source)
    image = bytearray(base)
    ranges = [(TCM_CODE, 0x100), (PN_CODE, 0x100), (CONTROL, 32 + 162)]
    for address, size in ranges:
        at = export.file_offset(address, size)
        if image[at:at + size] != b'\xFF' * size:
            raise ValueError('Diagnostic reservation not erased')
    at = export.file_offset(CONTROL, 32)
    image[at:at + 32] = b'\0' * 32
    assert len(MARKER) == 16
    image[at + 4:at + 20] = MARKER
    struct.pack_into('>81h', image, export.file_offset(PN_TABLE, 162), *PN_RAW)
    for hook, code, purpose, linked, expected in [
        (TCM_HOOK, TCM_CODE, 'tcm', False, bytes.fromhex('3bcf9de6')),
        (PN_CALL, PN_CODE, 'demand', True, P.p32(P.branch(PN_CALL, P.LOOKUP, True))),
    ]:
        offset = export.file_offset(hook, 4)
        if image[offset:offset + 4] != expected:
            raise ValueError('Original hook instruction mismatch')
        image[offset:offset + 4] = P.p32(P.branch(hook, code, linked))
        code_bytes = shim(code, purpose)
        offset = export.file_offset(code, len(code_bytes))
        image[offset:offset + len(code_bytes)] = code_bytes
    candidate = export.repair(image)
    checks = export.audit(candidate)
    if not all(x['sum_valid'] and x['crc_valid'] for x in checks):
        raise ValueError('Integrity checks failed')
    if len(candidate) != len(source):
        raise ValueError('File length changed')
    manifest = dict(status='DEFAULT_DISABLED_HARDWARE_UNVERIFIED',
                    source_sha256=hashlib.sha256(source).hexdigest(),
                    pilot_base_sha256=pilot_manifest['candidate_sha256'],
                    candidate_sha256=hashlib.sha256(candidate).hexdigest(),
                    switches=dict(tcm_speed_request_exclusion=export.file_offset(CONTROL),
                                  stationary_demand_table=export.file_offset(CONTROL + 1)),
                    default_switch_values=[0, 0],
                    guard=dict(gear_states=[0, 9], vehicle_speed_raw_equals=0,
                               tcm_request_status_required=1),
                    hooks=dict(tcm=TCM_HOOK, pn_call=PN_CALL),
                    reservations=[dict(cpu=a, size=s, file_offset=export.file_offset(a, s)) for a, s in ranges],
                    pn_table_cpu=PN_TABLE, pn_table_file_offset=export.file_offset(PN_TABLE, 162),
                    integrity=checks,
                    limitations=['Internal gear/status qualification is not verified on the truck',
                                 'A false P/N or zero-speed input could satisfy this software guard',
                                 'Live TCM arbitration and engine behavior remain unverified',
                                 'Default-off adds code execution; host tests do not prove hardware equivalence'])
    return candidate, manifest


def config(full_config, pilot_csv, manifest):
    parse = lambda text: list(csv.reader(line for line in text.splitlines()
                                        if line and not line.startswith('#')))
    original = parse(full_config)
    combined = parse(pilot_csv)
    donor = next(r for r in original[1:] if r[5] == 'Z' and 'GM name: KtDTRC_M_EngTrqReqForRPM ' in r[3])
    by_id = {r[0]: r for r in original[1:] if r[5] != 'C'}
    for fid, title in [('F950', 'Stationary PN Diagnostics - DEFAULT OFF'),
                       ('F951', 'Diagnostic Switches'), ('F952', 'Shared PN Axes'),
                       ('F953', 'Diagnostic PN Torque Demand')]:
        combined.append(['FFFF', '0x0000', title, '', '0', 'C'] + ['0'] * 11 + [fid, '0', '0', ''])
    for index, (key, title) in enumerate([
        ('tcm_speed_request_exclusion', 'Stationary PN - Exclude TCM Speed Request'),
        ('stationary_demand_table', 'Stationary PN - Use Diagnostic Torque Table'),
    ]):
        combined.append([f'C{9400 + index}', hex(manifest['switches'][key]), title,
                         'Hardware unverified. Default 0. Requires exact new diagnostic firmware. Internal gear 0 or 9 and VSS raw zero only.',
                         '', 'N', '1', '1', 'MSB', 'U', '1', '0', '0', '0', '1', '1', '', 'F950', 'F951', '', ''])
    axes = donor[16].split(':')
    remap = {old: f'C{9402 + i}' for i, old in enumerate(axes)}
    for old in axes:
        row = by_id[old].copy()
        row[0] = remap[old]
        row[2] = 'Shared PN ' + ('RPM' if row[5] == 'X' else 'Pedal') + ' Axis'
        row[17:20] = ['F950', 'F952', '']
        if row[16]:
            row[16] = remap[row[16]]
        combined.append(row)
    row = donor.copy()
    row[0], row[1], row[2] = 'C9404', hex(manifest['pn_table_file_offset']), 'Stationary PN Diagnostic Torque Demand'
    row[3] = 'Copy of earlier A-build PN demand. Requires diagnostic demand switch=1 and stationary PN guard. Shared axes also affect original table. Hardware unverified.'
    row[16] = ':'.join(remap[x] for x in axes)
    row[17:20] = ['F950', 'F953', '']
    combined.append(row)
    output = io.StringIO(newline='')
    output.write('# HARDWARE UNVERIFIED - both stationary diagnostic switches default OFF\r\n')
    csv.writer(output, lineterminator='\r\n').writerows(combined)
    return output.getvalue()


def verify_readback(data, source):
    expected, manifest = build(source)
    export = Export(data)
    pilot = verify_pilot(data, source)
    hooks = []
    for hook, code, purpose in [(TCM_HOOK, TCM_CODE, 'tcm'), (PN_CALL, PN_CODE, 'demand')]:
        at = export.file_offset(hook, 4)
        expected_at = Export(expected).file_offset(hook, 4)
        raw = shim(code, purpose)
        offset = export.file_offset(code, len(raw))
        hooks.append(dict(purpose=purpose,
                          hook_matches=data[at:at + 4] == expected[expected_at:expected_at + 4],
                          code_matches=data[offset:offset + len(raw)] == raw))
    offset = export.file_offset(CONTROL, 32)
    switches = list(data[offset:offset + 2])
    marker_matches = data[offset + 4:offset + 20] == MARKER
    passed = (pilot['status'] == 'STATIC_PATCH_PRESENT' and marker_matches and
              all(value in (0, 1) for value in switches) and
              all(row['hook_matches'] and row['code_matches'] for row in hooks))
    return dict(status='STATIC_DIAGNOSTIC_PATCH_PRESENT' if passed else 'STATIC_CHECK_FAILED',
                diagnostic_switches=switches, marker_matches=marker_matches,
                hooks=hooks, pilot_patch_status=pilot['status'], integrity=export.audit(),
                limitation='File presence does not establish live gear qualification, ECU execution or engine behavior')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--out', type=Path)
    action.add_argument('--verify', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.verify:
        report = verify_readback(args.verify.read_bytes(), args.source.read_bytes())
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report['status'] == 'STATIC_DIAGNOSTIC_PATCH_PRESENT' else 1)
    candidate, manifest = build(args.source.read_bytes())
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / '9844_PILOT_PN_DIAGNOSTIC_DISABLED_UNVERIFIED.bin').write_bytes(candidate)
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    full = (root / 'deliverables/ezlynk/9844/EZLYNK_L5P_9844_Performance_Maps.csv').read_text(encoding='latin1')
    pilot_manifest = json.loads((root / 'deliverables/pilot_sotf_9844/manifest.json').read_text())
    content = config(full, P.config(full, pilot_manifest), manifest)
    (args.out / 'EZLYNK_9844_Pilot_and_PN_DIAGNOSTIC.csv').write_bytes(content.encode('latin1'))
    print(json.dumps({k: v for k, v in manifest.items() if k != 'integrity'}, indent=2))
