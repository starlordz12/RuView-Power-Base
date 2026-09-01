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
| Target cell | **Molicel INR-18650-M35A**, 3.6 V / 3.35 Ah — max charge **1.7 A** |

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

### G2 — Cell confirmed as Molicel INR-18650-M35A ✅ resolved

Cell is a **Molicel INR-18650-M35A, 3.6 V / 3.35 Ah**, whose **maximum charge current is
1.7 A** — the spec's 2.0 A target would have exceeded it by 18% on every cycle. Charge
policy set in [D4](DECISIONS.md#d4--cell-is-a-molicel-inr-18650-m35a-the-specs-20a-target-is-unsafe-for-it):
1.0 A default, 1.5 A maximum, 1.7 A hard ceiling, 2.0 A of copper.

This produced a **new hardware requirement** — see G4.

### G3 — GPIO assignment ✅ resolved

Proposed map in [MECHANICAL.md](MECHANICAL.md#proposed-carrier-gpio-assignment). All carrier
signals land on J1, leaving J2 entirely free for RuView. I2C on the ESP32-S3 default pair
(GPIO8/9). No strapping, PSRAM, USB, UART or RGB pins used.

### G4 — ILIM resistor is a safety-critical component ⛔ must be in the schematic

The BQ25895 powers up charging at **2048 mA** with no host present, and its watchdog
restores that default while leaving a host-raised `IINLIM` in place. Because the ESP32 is a
**removable** module, "no host present" is a supported configuration, not a fault.

`RILIM = 680 Ω` on the ILIM pin is the hardware clamp that makes this safe, and it works
because `EN_ILIM` defaults to Enable and is restored by the watchdog. Full derivation in
[D5](DECISIONS.md#d5--the-charge-current-ceiling-is-enforced-in-hardware-by-the-ilim-resistor).

**Treat this resistor as safety-critical.** It must not be value-engineered, substituted, or
marked DNP, and the BOM must say so.

## Open engineering questions

Carried from [DECISIONS.md](DECISIONS.md#d6--still-open):

- CH224K VDD supply topology — resistor from VBUS or a discrete LDO?
- Whether a discrete 1S protection IC is required. Working assumption: **yes** — the
  installed M35A is a bare cell with no protection PCB, and the holder accepts whatever
  18650 the user fits.
- NTC network values, sized to the M35A's permitted charging temperature window rather
  than the charger's defaults.
- TPS63070 feedback divider and inductor, from TI's reference layout.

## Quality gate before order

Spec §39's checklist is the release gate. **0 of 22 items passed.** It is reproduced
there and will be tracked here once Stage B begins.

## Session log

| Date | What happened |
|---|---|
| 2026-08-31 | Project created. Board identity corrected to YD-ESP32-S3 V1.3 (D1). Architecture trimmed: CH224K replaces STUSB4500 (D2), PCA9633 dropped (D3). KiCad 10.0.6 installed. Four critical actives validated with exact MPNs; USB-C, sockets and holder selected. Board size estimated ~90 × 60 mm. |
| 2026-08-31 | Vendor drawing read: YD board is 27.94 × 57.15 mm, rows 25.40 mm, antenna overhangs pin-1 edge by 6.24 mm; all 44 pins confirmed identical to official DevKitC-1. GPIO map proposed on J1 only (G3 closed). Cell marking found to match neither P30B nor M35A — charge policy split to 2.0 A hardware / 1.0 A firmware default (D4). |
| 2026-08-31 | Cell confirmed as Molicel INR-18650-M35A: max charge 1.7 A, so the spec's 2.0 A target was unsafe (D4). Found that BQ25895 `ICHG` defaults to 2048 mA and is watchdog-reset while `IINLIM` is not — a removable ESP32 leaves the cell charging over its limit. Fixed in hardware with a 680 Ohm ILIM resistor, relying on `EN_ILIM` defaulting to Enable (D5). Samsung 35E evaluated, no change warranted. |
