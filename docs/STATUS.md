# Status

**Current position:** Stage A (validate) — complete except for two physical checks that do
not block schematic work.

**Next action:** Stage B — draw the seven schematic sheets, starting with the CH224K PD
input and the BQ25895 charger/power-path, both against vendor reference designs.

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

### G1 — YD-ESP32-S3 V1.3 mechanical and header map 🟡 resolved on paper, caliper check owed

Vendor drawing and schematic obtained and read. Board geometry and the full 44-pin map are
recorded in [MECHANICAL.md](MECHANICAL.md) and confirmed self-consistent: **27.94 × 57.15 mm,
rows 25.40 mm apart, 22 pins at 2.54 mm, antenna overhangs the pin-1 edge by 6.24 mm.**
The pinout is **identical to the official Espressif DevKitC-1**.

Remaining: three caliper measurements on the user's physical V1.3 board, because V1.3 sits
between the vendor's "counterfeit V1.2" and "authentic V1.4" and is not itself documented.
The user has calipers and has agreed. **Not blocking schematic work; blocking before layout
is committed.**

### G2 — Cell identity does not match the spec's assumption ⛔ blocks charge configuration

The cell marking matches neither the P30B nor the M35A cleanly, and the two differ by 5× in
permitted charge current. Resolved for now by building the hardware for 2.0 A and defaulting
the firmware to 1.0 A — see [D4](DECISIONS.md#d4--hardware-built-for-20a-firmware-defaults-to-10a-until-the-cell-is-identified).

**Does not block layout.** Blocks the firmware default constant and the release gate.

### G3 — GPIO assignment ✅ resolved

Proposed map in [MECHANICAL.md](MECHANICAL.md#proposed-carrier-gpio-assignment). All carrier
signals land on J1, leaving J2 entirely free for RuView. I2C on the ESP32-S3 default pair
(GPIO8/9). No strapping, PSRAM, USB, UART or RGB pins used.

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
| 2026-08-31 | Vendor drawing read: YD board is 27.94 × 57.15 mm, rows 25.40 mm, antenna overhangs pin-1 edge by 6.24 mm; all 44 pins confirmed identical to official DevKitC-1. GPIO map proposed on J1 only (G3 closed). Cell marking found to match neither P30B nor M35A — charge policy split to 2.0 A hardware / 1.0 A firmware default (D4). |
