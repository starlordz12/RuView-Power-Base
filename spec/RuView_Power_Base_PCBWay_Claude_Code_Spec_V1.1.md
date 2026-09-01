# RuView ESP32-S3 N8R8 18650 USB-C PD Power Base
## Claude Code / KiCad Implementation Specification
**Target manufacturer:** PCBWay turnkey PCBA  
**Target host board:** Espressif ESP32-S3-DevKitC-1 N8R8, 44-pin (2 × 22 headers)  
**Project role:** Battery/power carrier board for RuView Wi-Fi sensing nodes  
**Revision target:** V1.0 prototype  
**EDA:** KiCad 8 or newer  
**PCB:** 2-layer FR-4 unless layout/thermal analysis justifies 4-layer

---

# 1. Goal

Design a removable battery/power base that the ESP32-S3-DevKitC-1 N8R8 plugs into through two 22-pin female headers.

The base must:

- Hold one replaceable 18650 Li-ion cell.
- Support true USB-C to USB-C input.
- Prefer USB-C Power Delivery when available.
- Continue powering the ESP32 while the battery is charging.
- Automatically supplement USB input with battery current if system demand momentarily exceeds the available input budget.
- Present a regulated 5.0 V rail to the ESP32 DevKitC 5V pin.
- Monitor real battery state of charge with a dedicated fuel-gauge IC.
- Show battery percentage using LEDs.
- Keep the ESP32 GPIO headers accessible.
- Minimize RF interference near the ESP32 PCB antenna.
- Be manufacturable and assemblable by PCBWay using normal, conservative design rules.
- Use parts that are active/current-production wherever possible.
- Be safe for unattended indoor sensor-node operation.

This is **not** a USB data board. The USB-C connector on the power base is primarily for power input and charging.

---

# 2. Preferred Power Architecture

Use the following architecture unless component availability or a concrete electrical issue requires substitution.

```text
USB-C receptacle
        |
        | CC1 / CC2
        v
STUSB4500 USB-C PD sink controller
        |
        | Negotiate preferred 9 V PDO
        | Fall back to 5 V USB-C when PD is unavailable
        v
Input protection / TVS / filtering
        |
        v
BQ25895 1-cell switch-mode charger + NVDC power-path manager
        |
        +----------------------+
        |                      |
        v                      v
  18650 Li-ion            VSYS power-path rail
                               |
                               v
                     TPS63070 buck-boost
                               |
                               | regulated 5.0 V
                               v
                    ESP32-S3 DevKitC-1 5V
```

### Why this architecture

The design should not use a TP4056-style linear charger.

The BQ25895 provides:

- switch-mode charging,
- single-cell Li-ion support,
- power-path management,
- instant-on behavior,
- input-current optimization,
- battery supplement mode,
- thermal regulation,
- I2C control/telemetry.

The STUSB4500 provides true USB-C Power Delivery sink negotiation without requiring the ESP32 to be running.

The TPS63070 creates a stable 5.0 V system rail from the BQ25895 system/battery rail across the usable 1-cell battery voltage range.

---

# 3. USB-C Power Delivery Requirements

## 3.1 Connector

Use a robust USB-C receptacle from a major manufacturer such as:

- GCT
- Amphenol
- Molex
- TE Connectivity
- Würth Elektronik

Prefer a connector with:

- through-hole shell stakes,
- SMT signal pins,
- readily available KiCad/STEP model,
- high mechanical retention.

USB 2.0 D+ and D- are not required for the RuView power base unless needed by the chosen charger implementation.

## 3.2 PD Controller

**Preferred:** STMicroelectronics STUSB4500.

Requirements:

- Configure as sink-only.
- Dead-battery operation enabled.
- Preferred PDO:
  - 9 V
  - request enough current for the charger/system budget, preferably 2 A or greater if source supports it.
- Secondary PDO:
  - 5 V / 3 A.
- Do not request >12 V because the selected BQ25895 input operating range is 3.9-14 V.
- Default safe target should be **9 V** because it reduces cable current while remaining comfortably inside the charger input range.

Store PDO configuration in STUSB4500 NVM so the board can negotiate power without the ESP32.

## 3.3 Non-PD fallback

If attached to a normal USB-C source with no PD contract:

- board must operate from 5 V VBUS,
- USB-C CC implementation must be standards-compliant,
- board must not depend on USB-A-to-C behavior.

## 3.4 Input protection

Add:

- USB-C VBUS TVS diode,
- ESD protection on CC1/CC2,
- input bulk capacitance per STUSB4500 and BQ25895 reference guidance,
- input fuse or resettable protection if justified,
- reverse/backfeed prevention handled by the PD/power-path architecture.

---

# 4. Charger / Power-Path Stage

## 4.1 Preferred IC

**Texas Instruments BQ25895**

