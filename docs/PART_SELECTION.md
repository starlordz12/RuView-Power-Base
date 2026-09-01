# Stage A — part validation

Spec §24 Stage A requires every critical part be confirmed active and available, with an
exact MPN, before the schematic is drawn. Spec §39 forbids "generic header" or "generic
battery holder" placeholders in the released BOM.

**Legend:** ✅ validated · 🟡 selected, needs datasheet confirmation · ⬜ not yet selected

## Critical actives

| Ref | Function | MPN | Mfr | Package | Status | KiCad |
|---|---|---|---|---|---|---|
| U1 | USB-C PD sink trigger | `CH224K` | WCH | SSOP-10-1EP 3.9×4.9 | ✅ active | stock symbol + footprint |
| U2 | 1S charger + NVDC power path | `BQ25895RTW` | Texas Instruments | WQFN-24-1EP 4×4 | ✅ active | stock symbol + `Texas_RTW_WQFN-24-1EP_4x4mm_..._ThermalVias` |
| U3 | 5 V buck-boost | `TPS63070RNMR` | Texas Instruments | VQFN-HR-15 (RNM) 2.5×3 | ✅ active, 11.9k stock Digi-Key | **symbol + footprint both custom** |
| U4 | Fuel gauge | `MAX17048G+T10` | Analog Devices | TDFN-8-EP 2×2 | ✅ active | **symbol custom**; footprint from stock DFN-8 2×2 family, EP to be matched |
| U5 | 1S protection | ⬜ | — | — | open, see D6 | — |

The two custom symbols and one custom footprint (TPS63070) are the whole custom-part
burden. Everything else is stock or a generic passive.

## Connectors and electromechanical

| Ref | Function | MPN | Mfr | Notes |
|---|---|---|---|---|
| J1 | USB-C receptacle | `USB4085-GF-A` | GCT | ✅ THT with 4 retention/grounding posts, 100 W rated. Stock KiCad footprint `USB_C_Receptacle_GCT_USB4085`. GCT is on the spec §3.1 approved list. |
| J2, J3 | ESP32 sockets, 22-pos | `SSW-122-01-G-S` | Samtec | ✅ 2.54 mm, gold, THT, 4.7 A/pin. Samtec is first-tier on the spec §31.1 list. Two required. Mating depth option to be fixed against the DevKit underside envelope per §34. |
| BT1 | 18650 holder | `BK-18650-PC2` | MPD | 🟡 most compact validated option at ~78.5 × 22.5 mm. MPD is on the spec §35 approved list. |

### Holder alternatives, measured from KiCad stock footprints

| Candidate | Footprint extent | Note |
|---|---|---|
| MPD `BK-18650-PC2` | 78.5 × 22.5 mm | most compact — current selection |
| MPD `BH-18650-PC` | 79.2 × 22.4 mm | equivalent, second source |
| Keystone `1042` | 87.9 × 21.7 mm | 9 mm longer; grows the board |

Keystone `1043P` (polarized, mechanically blocks reverse cell insertion) is attractive
against spec §6.3 but ships no stock KiCad footprint and measures 77 × 20.65 × 14.86 mm.
Worth revisiting if reverse-insertion protection is chosen mechanically rather than
electrically.

## Board size consequence

Cell holder ~78.5 mm long, mounted alongside a ~25.4 mm wide DevKit per spec §33, puts
the carrier near **90 × 60 mm**. That sits inside PCBWay's ≤100 × 100 mm price tier,
which is the single largest lever on bare-PCB cost. Treat 100 mm as a hard budget in
layout.

## Safety-critical passives

| Ref | Value | Why it is safety-critical |
|---|---|---|
| `RILIM` | **680 Ω**, 1%, 0603 | Sets the BQ25895 hardware input-current clamp that keeps charge current under the cell's 1.7 A limit when no host is present. Derived in [DECISIONS.md D5](DECISIONS.md#d5--the-charge-current-ceiling-is-enforced-in-hardware-by-the-ilim-resistor). **Do not substitute, value-engineer, or mark DNP.** |

## Still to select

⬜ VBUS TVS · ⬜ CC-line ESD array · ⬜ TPS63070 inductor (per TI reference layout) ·
⬜ BQ25895 inductor · ⬜ 5 V load switch for SW1 · ⬜ 10 kΩ NTC · ⬜ power switch ·
⬜ momentary button · ⬜ LEDs and series resistors · ⬜ all passives

Passives are chosen after the reference layouts are worked, since the converter
capacitor and inductor ratings follow directly from them (spec §39).

## Lifecycle check

All four critical actives confirmed **active / in production** as of 2026-08-31. None
NRND. Re-confirm immediately before the order is placed — spec §20 requires production
status be verified before final routing, and stock moves.

## Sources

- [TPS63070RNMR — Digi-Key](https://www.digikey.in/en/products/detail/texas-instruments/TPS63070RNMR/6175216)
- [TPS63070 product page — TI](https://www.ti.com/product/TPS63070)
- [MAX17048G+T10 — Digi-Key](https://www.digikey.com/en/products/detail/analog-devices-inc-maxim-integrated/MAX17048-T10/3758921)
- [MAX17048 — Analog Devices](https://www.analog.com/en/products/max17048.html)
- [USB4085-GF-A — Digi-Key](https://www.digikey.com/en/products/detail/gct/USB4085-GF-A/9859662)
- [USB4085 — GCT](https://gct.co/connector/usb4085)
- [SSW-122-02-G-S socket strip — Samtec](https://www.samtec.com/products/ssw-122-02-g-s)
- [CH224 sink controller family — DONE.LAND](https://done.land/components/power/powersupplies/usb/usbtriggers/ch224/)
- [CH224K vs HUSB238 comparison](https://knightli.com/en/2026/04/11/usb-pd-decoy-chip-comparison/)
- [Keystone 1043 18650 holder](https://www.keyelco.com/product.cfm/product_id/919)
