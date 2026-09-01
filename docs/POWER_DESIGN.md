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

⬜ **Exact series resistor values** must be read off the manual's reference schematic
figures (§6.1–6.3) rather than inferred. This is the one open value in this section.

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
safe. Per spec §16 and §6, the thermistor must sit against the **cell body**, not read
PCB ambient.

### Required decoupling ✅ resolved

Straight from the SLUSC88C pin descriptions — these are not optional:

| Pin | Component |
|---|---|
| REGN | **4.7 µF**, 10 V ceramic, close to IC (also biases the TS divider) |
| BAT | **10 µF** close to pin |
| SYS | **20 µF** close to pin |
| BTST → SW | **0.047 µF** bootstrap |

---

## 3. 5 V rail — TPS630701 (changed from TPS63070)

### Part change ✅ resolved

**Use `TPS630701RNMR` — the fixed 5.0 V variant** — instead of the adjustable TPS63070
the spec named. Same VQFN-HR-15 (RNM) 2.5 × 3 mm package, same reference layout, active
and stocked at Digi-Key.

| Device | Output | Output discharge |
|---|---|---|
| TPS63070 | adjustable 2.5–9 V | off |
| **TPS630701** | **fixed 5.0 V** | off |
| TPS630702 | adjustable | on |

Why: the board only ever needs 5.0 V. The fixed variant removes the feedback divider,
which removes two resistors, a ±1% accuracy stack-up, and — the real reason — **a failure
mode where a wrong or damaged divider resistor puts an out-of-spec voltage onto the
ESP32's 5 V pin.** For fixed versions the FB pin connects directly to VOUT.

*(Retained for reference: the adjustable part would need R1 = 680 kΩ, R2 = 130 kΩ for
5.0 V, from SLVSC58B Table 4, with VFB = 800 mV.)*

### Passives ✅ resolved — from TI's reference BOM (SLVSC58B Table 2)

| Item | Value |
|---|---|
| **L** | **1.5 µH** — Coilcraft `XFL4020-152ME` |
| CIN | 2 × 10 µF / 25 V / X7S / 0805 |
| COUT | 3 × 22 µF / 16 V / X6S / 0805 |
| VIN local | 10 µF / 25 V / X5R / 0603 |

25 V input capacitors also cover the 20 V CFG1 failure mode above.

---

## 4. Battery protection — BQ29700 + external FETs

### Protector ✅ selected

**TI `BQ29700DSE`**, WSON-6, 1.5 × 1.5 × 0.75 mm. Drives two low-side N-FETs in the cell's
negative path. Factory-programmed thresholds (SLUSBU9 §11.2.1):

| Protection | Threshold | Delay | Release |
|---|---|---|---|
| Overcharge (OVP) | **4.275 V** | 1.2 s | 4.175 V |
| Over-discharge (UVP) | **2.800 V** | 150 ms | 3.100 V |
| Charge overcurrent (OCC) | −70 mV | 9 ms | — |
| Discharge overcurrent (OCD) | **100 mV** | 18 ms | BAT−V⁻ > 1 V |
| Load short circuit (SCC) | 500 mV | 250 µs | 1 V |

OVP at 4.275 V sits correctly above the BQ25895's 4.208 V charge target — the protector is
a genuine second layer, not a nuisance trip. UVP at 2.800 V is a sane floor for the M35A.

Support components per the typical application schematic: **0.1 µF**, **2.2 kΩ**,
**330 Ω**, and an optional 5 MΩ gate-source resistor.

### ⚠ FET selection — the constraint that rules out the obvious parts

**OCD is sensed as a voltage across the FETs, not by a sense resistor.** The trip current
is therefore set entirely by the FETs' on-resistance:

```text
I_trip  =  VOCD / (2 × RDS(on))  =  100 mV / (2 × RDS(on))
```

Our worst-case legitimate discharge, which must **not** trip:

| | |
|---|---|
| 5 V rail transient target (spec §22) | 2.0 A → 10 W |
| Buck-boost efficiency (boost region) | ~88% |
| Cell voltage, worst case | 3.2 V |
| **Peak cell current** | **≈ 3.55 A** |
| Target trip point, ~1.7× margin | **≈ 6 A** |
| **Required total RDS(on)** | **≤ 16.7 mΩ** → **≤ 8.3 mΩ per FET** |

**This rules out the two parts every reference design reaches for:**

| Candidate | RDS(on) | Resulting trip | Verdict |
|---|---|---|---|
| AO8810 | 23 mΩ @ VGS 2.5 V | **≈ 2.2 A** | ❌ nuisance-trips on WiFi transients |
| FS8205A | 25 mΩ @ VGS 4.5 V | **≈ 2.0 A** | ❌ same, worse |
| AON7534 (×2, singles) | 8.5 mΩ @ VGS 4.5 V | ≈ 5.9 A | 🟡 viable, needs VGS derating check |

⬜ **Open.** Final FET selection needs a common-drain dual (or two singles) at **≤ 8.3 mΩ
measured at the gate drive the BQ29700 actually delivers** — `VOH` is only **3.4–3.7 V**
(SLUSBU9 §7.5), *not* the 4.5 V or 10 V at which datasheets headline their RDS(on). The
RDS(on)-vs-VGS curve must be read at 3.4 V, and the number will be worse than the headline.

Reading RDS(on) at the headline VGS instead of the actual gate drive is precisely how this
circuit gets designed wrong, and it is why the AO8810 appears acceptable until the
arithmetic is done.

---

## Summary of what is still open

| Item | Blocking |
|---|---|
| ⬜ CH224K VDD and VBUS series resistor values | schematic |
| ⬜ Protection FET part, verified at VGS = 3.4 V | schematic |
| ⬜ VBUS TVS and CC-line ESD parts | schematic |
| ⬜ 5 V load switch for SW1 | schematic |
| ⬜ M35A charging temperature window vs the assumed 0–45 °C | confirmation only — current choice is the conservative one |