Use the latest datasheet/reference design.

Important capabilities:

- 1-cell Li-ion/Li-polymer charging,
- up to 5 A charger capability,
- 3.9-14 V operating input range,
- NVDC power-path management,
- battery supplement mode,
- instant-on support,
- thermal regulation/shutdown,
- I2C configuration and ADC telemetry.

## 4.2 Charge-current policy

Do **not** simply configure the board for the charger's maximum current.

V1 shall default to a conservative charge current suitable for a typical quality 18650.

Recommended firmware/default configuration:

- **1.0 A nominal charge current** for universal prototype use.
- Provide firmware/config option for **1.5 A or 2.0 A only when the installed cell's manufacturer explicitly permits it**.
- Never assume all 18650 cells can safely accept 2-5 A charging.

The PCB copper and thermal design should support at least 2 A charging even if firmware defaults lower.

## 4.3 Battery temperature

Strongly preferred:

- add provision for a 10 kΩ NTC thermistor touching or adjacent to the 18650 cell,
- route it to the charger TS input according to TI's reference design.

If a removable cell holder is used, design the NTC so it measures the cell body rather than just PCB ambient temperature.

## 4.4 Power-path behavior

The board must:

1. Run the ESP32 directly from incoming USB power when available.
2. Charge the cell from remaining input power.
3. Allow battery supplement current when transient system demand exceeds the available input budget.
4. Continue running if the battery is missing when USB input is sufficient.
5. Continue running from battery immediately after USB removal.

No reboot should occur during normal USB insertion/removal if the load remains inside design limits.

---

# 5. 5 V System Rail

## 5.1 Preferred converter

**Texas Instruments TPS63070** buck-boost converter.

Configure for:

- output: **5.0 V**
- continuous design target: at least 1 A for the ESP32 node
- transient capability: design for up to approximately 2 A where practical

The TPS63070 supports a wide input range and can provide 5 V from a 1-cell system rail in both buck and boost operating regions.

## 5.2 Output

Route regulated 5 V to:

- ESP32-S3-DevKitC-1 **5V** pin,
- 5 V test pad,
- optional accessory header if included.

Do not directly connect the raw 18650 voltage to the ESP32 5V pin.

## 5.3 Decoupling

Follow the TPS63070 reference layout closely.

Place:

- input capacitors,
- output capacitors,
- inductor,
- feedback components

as close to the converter as possible.

Keep the switching loop compact.

---

# 6. Battery and Cell Holder

## 6.1 Cell

1 × removable 18650 Li-ion cell.

Design for common flat-top or button-top cells only if the chosen holder supports both reliably.

Recommended prototype cells should be:

- authentic,
- name-brand,
- protected if the mechanical holder and length permit,
- cell chemistry compatible with 4.2 V charging.

## 6.2 Holder

Use a quality PCB-mount holder from a known manufacturer where possible.

Prefer:

- Keystone Electronics,
- MPD,
- Bulgin,
- or equivalent industrial component.

Avoid no-name spring holders in the production BOM unless necessary.

## 6.3 Polarity

Silkscreen must very clearly show:

- `BAT +`
- `BAT -`

Add electrical reverse-insertion protection if practical without materially reducing efficiency.

Never rely only on silkscreen for battery safety.

---

# 7. Fuel Gauge

## 7.1 Preferred IC

**Analog Devices MAX17048**

Use the 1-cell configuration.

Reasons:

- dedicated state-of-charge estimation,
- ModelGauge algorithm,
- no current-sense resistor required,
- low quiescent current,
- I2C interface,
- reports SOC and cell voltage,
- recommended for new designs.

Connect to the ESP32 using I2C.

## 7.2 I2C bus

Create a shared system I2C bus for:

- MAX17048
- BQ25895
- LED driver
- optional STUSB4500 access/debug if desired

Include correctly sized pull-ups to 3.3 V.

Select ESP32 GPIOs that:

- are available on the DevKitC header,
- are not boot strapping pins,
- do not conflict with RuView requirements.

Claude Code must verify the RuView firmware and ESP32-S3 DevKitC pin map before final pin assignment.

---

# 8. Battery Percentage LEDs

## 8.1 Display concept

Provide a **4-segment battery gauge** plus a dedicated charge/status LED.

Main gauge:

- LED1 = 0-25 %
- LED1-2 = 26-50 %
- LED1-3 = 51-75 %
- LED1-4 = 76-100 %

The SOC value must come from the MAX17048, not from simple battery-voltage thresholds.

## 8.2 LED driver

Preferred:

**PCA9633** or another small I2C constant-current/PWM-capable 4-channel LED driver that is readily sourced by PCBWay.

Reasons:

- uses only I2C instead of consuming four ESP32 GPIOs,
- allows brightness control,
- supports animations during charging,
- reduces RuView pin conflicts.

