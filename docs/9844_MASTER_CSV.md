# 9844 EZ LYNK master

`deliverables/master/TSM_9844_MASTER_EZLYNK.csv` consolidates the compatible
9844 performance, fixed-v3 P/N/vane, pilot-SOTF and stationary-diagnostic CSVs.
It targets `9844_PILOT_PN_DIAGNOSTIC_DISABLED_UNVERIFIED.bin`.

The master contains 1,125 definitions in 77 folders: 398 two-dimensional maps,
457 X/Y definitions and 270 numeric/selection definitions. All 45 pilot copies,
both stationary diagnostic controls and the separate diagnostic P/N demand table
are present. The five inactive per-tune rail-pump copies are retained as labeled
reference items; editing those copies has no runtime effect in this BIN.

All map IDs are unique numeric `C` IDs. Folder IDs and axis references have been
remapped. Duplicate physical definitions and equivalent manual axes are merged,
while canonical full-config descriptions, addresses, units and scaling remain.
Floating-point S/U flags are treated as equivalent; the full config's higher
precision P/N unit conversion is retained over the small config's rounded form.
Alternate labels are retained in descriptions. Unused manual axes from discarded
duplicate definitions are omitted. Duplicate matrix axes were checked against
actual BIN values before merging, including ROM-versus-manual representations.

This is not a merge of incompatible ECU layouts. 9843 definitions, obsolete
swapped-axis configurations, WinOLS-format map lists and NOT_INCLUDED reports
are excluded. They are separate layouts/formats or reports, not additional
compatible EZ LYNK definitions for this binary.

Validation: three source-coverage tests pass, including all 489 input matrix
definitions and their axis vectors. The repo validator reports zero structural,
range/nonfinite or overlap errors. Its CRLF-only parsing assumption was adapted
in memory for the check. Live EZ LYNK import has not been performed here.

The CSV contains definitions only. Compiling/importing it does not modify a BIN,
enable diagnostic controls or validate the firmware on hardware. The diagnostic
BIN's default-off controls remain off until its actual bytes are edited.

Reproduce from the repository root:

```sh
python tools/compile_9844_master.py --binary /path/to/9844_PILOT_PN_DIAGNOSTIC_DISABLED_UNVERIFIED.bin --out deliverables/master/TSM_9844_MASTER_EZLYNK.csv
python -m unittest discover -s tools -p test_compile_9844_master.py -v
```

Source/output hashes, merge counts and validation results are in the companion
report JSON. No firmware changes are made by the compiler.
