# Per-position pilot quantity: 9844 development prototype

## Status

**Not flash-ready.** This adds a reproducible experimental firmware builder and
an EZ LYNK definition file, not a verified ECU release. No hardware was connected.
The generated binary is deliberately named `CHECKSUM_UNFINISHED` and is not
committed. Do not mistake passing host tests for a successful ECU bench test.

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
| Nine shim slots | `0x466800–0x4670FF` | `0x266800–0x2670FF` |
| Control header and 45 tables | `0x170000–0x17547F` | `0x50FFE0–0x51545F` |

Those ranges are all 0xFF in the exact source. **That does not establish physical
flash availability, executable/calibration mapping, checksum coverage or flash
tool support.** Their reservation remains provisional until those are verified.

Instruction encodings were checked against the NXP/Freescale
[VLE Programming Environments Manual](https://www.nxp.com/docs/en/reference-manual/VLEPEM.pdf)
and the repo's existing VLE decoder. The test interpreter is intentionally a
small host model, not a full e200/SPE emulator.

## Reproduce locally

From the repository root, using Python 3 and no third-party dependencies:

```sh
python -m unittest discover -s tools -p test_pilot_sotf_9844.py -v
python tools/pilot_sotf_9844.py 'uploads/ECM-binary-file-G66E41AT1-Nelly_11-10-26_-JOSEPH_CLARK_SOTF_Will_Miller_edit__nelly_3_V3_11_10_26_V2__exported.bin' --out /tmp/pilot-sotf-bench
```

Output includes an unfinished development binary, manifest and standalone
experimental EZ LYNK CSV. The CSV alone cannot make stock firmware switch pilots.
The existing full configuration has not been overwritten. The numeric extension
control defaults to 1 in the generated candidate; 0 selects base tables.

## Host validation completed

- All nine original calls match the expected branch to the shared lookup.
- All 45 initial copies match their source tables byte-for-byte.
- Changed bytes are confined to the nine calls and two reserved ranges.
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

Candidate SHA-256:

`f821b82165143328f2f13c45fa9467297b2e42c1632f0379268d42fa8daed32f`

The generated candidate differs from the clean source at 22,694 bytes. This
includes initialized header bytes, 21,600 bytes of table storage, shim code and
the changed branch instructions; byte-difference counts need not equal sizes.

## Remaining work before any flash

1. Confirm both proposed reservations are usable mapped flash in this exact
   export and programming workflow; confirm the new code region's VLE mapping.
2. Resolve program/calibration checksums and applicable authentication checks
   without assuming a tool will automatically handle the changes.
3. Independently verify the emitted instructions and full calling convention,
   including e200/SPE state, interrupts, stack headroom and watchdog timing.
4. Bench-test original-equivalent copies, disable/startup behavior and repeated
   position transitions; read back both program and calibration to confirm writes.
5. Verify actual pilot contribution selection and final commanded quantities in
   normal operation before making a calibration change. Host checks do not prove
   this or engine behavior.

No test result presently resolves these items, and no ready-to-flash binary is
included in the repository changes.
