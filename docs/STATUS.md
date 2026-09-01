# Status

**Current position:** Stage A complete. Every fitted part has an exact MPN; no generic
placeholders remain, satisfying spec §39's first BOM condition.

**Next action:** Stage B — build the three custom KiCad symbols (TPS630701, MAX17048,
BQ29700) and the VQFN-HR-15 footprint, then draw the seven schematic sheets.

**Do not order. Nothing here has passed ERC, DRC, or a gerber inspection.**

---

## Stage progress

| Stage | What it covers | State |
|---|---|---|
| A — Validate | datasheets, part availability, DevKit mechanical truth, GPIO map | ✅ **complete** — every fitted part has an MPN |
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

All architectural questions are closed. Resolved values live in
[POWER_DESIGN.md](POWER_DESIGN.md); part numbers in
[PART_SELECTION.md](PART_SELECTION.md). What remains is confirmation work, not design work
— carried from [DECISIONS.md D11](DECISIONS.md#d11--still-open):

| Item | Nature |
|---|---|
| ⬜ CH224K VDD / VBUS series resistor values | read off the manual's reference figures |
| ⬜ CSD16406Q3 RDS(on) at VGS ≈ 3.0 V | confirmation — even a pessimistic 10 mΩ still trips at ≈5 A |
| ⬜ CC1/CC2 ESD array final MPN | availability check |
| ⬜ L1 saturation ≥ 4 A | datasheet check |
| ⬜ NTC mounting | layout, per [D10](DECISIONS.md#d10--ntc-mounting-is-a-documented-compromise) |
| ⬜ SW2 height variant, status LED colour | trivial, at layout / BOM freeze |
| ⬜ M35A charging temperature window | confirmation; assumed 0–45 °C is the conservative choice |

## Quality gate before order

Spec §39's checklist is the release gate. **0 of 22 items passed.** It is reproduced
there and will be tracked here once Stage B begins.

## Session log

| Date | What happened |
|---|---|
| 2026-08-31 | Project created. Board identity corrected to YD-ESP32-S3 V1.3 (D1). Architecture trimmed: CH224K replaces STUSB4500 (D2), PCA9633 dropped (D3). KiCad 10.0.6 installed. Four critical actives validated with exact MPNs; USB-C, sockets and holder selected. Board size estimated ~90 × 60 mm. |
| 2026-08-31 | Vendor drawing read: YD board is 27.94 × 57.15 mm, rows 25.40 mm, antenna overhangs pin-1 edge by 6.24 mm; all 44 pins confirmed identical to official DevKitC-1. GPIO map proposed on J1 only (G3 closed). Cell marking found to match neither P30B nor M35A — charge policy split to 2.0 A hardware / 1.0 A firmware default (D4). |
| 2026-08-31 | Cell confirmed as Molicel INR-18650-M35A: max charge 1.7 A, so the spec's 2.0 A target was unsafe (D4). Found that BQ25895 `ICHG` defaults to 2048 mA and is watchdog-reset while `IINLIM` is not — a removable ESP32 leaves the cell charging over its limit. Fixed in hardware with a 680 Ohm ILIM resistor, relying on `EN_ILIM` defaulting to Enable (D5). Samsung 35E evaluated, no change warranted. |
| 2026-08-31 | Worked D6's open list. Resolved: CH224K VDD topology and the 6.8k CFG1 resistor for 9 V (and that an open CFG1 requests 20 V — survivable at 22 V abs max, caught by the existing §37 PD test); BQ25895 TS network from TI's own 0–45 °C worked example; switched to fixed-5 V TPS630701 to delete the feedback divider as a failure mode (D6); selected BQ29700DSE protection (D7). Found that AO8810 and FS8205A, the default protection FETs, would trip at ~2 A against our 3.55 A transient. |
| 2026-08-31 | Completed part selection — every fitted part now has an MPN. Protection FETs resolved to 2x TI CSD16406Q3 after finding the common-drain dual category tops out around 23 mOhm; TI's own layout example uses discrete singles and hits 7 A on the same threshold. TVS sized at 12 V not 24 V, because a 24 V part clamps at 38.9 V and would not protect a 22 V-max charger (D8). SW1 drives the converter EN pin, deleting the load-switch IC (D9). NTC mounting recorded as an honest compromise against the turnkey requirement (D10). |
