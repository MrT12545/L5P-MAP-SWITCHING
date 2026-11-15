"""Host-only checks for the default-off stationary/P-N diagnostic candidate."""
import csv
import json
from pathlib import Path
import random
import re
import struct
import unittest

import pypcode

import stationary_pn_9844 as S
import pilot_sotf_9844 as P
from e41_export_integrity import Export
from pilot_sotf_pcode_check import Machine, float_bits, float_value

ROOT = Path(__file__).resolve().parents[1]


def put(machine, address, value, width):
    for i, byte in enumerate(value.to_bytes(width, 'big')):
        machine.spaces['ram'][address + i] = byte


class StationaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = next((ROOT / 'uploads').glob('ECM*11_10*bin')).read_bytes()
        cls.pilot, cls.pilot_manifest = P.build(cls.source)
        cls.candidate, cls.manifest = S.build(cls.source)
        cls.context = pypcode.Context('PowerPC:BE:32:e200')
        cls.cache = {}

    def machine(self, gear, speed, enabled, purpose, status=1):
        m = Machine(self.context, self.candidate, self.cache)
        rng = random.Random(gear * 99991 + speed * 17 + enabled + status)
        for i in range(32):
            m.register(f'r{i}', rng.getrandbits(32))
        m.register('r1', 0x40030000)
        m.register('r15', 0x40018000)
        m.register('r3', S.PN_BASE)
        m.register('LR', 0x12345678)
        m.register('CTR', 0x87654320)
        for i in range(8):
            m.register(f'cr{i}', rng.randrange(16))
        put(m, 0x400134D8, gear, 2)
        put(m, 0x4001228E, speed, 2)
        put(m, 0x40011DE6, status, 2)
        put(m, S.CONTROL + (purpose == 'demand'), enabled, 1)
        return m

    def test_all_gear_speed_enable_status_cases_preserve_inputs(self):
        cases = 0
        for purpose in ('tcm', 'demand'):
            statuses = (0, 1, 2, 65535) if purpose == 'tcm' else (1,)
            for gear in list(range(16)) + [65534, 65535]:
                for speed in (0, 1, 128, 640, 3840):
                    for enabled in (0, 1, 255):
                        for status in statuses:
                            m = self.machine(gear, speed, enabled, purpose, status)
                            before = {f'r{i}': m.register(f'r{i}') for i in range(32)}
                            specials = {k: m.register(k) for k in ['LR', 'CTR'] + [f'cr{i}' for i in range(8)]}
                            active = gear in (0, 9) and speed == 0 and enabled == 1
                            if purpose == 'tcm':
                                expected = status if status < 32768 else status - 65536
                                expected &= 0xFFFFFFFF
                                if active and status == 1:
                                    expected = 0
                                m.run(S.TCM_CODE, stop=S.TCM_HOOK + 4)
                                before['r30'] = expected
                            else:
                                if active:
                                    before['r3'] = S.PN_TABLE
                                m.run(S.PN_CODE, stop=P.LOOKUP)
                            self.assertEqual({f'r{i}': m.register(f'r{i}') for i in range(32)}, before)
                            self.assertEqual({k: m.register(k) for k in specials}, specials)
                            cases += 1
        print('Independent SLEIGH guard/register cases:', cases)

    def test_unexpected_demand_pointer_is_untouched(self):
        m = self.machine(0, 0, 1, 'demand')
        m.register('r3', S.PN_BASE + 2)
        m.run(S.PN_CODE, stop=P.LOOKUP)
        self.assertEqual(m.register('r3'), S.PN_BASE + 2)

    def test_actual_demand_interpolation_4000rpm_full_pedal(self):
        for gear in (0, 1, 8, 9):
            for speed in (0, 1):
                for enabled in (0, 1):
                    m = self.machine(gear, speed, enabled, 'demand')
                    # Normalized prelookup fractions: pedal row 8/8; RPM column 7/8.
                    for reg, value in [('r4', 1.0), ('r5', 0.875), ('r6', 8.0),
                                       ('r7', 8.0), ('r8', 0.25)]:
                        m.register(reg, float_bits(value))
                    m.run(S.PN_CALL, stop=S.PN_CALL + 4)
                    active = gear in (0, 9) and speed == 0 and enabled == 1
                    self.assertEqual(float_value(m.register('r3'), 4), 462.75 if active else 35.75)

    def test_selector_to_hardcut_controlled_comparison(self):
        results = []
        for gear in (0, 1, 8, 9):
            for speed in (0, 3840):
                for enabled in (0, 1):
                    m = self.machine(gear, speed, enabled, 'tcm')
                    m.register('r29', 0)
                    m.register('r31', 5000 * 8)  # illustrative non-TCM selected ceiling
                    put(m, 0x40012776, 3800 * 8, 2)  # illustrative TCM speed request
                    m.run(S.TCM_HOOK, stop=0x2B9EC4)
                    source = m.register('r29')
                    request_excluded = enabled == 1 and gear in (0, 9) and speed == 0
                    self.assertEqual(source, 0 if request_excluded else 4)
                    selected_speed = m.register('r31')
                    self.assertEqual(selected_speed, (5000 if request_excluded else 3800) * 8)
                    # Same actual extreme-cut block used by the read-only audit.
                    m.register('r4', 65535)
                    put(m, 0x400123CA, 4300 * 8, 2)
                    put(m, 0x40011AD8, source, 2)
                    put(m, 0x4001D05D, 0, 1)
                    m.run(0x2BA0CE, stop=0x2BA146)
                    self.assertEqual(m.spaces['ram'][0x4001D05D], int(request_excluded))
                    results.append((gear, speed, enabled, source, m.spaces['ram'][0x4001D05D]))
        print('Selector-to-extreme-cut cases:', len(results))

    def test_default_off_integrity_reservations_and_existing_data(self):
        export = Export(self.candidate)
        self.assertEqual(self.candidate[export.file_offset(S.CONTROL):export.file_offset(S.CONTROL) + 2], b'\0\0')
        self.assertTrue(all(r['sum_valid'] and r['crc_valid'] for r in export.audit()))
        self.assertEqual(len(self.candidate), len(self.source))
        self.assertEqual(self.candidate[0x41AA78:0x41AA78 + 162], self.source[0x41AA78:0x41AA78 + 162])
        self.assertEqual(self.candidate[0x45F878:0x45F880], self.source[0x45F878:0x45F880])
        donor = next((ROOT / 'deliverables/builds_11-10-26_V2').glob('*_A_*.bin')).read_bytes()
        self.assertEqual(struct.pack('>81h', *S.PN_RAW), donor[0x41AA78:0x41AA78 + 162])
        allowed = [(export.file_offset(S.TCM_HOOK), export.file_offset(S.TCM_HOOK) + 4),
                   (export.file_offset(S.PN_CALL), export.file_offset(S.PN_CALL) + 4)]
        allowed += [(r['file_offset'], r['file_offset'] + r['size']) for r in self.manifest['reservations']]
        allowed += [(export.file_offset(cpu), export.file_offset(cpu) + 2)
                    for segment in export.segments for cpu in (segment.checksum_cpu, segment.crc_cpu)]
        self.assertFalse([i for i, (a, b) in enumerate(zip(self.pilot, self.candidate))
                          if a != b and not any(lo <= i < hi for lo, hi in allowed)])
        for cpu in (S.TCM_CODE, S.PN_CODE):
            self.assertEqual(cpu >> 12, 0x46673C >> 12)
            code = S.shim(cpu, 'tcm' if cpu == S.TCM_CODE else 'demand')
            instructions = self.context.disassemble(code, base_address=cpu).instructions
            self.assertEqual(sum(i.length for i in instructions), len(code))

    def test_combined_config_valid_ids_and_axes(self):
        full = (ROOT / 'deliverables/ezlynk/9844/EZLYNK_L5P_9844_Performance_Maps.csv').read_text(encoding='latin1')
        content = S.config(full, P.config(full, self.pilot_manifest), self.manifest)
        rows = list(csv.reader(line for line in content.splitlines() if line and not line.startswith('#')))
        self.assertTrue(all(len(row) == 21 for row in rows))
        maps = [r for r in rows[1:] if r[5] != 'C']
        self.assertEqual(len(maps), 55)
        self.assertTrue(all(re.fullmatch('C[0-9]+', r[0]) for r in maps))
        self.assertEqual(len({r[0] for r in maps}), len(maps))
        byid = {r[0]: r for r in maps}
        for row in maps:
            if row[5] == 'Z':
                x, y = (byid[k] for k in row[16].split(':'))
                self.assertEqual((x[5], y[5]), ('X', 'Y'))
                self.assertEqual(int(row[6]), int(x[6]) * int(y[6]))

    def test_diagnostic_readback_verifier_rejects_missing_hook(self):
        self.assertEqual(S.verify_readback(self.candidate, self.source)['status'],
                         'STATIC_DIAGNOSTIC_PATCH_PRESENT')
        missing = bytearray(self.candidate)
        offset = Export(self.source).file_offset(S.TCM_HOOK, 4)
        missing[offset:offset + 4] = self.source[offset:offset + 4]
        missing = Export(self.source).repair(missing)
        self.assertEqual(S.verify_readback(missing, self.source)['status'], 'STATIC_CHECK_FAILED')


if __name__ == '__main__':
    unittest.main()