If PCA9633 sourcing is poor, use a similar active-production I2C LED driver.

## 8.3 Dedicated status LED

Add one separate status LED tied to charger status or controlled by the ESP32.

Suggested behavior:

- charging: amber pulse or steady amber,
- fully charged: green or gauge all-on,
- charger fault: red blink,
- USB power present: optional indication.

If using a single-color status LED, document blink codes.

## 8.4 Gauge behavior

To reduce idle power:

- gauge LEDs should normally be off during battery-only operation,
- add a small momentary **BATTERY** button,
- pressing it displays the 4-bar SOC for approximately 5 seconds,
- during USB charging the gauge may remain enabled at low brightness.

Suggested charging animation:

```text
25%  [● ○ ○ ○]
50%  [● ● ○ ○]
75%  [● ● ● ○]
100% [● ● ● ●]

While charging:
solid completed segments + slow pulse on the next segment.
```

## 8.5 LED current

Use low-current LEDs.

Design typical LED current around:

- 1-2 mA per indicator,

unless the chosen driver requires another value.

Brightness should be firmware adjustable.

---

# 9. ESP32-S3 DevKitC-1 Mechanical Interface

Host board:

**Espressif ESP32-S3-DevKitC-1 N8R8**

The carrier must use:

- 2 × 22-position 2.54 mm female headers,
- exact Espressif DevKitC-1 spacing,
- enough header height to prevent underside component collision,
- removable ESP32 module.

Use Espressif's official board dimensions/DXF as the mechanical source of truth.

Do not guess header spacing from photographs.

---

# 10. GPIO Passthrough

Goal: retain GPIO accessibility.

Preferred mechanical implementation:

- DevKit plugs into two female headers on the battery base.
- Place parallel breakout pads/headers outside the DevKit footprint where practical.

At minimum expose:

- GND
- 5V
- 3V3
- system I2C SDA
- system I2C SCL
- UART TX/RX if available
- several spare GPIOs

If full pin duplication materially enlarges the board, prioritize the pins actually needed by RuView and debugging.

---

# 11. RF / Wi-Fi Layout Requirements

This is a RuView Wi-Fi sensing node.

RF performance is important.

The PCB antenna end of the ESP32-S3 DevKitC must extend beyond or sit over a defined RF keepout.

Under and immediately around the DevKit antenna:

- no battery,
- no ground pour on the carrier where avoidable,
- no switching converter,
- no inductor,
- no USB-C connector,
- no high-current traces,
- no LEDs,
- no large metal hardware.

Place:

- 18650 holder,
- PD controller,
- charger,
- buck-boost converter

toward the opposite end of the carrier.

Follow Espressif's antenna keepout guidance.

---

# 12. Suggested Physical Layout

Concept:

```text
         ESP32 PCB ANTENNA
               ↑
     +----------------------+
     |      ANTENNA         |
     |                      |
     | ESP32-S3 DevKitC-1   |
     |      N8R8            |
     |                      |
     +----------------------+
        ||              ||
       22p              22p
       headers / carrier

+----------------------------------+
|          RF KEEPOUT              |
|                                  |
|  Fuel gauge       LED BAR        |
|                                  |
|  USB-C PD    Charger    5V DC/DC |
|                                  |
|  [======== 18650 CELL ========]  |
|                                  |
| USB-C   POWER SW   BATTERY BTN    |
+----------------------------------+
```

The exact geometry must be adjusted after importing the official DevKitC mechanical drawing.

---

# 13. User Controls

Include:

## SW1 — SYSTEM POWER

A physical power switch.

Preferred behavior:

- OFF disconnects the regulated 5 V rail from the ESP32.
- Charging may continue while system is OFF.
- Fuel gauge may remain connected to the cell.
- Avoid placing large battery current directly through a tiny slide switch if an electronic load switch is more appropriate.

Preferred implementation:

- switch controls EN of the 5 V buck-boost or a load-switch IC.

## SW2 — BATTERY GAUGE

Momentary pushbutton.

Press:

- wakes/shows percentage LEDs for ~5 seconds.

Long press behavior may be defined in firmware later.

---

# 14. Test Points

Provide clearly labeled pads for:

- TP_VBUS
- TP_PD_VBUS
- TP_SYS
- TP_BAT
- TP_5V
- TP_3V3
- TP_GND
- TP_SDA
- TP_SCL
- charger STAT / INT if used

Make them accessible with the ESP32 installed.

---

# 15. Protection / Safety

Include appropriate protection for:

- USB VBUS ESD/transients,
- USB CC ESD,
- overvoltage,
- undervoltage,
- charger thermal regulation,
- battery overcharge,
- battery overdischarge,
- short circuit / overcurrent,
- reverse current/backfeed.

