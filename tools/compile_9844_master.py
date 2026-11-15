"""Compile compatible 9844 EZ LYNK definitions into one numeric-ID master.

9843 layouts, old swapped-axis configs, WinOLS lists and NOT_INCLUDED reports
are deliberately not imported as ECU definitions.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    'deliverables/ezlynk/9844/EZLYNK_L5P_9844_Performance_Maps.csv',
    'deliverables/ezlynk/9844/EZLYNK_config_9844_PN_FreeRev_SOTF_Vanes_FIXED_v3.csv',
    'deliverables/pilot_sotf_9844/EZLYNK_9844_Pilot_SOTF_BENCH.csv',
    'deliverables/stationary_pn_9844/EZLYNK_9844_Pilot_and_PN_DIAGNOSTIC.csv',
]
WIDTH = {'1': 1, '2': 2, '4': 4, 'F': 4}


def visible_layout(rows, old_folders):
    """Give each complete folder path its own IDs and plain operating groups."""
    folder_names = {r[17]: r[2] for r in old_folders}
    referenced = {token for r in rows if r[16] and r[5] in ('Z', 'Y')
                  for token in r[16].split(':')}
    roots = ['01 Pilot Injection', '02 Main Injection Quantity',
             '03 Main Injection Timing', '04 Turbo Vane Position',
             '05 Boost', '06 Rail Pressure and Fuel Pump',
             '07 Driver Demand', '08 Torque Management and Smoke Limits',
             '09 Rev and Speed Limiters', '10 Idle and Engine Speed',
             '11 Exhaust Brake', '12 Post Injection', '13 Other Fuel Control',
             '14 Stationary PN Diagnostics', '15 SOTF Controls', '90 Shared Axes']

    def group(row, gm, path):
        name = row[2]
        original = path[0] if path else ''
        if 'Stationary PN Diagnostics' in original or name.startswith('Stationary PN'):
            return roots[13]
        if 'Extension Enable' in name:
            return roots[14]
        if ('Injection - Pilot' in original or 'QntyR1' in gm or 'QntyR2' in gm
                or 'DT_R1' in gm or 'DT_R2' in gm or re.search(r'\bPilot [12]', name)):
            return roots[0]
        if 'Main Timing' in original or 'SOI_M' in gm or 'Main Injection Timing' in name or 'Main Timing' in name:
            return roots[2]
        if ('Main Quantity' in original or 'TorqToFuel' in gm or 't_ET_InjTbl' in gm
                or 'Main Pulse Width' in name):
            return roots[1]
        if 'VGT' in gm or 'Vane' in name or any('Vane Map Selection' in x for x in path):
            return roots[3]
        if 'BstSetPt' in gm or 'Boost and VGT' in original:
            return roots[4]
        if 'FHPC' in gm or 'Rail Pressure and Fuel Pump' in original:
            return roots[5]
        if 'DTRC' in gm or 'Driver Demand' in original or 'Park/Neutral Pedal' in name:
            return roots[6]
        if 'EATC' in gm or 'ECPC' in gm or 'Torque' in original or 'Smoke' in original:
            return roots[7]
        if 'Rev and Speed' in original:
            return roots[8]
        if 'Idle and Engine' in original:
            return roots[9]
        if 'Exhaust Brake' in original:
            return roots[10]
        if 'Post' in original:
            return roots[11]
        return roots[12]

    classified = []
    counts = collections.Counter()
    pilot_names = 0
    for original_row in rows:
        row = original_row.copy()
        path = [folder_names[x] for x in row[17:20] if x and x != '0']
        gm_match = re.search(r'GM name:\s*(\S+)', row[3])
        gm = gm_match.group(1) if gm_match else row[2]
        tune = re.search(r'\bTune ([1-5])\b', row[2])
        position = f'Tune {tune.group(1)}' if tune else 'Base and Shared'
        root = group(row, gm, path)
        old_name = row[2]
        pilot = re.search(r'KtFULC_V_QntyR([12])(?:_Ptn([12]))?_(Lo|Mid|Sea)BC1', gm)
        if pilot and tune:
            layer = {'Lo': 'Low Baro', 'Mid': 'Mid Baro', 'Sea': 'Sea Level'}[pilot.group(3)]
            pattern = f' - Pattern {pilot.group(2)}' if pilot.group(2) else ''
            row[2] = f'Tune {tune.group(1)} - Pilot {pilot.group(1)} Quantity{pattern} - {layer}'
            pilot_names += 1
        elif gm.startswith('KtETQC_m_TorqToFuel_'):
            layer_match = re.search(r'_(Lo|Mid|Sea)BC1', gm)
            layer = {'Lo': 'Low Baro', 'Mid': 'Mid Baro', 'Sea': 'Sea Level'}.get(
                layer_match.group(1) if layer_match else '', 'Other Mode or Correction')
            prefix = f'Tune {tune.group(1)} - ' if tune else ''
            if layer_match:
                row[2] = prefix + 'Main Injection Quantity - Torque to Fuel - ' + layer
            else:
                row[2] = 'Main Injection Quantity - ' + old_name
        if row[2] != old_name:
            row[3] += ' | Previous label: ' + old_name
        if row[0] in referenced and row[5] in ('X', 'Y'):
            logical = (roots[15], re.sub(r'^\d+ ', '', root), 'Breakpoints')
        else:
            kind = {'Z': 'Tables', 'X': 'Curves', 'Y': 'Curves', 'N': 'Parameters', 'S': 'Switches'}[row[5]]
            if tune:
                family = re.sub(r'^\d+ ', '', root)
                if 't_ET_InjTbl' in gm or 'Pulse Width' in row[2]:
                    family = 'Pulse Width'
                elif pilot:
                    family = 'Pilot Injection Quantity'
                if row[5] in ('N', 'S'):
                    family += ' - ' + kind
                logical = ('00 SOTF Tunes', position, family)
            else:
                logical = (root, position, kind)
            counts[root] += 1
        classified.append((row, logical))
    folders = []
    identities = {}

    def folder(path):
        if path not in identities:
            fid = f'F{len(identities) + 1}'
            identities[path] = fid
            folders.append(['FFFF', '0x0000', path[-1], '', '0', 'C'] + ['0'] * 11 + [fid, '0', '0', ''])
        return identities[path]

    # Root declaration order is explicit, so the four requested groups come first.
    for root in ['00 SOTF Tunes'] + roots:
        if any(path[0] == root for _, path in classified):
            folder((root,))
    result = []
    for row, path in classified:
        row[17:20] = [folder(path[:i + 1]) for i in range(3)]
        result.append(row)
    return result, folders, dict(counts), pilot_names


def parse(text):
    return [r for r in csv.reader(line for line in text.splitlines()
                                  if line and not line.startswith('#')) if any(r)]


def close(a, b):
    return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-12)


def values(row, binary):
    count = int(row[6])
    if row[1] == 'MANUAL':
        return [float(x) for x in row[20].split(';')]
    address = int(row[1], 16)
    fmt = {'1': 'b' if row[9] == 'S' else 'B',
           '2': 'h' if row[9] == 'S' else 'H',
           '4': 'i' if row[9] == 'S' else 'I', 'F': 'f'}[row[7]]
    raw = struct.unpack_from('>' + fmt * count, binary, address)
    return [x * float(row[10]) + float(row[11]) for x in raw]


def identity(row):
    if row[1] == 'MANUAL':
        tokens = []
        for token in row[20].split(';'):
            try:
                tokens.append(float(token))
            except ValueError:
                tokens.append(token.strip())
        return ('manual', row[5], tuple(tokens), row[4].casefold())
    return ('rom', int(row[1], 16), int(row[6]), WIDTH[row[7]])


def compile_master(binary):
    sources = []
    header = None
    for relative in INPUTS:
        path = ROOT / relative
        raw = path.read_bytes()
        rows = parse(raw.decode('latin1'))
        if header is None:
            header = rows[0]
        if rows[0] != header or any(len(r) != 21 for r in rows):
            raise ValueError(f'Invalid header/width in {relative}')
        maps = {r[0]: r for r in rows[1:] if r[5] != 'C'}
        if len(maps) != sum(r[5] != 'C' for r in rows[1:]):
            raise ValueError(f'Duplicate IDs within {relative}')
        folders = {r[17]: r for r in rows[1:] if r[5] == 'C'}
        sources.append(dict(path=relative, rows=rows[1:], maps=maps, folders=folders,
                            sha256=hashlib.sha256(raw).hexdigest()))
    canonical = []
    by_storage = {}
    aliases = {}
    duplicate_count = 0
    duplicate_checks = 0
    for source_index, source in enumerate(sources):
        for row in source['rows']:
            if row[5] == 'C':
                continue
            key = identity(row)
            origin = (source_index, row[0])
            if key in by_storage:
                prior = by_storage[key]
                old = prior['row']
                semantic = (row[5], row[7], row[8], '' if row[7] == 'F' else row[9], row[4].casefold())
                old_semantic = (old[5], old[7], old[8], '' if old[7] == 'F' else old[9], old[4].casefold())
                if semantic != old_semantic or not close(row[10], old[10]) or not close(row[11], old[11]):
                    raise ValueError(f'Incompatible interpretations at {key}: {old[2]} / {row[2]}')
                # A matrix's duplicate definitions must have the same X/Y values,
                # even when one CSV uses ROM axes and another manual axes.
                if row[5] == 'Z':
                    original_source = sources[prior['source']]
                    for old_id, new_id in zip(old[16].split(':'), row[16].split(':')):
                        old_axis = original_source['maps'][old_id]
                        new_axis = source['maps'][new_id]
                        left, right = values(old_axis, binary), values(new_axis, binary)
                        if old_axis[5] != new_axis[5] or len(left) != len(right) or not all(close(a, b) for a, b in zip(left, right)):
                            raise ValueError(f'Duplicate table axis disagreement: {row[2]}')
                        duplicate_checks += 1
                aliases[origin] = prior
                if row[2] != old[2] and row[2] not in prior['alternate_names']:
                    prior['alternate_names'].append(row[2])
                duplicate_count += 1
            else:
                entry = dict(row=row.copy(), source=source_index, origin=origin, alternate_names=[])
                canonical.append(entry)
                by_storage[key] = entry
                aliases[origin] = entry
    # Manual axes belonging only to discarded duplicate tables need not clutter
    # the master. Keep every original full-config item and all referenced axes.
    referenced = set()
    for entry in canonical:
        row = entry['row']
        if row[16] and row[5] in ('Z', 'Y'):
            for token in row[16].split(':'):
                referenced.add(aliases[(entry['source'], token)]['origin'])
    discarded_manual_axes = [entry for entry in canonical
                             if entry['source'] != 0 and entry['row'][1] == 'MANUAL'
                             and entry['row'][5] in ('X', 'Y') and entry['origin'] not in referenced]
    canonical = [entry for entry in canonical if entry not in discarded_manual_axes]
    ids = {entry['origin']: f'C{i + 1}' for i, entry in enumerate(canonical)}
    folder_rows = []
    folder_by_title = {}

    def folder(source_index, old_id):
        if old_id in ('', '0'):
            return old_id
        source_row = sources[source_index]['folders'].get(old_id)
        if source_row is None:
            raise ValueError(f'Unknown folder {old_id}')
        title_key = source_row[2].strip().casefold()
        if title_key not in folder_by_title:
            row = source_row.copy()
            row[17] = f'F{len(folder_rows) + 1}'
            folder_rows.append(row)
            folder_by_title[title_key] = row[17]
        return folder_by_title[title_key]

    pump_copies = set()
    switch_list = ROOT / 'deliverables/sotf_switch_lists/SOTF_switched_maps_9844.csv'
    with switch_list.open() as switch_file:
        for row in csv.DictReader(switch_file):
            if row['Base map'] == 'KtFHPC_I_MU_FlowToCurrCvrtr':
                pump_copies.add(int(row['Copy bin offset'][1:], 16))
    output_maps = []
    coverage = collections.Counter()
    for entry in canonical:
        row = entry['row'].copy()
        row[0] = ids[entry['origin']]
        if row[16] and row[5] in ('Z', 'Y'):
            row[16] = ':'.join(ids[aliases[(entry['source'], token)]['origin']]
                               for token in row[16].split(':'))
        row[17:20] = [folder(entry['source'], old) for old in row[17:20]]
        if entry['alternate_names']:
            row[3] += ' | Also named: ' + ' / '.join(entry['alternate_names'])
        if row[1] != 'MANUAL' and int(row[1], 16) in pump_copies:
            row[2] = 'Inactive - ' + row[2]
            row[3] += ' | Rail-pump SOTF switching is disabled in the supplied diagnostic BIN; this copy is reference only.'
        output_maps.append(row)
        coverage[entry['source']] += 1
    if not all(re.fullmatch(r'C[0-9]+', r[0]) for r in output_maps):
        raise ValueError('Invalid master ID')
    output_maps, folder_rows, navigation, pilot_names = visible_layout(output_maps, folder_rows)
    result = [header] + folder_rows + output_maps
    stream = io.StringIO(newline='')
    stream.write('# TSM 9844 MASTER - latest pilot and stationary PN diagnostic firmware definitions\r\n')
    stream.write('# For 9844_PILOT_PN_DIAGNOSTIC_DISABLED_UNVERIFIED.bin; hardware remains unverified. Definitions do not enable switches.\r\n')
    stream.write('# 9843 addresses and obsolete swapped-axis configs are excluded. X is across; Y is down.\r\n')
    csv.writer(stream, lineterminator='\r\n').writerows(result)
    master = stream.getvalue().encode('latin1')
    report = dict(binary_sha256=hashlib.sha256(binary).hexdigest(),
                  output_sha256=hashlib.sha256(master).hexdigest(),
                  folders=len(folder_rows), maps=len(output_maps),
                  map_types=dict(collections.Counter(r[5] for r in output_maps)),
                  input_maps=sum(len(s['maps']) for s in sources),
                  deduplicated_maps=duplicate_count,
                  discarded_unreferenced_manual_axes=len(discarded_manual_axes),
                  duplicate_axis_vector_checks=duplicate_checks,
                  inactive_rail_pump_copies=len(pump_copies),
                  navigation_definition_counts=navigation,
                  plain_named_per_tune_pilot_tables=pilot_names,
                  sources=[dict(path=s['path'], sha256=s['sha256'], input_maps=len(s['maps']),
                                new_canonical_items=coverage[i]) for i, s in enumerate(sources)],
                  excluded='9843 configs; obsolete swapped-axis configs; NOT_INCLUDED reports; WinOLS-format lists',
                  live_ezlynk_import_verified=False)
    return master, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    master, report = compile_master(args.binary.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(master)
    args.out.with_suffix('.report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
