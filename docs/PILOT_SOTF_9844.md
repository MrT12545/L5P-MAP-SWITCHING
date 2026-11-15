# Per-position pilot quantity: 9844 development prototype

## Status

**Not flash-ready.** This adds a reproducible experimental firmware builder and
an EZ LYNK definition file, not a verified ECU release. No hardware was connected.
The generated binary is named `HARDWARE_UNVERIFIED` and is not committed.
Program/calibration additive sums and CRCs are now corrected and checked.
Do not mistake passing host tests for a successful ECU bench test.

Supported input is only the tuner's clean 11-10-26 V2 export, SHA-256:

`e19408dd83316edc3deb463b5eae44414da0b1035a1819126f9d1efa5922a45d`

The builder rejects other revisions, edited files, builds A/B/C, and a second
application of the patch. Supporting another source requires a separate review.

## Implemented scope

Nine Normal-mode **BC1 contributions** receive five copies each:

| Quantity family | Layers | Copies |
|---|---|---:|
| Pilot 1, pattern 1 | Low / Mid / Sea baro | 15 |
| Pilot 1, pattern 2 | Low / Mid / Sea baro | 15 |
| Pilot 2 | Low / Mid / Sea baro | 15 |

All 45 copies initially contain exactly the source table bytes. Axes remain
shared. The quantity unit is mm³, scaling 1/128, signed big-endian 16-bit values;
each table has 15 RPM columns and 16 quantity rows, 480 bytes.

These are **not all pilot tables in the firmware**. AC11 and CC11 contributions,
special-mode pilot tables, cranking, dwell, timing, pulse enable logic and other
corrections remain as in the source. GM code calculates/blends several of those
contributions; changing one BC1 copy does not guarantee an equal change in final
injected pilot volume. This prototype does not force a combustion mode or change
any EGR, regeneration, diagnostic or protective-mode settings.

## Mechanism

Each of the nine known BC1 lookup calls is redirected to its own small tail-call
shim. The shared GM interpolation function itself is unchanged. Each shim:

1. Saves CR, r0, r6 and r7 in a 32-byte stack frame.
2. Reads the existing HPT readiness byte at CPU `0x4005E400` and selected-position
   byte at CPU `0x4005E414`.
3. Selects a copy only when readiness is exactly 2, position is 1–5, and the
   extension enable byte is exactly 1.
4. Replaces only the map-data pointer in r3, restores the saved state, and
   tail-branches to the original interpolation routine at CPU `0x31FD7C`.

r4–r8 interpolation inputs/scaling, LR, CTR and other GPRs are preserved by the
shim. Position 0, invalid position, startup, and disabled extension use the
original r3 pointer. No persistent RAM slots, HPT descriptor counts, HPT loader
code, or global interpolation entry points are changed. Selection is read for
each lookup, so atomic coordination with all other HPT maps during a tune change
has not been demonstrated.

The nine call sites, base/copy addresses and file offsets are in
`deliverables/pilot_sotf_9844/manifest.json`. Proposed reservations:

| Region | CPU addresses | Export-file offsets |
|---|---|---|
| Nine shim slots | `0x466800–0x466C7F` | `0x266800–0x266C7F` |
| Control header and 45 tables | `0x170000–0x17547F` | `0x50FFE0–0x51545F` |

Those ranges are all 0xFF in the exact source and lie within the file's declared
program/engine-calibration transfer blocks. The shims now fit in the same 4 KiB
page (`0x466000–0x466FFF`) as the final existing HPT instructions, reducing the
placement uncertainty. **This does not prove live MMU permissions, physical flash
behavior or flash-tool support.**