If the BQ25895 and selected cell protection do not provide all required battery protections, add a dedicated 1S protection stage.

Do not treat a removable protected cell as the only board-level safety mechanism without explicit design review.

---

# 16. Thermal Design

The charger and buck-boost stages may dissipate meaningful heat.

Requirements:

- follow vendor exposed-pad recommendations,
- use thermal vias beneath QFN thermal pads where required,
- use substantial copper around power IC ground/thermal pads,
- keep thermally sensitive fuel-gauge circuitry away from power inductors,
- keep the 18650 away from charger hot spots,
- place the NTC to measure the cell, not the charger.

Prototype acceptance should include thermal testing during:

- 5 V charging,
- 9 V PD charging,
- battery-only operation,
- simultaneous charge + maximum expected ESP32 load.

---

# 17. PCBWay Fabrication Targets

Use conservative rules.

Preferred V1 PCB:

- 2-layer FR-4
- 1.6 mm thickness
- 1 oz copper
- lead-free HASL or ENIG
- standard green solder mask unless changed intentionally
- white silkscreen
- standard plated through holes

Design targets:

- signal width: >= 8 mil
- signal spacing: >= 8 mil
- ordinary power traces: >= 12-20 mil
- battery / 5 V high-current paths: use broad pours or much wider traces based on current/temperature calculation
- avoid blind/buried vias
- avoid via-in-pad unless absolutely required by a package
- prefer standard drill sizes
- use solid ground regions except RF keepout
- use appropriate thermal-relief settings for through-hole headers

Do not design against PCBWay's absolute minimum capabilities when unnecessary.

---

# 18. PCBWay Turnkey PCBA Output Package

Claude Code must generate a complete manufacturing folder.

PCBWay requests at minimum for assembly:

- BOM
- Gerbers
- pick-and-place / centroid file

Project output:

```text
RuView-Power-Base/
|
+-- README.md
+-- docs/
|   +-- DESIGN_SPEC.md
|   +-- BRINGUP.md
|   +-- TEST_PLAN.md
|   +-- PCBWAY_ORDER_NOTES.md
|
+-- hardware/
|   +-- kicad/
|   |   +-- RuView-Power-Base.kicad_pro
|   |   +-- RuView-Power-Base.kicad_sch
|   |   +-- RuView-Power-Base.kicad_pcb
|   |
|   +-- fabrication/
|   |   +-- gerbers/
|   |   +-- gerbers.zip
|   |   +-- drill/
|   |   +-- fabrication-drawing.pdf
|   |
|   +-- assembly/
|   |   +-- BOM.csv
|   |   +-- CPL.csv
|   |   +-- assembly-drawing-top.pdf
|   |   +-- assembly-drawing-bottom.pdf
|   |   +-- schematic.pdf
|   |
|   +-- mechanical/
|       +-- board.step
|       +-- board.dxf
|       +-- esp32-devkitc-reference/
|
+-- firmware/
    +-- battery_monitor/
        +-- README.md
        +-- source/
```

---

# 19. BOM Requirements

For every BOM line include:

- reference designator,
- quantity,
- manufacturer,
- exact manufacturer part number,
- description,
- package,
- SMT/THT classification,
- distributor part number if available,
- acceptable substitution notes,
- DNP status.

Prefer parts available from:

- Digi-Key
- Mouser
- LCSC

PCBWay sourcing compatibility is important.

Do not substitute critical power ICs without rechecking:

- electrical limits,
- pinout,
- package,
- thermal behavior,
- reference layout.

---

# 20. Critical Preferred Components

Primary choices:

| Function | Preferred component |
|---|---|
| USB-C PD sink | STUSB4500 |
| 1S charger / power path | TI BQ25895 |
| 5 V buck-boost | TI TPS63070 |
| Fuel gauge | Analog Devices MAX17048 |
| LED driver | PCA9633 or equivalent |
| Battery | 1 × 18650 Li-ion |
| Host | ESP32-S3-DevKitC-1 N8R8 |

Before final PCB routing, verify current production status and availability.

---

# 21. Firmware Behavior

A small ESP32 support module should expose:

```text
battery_percent
battery_voltage
charging
charge_complete
usb_present
pd_voltage
charger_fault
```

### LED logic

Battery button press:

- 0-25%: LED1
- 26-50%: LED1 + LED2
- 51-75%: LED1 + LED2 + LED3
- 76-100%: LED1 + LED2 + LED3 + LED4

During charging:

- completed segments solid,
- next segment slowly pulses,
- at full charge all four LEDs briefly illuminate,
- then switch to low-power indication.

Critical battery:

- below configurable SOC, e.g. 10%, LED1 flashes briefly on button press.

Do not use LED activity that materially reduces battery runtime.

---

