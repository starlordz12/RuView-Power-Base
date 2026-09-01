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

## D6 — TPS630701 (fixed 5 V) replaces the TPS63070 (adjustable)

**Spec said:** §5.1 — "Texas Instruments TPS63070 buck-boost converter. Configure for
output: 5.0 V."

**Decision:** use **`TPS630701RNMR`**, the fixed 5.0 V member of the same family. Same
VQFN-HR-15 (RNM) 2.5 × 3 mm package, same reference layout, same passives, active and
stocked at Digi-Key.

**Reasoning:** the board only ever needs 5.0 V, so the adjustable part's feedback divider
is pure liability. Removing it removes two resistors, a ±1% accuracy stack-up, and — the
reason that actually matters — **a failure mode in which a wrong, damaged, or
mis-assembled divider resistor puts an out-of-spec voltage directly onto the ESP32's 5 V
pin.** On fixed versions the FB pin ties straight to VOUT and no such failure exists.

This is the same principle as [D5](#d5--the-charge-current-ceiling-is-enforced-in-hardware-by-the-ilim-resistor):
prefer the variant whose failure modes are structurally absent over the one that needs a
component to be correct.

Values in [POWER_DESIGN.md §3](POWER_DESIGN.md#3-5-v-rail--tps630701-changed-from-tps63070).

---

## D7 — Battery protection: BQ29700 with low-RDS(on) FETs

**Spec said:** §15 — "If the BQ25895 and selected cell protection do not provide all
required battery protections, add a dedicated 1S protection stage."

**Decision: the protection stage is required.** The installed M35A is a **bare cell with
no protection PCB**, and the holder accepts whatever 18650 a user fits. The BQ25895
provides charge-side protection but is not an independent second layer — if the charger
itself faults, nothing else stands between the cell and the system.

**Selected:** TI **`BQ29700DSE`** (WSON-6, 1.5 × 1.5 mm) driving two low-side N-FETs in
the cell's negative path. OVP 4.275 V, UVP 2.800 V, OCD 100 mV, SCC 500 mV.

OVP at 4.275 V sits deliberately above the BQ25895's 4.208 V charge target, so the
protector is a genuine backstop rather than a part that fights the charger.

### The finding worth carrying forward

**OCD is sensed as a voltage across the FETs**, so the overcurrent trip point is set
entirely by their on-resistance: `I_trip = 100 mV / (2 × RDS(on))`.

Working the arithmetic for this board's ~3.55 A peak cell current rules out **both** parts
that battery-protection reference designs default to:

| Part | RDS(on) | Trip current | |
|---|---|---|---|
| AO8810 | 23 mΩ | ≈ 2.2 A | ❌ below our own transient |
| FS8205A | 25 mΩ | ≈ 2.0 A | ❌ worse |

Either would nuisance-trip on WiFi transients and look like random brownouts.

**Requirement: ≤ 8.3 mΩ per FET — measured at VGS = 3.4 V**, which is the BQ29700's actual
`VOH` gate drive, *not* the 4.5 V or 10 V at which FET datasheets headline their RDS(on).
Reading the headline figure instead of the curve at the real gate voltage is exactly how
this circuit gets built wrong.

**Resolved:** TI's own layout example (SLUSBU9 Figure 32) pairs the BQ29700 with **two
discrete `CSD16406Q3` singles**, not a common-drain dual — which is why searching the dual
category kept coming up short. At **7.4 mΩ max (VGS 4.5 V)** two in series give an OCD trip
of **≈ 6.8 A**, and TI's own design table claims 7 A with this exact combination. Comfortably
above our 3.55 A transient, comfortably below the cell's 10 A rating.

⬜ Still to confirm at schematic: RDS(on) read off the curve at **VGS ≈ 3.0 V** (the gate
drive at a low cell), not the headline 4.5 V figure.

---

## D8 — The VBUS TVS is 12 V, not the 24 V a PD board suggests

**The obvious choice is wrong.** A USB-C PD board can see 20 V on VBUS, which points
straight at a 24 V-standoff TVS such as `SMAJ24A`. That part **would protect nothing on
this board**: its clamping voltage is **38.9 V**, and the BQ25895's absolute maximum is
**22 V**. The charger dies long before the TVS does anything useful.

**Decision:** size the TVS for the voltage this board actually operates at. It requests
**9 V and never more**, so `SMAJ12A` — 12 V standoff, 13.3 V breakdown, **19.9 V clamp** —
stands off 9 V ±5% comfortably while clamping *below* the 22 V the charger must survive.

**What this deliberately does not cover:** the open-`R_CFG1` fault that would request 20 V
(see [POWER_DESIGN.md §1](POWER_DESIGN.md#voltage-selection--resolved--and-safety-relevant)).
Covering that would require a standoff above 20 V, which forces the clamp above 22 V and
abandons protection of the part we are protecting. The two requirements are mutually
exclusive, so the fault is handled where it belongs: **an open CFG1 is a build defect, and
spec §37's production test already requires verified 9 V negotiation on every board.**

Choosing the higher-voltage part here would have felt safer and protected less.

---

## D9 — SW1 switches the converter's EN pin; no load-switch IC

**Spec said:** §13 — "OFF disconnects the regulated 5 V rail from the ESP32 ... Avoid
placing large battery current directly through a tiny slide switch if an electronic load
switch is more appropriate. Preferred implementation: switch controls EN of the 5 V
buck-boost or a load-switch IC."

**Decision:** a plain SPDT slide switch (`EG1218`) drives the **TPS630701 `EN` pin**
directly. No load-switch IC.

**Why this is sufficient rather than a shortcut:**

- The switch carries **only EN-pin current — microamps.** The spec's concern about routing
  battery current through a small slide switch does not arise.
- The TPS63070 family **disconnects the load from the input in shutdown** (SLVSC58B §1),
  so EN-low is a true disconnect, not merely a converter stop with a leakage path.
- It is the first of the two implementations the spec itself names as preferred.

Removes an IC, its passives, and its footprint. The `EG1218` is rated 200 mA / 30 V, which
is orders of magnitude beyond what it will ever carry here.

---

## D10 — NTC mounting is a documented compromise

**Spec said:** §4.3 — "add provision for a 10 kΩ NTC thermistor **touching or adjacent to**
the 18650 cell ... design the NTC so it measures the cell body rather than just PCB ambient
temperature."

**The conflict:** §31 requires **full turnkey assembly with no customer soldering**. A
leaded thermistor bent up against a cell body cannot be placed reliably by an automated
line, and asking PCBWay to hand-form and position one against a removable cell is not a
process that repeats across a build.

**Decision:** 0603 SMD NTC on the top layer, positioned **directly beneath the cell body**
between the holder's contacts, with:

- a local copper island coupling it to the cell side of the board,
- deliberate thermal isolation from the power side (the charger and both converters sit at
  the opposite end of the board by §33 zoning),
- no ground-pour connection that would tie it to the board's thermal mass.

**Stated honestly: this measures cell-adjacent PCB temperature, not the cell body.** It
will track cell temperature with a lag and an offset, and it is a weaker measurement than
the spec asks for. It is chosen because the alternative conflicts with a hard requirement,
not because it is equivalent.

**Consequence for the test plan:** the NTC's actual correlation to cell temperature must be
characterised during the §16 thermal tests — measuring both the NTC reading and the cell
surface with a separate probe during a full charge — rather than assumed. If the offset is
large enough to matter, the TS divider gets re-tuned to compensate.

---

## D11 — Still open

- ⬜ **CH224K VDD and VBUS series resistor values.** Topology confirmed (internal
  high-voltage LDO, series R from VBUS, 1 µF decoupling; no external LDO). Exact values
  must come from the manual's reference schematic figures §6.1–6.3.
- ⬜ **CC1/CC2 ESD array final MPN.** Semtech `µClamp2411ZA` selected on the strength of
  Semtech's own USB Type-C ESD application note; availability and an LCSC-sourceable
  equivalent still to confirm.
- ⬜ **L1 saturation current** — must be ≥ 4 A, since the charger inductor carries system
  current as well as charge current.
- ⬜ **SW2 tactile height variant** — depends on the enclosure, which is not yet designed.
- ⬜ **Status LED colour suffix** — trivial, at BOM freeze.
- ⬜ **M35A charging temperature window** versus the assumed 0–45 °C. Confirmation only;
  the assumed window is the conservative one.