Instruction encodings were checked against the NXP/Freescale
[VLE Programming Environments Manual](https://www.nxp.com/docs/en/reference-manual/VLEPEM.pdf)
and the repo's existing VLE decoder. An independent Ghidra SLEIGH decoder through
`pypcode 4.1.0` also decodes the generated shims. Its `e_mull2i.` spelling notes a
CR0 update that the small repo decoder does not show; the shim restores the full
CR before continuing. Both host interpreters are models, not full ECU emulators.

## Export layout and integrity

`tools/e41_export_integrity.py` parses the range descriptors in the supplied
export instead of assuming one flat CPU-address translation. The program has two
transfer blocks: `0x200000–0x57FFCF` and `0x57FFF0–0x5FFFFF`. Five calibration
segments follow. Their concatenated lengths equal the export's 5,898,192 bytes.
The omitted 32-byte program gap matters for translating later CPU addresses;
the pilot hook/shim locations are before that gap.

The descriptors also give CRC and additive-sum coverage. For all six segments:

- CRC is CRC-16/ARC, stored little-endian in the excluded CRC word.
- The additive word is big-endian and makes the sum of covered 16-bit words,
  including that checksum word, zero modulo 65536.
- CRC excludes both integrity words; the additive sum includes the CRC word.
  Repair therefore writes CRC first and additive sum second.

All 36 stored integrity words (six segments times two words times three source
binaries) reproduce exactly. Repair is byte-identical on each original file.
The candidate passes all 12 checks after the program and engine-calibration
edits. No authentication/signature mechanism was changed or validated.

## Reproduce locally

From the repository root, using Python 3 and no third-party dependencies:

```sh
python -m unittest discover -s tools -p test_pilot_sotf_9844.py -v
python tools/pilot_sotf_9844.py 'uploads/ECM-binary-file-G66E41AT1-Nelly_11-10-26_-JOSEPH_CLARK_SOTF_Will_Miller_edit__nelly_3_V3_11_10_26_V2__exported.bin' --out /tmp/pilot-sotf-bench
```

Output includes a checksum-corrected development binary, manifest and standalone
experimental EZ LYNK CSV. The CSV alone cannot make stock firmware switch pilots.
The existing full configuration has not been overwritten. The numeric extension
control defaults to 1 in the generated candidate; 0 selects base tables.

Optional independent decoder/numeric checks:

```sh
python -m pip install pypcode==4.1.0
python tools/pilot_sotf_pcode_check.py
```

Read-only check of a future same-format readback/export:

```sh
python tools/verify_pilot_sotf_9844.py /path/to/readback.bin
```

This accepts edited pilot copies while checking all nine calls/shims, the marker,
enable value and all segment sums/CRCs. A matching file is not proof of ECU
execution. A calibration-only readback cannot verify the program patch.

## Host validation completed

- All nine original calls match the expected branch to the shared lookup.
- All 45 initial copies match their source tables byte-for-byte.
- Changed bytes are confined to the nine calls, two reserved ranges and declared
  checksum/CRC words.
- Output length equals input length, 5,898,192 bytes.
- 27,648 modeled selector paths cover every 8-bit position, readiness values
  0/1/2/255, and enable values 0/1/255, with randomized GPR/CR inputs.
- Modeled GPR/CR preservation and stack-write bounds pass; longest modeled path
  is 31 shim instructions. That count is not a measured timing result.
- Experimental CSV: 45 table copies, four shared axes, one control, eight folders;
  no duplicate map IDs, missing axis references, out-of-file addresses, numeric
  range failures or overlapping definitions in the repo validator.
- The repo validator needed its CRLF-only split changed to `splitlines()` in
  memory to run on LF checkout files. This patch does not modify that validator.
- Independent SLEIGH P-code checks execute the actual patched call, shim and GM
  interpolation instructions: 162 original-equivalence cases, 360 cases with
  distinct synthetic values in all 45 copies, and 72 fallback numeric cases.
  The equivalence cases compare all GPRs plus LR/CTR/CR fields. Synthetic cases
  include interpolation, corners and out-of-range fraction clamping. These are
  finite host checks, not measured ECU tests. See `validation.json`.

The current candidate SHA-256 and changed-byte count are recorded in
`deliverables/pilot_sotf_9844/manifest.json`. This includes initialized header
bytes, 21,600 bytes of table storage, shim code, branch instructions and integrity
words; byte-difference counts need not equal reservation sizes.

## Remaining work before any flash

1. Confirm the export-declared reservations and same-page placement are usable in
   the actual ECU and programming workflow; static range tables are not a live
   MMU or flash readback.
2. Confirm ECU/tool acceptance, including applicable authentication requirements.
   The additive sums/CRCs are resolved; that does not establish flash acceptance.
3. Verify on hardware the full calling convention, e200/SPE state, interrupts,
   stack headroom, watchdog timing and tune-transition behavior.
4. Bench-test original-equivalent copies, disable/startup behavior and repeated
   position transitions; read back both program and calibration to confirm writes.
5. Verify actual pilot contribution selection and final commanded quantities in
   normal operation before making a calibration change. Host checks do not prove
   this or engine behavior.

Those hardware/tool acceptance items remain open. No hardware-validated binary
is included in the repository changes.
