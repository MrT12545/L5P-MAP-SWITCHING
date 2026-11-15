# L5P Duramax SOTF Tuning Thread

Work from one conversation on GM E41 L5P Duramax tunes. It covers three files:

- **Stock P1B.** Cal E2015G5126111_P1B.
- **9843.** HP Tuners SOTF OS 69709843, cal E2015G5138011_P2B.
- **9844.** HP Tuners SOTF OS 69709844, cal E2015G5141011_P2B. The truck runs the 11-10-26 V2 revision.

The full conversation is in [`conversation/THREAD.md`](conversation/THREAD.md). It holds only the visible messages; tool calls and tool output are left out.

## What's here

| Folder | Contents |
|---|---|
| `conversation/` | The thread as Markdown. |
| `deliverables/ezlynk/9844/` | Full EZ LYNK performance-map config for 9844, plus the small P/N + vane config (v3, with the EGR-override settings). |
| `deliverables/ezlynk/9843/` | Full EZ LYNK performance-map config for 9843, plus the small P/N + vane configs (v2 and lb-ft). |
| `deliverables/winols/` | Named WinOLS map lists for 9843 and 9844, with the "not included" lists. |
| `deliverables/sotf_switch_lists/` | Every map HP Tuners switches per steering-wheel position, with base and copy addresses. |
| `deliverables/builds_11-10-26_V2/` | Modified 11-10-26 V2 files A, B and C, plus the paste sheet. |
| `tools/` | The Python scripts used for the analysis. They expect the original scratchpad layout and are kept for reference. |
| `uploads/` | The files you sent during the thread, byte-for-byte as uploaded (upload ID prefix removed from the names). |

### Files in `uploads/`

| File | What it is |
|---|---|
| `168852_E41_..._P1B.olsx` | Encrypted OLSx download; unreadable outside WinOLS. |
| `E2015G5126112_P1B_E2015G5126111_P1B.zip` | WinOLS project with the stock P1B binary. |
| `WinOLS_GMC_Sierra_3500_HD_..._P1B.csv` | Stock WinOLS map definitions (the source for all naming and placement). |
| `JOSEPH_CLARK_SOTF_..._11_10_26_V2_.hpt` | HP Tuners file for 11-10-26 V2. |
| `ECM-binary-file-..._9843_SOTF_...bin` | 9843 SOTF binary. |
| `JOSEPH_CLARK_SOTF_..._10_29_26__exported.bin` | 9844 SOTF binary, 10-29 revision. |
| `ECM-binary-file-..._11_10_26_V2__exported.bin` | Tuner's clean 9844 11-10-26 V2 binary; the base for builds A, B and C. |
| `ECU-Profile-..._EZ_EDIT_V1_.zip` | The EZ LYNK profile that was flashed with the old config's edits. |
| `EZLYNK_config_9844_PN_FreeRev_SOTF_Vanes.csv` | The old EZ LYNK config with swapped axes; don't use it. |
| `Custom-ECU-configurations-guide.pdf` | EZ LYNK custom configuration guide. |

## The 11-10-26 V2 builds

All three start from the tuner's clean 11-10-26 V2 file.

| File | What it changes |
|---|---|
| **A** daily | Park/Neutral torque table rebuilt from the rolling-neutral pedal map. Idle hiss on tunes 1–3 and rumble on tunes 4–5, in the per-tune vane maps. |
| **B** test | A plus `KeDTRC_b_UseBaseProgOnly = 1`, so standstill uses the rolling pedal maps. This also changes launches from a stop. |
| **C** daily | A plus EGR-override thresholds of 250 / 240, so every tune always uses its own vane maps. If EGR is working, this also changes vane position while EGR is open. |

## Key findings (9844)

- **Per-tune maps.** HP Tuners switches 33 maps per position, 1–5; position 0 uses the base maps.
  - The rail-pump current map is switched off in this file, so in practice 32 maps change per tune.
  - Pilot and post injection are not switched.
  - The per-tune fuel cut slot is disabled, so the 4200 / 4175 fuel cut is shared by every tune.
- **When the shared base maps are used instead:**
  - **EGR open.** Above 3% EGR valve position the ECU uses shared EGR-open vane tables (back below 1%).
  - **Standstill.** Below 15 kph driver demand comes from the Park/Neutral table.
  - **Other combustion modes.** Any mode other than Normal (regen, C2, C3, SCR heat-up) uses its own unswitched maps.
- **Forced Normal mode.** HP Tuners forces Normal combustion mode when temperatures are above per-tune thresholds. Tunes 4–5 are always forced; tunes 1–3 only once warm.
- **Tune 4.** Its torque-to-fuel 3600 rpm row is zero, so it stops at about 3550–3600 rpm. This is intentional.
- **EZ LYNK axes.** X is across the top (the fast index in memory) and Y is down the side. Older configs had the axes swapped; use the FIXED / v3 configs.

## Caution

Keep the original files and a way to reflash them. These builds were checked against the file data only, not on the truck.
