# 9844 pilot SOTF: hardware verification record

Status: **hardware unverified**. This record separates a successful file check
from a successful ECU test. No ECU programming or live-engine test has been
performed by the software author.

The candidate is built from the clean 11-10-26 V2 binary. It includes the pilot
extension only; it does not include the separate A/B/C P/N and vane experiments.
All 45 pilot copies initially equal their base tables. Ordinary corrections,
timing, dwell and axes remain shared. This is for 9844 only, not 9843.

## Before any hardware write

- Record ECU hardware identification, OS and calibration identification from the
  actual module. A filename alone is insufficient.
- Retain the verified original read and the clean source. Confirm the recovery
  method works for this controller and that the bench setup follows its maker's
  power/wiring instructions. This document supplies no pinout or power settings.
- Establish that the chosen programming workflow can write the modified program
  region and the new calibration region. A successful calibration-only write
  cannot install this feature. Resolve any tool/authentication incompatibility
  before proceeding; valid sums/CRCs alone do not establish acceptance.
- Independently review the proposed locations and code for this ECU. Export
  descriptors and same-page placement are static evidence, not a live MMU test.

## First hardware acceptance test

Use the original-equivalent candidate, with its pilot copies unedited, for the
first controlled bench evaluation by someone equipped to recover the module.
No vehicle, driving, RPM or load test is specified by this document.

Record these observations rather than treating a programming progress bar as a
pass:

| Observation | Result / evidence |
|---|---|
| Exact ECU and source identities agree | |
| Workflow supports the modified program and calibration regions | |
| Programming accepted and completed | |
| Module remains responsive after the required reset/key cycle | |
| Complete program and calibration readback obtained | |
| Readback checker passes all nine calls and nine shims | |
| Readback checker passes marker, copies and all six segment checks | |
| Unexpected resets or new faults investigated | |

Run the packaged read-only verifier on a complete same-format export:

```sh
python tools/verify_pilot_sotf_9844.py readback.bin --source uploads/ECM_9844_11_10_V2_clean.bin
```

`STATIC_PATCH_PRESENT` means the inspected file contains the patch and passes its
integrity checks. It does not establish live execution. A downloaded profile
file may show what was published; it is not necessarily a read from ECU flash.
Retain the programming log and explain the readback's provenance.

## Live pilot-selection validation remains separate

A powered bench ECM without a running engine cannot demonstrate actual pilot
delivery. The next controlled validation needs appropriate engine/instrumentation
support and operating limits selected by the person responsible for the engine.
Do not improvise a high-RPM or road test from this file.

Where the scanner exposes the signals, record engine RPM, selected SOTF position,
active combustion mode, pilot pulse enable/count, commanded pilot 1/2 quantity,
rail pressure, coolant/air temperature and relevant quantity corrections. Confirm
signal meanings and units before comparing them with mm³ table values.

Check position 0 and positions 1–5, startup/not-ready behavior, extension-disabled
behavior and repeated tune transitions. The first candidate has equal copies,
so equal output across positions is expected and cannot prove switching.
Distinguishable calibration changes require a separately reviewed test plan.
Shared corrections and pulse-enable logic can mask a base-table change.

Record desired versus observed behavior at each validated operating point. An
unchanged base table result, a successful flash, and the glow-plug tune indicator
each supply different evidence; none alone proves actual pilot selection.

## Current unperformed checks

Hardware acceptance, actual flash readback, live MMU/flash behavior, interrupts,
stack/watchdog timing, tune transitions and final commanded/delivered pilot
behavior remain unverified. The existing host test results do not resolve them.
