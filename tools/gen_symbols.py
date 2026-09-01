#!/usr/bin/env python3
"""Generate hardware/lib/RuView.kicad_sym.

Three parts KiCad does not ship. Pin data is transcribed from the vendor
datasheets cited against each part; do not edit the generated library by hand,
edit this file and re-run it.

    python tools/gen_symbols.py

Run tools/check_symbols.py afterwards to verify the result loads in KiCad.
"""
import io
import os

LIB_VERSION = "20251024"

# ---------------------------------------------------------------------------
# Pin tables. (number, name, electrical_type, side)
# side: L=left  R=right  T=top  B=bottom
# ---------------------------------------------------------------------------

TPS630701 = dict(
    name="TPS630701RNMR",
    ref="U",
    value="TPS630701RNMR",
    footprint="RuView:Texas_RNM_VQFN-HR-15_2.5x3mm_P0.5mm",
    datasheet="https://www.ti.com/lit/ds/symlink/tps63070.pdf",
    description="Buck-boost converter, fixed 5.0 V output, 2 A, VQFN-HR-15",
    keywords="buck-boost fixed 5V regulator TI",
    fp_filters="*VQFN-HR*15*2.5x3mm*",
    # SLVSC58B section 6, Pin Configuration and Functions
    pins=[
        ("12", "VIN", "power_in", "L"),
        ("13", "VIN", "power_in", "L"),
        ("14", "EN", "input", "L"),
        ("1", "PS/SYNC", "input", "L"),
        ("15", "VSEL", "input", "L"),
        ("11", "L1", "passive", "L"),
        ("9", "L2", "passive", "R"),
        ("7", "VOUT", "power_out", "R"),
        ("8", "VOUT", "power_out", "R"),
        ("5", "FB", "input", "R"),
        ("6", "FB2", "output", "R"),
        ("2", "PG", "open_collector", "R"),
        ("3", "VAUX", "passive", "R"),
        ("4", "GND", "power_in", "B"),
        ("10", "PGND", "power_in", "B"),
    ],
)

MAX17048 = dict(
    name="MAX17048",
    ref="U",
    value="MAX17048G+T10",
    footprint="Package_DFN_QFN:DFN-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm",
    datasheet="https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf",
    description="1-cell ModelGauge Li+ fuel gauge, I2C, TDFN-8-EP 2x2mm",
    keywords="fuel gauge battery SOC ModelGauge I2C Maxim ADI",
    fp_filters="DFN*1EP*2x2mm*P0.5mm*",
    # Datasheet Rev, Pin/Bump Configurations, TDFN column (verified against the
    # ADI datasheet directly - the WLP bump map is a DIFFERENT order.)
    pins=[
        ("2", "CELL", "input", "L"),
        ("1", "CTG", "passive", "L"),
        ("7", "SCL", "input", "R"),
        ("8", "SDA", "bidirectional", "R"),
        ("5", "~{ALRT}", "open_collector", "R"),
        ("6", "QSTRT", "input", "R"),
        ("3", "VDD", "power_in", "T"),
        ("4", "GND", "power_in", "B"),
        ("9", "EP", "passive", "B"),
    ],
)

AP9214L = dict(
    name="AP9214L",
    ref="U",
    value="AP9214L",
    footprint="RuView:Diodes_U-DFN2535-6",
    datasheet="https://www.diodes.com/assets/Datasheets/AP9214L.pdf",
    description="1-cell Li+ protection IC with integrated dual common-drain NMOS, U-DFN2535-6",
    keywords="battery protection 1S lithium overcharge overdischarge Diodes",
    fp_filters="*U-DFN2535*",
    # DS38413, Pin Descriptions, Pin-out Option 1.
    # EP is the common drain of both FETs and is left electrically OPEN.
    pins=[
        ("3", "VDD", "power_in", "L"),
        ("2", "VSS", "power_in", "L"),
        ("1", "S1", "passive", "R"),
        ("6", "S2", "passive", "R"),
        ("4", "VM", "passive", "R"),
        ("5", "NC", "no_connect", "R"),
        ("7", "EP", "passive", "B"),
    ],
)

PARTS = [TPS630701, MAX17048, AP9214L]

GRID = 2.54
PIN_LEN = 2.54


