# Power design — resolved component values

Values derived from vendor datasheets during Stage A/B. Every number here has a cited
source. Anything not yet confirmed is marked ⬜ and must not be treated as settled.

Sources: TI **SLUSC88C** (BQ25895), TI **SLVSC58B** (TPS63070/1/2), TI **SLUSBU9**
(BQ29700), WCH **CH224 manual v1F**.

---

## 1. USB-C PD input — CH224K

### VDD supply ✅ resolved

The CH224K has a **built-in high-voltage LDO**. VDD is fed from VBUS through a **series
resistor** with a **1 µF decoupling capacitor** to GND. **No external LDO is required.**

> "VDD — working power input of power supply ... external 1uF decoupling capacitor,
> series resistor to VBUS" — CH224 manual §4, pin description

The `VBUS` pin is a separate analog voltage-detection input and **also requires its own
series resistor** to the VBUS net.

- VDD operating range: **3.0–3.6 V** (absolute max 3.6 V)
- VBUS input range: **4–22 V**

**Values from the manual's reference schematic §6.1 (confirmed):**

| Net | Component |
|---|---|
| VBUS → VDD | **1 kΩ series**, plus **1 µF** VDD to GND |
| VBUS → VBUS pin | **10 kΩ series** |
| CFG1 → GND | **6.8 kΩ** (selects 9 V) |
| PG | **10 kΩ** pull-up (open-drain output) |

⚠ **Size the VDD series resistor at 1206, not 0603.** VDD is a **shunt** regulator holding
3.3 V and sinking the excess, so the series resistor carries `(VBUS − 3.3) / 1 kΩ`:

| VBUS | Current into shunt | Power in R |
|---|---|---|
| 9 V (normal) | 5.7 mA | 32 mW ✅ |
| 20 V (open-CFG1 fault) | 16.7 mA — within the ~20 mA shunt capability | **279 mW** ⚠ |

A 0603 (100 mW) would be destroyed in the fault case and an 0805 (125 mW) is still under.
A 1206 at 250 mW survives it. Costs nothing and removes a burn hazard from a fault we
already know is reachable.

### Voltage selection ✅ resolved — and safety-relevant

Single resistor from **CFG1 to GND** selects the requested voltage:

| CFG1 resistor | Requested voltage |
|---|---|
| **6.8 kΩ** | **9 V ← our target** |
| 24 kΩ | 12 V |
| 56 kΩ | 15 V |
| **NC / open** | **20 V** ⚠ |

> ⚠ **An open or missing CFG1 resistor requests 20 V.** The manual warns of exactly this:
> "CFG1 may be in a floating state ... and 20V may be requested at this time. If the
> system cannot withstand 20V input, then a configuration resistor should be added."

**Consequence, assessed rather than assumed:** the BQ25895's VBUS **absolute maximum is
22 V** (SLUSC88C §7.1) while its **recommended operating maximum is 14 V** (§7.3). So a
20 V request is *survivable but out of spec* — the charger raises `CHRG_FAULT = 01`
(input fault, VBUS > VACOV) and stops charging. **The board bricks its charging function
rather than destroying itself.**

Mitigations, in order:

1. `R_CFG1 = 6.8 kΩ` is **safety-critical** — never DNP, never substitute.
2. All VBUS-side capacitors rated **25 V**, so 20 V is non-destructive.
3. **Already covered by test:** spec §37 production test item 4 requires verifying 9 V
   negotiation against a known PD source on every board, which detects an open CFG1
   before the board ships.

---

## 2. Charger — BQ25895

### ILIM hardware clamp ✅ resolved

