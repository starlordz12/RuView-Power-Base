# Stage A — part validation

Spec §24 Stage A requires every critical part be confirmed active and available, with an
exact MPN, before the schematic is drawn. Spec §39 forbids "generic header" or "generic
battery holder" placeholders in the released BOM.

**Legend:** ✅ selected and validated · 🟡 series fixed, variant pending · ⬜ open

---

## Integrated circuits

| Ref | Function | MPN | Mfr | Package | Status |
|---|---|---|---|---|---|
| U1 | USB-C PD sink trigger | `CH224K` | WCH | SSOP-10-1EP 3.9×4.9 | ✅ active · stock KiCad symbol + footprint |
| U2 | 1S charger + NVDC power path | `BQ25895RTW` | Texas Instruments | WQFN-24-1EP 4×4 | ✅ active · stock symbol + thermal-via footprint |
| U3 | 5 V buck-boost, **fixed 5 V** | `TPS630701RNMR` | Texas Instruments | VQFN-HR-15 (RNM) 2.5×3 | ✅ active · symbol + footprint custom · [D6](DECISIONS.md#d6--tps630701-fixed-5-v-replaces-the-tps63070-adjustable) |
| U4 | Fuel gauge | `MAX17048G+T10` | Analog Devices | TDFN-8-EP 2×2 | ✅ active · symbol custom |
| U5 | 1S battery protection | `BQ29700DSE` | Texas Instruments | WSON-6 1.5×1.5 | ✅ active · symbol custom · [D7](DECISIONS.md#d7--battery-protection-bq29700-with-low-rdson-fets) |

Custom-library burden: **symbols** for TPS630701, MAX17048, BQ29700; **one footprint** for
the TPS630701's VQFN-HR-15. Everything else is KiCad stock.

## Discrete semiconductors

| Ref | Function | MPN | Mfr | Package | Notes |
|---|---|---|---|---|---|
| Q1, Q2 | Protection FETs | `CSD16406Q3` | Texas Instruments | SON 3.3×3.3 | ✅ **TI's own reference pairing with the BQ29700.** 7.4 mΩ max @ VGS 4.5 V; two in series → OCD trips ≈ 6.8 A against our 3.55 A transient. |
| D1 | VBUS TVS | `SMAJ12A` | Littelfuse | DO-214AC (SMA) | ✅ 12 V standoff, 13.3 V breakdown, **19.9 V clamp** |
| D2 | CC1/CC2 ESD | `µClamp2411ZA` | Semtech | — | 🟡 24 V operating; selected per Semtech's USB Type-C ESD application note for CC pins |
| D3–D6 | SOC indicator LEDs ×4 | `APT1608SGC` | Kingbright | 0603 | ✅ super-bright green, 568 nm |
| D7 | Charge/status LED | `APT1608` series, amber | Kingbright | 0603 | 🟡 colour suffix at BOM freeze |

### Why the TVS is 12 V and not 24 V

The obvious choice for a USB-C PD board is a 24 V-standoff TVS such as `SMAJ24A`, since
VBUS can legitimately reach 20 V. **That part would protect nothing here.** Its clamping
voltage is **38.9 V** — far above the BQ25895's **22 V absolute maximum**. The charger
would be destroyed long before the TVS conducted meaningfully.

This board requests **9 V and never more**, so the TVS is sized for the voltage the design
actually operates at. `SMAJ12A` stands off 12 V with comfortable margin over 9 V ±5% and
clamps at **19.9 V — below the 22 V the charger must survive.**

**What this deliberately does not cover:** the open-`R_CFG1` fault that would request 20 V.
That is a *build defect*, not an operating condition, and spec §37's production test
already requires verified 9 V negotiation on every board. Sizing the TVS to ride out that
fault would mean abandoning protection of the very part we are trying to protect.

## Magnetics

| Ref | Function | MPN | Mfr | Value |
|---|---|---|---|---|
| L1 | BQ25895 charger inductor | `XFL4020-222ME` | Coilcraft | 2.2 µH |
| L2 | TPS630701 inductor | `XFL4020-152ME` | Coilcraft | 1.5 µH |

L2 is TI's own reference-BOM part (SLVSC58B Table 2). L1 is the same family for
consistency. The BQ25895 runs at 1.5 MHz and needs saturation ≥ ICHG + ½·I_ripple, with
system current sharing the same inductor — ⬜ **verify saturation ≥ 4 A** at schematic.

## Connectors and electromechanical

| Ref | Function | MPN | Mfr | Notes |
|---|---|---|---|---|
| J1 | USB-C receptacle | `USB4085-GF-A` | GCT | ✅ THT, 4 retention posts, 100 W. Stock KiCad footprint. §3.1 approved mfr. |
| J2, J3 | ESP32 sockets, 22-pos ×2 | `SSW-122-01-G-S` | Samtec | ✅ 2.54 mm, gold, THT, 4.7 A/pin. §31.1 first tier. |
| BT1 | 18650 holder | `BK-18650-PC2` | MPD | ✅ 78.5 × 22.5 mm, most compact validated option. §35 approved mfr. |
| SW1 | System power | `EG1218` | E-Switch | ✅ SPDT slide, THT. Switches **the converter's EN pin only** — [D9](DECISIONS.md#d9--sw1-switches-the-converters-en-pin-no-load-switch-ic). |
| SW2 | Battery gauge button | `PTS645` series | C&K | 🟡 THT tactile, 50 mA/12 V, 100k operations. Height variant fixed at layout. |

### Holder alternatives, measured from KiCad stock footprints

| Candidate | Extent | Note |
|---|---|---|
| MPD `BK-18650-PC2` | 78.5 × 22.5 mm | most compact — selected |
| MPD `BH-18650-PC` | 79.2 × 22.4 mm | equivalent second source |
| Keystone `1042` | 87.9 × 21.7 mm | 9 mm longer; grows the board |

## Thermal sensing

| Ref | MPN | Mfr | Notes |
|---|---|---|---|
| RT1 | `NCP18XH103F03RB` | Murata | 10 kΩ NTC, 0603, B = 3380 K |

TI's worked example assumes a 103AT (B = 3435 K). With B = 3380 the hot threshold lands at
essentially 45 °C and the cold threshold shifts about **0.8 °C warmer** — very slightly
more conservative. Acceptable: the error direction is safe.

⬜ **Mounting is an open mechanical question** — see [D10](DECISIONS.md#d10--ntc-mounting-is-a-documented-compromise).

## Safety-critical passives

These carry consequences beyond their nominal function. **None may be substituted,
value-engineered, or marked DNP,** and the BOM must say so explicitly.

| Ref | Value | Why |
|---|---|---|
| `R_CFG1` | **6.8 kΩ** 1% 0603 | Selects the 9 V PD request. **Open or missing requests 20 V**, exceeding the charger's 14 V operating maximum and halting charging. |
| `R_ILIM` | **680 Ω** 1% 0603 | Hardware clamp keeping charge current under the cell's 1.7 A limit when no host is present — [D5](DECISIONS.md#d5--the-charge-current-ceiling-is-enforced-in-hardware-by-the-ilim-resistor). |
| `R_TS1` / `R_TS2` | **5.23 kΩ** / **30.1 kΩ** 1% 0603 | Set the 0–45 °C charge temperature window. Wrong values move the window silently. |

## Remaining passives

| Function | Value |
|---|---|
| LED series resistors ×5 | 680 Ω 0603 → ≈2 mA at 3.3 V (spec §8.5 wants 1–2 mA) |
| I²C pull-ups ×2 | 4.7 kΩ to 3V3 |
| BQ29700 support | 0.1 µF, 2.2 kΩ, 330 Ω (SLUSBU9 Figure 25) |
| BQ25895 decoupling | REGN 4.7 µF/10 V · BAT 10 µF · SYS 20 µF · BTST 0.047 µF |
| TPS630701 | CIN 2×10 µF/25 V · COUT 3×22 µF/16 V · VIN local 10 µF/25 V |
| CH224K | VDD 1 µF + ⬜ series R · VBUS ⬜ series R |

All VBUS-side capacitors are **25 V rated**, which also makes the 20 V CFG1 fault
non-destructive.

## Board size consequence

Cell holder ~78.5 mm long, mounted alongside the 27.94 mm wide DevKit per spec §33, puts
the carrier near **90 × 60 mm** — inside PCBWay's ≤100 × 100 mm price tier, the single
largest lever on bare-PCB cost. Treat 100 mm as a hard budget in layout.

## Lifecycle check

All ICs and discrete semiconductors confirmed **active / in production** as of 2026-08-31.
None NRND. Re-confirm immediately before the order — spec §20 requires production status be
verified before final routing, and stock moves.

## Still open

| Item | Blocking |
|---|---|
| ⬜ CH224K VDD and VBUS series resistor values | schematic |
| ⬜ CC ESD array final MPN and availability | schematic |
| ⬜ L1 saturation current confirmation | schematic |
| ⬜ NTC mounting method | layout |
| ⬜ SW2 tactile height variant | layout / enclosure |
| ⬜ Status LED colour suffix | BOM freeze |

## Sources

- [BQ25895 SLUSC88C — TI](https://www.ti.com/lit/ds/symlink/bq25895.pdf)
- [TPS63070/1/2 SLVSC58B — TI](https://www.ti.com/lit/ds/symlink/tps63070.pdf)
- [BQ29700 SLUSBU9 — TI](https://media.digikey.com/pdf/Data%20Sheets/Texas%20Instruments%20PDFs/BQ29700.pdf)
- [CSD16406Q3 — TI](https://www.ti.com/product/CSD16406Q3)
- [TPS630701RNMR — Digi-Key](https://www.digikey.com/en/products/detail/texas-instruments/TPS630701RNMR/6175215)
- [MAX17048 — Analog Devices](https://www.analog.com/en/products/max17048.html)
- [USB4085 — GCT](https://gct.co/connector/usb4085)
- [SSW socket strip — Samtec](https://www.samtec.com/products/ssw-122-02-g-s)
- [SMAJ12A — Littelfuse](https://www.littelfuse.com/products/tvs-diodes/surface-mount/smaj/smaj12a.aspx)
- [ESD protection of USB Type-C interfaces — Semtech](https://www.semtech.com/uploads/design-support/TVS_App_Notes-SI21-03-ESD_Protection_of_USB_Type-C_Interfaces.pdf)
- [APT1608SGC — Kingbright](https://www.kingbrightusa.com/images/catalog/spec/apt1608sgc.pdf)
- [PTS645 tactile switch — C&K](https://www.ckswitches.com/media/1471/pts645.pdf)
- [EG1218 slide switch — E-Switch](https://www.e-switch.com/product/eg-series-subminiature-slide-switch/)
