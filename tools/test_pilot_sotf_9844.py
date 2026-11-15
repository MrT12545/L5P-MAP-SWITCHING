"""Instruction-level shim tests, not an ECU/PowerPC hardware emulator.

The decoder below consumes emitted bytes, independently of the build instruction
helpers. It implements only the subset executed by the shim, per NXP VLEPEM.
No SPE interpolation, interrupts, MMU, ECC, watchdog or checksum simulation.
"""
import csv
import io
from pathlib import Path
import random
import re
import struct
import unittest

import pilot_sotf_9844 as P
from e41_export_integrity import Export, crc16_arc
from verify_pilot_sotf_9844 import verify

ROOT = Path(__file__).resolve().parents[1]


def sx(v, bits):
    return v - (1 << bits) if v & (1 << (bits - 1)) else v


def execute(code, cpu, registers, cr, state, tune, enabled):
    regs = registers.copy()
    memory = {0x4005E400: state, 0x4005E414: tune, P.DATA_CPU: enabled}
    writes = set()
    pc = cpu
    steps = 0

    def read(address, width):
        return int.from_bytes(bytes(memory[address + i] for i in range(width)), 'big')

    def write(address, value, width):
        for i, byte in enumerate(value.to_bytes(width, 'big')):
            memory[address + i] = byte
            writes.add(address + i)

    def compare(a, b, signed):
        nonlocal cr
        if signed:
            a, b = sx(a, 32), sx(b, 32)
        nibble = (8 if a < b else 4 if a > b else 2) | ((cr >> 28) & 1)
        cr = (cr & 0x0FFFFFFF) | nibble << 28

    while pc != P.LOOKUP:
        steps += 1
        if steps > 64:
            raise AssertionError('shim did not tail-call original lookup')
        offset = pc - cpu
        h = struct.unpack_from('>H', code, offset)[0]
        if h >> 12 not in (1, 3, 5, 7):
            reg = h & 15
            if reg >= 8:
                reg += 16
            if h & 0xFE00 == 0x2200:
                compare(regs[reg], ((h >> 4) & 31) + 1, False)
            elif h & 0xFE00 == 0x2A00:
                compare(regs[reg], (h >> 4) & 31, True)
            else:
                raise AssertionError(f'Unexpected short {h:04x}')
            pc += 2
            continue
        w = struct.unpack_from('>I', code, offset)[0]
        op, rd, ra = w >> 26, (w >> 21) & 31, (w >> 16) & 31
        next_pc = pc + 4
        if w == 0x182106E0:
            old = regs[1]
            regs[1] = (old - 32) & 0xFFFFFFFF
            write(regs[1], old, 4)
        elif op in (12, 20, 21):
            address = ((regs[ra] if ra else 0) + sx(w & 0xFFFF, 16)) & 0xFFFFFFFF
            if op == 21:
                write(address, regs[rd], 4)
            else:
                regs[rd] = read(address, 1 if op == 12 else 4)
        elif w == 0x7C000026:
            regs[0] = cr
        elif w == 0x7C0FF120:
            cr = regs[0]
        elif op == 28 and (w >> 11) & 31 == 28:
            immediate = ((w >> 16) & 31) << 11 | w & 0x7FF
            regs[rd] = immediate << 16
        elif op == 28 and (w >> 11) & 31 == 20:
            immediate = sx(((w >> 21) & 31) << 11 | w & 0x7FF, 16)
            regs[ra] = (regs[ra] * immediate) & 0xFFFFFFFF
        elif op == 7:
            regs[rd] = ((regs[ra] if ra else 0) + sx(w & 0xFFFF, 16)) & 0xFFFFFFFF
        elif op == 31 and (w >> 1) & 1023 == 266:
            rb = (w >> 11) & 31
            regs[rd] = (regs[ra] + regs[rb]) & 0xFFFFFFFF
        elif op == 30 and not (w >> 25) & 1:
            if w & 1:
                raise AssertionError('Tail-call shim unexpectedly changes LR')
            next_pc = pc + sx(w & 0x1FFFFFE, 25)
        elif op == 30:
            bo, bi = (w >> 20) & 3, (w >> 16) & 15
            condition = bool(cr & (1 << (31 - bi)))
            if bo not in (0, 1):
                raise AssertionError('unexpected CTR branch')
            if condition == bool(bo):
                next_pc = pc + sx(w & 0xFFFE, 16)
        else:
            raise AssertionError(f'Unexpected instruction {w:08x}')
        pc = next_pc
    return regs, cr, writes, steps


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = next((ROOT / 'uploads').glob('ECM*11_10*bin')).read_bytes()
        cls.candidate, cls.manifest = P.build(cls.source)

    def test_source_guard(self):
        altered = bytearray(self.source)
        altered[0] ^= 1
        with self.assertRaises(ValueError):
            P.build(altered)

    def test_all_state_tune_enable_paths_and_register_preservation(self):
        rng = random.Random(9844)
        paths = 0
        max_steps = 0
        for index, (_, original, _) in enumerate(P.TABLES):
            cpu = P.CODE_CPU + index * P.WRAPPER_STRIDE
            base = P.DATA_CPU + 32 + index * 5 * P.TABLE_BYTES
            code = self.candidate[cpu - 0x200000:cpu - 0x200000 + P.WRAPPER_STRIDE]
            for state in (0, 1, 2, 255):
                for tune in range(256):
                    for enabled in (0, 1, 255):
                        regs = [rng.getrandbits(32) for _ in range(32)]
                        regs[1], regs[3] = 0x40030000, original
                        cr = rng.getrandbits(32)
                        result, final_cr, writes, steps = execute(code, cpu, regs, cr, state, tune, enabled)
                        expected = regs.copy()
                        if state == 2 and enabled == 1 and 1 <= tune <= 5:
                            expected[3] = base + (tune - 1) * P.TABLE_BYTES
                        self.assertEqual(result, expected)
                        self.assertEqual(final_cr, cr)
                        self.assertTrue(all(regs[1] - 32 <= a < regs[1] for a in writes))
                        max_steps = max(max_steps, steps)
                        paths += 1
        print(f'Instruction-model paths: {paths}; maximum shim instructions: {max_steps}')

    def test_calls_copies_and_change_boundaries(self):
        self.assertEqual(len(self.source), len(self.candidate))
        allowed = [tuple(self.manifest['program_reservation']),
                   tuple(self.manifest['calibration_reservation'])]
        allowed += [(offset, offset + 2) for offset in self.manifest['integrity_file_offsets']]
        for _, _, call in P.TABLES:
            allowed.append((call - 0x200000, call - 0x200000 + 4))
        for index, (name, original, call) in enumerate(P.TABLES):
            w = struct.unpack_from('>I', self.candidate, call - 0x200000)[0]
            self.assertEqual(w >> 26, 30)
            self.assertEqual(w & 1, 1)
            self.assertEqual(call + sx(w & 0x1FFFFFE, 25), P.CODE_CPU + index * P.WRAPPER_STRIDE)
            raw = self.source[original + P.CAL_FILE_DELTA:original + P.CAL_FILE_DELTA + P.TABLE_BYTES]
            for row in (r for r in self.manifest['tables'] if r['name'] == name):
                at = row['file_offset']
                self.assertEqual(self.candidate[at:at + P.TABLE_BYTES], raw)
        unexpected = [i for i, (a, b) in enumerate(zip(self.source, self.candidate))
                      if a != b and not any(s <= i < e for s, e in allowed)]
        self.assertEqual(unexpected, [])

    def test_export_ranges_checksums_and_source_fixtures(self):
        self.assertEqual(crc16_arc(b'123456789'), 0xBB3D)
        fixtures = list((ROOT / 'uploads').glob('*.bin'))
        self.assertEqual(len(fixtures), 3)
        for path in fixtures:
            data = path.read_bytes()
            export = Export(data)
            self.assertEqual(len(export.segments), 6)
            self.assertTrue(all(r['sum_valid'] and r['crc_valid'] for r in export.audit()))
            self.assertEqual(export.repair(data), data)
        export = Export(self.candidate)
        self.assertTrue(all(r['sum_valid'] and r['crc_valid'] for r in export.audit()))
        broken = bytearray(self.candidate)
        broken[self.manifest['tables'][0]['file_offset']] ^= 1
        report = export.audit(broken)
        self.assertEqual([r['segment'] for r in report if not r['sum_valid'] or not r['crc_valid']],
                         ['calibration_5'])
        self.assertEqual(export.repair(broken), Export(export.repair(broken)).repair(export.repair(broken)))

    def test_wrapper_placement_and_mapping(self):
        export = Export(self.source)
        for index, (_, base, call) in enumerate(P.TABLES):
            address = P.CODE_CPU + index * P.WRAPPER_STRIDE
            self.assertEqual(address >> 12, 0x46673C >> 12)
            self.assertEqual(export.file_offset(address, P.WRAPPER_STRIDE), address - 0x200000)
            self.assertEqual(export.file_offset(call, 4), call - 0x200000)
            self.assertEqual(export.file_offset(base, P.TABLE_BYTES), base + P.CAL_FILE_DELTA)

    def test_readback_verifier_accepts_edits_and_rejects_missing_code(self):
        self.assertEqual(verify(self.candidate, self.source)['status'], 'STATIC_PATCH_PRESENT')
        self.assertEqual(verify(self.source, self.source)['status'], 'STATIC_CHECK_FAILED')
        edited = bytearray(self.candidate)
        at = self.manifest['tables'][0]['file_offset']
        struct.pack_into('>h', edited, at, 512)
        edited = Export(self.candidate).repair(edited)
        report = verify(edited, self.source)
        self.assertEqual(report['status'], 'STATIC_PATCH_PRESENT')
        self.assertTrue(report['copies'][0]['differs_from_original'])
        missing_code = bytearray(self.candidate)
        at = P.TABLES[0][2] - 0x200000
        missing_code[at:at + 4] = self.source[at:at + 4]
        missing_code = Export(self.candidate).repair(missing_code)
        self.assertEqual(verify(missing_code, self.source)['status'], 'STATIC_CHECK_FAILED')

    def test_config_uses_all_copies_with_valid_axes(self):
        source = (ROOT / 'deliverables/ezlynk/9844/EZLYNK_L5P_9844_Performance_Maps.csv').read_text(encoding='latin1')
        content = P.config(source, self.manifest)
        rows = list(csv.reader(line for line in content.splitlines() if not line.startswith('#')))
        self.assertTrue(all(len(row) == 21 for row in rows))
        maps = [r for r in rows[1:] if r[5] != 'C']
        self.assertTrue(all(re.fullmatch(r'C[0-9]+', r[0]) for r in maps),
                        'EZ LYNK Unique ID must be C followed by a number')
        self.assertEqual(len({r[0] for r in maps}), len(maps))
        by_id = {r[0]: r for r in maps}
        tables = [r for r in maps if r[5] == 'Z']
        self.assertEqual(len(tables), 45)
        self.assertEqual({int(r[1], 16) for r in tables}, {r['file_offset'] for r in self.manifest['tables']})
        for table in tables:
            x, y = (by_id[k] for k in table[16].split(':'))
            self.assertEqual((x[5], y[5]), ('X', 'Y'))
            self.assertEqual(int(x[6]) * int(y[6]), int(table[6]))


if __name__ == '__main__':
    unittest.main()
