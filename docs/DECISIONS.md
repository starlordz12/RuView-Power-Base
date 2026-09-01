# Design decisions

Where this build departs from `spec/RuView_Power_Base_PCBWay_Claude_Code_Spec_V1.1.md`,
and why. The V1.1 spec remains the requirements baseline; these are the reasoned
exceptions to it.

---

## D1 — Host board is the YD-ESP32-S3 V1.3, not an Espressif DevKitC-1

**Spec said:** §9 — "Use Espressif's official board dimensions/DXF as the mechanical
source of truth. Do not guess header spacing from photographs."

**Reality:** The user's five boards are **YD-ESP32-S3 Core Board N8R8, rev V1.3 (2022)**
from VCC-GND Studio, confirmed by the board silkscreen and independently recorded in the
owner's [esp32-n8r8-project](https://github.com/starlordz12/esp32-n8r8-project) guide
("confirmed the board from physical inspection and photos"). This is a DevKitC-1
*compatible* clone, not the Espressif board.

**Decision:** Design to VCC-GND's published mechanical drawing and schematic
(`vcc-gnd/YD-ESP32-S3`, files `ESP32-S3-Metric.pdf` and `YD-ESP32-S3-SCH-V1.4.pdf`).

**Residual risk — open.** The vendor README states that the authentic board is **V1.4**
and that counterfeit boards copy **V1.2 from early 2022**. The user's board is **V1.3**,
an intermediate revision for which no schematic is published. The mechanical drawing in
the vendor package is dated March 2022, which is closer to the V1.3 era than the V1.4
schematic is. **Physical measurement of the actual board is required before layout is
committed.** Tracked in [STATUS.md](STATUS.md) as gate item G1.

**Why it matters:** Socket row spacing and header pin order are unrecoverable errors. A
carrier built to the wrong footprint is scrap, and at turnkey PCBA quantity 5 that is the
entire order.

---

## D2 — CH224K PD trigger replaces the STUSB4500

**Spec said:** §3.2 — "Preferred: STMicroelectronics STUSB4500 ... Store PDO
configuration in STUSB4500 NVM so the board can negotiate power without the ESP32."

**Problem:** The STUSB4500 ships with a default 5 V PDO profile. Requesting 9 V requires
writing the PDO configuration into its NVM. **PCBWay turnkey assembly does not program
device NVM.** A board built exactly to spec would therefore arrive negotiating 5 V, not
the 9 V the spec targets, until something programs it in-circuit over I2C. That directly
contradicts §37's requirement that boards arrive functional and §31's "customer
post-assembly soldering required: none" intent.

**Decision:** Use the **WCH CH224K**. Its output voltage is set by a resistor on the CFG
pins — no programming step, no NVM, no MCU dependency, correct behaviour on first power
application straight from the assembler.

**Secondary benefits:**

- Lower cost, and heavily stocked through LCSC, which is PCBWay's primary sourcing channel.
- Ships in **SSOP-10** rather than the STUSB4500's QFN-24 — easier assembly, easier
  inspection, no X-ray needed for that part.
- KiCad ships a stock `CH224K` symbol and `SSOP-10-1EP` footprint, removing a custom-part
  risk from the critical path.

**What is given up:** No I2C telemetry of the PD contract, so the firmware cannot read
back the negotiated voltage from the PD controller. Mitigated by measuring VBUS through
the BQ25895's own ADC, which the spec already requires for `pd_voltage` in §21.

---

## D3 — SOC LEDs driven from ESP32 GPIOs; PCA9633 dropped

**Spec said:** §8.2 — "Preferred: PCA9633 ... uses only I2C instead of consuming four
ESP32 GPIOs."

**Reasoning:** The stated benefit does not apply to this host. The PCA9633 still requires
the ESP32 to be running to display anything, so it saves no functional capability — only
pins. The YD-ESP32-S3 N8R8 exposes far more free GPIO than RuView's CSI sensing workload
consumes, and every LED behaviour the spec asks for (brightness control in §8.5,
charge-pulse animation in §21) is available directly from the ESP32-S3's LEDC PWM
peripheral on any GPIO.

**Decision:** Drive four SOC LEDs and one status LED from five GPIOs with series
resistors. Removes an IC, an I2C address, a custom KiCad symbol, and BOM cost, with no
loss of specified behaviour.

**Constraint this creates:** Five GPIOs must be chosen that are not strapping pins
(GPIO0/3/45/46), not the PSRAM bus (GPIO35/36/37), not native USB (GPIO19/20), not UART0
(GPIO43/44), and not the onboard RGB LED (GPIO48). Pin assignment is blocked on the YD
V1.3 header map — gate item G1.

---

## D4 — Cell is a Molicel INR-18650-M35A; the spec's 2.0 A target is unsafe for it

**Spec said:** §30.1 — 2.0 A nominal charging target, on the assumption the cell is a
Molicel INR-18650-P30B (9 A maximum charge).

**Confirmed cell: Molicel INR-18650-M35A, 3.6 V / 3.35 Ah.** Not a P30B.

| | M35A (installed) | P30B (spec assumed) | Samsung 35E (considered) |
|---|---|---|---|
| Capacity, minimum | 3350 mAh | 3000 mAh | 3350 mAh |
| Standard charge | 1.7 A | 3 A | 1.7 A |
| **Maximum charge** | **1.7 A** | 9 A | **2.0 A** |
| Continuous discharge | 10 A | 30 A | 8 A |

**The spec's 2.0 A target exceeds this cell's 1.7 A maximum by 18%.** Building §30.1 as
written would have overcharged the installed cell on every single cycle.

**Decision:**

