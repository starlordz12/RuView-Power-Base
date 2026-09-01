# YD-ESP32-S3 mechanical and header reference

Derived from VCC-GND's `ESP32-S3-Metric.pdf` (in [vcc-gnd/YD-ESP32-S3](https://github.com/vcc-gnd/YD-ESP32-S3)),
read on 2026-08-31. Dimensions are the drawing's own dimension callouts; header geometry
was independently confirmed by extracting the 44 pad coordinates from the PDF vector data
and checking them against those callouts.

**Not yet caliper-verified against the user's physical V1.3 board.** See G1 in
[STATUS.md](STATUS.md).

## Board geometry

| Dimension | Value | Source |
|---|---|---|
| Board width | **27.94 mm** | drawing callout |
| Board length | **57.15 mm** | drawing callout |
| Header row spacing (centre to centre) | **25.40 mm** | callout; = 10 × 2.54 exactly |
| Pin pitch | **2.54 mm** | extracted, 21.6150 pt/step at drawing scale |
| Pins per row | **22** | 44 pads extracted, 22 per header |
| Pin-1 centre to nearest board edge | **1.91 mm** | callout |
| Header pin span (pin 1 → pin 22) | **53.34 mm** | callout; = 21 × 2.54 exactly |
| Overall length incl. module overhang | **63.39 mm** | callout |
| **Module antenna overhang past board edge** | **6.24 mm** | 63.39 − 57.15 |

Consistency check: 53.34 + 1.91 + 1.91 = 57.16 ≈ 57.15 mm ✅ — the header block is
centred on the board and the callouts are self-consistent.

### RF consequence

The ESP32-S3-WROOM-1 module **overhangs the pin-1 end of the board by 6.24 mm**, and that
overhang is where the PCB antenna sits. The carrier must carry **no copper, no pour, no
components and ideally no board material** under or beside that overhang. This is the
single hardest constraint on carrier outline — spec §11 and §33.2.

Pin 1 is `3V3` on J1 / `GND` on J2, both marked with square pads. **The antenna end is the
pin-1 end**, and the two USB-C connectors are at the pin-22 end.

## Header pinout — verified

Both rows read from the drawing silkscreen and confirmed **identical to the official
Espressif ESP32-S3-DevKitC-1**. The board is pin-compatible; only the mechanical outline
differs from Espressif's.

| Pin | J1 (left) | J2 (right) |
|:--:|---|---|
| 1 | `3V3` ◼ | `GND` ◼ |
| 2 | `3V3` | `TX` (GPIO43) |
| 3 | `RST` | `RX` (GPIO44) |
| 4 | GPIO4 | GPIO1 |
| 5 | GPIO5 | GPIO2 |
| 6 | GPIO6 | GPIO42 |
| 7 | GPIO7 | GPIO41 |
| 8 | GPIO15 | GPIO40 |
| 9 | GPIO16 | GPIO39 |
| 10 | GPIO17 | GPIO38 |
| 11 | GPIO18 | GPIO37 ⛔ |
| 12 | GPIO8 | GPIO36 ⛔ |
| 13 | GPIO3 ⚠ | GPIO35 ⛔ |
| 14 | GPIO46 ⚠ | GPIO0 ⚠ |
| 15 | GPIO9 | GPIO45 ⚠ |
| 16 | GPIO10 | GPIO48 ⛔ |
| 17 | GPIO11 | GPIO47 |
| 18 | GPIO12 | GPIO21 |
| 19 | GPIO13 | GPIO20 ⛔ |
| 20 | GPIO14 | GPIO19 ⛔ |
| 21 | `5Vin` | `GND` |
| 22 | `GND` | `GND` |

◼ square pad, pin-1 marker ⚠ strapping pin — do not drive ⛔ reserved, do not use

**Reserved:** GPIO35/36/37 are the octal PSRAM bus on N8R8. GPIO19/20 are native USB.
GPIO48 is the onboard WS2812. GPIO43/44 are UART0 to the CH343P.
**Strapping:** GPIO0, 3, 45, 46.

## Proposed carrier GPIO assignment

All carrier signals land on **J1**, leaving J2 entirely free for RuView. Every pin below
is a plain GPIO — no strapping, no PSRAM, no USB, no UART.

| Signal | GPIO | J1 pin |
|---|---|---|
| I2C SDA (BQ25895, MAX17048) | GPIO8 | 12 |
| I2C SCL | GPIO9 | 15 |
| SOC LED 1 | GPIO4 | 4 |
| SOC LED 2 | GPIO5 | 5 |
| SOC LED 3 | GPIO6 | 6 |
| SOC LED 4 | GPIO7 | 7 |
| Status LED | GPIO15 | 8 |
| Battery gauge button (SW2) | GPIO16 | 9 |
| BQ25895 `/INT` | GPIO17 | 10 |
| MAX17048 `/ALRT` | GPIO18 | 11 |
| 5 V rail in | `5Vin` | 21 |
| Ground | `GND` | 22 |

GPIO8/GPIO9 are the ESP32-S3 default I2C pair, so stock driver defaults work unmodified.
GPIO10–14 on J1 remain free and should be brought to the breakout pads per spec §10.

## Verification still owed

Caliper-check on the user's physical V1.3 board, since V1.3 is an undocumented revision
between the vendor's "counterfeit V1.2" and "authentic V1.4":

1. **Header row spacing**, centre to centre — expect **25.40 mm**
2. **Board width and length** — expect **27.94 × 57.15 mm**
3. **Module overhang past the pin-1 board edge** — expect **6.24 mm**

If any disagree, the physical board wins and this document is wrong.