`RILIM = 680 Ω`. Full derivation and the reasoning for why this must be hardware rather
than firmware is in [DECISIONS.md D5](DECISIONS.md#d5--the-charge-current-ceiling-is-enforced-in-hardware-by-the-ilim-resistor).

### NTC / TS network ✅ resolved

TI gives the answer directly for our exact temperature window (SLUSC88C §8.2.7.5,
Figure 8-6, Equation 2). Thermistor **103AT** (10 kΩ NTC, TI's own recommendation in the
pin description), divider from REGN to TS to GND:

| For a 0 °C to 45 °C Li-ion charge window | Value |
|---|---|
| RTH at 0 °C (cold) | 27.28 kΩ |
| RTH at 45 °C (hot) | 4.91 kΩ |
| **RT1** (TS to GND) | 5.21 kΩ → **5.23 kΩ**, E96 1% |
| **RT2** (REGN to TS) | 29.87 kΩ → **30.1 kΩ**, E96 1% |

TS thresholds are ratiometric to REGN: `VLTF` 73.25%, `VHTF` 48.25%, `VTCO` 44.75%.

0–45 °C is the standard Li-ion charging window and the conservative choice. If the M35A
datasheet permits a wider range, we have simply been cautious — the error direction is
safe.

Spec §4.3 wants the thermistor measuring the **cell body** rather than PCB ambient. That
conflicts with the §31 full-turnkey requirement, and the compromise actually being built —
an 0603 NTC directly beneath the cell, thermally isolated from the power side — is recorded
honestly in [D10](DECISIONS.md#d10--ntc-mounting-is-a-documented-compromise), including the
thermal-test characterisation it obliges.

### Required decoupling ✅ resolved

Straight from the SLUSC88C pin descriptions — these are not optional:

| Pin | Component |
|---|---|
| REGN | **4.7 µF**, 10 V ceramic, close to IC (also biases the TS divider) |
| BAT | **10 µF** close to pin |
| SYS | **20 µF** close to pin |
| BTST → SW | **0.047 µF** bootstrap |

---

## 3. 5 V rail — TPS63061 (changed from TPS63070)

**`TPS63061`** — fixed 5.0 V, 2.5–12 V input, S-PWSON-10. **KiCad ships both the symbol and
`Package_SON:Texas_S-PWSON-N10_ThermalVias`.**

Chosen over the spec's TPS63070 for two reasons: the fixed output deletes the feedback
divider and its failure mode, and the TPS63070's HotRod VQFN-HR-15 land pattern (L-shaped
pads, mixed solder-mask definitions) is not shipped by KiCad and would have had to be
hand-built for a turnkey order. Full reasoning and the capability trade in
[D6](DECISIONS.md#d6--tps63061-fixed-5-v-son-10-replaces-the-tps63070).

### Available output current — always boost on this board

TI quotes 2 A in buck and **1.3 A in boost**. The cell is 3.0–4.2 V into a 5 V rail, so
**boost always applies.** From TI Equation 2, `IOUT = η × ISW × (1 − D)`:

| Cell | Duty | At 5 V |
|---|---|---|
| 3.0 V | 0.40 | **1.08 A** |
| 3.6 V | 0.28 | **1.30 A** |
| 4.2 V | 0.16 | **1.51 A** |

Spec §22's 1.0 A continuous is met at every cell voltage. Its ~2 A transient aspiration is
not; the node draws ~0.7 A, leaving ~1.5× at worst case.

### Passives (TPS6306x datasheet §9.2.2)

| Item | Value |
|---|---|
| **L** | **1.0 µH** — Coilcraft `XFL4020-102ME`, TI Table 9-3 (5.1 A ISAT, 10.8 mΩ) |
| COUT | **66 µF** (3 × 22 µF) — TI's "typical application" pairing with 1.0 µH |
| CIN | **≥ 20 µF** ceramic, close to VIN/PGND |
| FB | tie directly to VOUT (fixed version) |

Pinout (stock symbol): 1 L1 · 2 VIN · 3 EN · 4 PS/SYNC · 5 PG · 6 VAUX · 7 GND · 8 FB ·
9 VOUT · 10 L2 · 11 PGND (exposed pad).

---

## 4. Battery protection — AP9214L (integrated protector + FETs)

**Diodes Incorporated `AP9214L`**, U-DFN2535-6, < 0.6 mm thick. One package containing a
1-cell protector and a matched dual common-drain N-FET.

| Parameter | Value |
|---|---|
| Integrated RSS(on) | **13.5 mΩ typ**, specified at **VDD = 3.5 V** |
| Overcharge detect | 3.5–4.5 V, 5 mV steps, ±25 mV |
| Overdischarge detect | 2.0–3.4 V, 10 mV steps, ±35 mV |
| **Discharge overcurrent (VDOC)** | **0.05–0.32 V, 10 mV steps, ±15 mV** |
| Short-circuit detect | 0.45–0.7 V |
| Charge overcurrent | −0.2 to −0.05 V |
| Quiescent | 3.0 µA typ normal · 0.1 µA power-down |
| External components | **R1 220 Ω · R2 1.0 kΩ · C1 100 nF** |

### Trip point

Overcurrent is sensed as a voltage across the FETs, so:

```text
I_trip  =  VDOC / RSS(on)  =  100 mV / 13.5 mΩ  ≈  7.4 A
```

Against this board's **3.55 A** worst-case transient that is roughly 2× margin, and it sits
well below the M35A's 10 A discharge rating. Because RSS(on) is characterised at
**VDD = 3.5 V**, this figure holds at the real 1S operating point rather than at a
datasheet-convenient gate voltage.

### Why discrete FETs were rejected — see [D7](DECISIONS.md#d7--battery-protection-integrated-ap9214l-after-two-wrong-answers)

In a 1S pack the gate drive **is the cell voltage**, 2.5–4.2 V and falling as it depletes.

- Common-drain duals (AO8810, AO8816, FS8205A) sit at 23–25 mΩ at VGS 2.5 V → trip ≈ **2.2 A**,
  *below this board's own transient*.
- TI's reference `CSD16406Q3` looks better at 5.9 mΩ — but only at VGS 4.5 V. Its on-resistance
  goes vertical below ~3.2 V gate (Figure 7) and `Vth` is 1.8 V, so at a depleted cell it is
  barely enhanced. It is a point-of-load FET, not a 1S protection FET.

**RDS(on) quoted at VGS 4.5 V is meaningless for 1S protection.** Only on-resistance at cell
voltage counts.

⬜ **Open:** exact orderable variant. Wanted VCU ≈ 4.28–4.35 V, VDL ≈ 2.5–2.8 V, VDOC ≈ 100 mV;
thresholds are factory-programmed, so the variant must match what is stocked.

---

## Summary of what is still open

| Item | Blocking |
|---|---|
| ⬜ CH224K VDD and VBUS series resistor values | schematic |
| ⬜ CSD16406Q3 RDS(on) confirmed at VGS ≈ 3.0 V | schematic — confirmation, not risk |
| ⬜ CC1/CC2 ESD array final MPN | schematic |
| ⬜ L1 saturation current ≥ 4 A | schematic |
| ⬜ NTC mounting method | layout — see [D10](DECISIONS.md#d10--ntc-mounting-is-a-documented-compromise) |
| ⬜ M35A charging temperature window vs the assumed 0–45 °C | confirmation only; current choice is conservative |
