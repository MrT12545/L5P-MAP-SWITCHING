"""Read-only audit of the supplied 9844 stationary/rolling hardcut paths.

Requires pypcode 4.1.0 for the small instruction-block reproduction. It does not
model live TCM messages or prove which limiter source a truck selects.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

import pypcode

import olscsv as O
from pilot_sotf_pcode_check import Machine


ROOT = Path(__file__).resolve().parents[1]


def audit(path):
    image = path.read_bytes()
    maps = {r['IdName']: r for r in O.load(str(ROOT / 'deliverables/winols/WinOLS_L5P_9844_MapList_Named.csv'))}
    wanted = ['KeEOSC_n_RPM_EngExtremeHystHi', 'KeEOSC_n_RPM_EngExtremeHystLo',
              'KeEOSC_n_FC_EngSpdLmtOfst', 'KeEOSC_n_FC_AntiStallLim',
              'KeDTRC_b_UseBaseProgOnly', 'KeDTRC_v_MinARM']
    values = {}
    for name in wanted:
        row = maps[name]
        values[name] = dict(cpu=row['Fieldvalues.StartAddr.Cpu'], file_offset=row['Fieldvalues.StartAddr'],
                            value=O.decode_map(image, row)[2][0])
    table = maps['KtDTRC_M_EngTrqReqForRPM']
    cols, rows, data = O.decode_map(image, table)
    pn = dict(cpu=table['Fieldvalues.StartAddr.Cpu'], file_offset=table['Fieldvalues.StartAddr'],
              rpm=O.axis(image, table, 'X', cols), pedal=O.axis(image, table, 'Y', rows),
              full_pedal_nm=data[-cols:], full_pedal_lbft=[x * 0.737562149 for x in data[-cols:]])
    comments = {}
    stock_definitions = next((ROOT / 'uploads').glob('WinOLS*.csv'))
    for row in csv.DictReader(stock_definitions.open(encoding='latin1', newline=''), delimiter=';'):
        if row['IdName'] in ['KeEOSC_n_FC_EngSpdLmtOfst', 'KeEOSC_n_FC_AntiStallLim']:
            comments[row['IdName']] = re.sub('<[^>]+>', ' ', row.get('Comment', '')).strip()
    # Reproduce the actual extreme-cut block with a fixed arbitrated speed
    # limit of 3800 rpm, source-state 0 versus source-state 4, and prior cut=0.
    # State 4 comes from the external transmission-speed input path identified
    # at 0x429FCC/0x429FD0 -> 0x2B9EA2..0x2B9EC2 -> 0x2B9EFC.
    offset = values['KeEOSC_n_FC_EngSpdLmtOfst']['value']
    anti_stall = values['KeEOSC_n_FC_AntiStallLim']['value']
    threshold_raw = max(min(round((3800 + offset) * 8), 65535), round(anti_stall * 8))
    context = pypcode.Context('PowerPC:BE:32:e200')
    cache = {}
    matrix = []
    for mode in (0, 4):
        for rpm in (3800, 4200, 4300, 8000):
            for road_kph in (0, 30):
                machine = Machine(context, image, cache)
                for reg in range(32):
                    machine.register(f'r{reg}', 0)
                machine.register('r15', 0x40018000)
                machine.register('r4', threshold_raw)

                def put(address, value, width):
                    for index, byte in enumerate(value.to_bytes(width, 'big')):
                        machine.spaces['ram'][address + index] = byte

                put(0x400123CA, rpm * 8, 2)  # current engine speed, 1/8 rpm
                put(0x40011AD8, mode, 2)    # arbitrated limiter source
                put(0x400134D8, 0, 2)       # fixed gear state for controlled comparison
                put(0x4001D05D, 0, 1)       # no previous extreme cut
                put(0x4001228E, road_kph * 128, 2)  # VSS used by separate stopped guard
                machine.run(0x2BA0CE, stop=0x2BA146)
                result = machine.spaces['ram'][0x4001D05D]
                expected = int(mode != 4 and rpm > 4200)
                if result != expected:
                    raise AssertionError((mode, rpm, road_kph, result, expected))
                matrix.append(dict(limiter_source=mode, engine_rpm=rpm, vehicle_kph=road_kph,
                                   extreme_fuel_cut_flag=result))
    return dict(source_file=path.name, source_sha256=hashlib.sha256(image).hexdigest(),
                calibration=values, pn_table=pn, original_definition_notes=comments,
                controlled_example=dict(arbitrated_limit_rpm=3800,
                                        tcm_cut_threshold_raw=threshold_raw,
                                        tcm_cut_threshold_rpm=threshold_raw / 8,
                                        prior_cut_flag=0, gear_state=0),
                instruction_block_cases=matrix,
                conclusion='A selected transmission-speed limit can suppress the shared extreme hardcut; live activation remains unproven',
                limits=['No actual TCM traffic, ECU trace or datalog is available',
                        'The tested source states are controlled inputs, not observed truck states',
                        'This is not a complete limiter, arbitration, hysteresis or engine model',
                        'No calibration or firmware was changed'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', nargs='?', type=Path,
                        default=next((ROOT / 'uploads').glob('ECM*11_10*bin')))
    args = parser.parse_args()
    print(json.dumps(audit(args.binary), indent=2))