# 22. Power Budget / Initial Targets

Design assumptions for V1:

- ESP32 5 V rail continuous target: 1.0 A minimum
- transient design target: approximately 2.0 A
- default battery charge current: 1.0 A
- optional validated charge current: 1.5-2.0 A with appropriate cell
- preferred USB-C PD input: 9 V
- fallback input: 5 V USB-C
- battery: 1S, nominal 3.6/3.7 V, full-charge 4.2 V

Do not size components based solely on average ESP32 current. Wi-Fi current spikes must be included.

---

# 23. PCB Layout Priorities

Priority order:

1. Battery and USB safety.
2. Correct power-path operation.
3. Stable 5 V rail.
4. Charger and converter thermal performance.
5. RF antenna keepout.
6. Short high-current paths.
7. Correct QFN exposed-pad implementation.
8. Mechanical alignment with DevKitC headers.
9. I2C integrity.
10. Visual cleanliness.

Power stages should be placed and routed according to manufacturer reference layouts before routing low-current signals.

---

# 24. Claude Code Implementation Instructions

Claude Code should execute this work in stages.

## Stage A — Validate

Before drawing the schematic:

1. Download/review official datasheets for:
   - STUSB4500
   - BQ25895
   - TPS63070
   - MAX17048
   - chosen LED driver
   - chosen USB-C receptacle
2. Obtain official Espressif ESP32-S3-DevKitC-1 dimensions/pinout.
3. Confirm the exact N8R8 DevKitC is 44-pin / 2 × 22.
4. Identify RuView-required GPIOs before reserving I2C or control pins.
5. Verify all critical parts are active and available.

## Stage B — Schematic

Create clearly separated schematic sheets:

```text
01_USB_C_PD
02_CHARGER_POWER_PATH
03_5V_BUCK_BOOST
04_BATTERY_FUEL_GAUGE
05_LED_STATUS
06_ESP32_HEADERS
07_TEST_DEBUG
```

Add net labels extensively.

## Stage C — ERC

Run KiCad ERC.

Resolve all genuine errors.

Document intentional exceptions.

## Stage D — PCB

1. Import official mechanical references.
2. Lock DevKitC header locations.
3. Define antenna keepout.
4. Place power circuitry.
5. Route power loops first.
6. Route I2C/control.
7. Add planes.
8. Add thermal vias.
9. Add test pads.
10. Add silkscreen labels.

## Stage E — DRC

Create a PCBWay-friendly rule set.

Run DRC.

Zero unexplained violations before release.

## Stage F — Manufacturing

Generate:

- RS-274X Gerbers
- Excellon drill files
- BOM.csv
- CPL.csv / pick-and-place
- schematic PDF
- assembly drawings
- fabrication drawing
- STEP model
- Gerber ZIP

Open and visually inspect exported Gerbers before marking release complete.

---

# 25. Prototype Bring-Up Tests

Test in this order.

## No battery

1. Inspect for shorts.
2. Connect USB-C 5 V source.
3. Verify negotiated/default VBUS.
4. Verify SYS.
5. Verify regulated 5.0 V.
6. Verify ESP32 boots.

## USB-C PD

1. Connect known PD source.
2. Confirm 9 V PDO.
3. Confirm charger accepts input.
4. Verify thermals.

## Battery only

1. Insert known-good 18650.
2. Verify polarity/protection.
3. Verify fuel gauge sees cell.
4. Verify 5.0 V.
5. Boot ESP32.
6. Test Wi-Fi load.

## Simultaneous operation

1. Run ESP32 high Wi-Fi activity.
2. Connect USB-C.
3. Verify no reset.
4. Verify battery charges.
5. Remove USB-C.
6. Verify no reset.

## Gauge

1. Compare MAX17048 SOC against cell condition.
2. Verify battery button.
3. Verify LED thresholds.
4. Verify charge animation.
5. Verify full-charge behavior.

## Thermal

Measure temperatures at:

- BQ25895
- TPS63070
- power inductor(s)
- USB-C connector
- 18650 cell

at worst expected operating conditions.

---

# 26. Acceptance Criteria

V1 is considered successful when:

- C-to-C charging works from multiple USB-C chargers.
- USB-PD 9 V negotiation works from multiple PD sources.
- 5 V fallback works.
- ESP32 runs while charging.
- USB insertion/removal does not reboot the ESP32.
- Battery can power the node independently.
- 5 V rail remains within acceptable tolerance during Wi-Fi transients.
- MAX17048 provides stable SOC readings.
- 4-segment LEDs correctly represent SOC.
- battery gauge button works.
- charging/status indication works.
- PCB and cell remain within safe thermal limits.
- Wi-Fi performance is not materially degraded by the battery base.
- PCBWay manufacturing files pass DFM review.

---

# 27. Design Review Warning

