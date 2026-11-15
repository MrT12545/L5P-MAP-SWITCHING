"""Read-only check for this prototype in a same-format E41 binary export.

Can check a future ECU readback without requiring quantity copies to retain their
initial values. Does not communicate with, program, or validate hardware behavior.
"""
import argparse
import json
from pathlib import Path

from e41_export_integrity import Export
import pilot_sotf_9844 as P


def verify(data, source):
    expected, manifest = P.build(source)
    export = Export(data)
    checks = []
    for i, (name, _, call) in enumerate(P.TABLES):
        cpu = P.CODE_CPU + i * P.WRAPPER_STRIDE
        at = export.file_offset(call, 4)
        call_matches = data[at:at + 4] == expected[call - 0x200000:call - 0x200000 + 4]
        code = P.wrapper(cpu, P.DATA_CPU + 32 + i * 5 * P.TABLE_BYTES)
        at = export.file_offset(cpu, len(code))
        wrapper_matches = data[at:at + len(code)] == code
        checks.append(dict(name=name, call_matches=call_matches, wrapper_matches=wrapper_matches))
    integrity = export.audit()
    at = export.file_offset(P.DATA_CPU, 32)
    enable = data[at]
    header_matches = data[at + 4:at + 20] == b'TSM_PILOT_DEV001'
    copies = []
    for row in manifest['tables']:
        at = export.file_offset(row['copy_cpu'], P.TABLE_BYTES)
        raw = data[at:at + P.TABLE_BYTES]
        source_at = row['base_cpu'] + P.CAL_FILE_DELTA
        copies.append(dict(name=row['name'], tune=row['tune'],
                           differs_from_original=raw != source[source_at:source_at + P.TABLE_BYTES],
                           entirely_erased=raw == b'\xFF' * P.TABLE_BYTES))
    valid = (all(x['call_matches'] and x['wrapper_matches'] for x in checks) and
             all(x['sum_valid'] and x['crc_valid'] for x in integrity) and
             header_matches and enable in (0, 1) and not any(x['entirely_erased'] for x in copies))
    return dict(status='STATIC_PATCH_PRESENT' if valid else 'STATIC_CHECK_FAILED',
                extension_enable=enable, header_matches=header_matches,
                calls_and_wrappers=checks, integrity=integrity, copies=copies,
                limitation='A matching export does not prove live ECU execution or pilot behavior')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = args.source or next((root / 'uploads').glob('ECM*11_10*bin'))
    report = verify(args.export.read_bytes(), source.read_bytes())
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'STATIC_PATCH_PRESENT' else 1)


if __name__ == '__main__':
    main()