def _prop(name, value, x, y, hide=False, justify=None):
    j = f"\n\t\t\t\t(justify {justify})" if justify else ""
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (
        f'\t\t(property "{name}" "{value}"\n'
        f"\t\t\t(at {x} {y} 0)\n"
        f"\t\t\t(show_name no)\n"
        f"\t\t\t(do_not_autoplace no){h}\n"
        f"\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t){j}\n\t\t\t)\n"
        f"\t\t)\n"
    )


def _pin(number, name, etype, x, y, rot):
    return (
        f"\t\t\t(pin {etype} line\n"
        f"\t\t\t\t(at {x} {y} {rot})\n"
        f"\t\t\t\t(length {PIN_LEN})\n"
        f'\t\t\t\t(name "{name}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n'
        f'\t\t\t\t(number "{number}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n'
        f"\t\t\t)\n"
    )


def build(part):
    sides = {s: [p for p in part["pins"] if p[3] == s] for s in "LRTB"}
    # Body sized so every pin lands on grid with a little headroom.
    half_h = max(len(sides["L"]), len(sides["R"]), 2) * GRID / 2 + GRID / 2
    half_w = max(len(sides["T"]), len(sides["B"]), 2) * GRID / 2 + 2 * GRID
    half_w = max(half_w, 3 * GRID)
    # Vertical pin names run up into the body; without extra height they collide
    # with the horizontal names on the left and right sides.
    if sides["T"] or sides["B"]:
        half_h += GRID
        half_w += GRID

    out = [
        f'\t(symbol "{part["name"]}"\n'
        "\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n"
        "\t\t(in_pos_files yes)\n\t\t(duplicate_pin_numbers_are_jumpers no)\n"
    ]
    out.append(_prop("Reference", part["ref"], -half_w, half_h + 1.27, justify="left"))
    out.append(_prop("Value", part["value"], half_w - 6.0, half_h + 1.27, justify="left"))
    out.append(_prop("Footprint", part["footprint"], 0, -half_h - 5.08, hide=True))
    out.append(_prop("Datasheet", part["datasheet"], 0, half_h + 5.08, hide=True))
    out.append(_prop("Description", part["description"], 0, 0, hide=True))
    out.append(_prop("ki_keywords", part["keywords"], 0, 0, hide=True))
    out.append(_prop("ki_fp_filters", part["fp_filters"], 0, 0, hide=True))

    out.append(f'\t\t(symbol "{part["name"]}_1_1"\n')
    out.append(
        f"\t\t\t(rectangle\n\t\t\t\t(start {-half_w} {half_h})\n\t\t\t\t(end {half_w} {-half_h})\n"
        "\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n"
        "\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)\n\t\t\t)\n"
    )

    def span(n):
        return [(n - 1 - 2 * i) * GRID / 2 for i in range(n)]

    for i, (num, nm, et, _) in enumerate(sides["L"]):
        y = span(len(sides["L"]))[i]
        out.append(_pin(num, nm, et, -half_w - PIN_LEN, y, 0))
    for i, (num, nm, et, _) in enumerate(sides["R"]):
        y = span(len(sides["R"]))[i]
        out.append(_pin(num, nm, et, half_w + PIN_LEN, y, 180))
    for i, (num, nm, et, _) in enumerate(sides["T"]):
        x = span(len(sides["T"]))[i]
        out.append(_pin(num, nm, et, -x, half_h + PIN_LEN, 270))
    for i, (num, nm, et, _) in enumerate(sides["B"]):
        x = span(len(sides["B"]))[i]
        out.append(_pin(num, nm, et, -x, -half_h - PIN_LEN, 90))

    out.append("\t\t)\n\t)\n")
    return "".join(out)


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dest = os.path.join(here, "hardware", "lib", "RuView.kicad_sym")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    body = "".join(build(p) for p in PARTS)
    text = (
        "(kicad_symbol_lib\n"
        f"\t(version {LIB_VERSION})\n"
        '\t(generator "ruview_gen_symbols")\n'
        '\t(generator_version "10.0")\n'
        f"{body})\n"
    )
    io.open(dest, "w", encoding="utf-8", newline="\n").write(text)
    total = sum(len(p["pins"]) for p in PARTS)
    print(f"wrote {dest}")
    print(f"  {len(PARTS)} symbols, {total} pins")
    for p in PARTS:
        print(f"    {p['name']:16s} {len(p['pins']):2d} pins")


if __name__ == "__main__":
    main()