This board handles a rechargeable lithium-ion cell.

Before ordering assembled boards:

- verify charger configuration,
- verify charge current against selected 18650 datasheet,
- verify NTC behavior,
- verify battery protection,
- verify USB-PD PDO configuration,
- verify power-path behavior,
- verify all QFN footprints,
- verify exposed-pad copper/vias,
- verify polarity,
- verify the 5 V rail cannot backfeed the DevKit USB connector improperly.

Do not order production quantities from an untested V1 design.

---

# 28. Reference Sources

Use vendor documentation as the design authority.

- Espressif ESP32-S3-DevKitC-1 documentation:  
  https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/

- STMicroelectronics STUSB4500 product/datasheet:  
  https://www.st.com/en/interfaces-and-transceivers/stusb4500.html

- Texas Instruments BQ25895:  
  https://www.ti.com/product/BQ25895

- Texas Instruments TPS63070:  
  https://www.ti.com/product/TPS63070

- Analog Devices MAX17048:  
  https://www.analog.com/en/products/max17048.html

- PCBWay PCBA file requirements:  
  https://www.pcbway.com/assembly-file-requirements.html

- PCBWay assembly process guidance:  
  https://www.pcbway.com/assembly-process.html

---

# 29. Final Design Intent

The desired result is a polished, reusable **RuView Power Base** that turns a stock ESP32-S3-DevKitC-1 N8R8 into a removable, rechargeable Wi-Fi sensing node.

The design should feel like a small commercial product rather than a hobby battery shield:

- true USB-C-to-C,
- USB Power Delivery,
- proper power-path management,
- efficient regulated 5 V,
- accurate fuel gauging,
- battery percentage LEDs,
- safe 18650 charging,
- removable ESP32,
- clean GPIO access,
- RF-conscious layout,
- PCBWay-turnkey ready.


---

# 30. V1.1 USER-LOCKED MECHANICAL / QUALITY REQUIREMENTS

These requirements override earlier conceptual layout language where there is any conflict.

## 30.1 User-supplied 18650

The intended cell is the user's Molicel 3000 mAh 18650.

The closest current Molicel specification matching 3000 mAh is the INR-18650-P30B family. **Do not finalize charger settings solely from the informal cell marking supplied in conversation.** Before release, Claude Code must verify the exact printed model number against the current Molicel datasheet.

If the installed cell is confirmed as Molicel INR-18650-P30B:

- nominal capacity: 3000 mAh typical
- nominal voltage: 3.6 V
- charge termination voltage: 4.2 V
- standard charge current: 3 A per current Molicel datasheet
- maximum charge current: 9 A per current Molicel datasheet
- continuous discharge rating: 30 A per current Molicel datasheet
- maximum diameter: 18.6 mm
- maximum height: 65.2 mm

Despite the cell's high capability, this product is not a fast-charger project.

### V1.1 charging target

Use:

- **2.0 A nominal charging target**
- firmware-selectable lower mode: **1.0 A**
- optional future 3.0 A mode only after completed thermal validation

2.0 A is intentionally conservative for a 3000 mAh high-performance cell while still providing useful recharge speed and leaving thermal margin in a compact enclosure.

Never enable the charger's silicon maximum simply because the IC supports it.

---

# 31. FULL TURNKEY PCBWAY ASSEMBLY — MANDATORY

This project is to be ordered as **PCBWay Turn-Key PCBA**, not bare PCBs.

The user does not want to solder components after delivery.

PCBWay must source and install, where supported:

- all SMD resistors/capacitors
- STUSB4500
- BQ25895
- TPS63070
- MAX17048
- LED driver
- USB-C receptacle
- TVS/ESD protection
- all inductors
- all MOSFETs/load switches
- all LEDs
- battery gauge pushbutton
- system power switch
- NTC / temperature components
- test points if implemented as components
- **both 22-position female ESP32 headers**
- **PCB-mount 18650 holder**
- any other through-hole hardware defined in the BOM

PCBWay explicitly supports:

- turnkey component sourcing
- SMT assembly
- through-hole (THT) assembly
- mixed SMT + THT assembly

The manufacturing package shall mark the order as:

```text
ASSEMBLY TYPE: FULL TURNKEY PCBA
PLACEMENT: SMT + THT / MIXED
CUSTOMER POST-ASSEMBLY SOLDERING REQUIRED: NONE
```

The only items expected to be installed by the user after delivery are:

1. the existing ESP32-S3-DevKitC-1 N8R8 module, which plugs into the female sockets;
2. the user's removable Molicel 18650 cell.

The carrier PCB itself must arrive electrically and mechanically assembled.

## 31.1 No-cheap-hardware rule

Do not use generic/no-name connectors, battery holders, switches, or headers merely to reduce BOM price.

