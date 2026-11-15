"""Check merged definitions retain physical coverage and matrix orientation."""
import json
from pathlib import Path
import re
import unittest

import compile_9844_master as C
import stationary_pn_9844 as S

ROOT = Path(__file__).resolve().parents[1]


class MasterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = next((ROOT / 'uploads').glob('ECM*11_10*bin')).read_bytes()
        cls.binary, _ = S.build(source)
        cls.master, cls.report = C.compile_master(cls.binary)
        cls.rows = C.parse(cls.master.decode('latin1'))
        cls.maps = [r for r in cls.rows[1:] if r[5] != 'C']
        cls.byid = {r[0]: r for r in cls.maps}
        cls.by_storage = {C.identity(r): r for r in cls.maps}

    def test_numeric_ids_folders_and_nonoverlapping_storage(self):
        self.assertEqual(len(self.maps), len(self.byid))
        self.assertTrue(all(re.fullmatch('C[0-9]+', r[0]) for r in self.maps))
        self.assertTrue(all(len(r) == 21 for r in self.rows))
        folders = {r[17] for r in self.rows[1:] if r[5] == 'C'}
        for row in self.maps:
            self.assertTrue(all(x in folders for x in row[17:20] if x and x != '0'))
            if row[16] and row[5] in ('Z', 'Y'):
                self.assertTrue(all(x in self.byid for x in row[16].split(':')))
        intervals = sorted((int(r[1], 16), int(r[1], 16) + int(r[6]) * C.WIDTH[r[7]])
                           for r in self.maps if r[1] != 'MANUAL')
        self.assertTrue(all(right[0] >= left[1] for left, right in zip(intervals, intervals[1:])))

    def test_all_source_rom_items_and_matrix_axes_retained(self):
        matrices = 0
        for source_path in C.INPUTS:
            rows = C.parse((ROOT / source_path).read_text(encoding='latin1'))
            byid = {r[0]: r for r in rows[1:] if r[5] != 'C'}
            for row in byid.values():
                if row[1] != 'MANUAL':
                    self.assertIn(C.identity(row), self.by_storage)
                if row[5] != 'Z':
                    continue
                target = self.by_storage[C.identity(row)]
                source_axes = [byid[x] for x in row[16].split(':')]
                target_axes = [self.byid[x] for x in target[16].split(':')]
                self.assertEqual([x[5] for x in target_axes], ['X', 'Y'])
                for a, b in zip(source_axes, target_axes):
                    left, right = C.values(a, self.binary), C.values(b, self.binary)
                    self.assertEqual(len(left), len(right))
                    self.assertTrue(all(C.close(x, y) for x, y in zip(left, right)))
                matrices += 1
        self.assertEqual(matrices, 489)

    def test_extension_coverage_and_reference_only_maps(self):
        pilot = json.loads((ROOT / 'deliverables/pilot_sotf_9844/manifest.json').read_text())
        pn = json.loads((ROOT / 'deliverables/stationary_pn_9844/manifest.json').read_text())
        addressed = {int(r[1], 16): r for r in self.maps if r[1] != 'MANUAL'}
        for row in pilot['tables']:
            self.assertIn(row['file_offset'], addressed)
        for address in pn['switches'].values():
            self.assertIn(address, addressed)
        self.assertIn(pn['pn_table_file_offset'], addressed)
        self.assertEqual(sum(r[2].startswith('Inactive - ') for r in self.maps), 5)
        self.assertEqual(self.report['maps'], 1125)
        self.assertEqual(self.report['map_types']['Z'], 398)

    def test_plain_core_groups_and_unique_folder_paths(self):
        folders = {r[17]: r[2] for r in self.rows[1:] if r[5] == 'C'}
        root_names = {folders[r[17]] for r in self.maps}
        for name in ['01 Pilot Injection', '02 Main Injection Quantity',
                     '03 Main Injection Timing', '04 Turbo Vane Position']:
            self.assertIn(name, root_names)
            self.assertTrue(any(r[5] == 'Z' and folders[r[17]] == name for r in self.maps))
        contexts = {}
        for row in self.maps:
            for level in range(3):
                fid = row[17 + level]
                context = (level, tuple(row[17:17 + level]))
                self.assertEqual(contexts.setdefault(fid, context), context)
        pilots = [r for r in self.maps if re.match(r'Tune [1-5] - Pilot [12] Quantity', r[2])]
        self.assertEqual(len(pilots), 45)
        self.assertTrue(all(folders[r[17]] == '01 Pilot Injection' for r in pilots))


if __name__ == '__main__':
    unittest.main()
