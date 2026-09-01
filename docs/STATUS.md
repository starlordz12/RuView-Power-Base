# Status

**Current position:** Stage A (validate) — part selection largely done, mechanical
verification blocked.

**Next action:** obtain the YD-ESP32-S3 mechanical drawing and confirm it against the
user's physical V1.3 board (gate item G1).

**Do not order. Nothing here has passed ERC, DRC, or a gerber inspection.**

---

## Stage progress

| Stage | What it covers | State |
|---|---|---|
| A — Validate | datasheets, part availability, DevKit mechanical truth, GPIO map | **in progress** |
| B — Schematic | 7 sheets per spec §24 Stage B | not started |
| C — ERC | zero unexplained violations | not started |
| D — PCB | placement, keepout, power routing, planes, thermal vias | not started |
| E — DRC | PCBWay-friendly rule set | not started |
| F — Manufacturing | gerbers, drill, BOM, CPL, drawings, STEP | not started |

## Environment

| Item | State |
|---|---|
| KiCad | ✅ 10.0.6 installed at `%LOCALAPPDATA%\Programs\KiCad\10.0` |
| `kicad-cli` | ✅ `%LOCALAPPDATA%\Programs\KiCad\10.0\bin\kicad-cli.exe` |
| Host board | YD-ESP32-S3 Core Board N8R8, **rev V1.3 (2022)**, ×5 |
| Target cell | Molicel 3000 mAh 18650, exact model unconfirmed |

## Blocking gate items

### G1 — YD-ESP32-S3 V1.3 mechanical and header map ⛔ blocking

Everything downstream of placement depends on this: socket row spacing, board outline,
antenna keepout position, and every GPIO assignment.

The vendor publishes `ESP32-S3-Metric.pdf` (116 KB) and `YD-ESP32-S3-SCH-V1.4.pdf`
(429 KB) in [vcc-gnd/YD-ESP32-S3](https://github.com/vcc-gnd/YD-ESP32-S3). **The
schematic is V1.4 and the user's board is V1.3** — the vendor README states authentic
boards are V1.4 and that clones copy V1.2, so V1.3 is undocumented territory.

Required before layout is committed:

1. Fetch the vendor mechanical drawing and schematic. *(awaiting download approval)*
2. Physically measure the user's board: socket row spacing centre-to-centre, overall
   length and width, and the distance from the pin-1 end to the antenna edge.
3. Reconcile measurement against the drawing. If they disagree, the physical board wins.

### G2 — Molicel cell model unconfirmed ⛔ blocks charge configuration

Spec §30.1 explicitly forbids finalising charger settings from the informal cell
description. The printed model number on the user's actual cell must be read and checked
against the current Molicel datasheet before the 2.0 A charge target is accepted.

### G3 — GPIO assignment ⛔ blocked by G1

Five LEDs, one button, and I2C need pins that avoid strapping (GPIO0/3/45/46), PSRAM
(GPIO35/36/37), native USB (GPIO19/20), UART0 (GPIO43/44) and the onboard RGB (GPIO48),
and that RuView does not claim.

## Open engineering questions

Carried from [DECISIONS.md](DECISIONS.md#d5---not-decided-yet):

- CH224K VDD supply topology — resistor from VBUS or a discrete LDO?
- BQ25895 I2C watchdog behaviour, and whether its **default** register state is safe for
  this cell with no host running. That is the state the board sits in whenever the ESP32
  is absent, held in reset, or crashed.
- Whether a discrete 1S protection IC is required. Working assumption: **yes**, because
  the cell is user-removable and may be unprotected.

## Quality gate before order

Spec §39's checklist is the release gate. **0 of 22 items passed.** It is reproduced
there and will be tracked here once Stage B begins.

## Session log

| Date | What happened |
|---|---|
| 2026-08-31 | Project created. Board identity corrected to YD-ESP32-S3 V1.3 (D1). Architecture trimmed: CH224K replaces STUSB4500 (D2), PCA9633 dropped (D3). KiCad 10.0.6 installed. Four critical actives validated with exact MPNs; USB-C, sockets and holder selected. Board size estimated ~90 × 60 mm. |