Preferred component sourcing priority:

1. Samtec / Harwin / Mill-Max / Amphenol / Molex / TE / Würth / Keystone / MPD
2. equivalent reputable industrial manufacturer
3. generic part only after explicit review

Female ESP32 sockets are a user-touch component and must have:

- firm insertion force,
- good plating,
- straight body molding,
- correct 2.54 mm pitch,
- enough mating cycles for development use,
- sufficient pin retention.

The battery holder must be mechanically rigid and appropriate for repeated cell replacement.

---

# 32. BOARD APPEARANCE / FINISH

## 32.1 Solder mask

**Primary choice: PURPLE.**

PCBWay currently lists purple solder mask as an available option.

If purple creates a material, lead-time, or assembly limitation that materially affects the project:

**Fallback: BLACK.**

Do not silently substitute another color.

## 32.2 Surface finish

Use:

**ENIG (Electroless Nickel Immersion Gold)**

rather than basic HASL for this build unless PCBWay DFM identifies a concrete issue.

Reasons:

- premium appearance
- flat pads
- good fine-pitch/QFN assembly
- good corrosion resistance
- cleaner finished product

## 32.3 Silkscreen

Preferred:

- white silkscreen on purple
- white silkscreen on black

Keep the visible top side clean.

Use restrained labels and a small product mark:

```text
RuView Power Base
REV V1.x
```

Avoid excessive reference designators in prominent visible areas if they can be placed on the underside without harming serviceability.

---

# 33. FINAL MECHANICAL CONCEPT — CENTERED ESP32 + SIDE 18650

The mechanical intent is now locked.

The ESP32-S3-DevKitC-1 is the centerpiece of the board.

The user should visually perceive:

```text
+------------------------------------------------+
|                                                |
|       +----------------------------+           |
|       |                            |  +-----+  |
|       |     ESP32-S3 DevKitC-1     |  |     |  |
|       |          N8R8              |  | 1   |  |
|       |                            |  | 8   |  |
|       |      CENTERPIECE           |  | 6   |  |
|       |                            |  | 5   |  |
|       +----------------------------+  | 0   |  |
|             ||          ||           |     |  |
|             || sockets  ||           |     |  |
|                                      +-----+  |
| USB-C     BAT LEDs    BUTTON     POWER SW     |
+------------------------------------------------+
```

The 18650 is mounted **parallel to the long axis of the ESP32**, offset to one side of the DevKit rather than placed directly underneath it.

"Vertical" in this specification means vertically oriented in the top-down board view along the long dimension of the product, **not** standing the cylindrical cell upright on its end.

## 33.1 Reasons for side placement

This layout is preferred because it:

- makes the ESP32 the visual center of the design;
- keeps the cell accessible;
- avoids placing a large metal cylinder under the ESP32;
- improves routing of BAT+/BAT- to the charger;
- creates a dedicated power side of the board;
- improves separation between switching power components and the ESP32 antenna;
- makes enclosure design easier;
- reduces total stack thickness.

## 33.2 RF orientation

The ESP32 antenna end shall face toward an outer board edge.

No battery shall sit beside or extend into the antenna's keepout region.

Preferred arrangement:

```text
             CLEAR RF EDGE
                   ^
                   |
       +-----------------------+
       | ESP32 PCB ANTENNA     |
       |                       |
       | ESP32-S3 DevKitC-1    |   [ 18650 ]
       |                       |   [ 18650 ]
       |                       |   [ 18650 ]
       +-----------------------+   [ 18650 ]
           ||             ||       [ 18650 ]
           ||             ||       [ 18650 ]
                                  POWER ZONE
```

The 18650 should begin below the antenna region when required to preserve antenna clearance.

## 33.3 Component zoning

Divide the carrier into functional zones:

### CENTER
- ESP32 female sockets
- ESP32 module
- minimal low-noise support circuitry

### BATTERY SIDE
- 18650 holder
- battery protection
- fuel gauge
- cell NTC

### LOWER / POWER SIDE
- USB-C receptacle
- STUSB4500
- BQ25895
- TPS63070
- inductors
- input protection
- power switch

### USER-INTERFACE EDGE
- four SOC LEDs
- charger/status LED
- battery gauge button
- power switch

This zoning should make the design visually intentional rather than appearing like development modules wired together.

---

# 34. PREMIUM FEMALE HEADER REQUIREMENT

The ESP32 must plug into two premium 2.54 mm female sockets.

The design must evaluate reputable socket-strip families from:

- Samtec
- Harwin
- Mill-Max

Preferred qualities:

- gold-plated contacts
- robust through-hole tails
- black housing
- low-profile but enough clearance for DevKit underside components
- correct mating depth for standard DevKitC male headers

Do not choose the exact header height until the ESP32 underside component envelope and carrier component height have been checked in the 3D model.

