# 9844 stationary P/N diagnostic candidate

## Status and scope

**Default disabled; hardware unverified.** This adds two independently controlled
experiments to the existing pilot-SOTF prototype. It does not establish that a
TCM request is the cause on the truck, nor that the internal gear/speed inputs
are reliable enough for an enabled vehicle release. No ECU was connected.

The source is the exact clean 11-10-26 V2 export accepted by the pilot builder.
The output includes the pilot quantity feature and keeps its 45 copies. Both
new stationary controls are **0** in the generated binary. The previous pilot
BIN and its standalone CSV are unchanged.

## Two controls

| CSV control | Value 0 | Value 1, when the software guard passes |
|---|---|---|
| Stationary PN - Exclude TCM Speed Request | Original arbitration input | Treat this one TCM speed-request input as inactive for this arbitration step |
| Stationary PN - Use Diagnostic Torque Table | Original P/N torque table | Substitute a separate copy of the earlier A-build's P/N demand table |

The raw guard requires internal gear state **0 or 9** and vehicle-speed raw value
**exactly zero**. The request experiment additionally requires request status
exactly 1. The demand experiment additionally requires the original P/N table
pointer. A control must be exactly 1; all other byte values leave its feature off.

The 0/9 pair is the same pair checked by the existing GM extreme-cut path. Its
live gear meaning, validity/failsoft behavior and the zero-speed signal still
need confirmation on this controller. **A false zero-speed or P/N indication
could satisfy this guard.** The checks performed here do not validate fault
containment or claim that the guard is production-qualified.

## Implementation

The transmission experiment replaces the load at CPU `0x2B9EA2` with a branch to
`0x466D00`. The shim executes the original load and only changes its local r30
result to zero when enabled and guarded. The shared network status/request RAM
is not overwritten. Other consumers can still see the original TCM signals.
The code then returns to `0x2B9EA6`, where the original arbitration comparison
continues. The shared hardcut code itself is not patched.

The demand experiment redirects the P/N interpolation call at `0x283762` through
`0x466E00`. Its shim chooses either the original data pointer or the new table
and tail-calls the unchanged GM interpolation routine. Original axes, fractions
and scaling are retained. The original P/N table is not edited.

Both shims preserve CR, LR, CTR and all GPRs other than the intended original
load result or selected pointer. They use temporary stack storage, not new
persistent RAM. Proposed code remains in the same 4 KiB page as the final
existing HPT code. This remains static placement evidence, not live MMU proof.

| Item | CPU address | Export offset |
|---|---|---|
| Request-control byte, default 0 | `0x175500` | `0x5154E0` |
| Demand-control byte, default 0 | `0x175501` | `0x5154E1` |
| Diagnostic P/N table, 81 signed words | `0x175520` | `0x515500` |
| Request shim reservation | `0x466D00–0x466DFF` | `0x266D00–0x266DFF` |
| Demand shim reservation | `0x466E00–0x466EFF` | `0x266E00–0x266EFF` |

The separate demand table reproduces the earlier A-build's values, with only
the new guard controlling its use. At full pedal / 4000 rpm it requests 462.75 Nm
(341.3 lb-ft), versus 35.75 Nm (26.4 lb-ft) in the original. It is not a dynamic
copy of each tune position's rolling pedal map and can exceed the rolling demand
of the milder positions. It is a diagnostic table, not a validated final tune.

Existing 4200/4175 cut/resume settings, the 8000 rpm TCM fuel-cut offset,
overspeed/bounce protections, original P/N table and pilot maps remain unchanged.
Tune 4's intentional zeroed 3600 rpm torque-to-fuel row also remains in place.
The test does not promise that every tune can reach the global cut, or that
other torque/fuel controls will allow it.

## Interpretation of the independent controls

| Request control | Demand control | Controlled question |
|---:|---:|---|
| 0 | 0 | Baseline with both diagnostic behaviors off |
| 1 | 0 | Does excluding this speed request change the selected limit source? Original stationary demand still tapers. |
| 0 | 1 | Does the separate demand table change the response? TCM speed arbitration remains original. |
| 1 | 1 | Both identified paths are addressed under the guard; other limits and shared corrections still apply. |

These define experiments, not instructions to enable an unverified file on a
vehicle. Confirm the actual request/source state and internal gear/speed inputs,
tool acceptance, recoverability and readback before considering enabled tests.
The first hardware evaluation should retain both zero controls. Default off
still adds code execution; passing host tests is not hardware-equivalence proof.

## Host checks completed

- Seven tests pass.
- 1,350 independent SLEIGH/P-code cases cover gear states 0–15 and invalid
  16-bit examples, zero/nonzero speed, enable values 0/1/255, request statuses
  0/1/2/65535, register preservation and CR/LR/CTR preservation.
- Sixteen cases execute actual arbitration and the extreme-cut instruction block
  in sequence. With an illustrative competing ceiling of 5000 rpm, TCM request
  of 3800 rpm and engine input of 4300 rpm, only the enabled zero-speed 0/9 cases
  exclude source 4 and allow the shared extreme-cut flag. Those values are
  host-model inputs, not measurements or engine-test instructions.
- Sixteen actual GM interpolation cases confirm original versus substituted
  torque values at the 4000 rpm / 100% pedal point, with other states unchanged.
- Byte-difference bounds preserve existing pilot code/data outside the new
  reservations, two hook sites and integrity words.
- All six segment sums/CRCs pass; file length is unchanged.
- The combined CSV has valid numeric C IDs and resolved axes. Its pilot section
  is retained, with two new controls, two shared axes and one new demand table.
- A readback check detects a missing diagnostic hook even when checksums have
  been corrected. A passing check establishes file presence only.

No interrupt, stack-headroom, watchdog, live gear-validity, VSS-fault, engine or
TCM-message timing validation was performed.

## Reproduce and check a readback

From the repository root, Python 3 with `pypcode==4.1.0`:

```sh
python -m unittest discover -s tools -p test_stationary_pn_9844.py -v
python tools/stationary_pn_9844.py 'uploads/ECM-binary-file-G66E41AT1-Nelly_11-10-26_-JOSEPH_CLARK_SOTF_Will_Miller_edit__nelly_3_V3_11_10_26_V2__exported.bin' --out /tmp/pn-diagnostic
python tools/stationary_pn_9844.py 'uploads/ECM-binary-file-G66E41AT1-Nelly_11-10-26_-JOSEPH_CLARK_SOTF_Will_Miller_edit__nelly_3_V3_11_10_26_V2__exported.bin' --verify /path/to/full_readback.bin
```

The new combined CSV requires the new diagnostic binary. It cannot install the
code itself. A profile export is not necessarily a readback from flash, and a
calibration-only export cannot verify the program hooks. Keep those evidence
types distinct.