- **Firmware default charge current: 1.0 A** (0.3 C) — roughly a 3.5 h charge.
- **Firmware maximum: 1.5 A** (0.45 C), 12% below the cell ceiling — roughly 2.5 h.
- **1.7 A is a hard ceiling that is never exceeded**, sized to the most restrictive cell
  in the table above rather than to the one currently installed.
- **PCB copper and thermal design still target 2.0 A**, per spec §4.2 — the headroom is
  free and the spec asks for it.

**Why the ceiling tracks the most restrictive cell, not the installed one:** the cell is
**user-removable**. The board cannot know what is in it. A Samsung 35E may be fitted later,
or something lower-rated — designing protection around whichever cell happened to ship
first is how a safety margin quietly disappears. Sizing for 1.7 A keeps the board safe for
the M35A, the 35E, and any quality 3500 mAh 18650 in this class.

The Samsung 35E was evaluated as an alternative and offers no reason to switch: identical
standard charge current, 0.3 A more maximum-charge headroom that this design deliberately
will not use, and a *lower* continuous discharge rating that is irrelevant at this node's
sub-1 A draw.

Note that "10 A max" printed on the M35A wrap is a **discharge** rating. It says nothing
about charge current, and the two must never be conflated.

**Consequence:** safe charge current becomes a **hardware** requirement, not merely a
firmware constant — see D5.

---

## D5 — The charge-current ceiling is enforced in hardware by the ILIM resistor

**Source:** TI BQ25895 datasheet SLUSC88C (March 2015, revised October 2022), REG00
Table 8-8, REG04, and §9.3.7 device operating modes.

### The failure this prevents

Three register facts combine badly:

1. **`ICHG` (REG04) powers up at 2048 mA** — already above the M35A's 1.7 A limit — and is
   **reset by the watchdog**.
2. **On power-on reset the device starts in default mode with the watchdog already
   expired, and keeps charging the battery** on a 12-hour safety timer. It does not wait
   for a host.
3. When the watchdog expires, all registers return to defaults **except `IINLIM`,
   `VINDPM`, `VINDPM_OS`, `BATFET_RST_EN`, `BATFET_DLY` and `BATFET_DIS`.**

Fact 3 is the trap. `IINLIM` **survives** watchdog expiry while `ICHG` **does not**. So:

> Firmware raises the input current limit for fast charging, then the ESP32 crashes, is
> held in reset, or is simply pulled out of its socket. The watchdog expires. `ICHG` snaps
> back to 2048 mA while the raised `IINLIM` persists. The cell is charged at 2048 mA
> against a 1700 mA limit, indefinitely, with no host present to correct it.

This is not a corner case for this product. **The ESP32 is a removable module by design.**
A board sitting on USB-C with no module installed is a supported configuration, and in that
configuration nothing ever writes a register.

### The fix

Size the **ILIM pin resistor** so the input current limit alone cannot push charge current
past the ceiling with no system load.

- `IINMAX = KILIM / RILIM`, with `KILIM = 390` maximum (datasheet §7.5, p4/p26).
- The actual input current limit is the **lower** of the ILIM pin setting and `IINLIM`.
- **`EN_ILIM` (REG00 bit 6) defaults to `1` = Enable, and is reset by the watchdog.**

That last point is what makes this work: firmware may clear `EN_ILIM` to lift the clamp
during normal supervised operation, but **any watchdog expiry restores it**. The failure
mode reverts to the hardware-safe state instead of away from it.

### Sizing

Worst case is the constant-current phase at the lowest cell voltage, taken as 3.0 V, with
zero system load — which is exactly the host-less case the clamp exists for.

| | |
|---|---|
| Target charge ceiling, no host | 1.5 A |
| Battery power | 1.5 A × 3.0 V = 4.5 W |
| Input power at ~90% efficiency | 5.0 W |
| Input current at 9 V | 0.556 A |
| `RILIM` = 390 / 0.556 | 701 Ω → **use 680 Ω** (E24) |
| Resulting `IINMAX` | 390 / 680 = **0.574 A** |
| Resulting charge current at 3.0 V | **≈ 1.55 A** ✅ under 1.7 A |
| Resulting charge current at 3.7 V | ≈ 1.26 A |

0.574 A clears the datasheet's **500 mA minimum settable ILIM current**, so the pin
remains in its valid operating range.

**To be confirmed during schematic work:** the 90% efficiency assumption against the
datasheet's efficiency curves at 9 V input, and the exact `KILIM` tolerance band — 390 is
quoted as a maximum, so the achieved limit will sit at or below the figures above. Erring
low is the safe direction here, and reduces charge current rather than raising it.

---

## D6 — Still open

Items that will become decisions during Stage B.

- **CH224K VDD supply.** The part's VDD sits around 3.3 V. Whether it is fed from VBUS
  through a series resistor relying on an internal regulator, or needs a discrete LDO,
  must be read off the WCH datasheet rather than inferred from the many trigger-board
  schematics floating around.
- **Board-level 1S protection.** Spec §15 requires a dedicated protection stage unless the
  BQ25895 plus the cell's own protection covers everything. The installed M35A is a bare
  cell with no PCB, and the holder accepts any 18650 the user fits — so the working
  assumption is that a discrete protection IC **is** required. This is the largest
  remaining open question in the power path.
- **NTC network values.** The BQ25895 `TS` thresholds must be sized so the charge window
  matches the M35A's permitted charging temperature range, not the charger's defaults.
- **TPS63070 feedback divider and inductor.** Both follow from TI's reference layout once
  the 5 V rail's transient budget is fixed.

*(The BQ25895 watchdog and default-register question that sat here has been resolved — see
D5.)*
