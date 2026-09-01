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

## D4 — Charge current defaults to 2.0 A, firmware-selectable to 1.0 A

**Spec said:** §30.1 — 2.0 A nominal, 1.0 A selectable, 3.0 A only after thermal
validation. Adopted as written.

**Note carried forward:** §30.1 also requires the exact Molicel model be confirmed
against the printed cell marking before release, not from the informal description. The
P30B figures quoted in the spec (3 A standard charge, 9 A max) are *not* to be treated as
confirmed. Gate item G2.

---

## D5 — Not decided yet

Open items that will become decisions once Stage A completes:

- **CH224K VDD supply.** The part's VDD is specified around 3.3 V. Whether it is fed from
  VBUS through a series resistor relying on an internal regulator, or needs a discrete
  LDO, must be read off the datasheet rather than inferred from trigger-board schematics.
- **BQ25895 I2C watchdog.** The charger resets its registers to defaults if the host does
  not service its watchdog. The firmware must either kick it or disable it, and the
  *default* register state must be independently verified as safe for this cell, because
  that is the state the board sits in whenever the ESP32 is absent, held in reset, or
  crashed.
- **Board-level 1S protection.** §15 requires a dedicated protection stage unless the
  BQ25895 plus cell protection covers everything. With a removable, possibly unprotected
  user cell, the working assumption is that a discrete protection IC **is** required.
