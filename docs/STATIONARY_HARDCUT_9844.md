# Why a 9844 hardcut can work rolling but not stationary

## Finding and its limit

The supplied 9844 code contains a specific **transmission engine-speed request**
path that can override the normal extreme-RPM hardcut behavior. This is more
specific than the earlier speculation about generic transmission torque
reduction. It can explain a smooth stationary ceiling even when the P/N torque
table is raised, while rolling neutral reaches the sharp 4200 rpm cut.

This path is proven to exist in the file, and its cut-flag behavior is reproduced
from the actual instructions. **It is not yet proven to be selected on the truck
at a standstill.** That requires a log or ECU trace. No new test tune is supplied.

## Relevant settings in clean 11-10-26 V2 and the pilot candidate

| Setting | CPU address | Export offset | Value |
|---|---|---|---:|
| `KeEOSC_n_RPM_EngExtremeHystHi` | `0xBF89C` | `0x45F87C` | 4200 rpm |
| `KeEOSC_n_RPM_EngExtremeHystLo` | `0xBF89E` | `0x45F87E` | 4175 rpm |
| `KeEOSC_n_FC_EngSpdLmtOfst` | `0xBF898` | `0x45F878` | 8000 rpm |
| `KeEOSC_n_FC_AntiStallLim` | `0xBF89A` | `0x45F87A` | 1200 rpm |
| `KeDTRC_b_UseBaseProgOnly` | `0x7A72C` | `0x41A70C` | 0 |
| `KeDTRC_v_MinARM` | `0x7A750` | `0x41A730` | 15 km/h |

The supplied stock definition's note for `FC_EngSpdLmtOfst` explicitly says it
controls fuel-cut enable at the engine-speed limit plus this offset **when the
TCM requests an engine-speed limit**. Its anti-stall companion limits that
threshold to the greater of the calculated value and the anti-stall calibration.
The stock note identifies the parameter's purpose; the addresses above are from
the relocated 9844 definitions and code references, not copied from the stock OS.

## Code path

1. The transmission-speed network input handling at `0x429FCC` / `0x429FD0`
   publishes an active/status value and requested engine-speed value into RAM
   `0x40011DE6` / `0x40012776`. Its network-diagnostic neighborhood matches the
   stock `TESN` transmission-engine-speed request definitions. This identification
   is also supported by the explicit TCM wording of the fuel-cut offset note.
2. Arbitration at `0x2B9EA2–0x2B9EC2` checks the active value. If this request is
   more restrictive than the selected speed limit, it adopts the request and sets
   limiter-source state **4**. The selected source is stored at `0x40011AD8`.
3. The extreme-cut routine at `0x2BA098` calculates a request-specific fuel-cut
   threshold from the selected speed limit plus `FC_EngSpdLmtOfst`, using an
   unsigned saturating add, then applies the anti-stall lower bound.
4. Above the shared 4200 rpm threshold, the routine initially sets the extreme-cut
   flag. However, the source-state-4 logic at `0x2BA12E–0x2BA13C` **clears it again
   while RPM is at or below the request-specific threshold**.

For example, with a hypothetical 3800 rpm selected transmission limit, adding
8000 rpm saturates the unsigned 16-bit, 1/8-rpm representation at **8191.875 rpm**.
That defeats the normal 4200 rpm extreme-cut request while source 4 is selected;
the separate governor may hold the engine below that point. The 3800 rpm input
is an example consistent with the report, not a value measured from a TCM file.

The same fixed source state gives the same extreme-cut result with VSS 0 or
30 km/h. The likely rolling/stopped distinction would be **whether the TCM speed
request is active and wins arbitration**, not a direct vehicle-speed enable bit
on the 4200 rpm threshold. Live source-state selection remains to be checked.

## Reproduced instruction behavior

`tools/audit_stationary_hardcut_9844.py` executes block `0x2BA0CE–0x2BA146`
through the existing SLEIGH/P-code host interpreter. With prior cut flag 0 and
the example request-specific threshold above:

| Selected source | RPM | Extreme-cut flag |
|---|---:|---:|
| 0, comparison state | 3800 | 0 |
| 0, comparison state | 4200 | 0 |
| 0, comparison state | 4300 | 1 |
| 4, transmission-speed request | 3800 | 0 |
| 4, transmission-speed request | 4200 | 0 |
| 4, transmission-speed request | 4300 | 0 |

The source comparison is controlled, not an observation of the truck. The audit
also checks both VSS values and an 8000 rpm simulated input. These high simulated
inputs are software tests, not instructions for an engine test. Hysteresis with
an already-active cut, full arbitration and engine behavior are not modeled.

## Additional issue in the pilot candidate: stationary driver demand

The pilot candidate was built on the **clean** file and intentionally does not
contain earlier A/B/C P/N changes. Its full-pedal P/N torque request still tapers:

| RPM | Requested torque, lb-ft |
|---:|---:|
| 3000 | 93.9 |
| 3500 | 60.3 |
| 3800, interpolated | 39.9 |
| 4000 | 26.4 |

That can prevent the engine from ever reaching the hardcut speed. Rolling
neutral above the driver-demand takeover region uses another path. Raising the
P/N table could address that demand limitation, but does not by itself address
the source-4 extreme-cut suppression described above. Earlier reports of an
800 lb-ft P/N request still failing therefore do not rule out this newly traced
request-specific cut logic.

## Decisive evidence still needed

Compare existing stationary and rolling-neutral logs, where the scanner exposes
the signals: actual engine RPM, APP, VSS, transmission requested engine-speed
limit, its active/status signal, selected engine-speed limiter source/limit,
driver requested torque, final torque/fuel quantity and fuel-cut status.

The predicted signature is a winning transmission-speed request/source 4 while
stationary, and a different selected source or inactive request while rolling.
If both cases have the same source state, this explanation alone is insufficient.
RAM addresses above are analysis references, not ready-made scanner PIDs.

No blind change to the 8000 rpm offset, transmission request handling or global
limiter is justified by a static file alone. No binary was modified during this
analysis.
