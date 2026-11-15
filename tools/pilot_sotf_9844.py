"""Build a checksum-corrected, hardware-UNVERIFIED pilot quantity SOTF candidate.

Only the exact clean 11-10-26 V2 export is accepted. No ECU communication.
No flashing or signature changes. Export-declared sums/CRCs are corrected.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
from e41_export_integrity import Export

SOURCE_SHA256 = 'e19408dd83316edc3deb463b5eae44414da0b1035a1819126f9d1efa5922a45d'
LOOKUP = 0x31FD7C
CODE_CPU = 0x466800
DATA_CPU = 0x170000
CAL_FILE_DELTA = 0x39FFE0
WRAPPER_STRIDE = 0x80
TABLE_BYTES = 480
# One existing Normal-mode BC1 call per table. Other pilot contributions stay shared.
TABLES = [
    ('KtFULC_V_QntyR1_Ptn1_LoBC1', 0xF9DD8, 0x3452B8),
    ('KtFULC_V_QntyR1_Ptn1_MidBC1', 0xFA198, 0x34527E),
    ('KtFULC_V_QntyR1_Ptn1_SeaBC1', 0xFA738, 0x3452EA),
    ('KtFULC_V_QntyR1_Ptn2_LoBC1', 0xFACD8, 0x3454F2),
    ('KtFULC_V_QntyR1_Ptn2_MidBC1', 0xFB098, 0x3454BA),
    ('KtFULC_V_QntyR1_Ptn2_SeaBC1', 0xFB638, 0x345526),
    ('KtFULC_V_QntyR2_LoBC1', 0xFBC68, 0x344D9E),
    ('KtFULC_V_QntyR2_MidBC1', 0xFC028, 0x344D66),
    ('KtFULC_V_QntyR2_SeaBC1', 0xFC5C8, 0x344DD2),
]


def p32(word):
    return struct.pack('>I', word)


def branch(pc, target, link=False):
    displacement = target - pc
    if displacement % 2 or not -(1 << 24) <= displacement < (1 << 24):
        raise ValueError('VLE branch target out of range/alignment')
    return 0x78000000 | (displacement & 0x1FFFFFE) | int(link)


def lis(rd, value):
    if not 0 <= value <= 0xFFFF:
        raise ValueError('lis immediate')
    return 0x7000E000 | rd << 21 | (value >> 11) << 16 | (value & 0x7FF)


def add16(rd, ra, value):
    if not -32768 <= value <= 32767:
        raise ValueError('add16 immediate')
    return 0x1C000000 | rd << 21 | ra << 16 | (value & 0xFFFF)


def mem(opcode, reg, base, displacement):
    return opcode | reg << 21 | base << 16 | (displacement & 0xFFFF)


def wrapper(cpu, copy_base):
    """Tail-call shim: preserve LR, CR, r0, r6/r7 and every other GPR except r3.

    r3 is the map pointer; r4-r7 are interpolation inputs; r8 is output scaling.
    Uses a 32-byte aligned stack frame and no persistent RAM allocation.
    Encodings follow NXP VLEPEM; fixed instruction examples also exist in source.
    """
    out = bytearray()
    fixups = []

    def emit(w):
        out.extend(p32(w))

    def short(w):
        out.extend(struct.pack('>H', w))

    def fallback(opcode):
        fixups.append((len(out), opcode))
        emit(0)

    emit(0x182106E0)  # e_stwu r1,-32(r1)
    emit(mem(0x54000000, 0, 1, 4))
    emit(mem(0x54000000, 6, 1, 8))
    emit(mem(0x54000000, 7, 1, 12))
    emit(0x7C000026)  # mfcr r0
    emit(mem(0x54000000, 0, 1, 16))
    emit(lis(6, 0x4006))
    emit(mem(0x30000000, 7, 6, -0x1C00))  # HPT readiness byte
    short(0x2217)  # se_cmpli r7,2
    fallback(0x7A020000)  # e_bne fallback
    emit(mem(0x30000000, 7, 6, -0x1BEC))  # HPT selected tune byte
    short(0x2A07)  # se_cmpi r7,0
    fallback(0x7A120000)  # e_beq fallback
    short(0x2247)  # se_cmpli r7,5
    fallback(0x7A110000)  # e_bgt fallback
    emit(lis(6, DATA_CPU >> 16))
    emit(mem(0x30000000, 6, 6, DATA_CPU & 0xFFFF))
    short(0x2A16)  # se_cmpi r6,1: exactly 1 enables extension
    fallback(0x7A020000)
    emit(add16(7, 7, -1))
    emit(0x7007A1E0)  # e_mull2i r7,480
    high = (copy_base + 0x8000) >> 16
    low = copy_base - (high << 16)
    emit(lis(6, high))
    emit(add16(6, 6, low))
    emit(0x7C663A14)  # add r3,r6,r7
    done = len(out)
    emit(mem(0x50000000, 0, 1, 16))
    emit(0x7C0FF120)  # mtcrf 255,r0
    emit(mem(0x50000000, 7, 1, 12))
    emit(mem(0x50000000, 6, 1, 8))
    emit(mem(0x50000000, 0, 1, 4))
    emit(add16(1, 1, 32))
    emit(branch(cpu + len(out), LOOKUP))
    for offset, opcode in fixups:
        distance = done - offset
        if distance % 2 or not -32768 <= distance <= 32766:
            raise ValueError('conditional branch range')
        struct.pack_into('>I', out, offset, opcode | (distance & 0xFFFE))
    if len(out) > WRAPPER_STRIDE:
        raise ValueError('wrapper exceeds reservation')
    return bytes(out)


def build(source):
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError('Source is not the exact clean 9844 11-10-26 V2 export')
    export = Export(source)
    source_integrity = export.audit()
    if not all(r['sum_valid'] and r['crc_valid'] for r in source_integrity):
        raise ValueError('Source integrity checks failed')
    result = bytearray(source)
    code_start = CODE_CPU - 0x200000
    code_end = code_start + len(TABLES) * WRAPPER_STRIDE
    data_start = DATA_CPU + CAL_FILE_DELTA
    data_end = data_start + 32 + len(TABLES) * 5 * TABLE_BYTES
    # Confirm the fixed translation assumptions against the file's own descriptors.
    if export.file_offset(CODE_CPU, code_end - code_start) != code_start:
        raise ValueError('Program mapping disagrees with export descriptors')
    if export.file_offset(DATA_CPU, data_end - data_start) != data_start:
        raise ValueError('Calibration mapping disagrees with export descriptors')
    # All shims stay in the same smallest Book E page size (4 KiB) as existing
    # HPT instructions. This is static placement evidence, not live-MMU proof.
    if CODE_CPU >> 12 != (CODE_CPU + len(TABLES) * WRAPPER_STRIDE - 1) >> 12:
        raise ValueError('Wrapper reservation crosses 4 KiB boundary')
    if source[code_start:code_end] != b'\xFF' * (code_end - code_start):
        raise ValueError('Program reservation is not erased')
    if source[data_start:data_end] != b'\xFF' * (data_end - data_start):
        raise ValueError('Calibration reservation is not erased')
    result[data_start:data_start + 32] = b'\x00' * 32
    result[data_start] = 1
    marker = b'TSM_PILOT_DEV001'
    assert len(marker) == 16
    result[data_start + 4:data_start + 20] = marker
    records = []
    for index, (name, original, call) in enumerate(TABLES):
        call_offset = call - 0x200000
        expected = p32(branch(call, LOOKUP, True))
        if source[call_offset:call_offset + 4] != expected:
            raise ValueError(f'Original call mismatch: {name}')
        address = CODE_CPU + index * WRAPPER_STRIDE
        data_cpu = DATA_CPU + 32 + index * 5 * TABLE_BYTES
        code = wrapper(address, data_cpu)
        offset = address - 0x200000
        result[offset:offset + len(code)] = code
        result[call_offset:call_offset + 4] = p32(branch(call, address, True))
        raw = source[original + CAL_FILE_DELTA:original + CAL_FILE_DELTA + TABLE_BYTES]
        for tune in range(1, 6):
            cpu = data_cpu + (tune - 1) * TABLE_BYTES
            result[cpu + CAL_FILE_DELTA:cpu + CAL_FILE_DELTA + TABLE_BYTES] = raw
            records.append(dict(name=name, tune=tune, base_cpu=original,
                                copy_cpu=cpu, file_offset=cpu + CAL_FILE_DELTA,
                                call_cpu=call, wrapper_cpu=address))
    if len(result) != len(source):
        raise ValueError('Candidate length changed')
    result = export.repair(result)
    candidate_integrity = export.audit(result)
    if not all(r['sum_valid'] and r['crc_valid'] for r in candidate_integrity):
        raise ValueError('Candidate integrity checks failed')
    manifest = dict(status='CHECKSUM_CORRECTED_HARDWARE_UNVERIFIED',
                    source_sha256=SOURCE_SHA256,
                    candidate_sha256=hashlib.sha256(result).hexdigest(),
                    changed_bytes=sum(a != b for a, b in zip(source, result)),
                    tables=records, enable_file_offset=data_start,
                    program_reservation=[code_start, code_end],
                    calibration_reservation=[data_start, data_end],
                    integrity=candidate_integrity,
                    integrity_file_offsets=[export.file_offset(cpu) for seg in export.segments
                                            for cpu in (seg.checksum_cpu, seg.crc_cpu)],
                    limitations=['Export sums and CRCs validated; no signature/authentication validation',
                                 'No hardware execution or timing validation',
                                 'Erased bytes alone do not prove usable mapped flash',
                                 'Only nine BC1 pilot quantity contributions switch; other contributions stay shared',
                                 'Existing axes, dwell, timing, enable logic and other combustion modes stay shared'])
    return bytes(result), manifest


def config(full_config, manifest):
    rows = list(csv.reader(line for line in full_config.splitlines()
                           if line and not line.startswith('#')))
    header, source_rows = rows[0], rows[1:]
    by_id = {r[0]: r for r in source_rows if r[5] != 'C'}
    source_maps = {}
    for name, _, _ in TABLES:
        matches = [r for r in source_rows if f'GM name: {name} ' in r[3] and r[5] == 'Z']
        if len(matches) != 1:
            raise ValueError(f'Expected one config definition for {name}')
        source_maps[name] = matches[0]
    output = [header]
    folders = [('F900', 'TSM Pilot SOTF - BENCH DEVELOPMENT')]
    folders += [(f'F90{n}', f'Tune {n} Pilot Quantity') for n in range(1, 6)]
    folders += [('F906', 'Pilot Axes - Shared'), ('F907', 'Extension Control')]
    for fid, title in folders:
        r = ['FFFF', '0x0000', title, '', '0', 'C'] + ['0'] * 11 + [fid, '0', '0', '']
        output.append(r)
    axis_ids = sorted({a for r in source_maps.values() for a in r[16].split(':')})
    # EZ LYNK requires C followed by a number, including axis/control IDs.
    renamed = {old: f'C{9000 + i}' for i, old in enumerate(axis_ids)}
    for old in axis_ids:
        r = by_id[old].copy()
        r[0] = renamed[old]
        r[2] = 'Pilot Shared Axis ' + old
        r[17:20] = ['F900', 'F906', '']
        if r[16]:
            r[16] = renamed[r[16]]
        output.append(r)
    for i, record in enumerate(manifest['tables']):
        r = source_maps[record['name']].copy()
        r[0] = f'C{9100 + i}'
        r[1] = hex(record['file_offset'])
        r[2] = f"Tune {record['tune']} " + record['name']
        r[3] = ('Experimental firmware extension required. Only this BC1 contribution switches; '
                'other pilot contributions and all axes stay shared. GM name: ' + record['name'])
        r[16] = ':'.join(renamed[a] for a in r[16].split(':'))
        r[17:20] = ['F900', f"F90{record['tune']}", '']
        output.append(r)
    # Numeric 0/1 control; exact 1 enables, all other byte values select base maps.
    output.append(['C9200', hex(manifest['enable_file_offset']), 'Pilot SOTF Extension Enable',
                   'BENCH DEVELOPMENT ONLY. 1 selects pilot copies when HPT state is ready and tune is 1-5; 0 uses base.',
                   '', 'N', '1', '1', 'MSB', 'U', '1', '0', '0', '0', '1', '1', '', 'F900', 'F907', '', ''])
    stream = io.StringIO(newline='')
    stream.write('# BENCH DEVELOPMENT ONLY - matching firmware required; hardware unverified\r\n')
    csv.writer(stream, lineterminator='\r\n').writerows(output)
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.read_bytes()
    candidate, manifest = build(source)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / '9844_PILOT_SOTF_BENCH_HARDWARE_UNVERIFIED.bin').write_bytes(candidate)
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    root = Path(__file__).resolve().parents[1]
    full = root / 'deliverables/ezlynk/9844/EZLYNK_L5P_9844_Performance_Maps.csv'
    with (args.out / 'EZLYNK_9844_Pilot_SOTF_BENCH.csv').open('w', encoding='latin1', newline='') as f:
        f.write(config(full.read_text(encoding='latin1'), manifest))
    print(json.dumps({k: v for k, v in manifest.items() if k != 'tables'}, indent=2))


if __name__ == '__main__':
    main()