The ESP32 should:

- press straight down into the sockets,
- feel secure,
- not wobble significantly,
- remain removable without tools,
- not require soldering.

---

# 35. PREMIUM 18650 HOLDER REQUIREMENT

Evaluate industrial holders from:

- Keystone Electronics
- Memory Protection Devices (MPD)

Requirements:

- single 18650
- PCB mount
- mechanically rigid
- plated spring/contact system
- repeated insertion/removal capable
- retains cell securely in normal indoor use
- side-loading/top-loading orientation appropriate for enclosure

The holder shall be installed by PCBWay during THT/mixed assembly.

The user must not need to solder or attach battery wires.

If the best holder has mounting pegs or large through-hole tabs, incorporate them into the PCB rather than switching to a cheaper SMT-only holder.

---

# 36. POWER DELIVERY V1.1 TARGET

The target is not merely "charges from USB-C." It must behave like a finished battery-powered product.

## Required operating modes

### USB-C PD connected, battery installed
- negotiate preferred 9 V PD
- power system rail
- power ESP32
- charge battery with available headroom
- no ESP32 reboot

### USB-C 5 V source connected, battery installed
- operate normally at reduced input power budget if required
- charge battery at an automatically safe input-limited rate
- no invalid PD dependency

### USB disconnected, battery installed
- seamless battery operation
- regulated 5.0 V to ESP32

### USB connected, battery removed
- ESP32 should operate if source capacity is sufficient
- charger should remain safe

### Heavy ESP32 transient during charging
- BQ25895 power path may use battery supplement
- 5 V rail remains stable
- no brownout

## Preferred PD policy

Primary:
- **9 V PD**

Do not request 15 V or 20 V.

The reason is to:

- reduce cable current versus 5 V,
- remain safely inside BQ25895 operating limits,
- reduce unnecessary conversion stress,
- keep implementation simple and robust.

---

# 37. BOARD-LEVEL FUNCTIONAL TEST REQUIREMENT

Because the user wants boards that arrive functional, request PCBWay functional testing if practical for prototype quantity.

Design a small bed-of-nails-friendly test interface or accessible pads.

At minimum, production test procedure should verify:

1. no battery short;
2. VBUS input;
3. USB-C attach;
4. PD negotiation to 9 V with a known PD source;
5. BQ25895 SYS output;
6. regulated 5.0 V output;
7. I2C acknowledgement from:
   - BQ25895
   - MAX17048
   - LED driver
8. four SOC LEDs illuminate;
9. charger/status LED illuminates;
10. battery gauge button input works;
11. power switch works.

If PCBWay will not perform the complete functional test at reasonable prototype cost, request at least:

- AOI
- X-ray inspection for QFN/leadless packages where appropriate
- continuity / power-rail test

and create a documented user acceptance test.

---

# 38. ASSEMBLY NOTES FOR PCBWAY

Add the following note to `PCBWAY_ORDER_NOTES.md`:

```text
This is a FULL TURNKEY mixed-technology PCBA.

Please quote procurement and assembly of ALL listed components,
including through-hole female ESP32 sockets and the PCB-mounted
18650 holder.

The customer does not intend to solder components after delivery.

Board solder mask preference:
1. Purple
2. Black only if purple is unavailable or materially incompatible

Surface finish: ENIG.

Please do not substitute critical power ICs, USB-C connector,
female socket headers, battery holder, or switches without approval.

Please flag any component that requires customer-supplied material
before order approval.

The removable ESP32-S3 DevKitC-1 module and removable 18650 cell
are NOT to be permanently assembled to the carrier PCB.
```

---

# 39. QUALITY GATE BEFORE PCBWAY ORDER

Claude Code shall not mark the design manufacturing-ready until all of the following are true:

- exact Molicel model confirmed;
- exact battery holder confirmed against cell dimensions;
- exact premium female header family selected;
- DevKitC 3D model mechanically checked;
- USB-C connector selected from reputable manufacturer;
- purple solder mask selected in PCBWay output notes;
- ENIG selected;
- full turnkey + mixed SMT/THT explicitly documented;
- BOM contains exact MPN for every fitted part;
- no "generic header" or "generic battery holder" placeholders remain;
- power-path simulation/calculation completed;
- converter inductor/capacitor ratings verified;
- 2 A charge configuration thermally reviewed;
- RF keepout checked in PCB layout;
- cell does not overlap antenna keepout;
- 3D STEP assembly visually inspected;
- ERC passes;
- DRC passes;
- exported Gerbers visually inspected;
- CPL orientation checked;
- battery polarity markings checked;
- USB-C connector orientation checked;
- female-header pin-1 orientation checked;
- test plan written.

The design priority is **robust function and premium feel**, not lowest possible PCB cost.
