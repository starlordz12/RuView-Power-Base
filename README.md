# RuView Power Base

A removable 18650 + USB-C PD power carrier for the **YD-ESP32-S3 N8R8** development
board, built as a RuView Wi-Fi sensing node base. Target: **PCBWay full turnkey PCBA,
quantity 5.**

The ESP32 plugs into two 22-position gold sockets and is removable without tools. The
carrier holds one replaceable 18650, negotiates 9 V USB-C Power Delivery, runs the node
while charging, and reports real state of charge from a dedicated fuel gauge.

## Status

**Stage A — validation. Not manufacturing-ready. Do not order.**

See [docs/STATUS.md](docs/STATUS.md) for the current gate position and what is blocking.

## Start here

| Document | What it is |
|---|---|
| [docs/STATUS.md](docs/STATUS.md) | Current position, open blockers, next action |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Where this build deliberately departs from the V1.1 spec, and why |
| [docs/PART_SELECTION.md](docs/PART_SELECTION.md) | Stage A part validation — exact MPNs, lifecycle status, sourcing |
| [spec/](spec/) | The original V1.1 specification, preserved verbatim as the requirements baseline |

## Hardware target

The host board is a **YD-ESP32-S3 Core Board, N8R8, revision V1.3 (2022)** — the
VCC-GND Studio board, *not* a genuine Espressif ESP32-S3-DevKitC-1. The V1.1 spec was
written against the Espressif board and instructs the designer to use Espressif's
official DXF as mechanical truth. **That instruction does not apply here.** See
[DECISIONS.md](docs/DECISIONS.md#d1).

## Architecture

```text
USB-C receptacle
      |  CC1/CC2 -> CH224K PD sink trigger (resistor-set 9 V, 5 V fallback)
      v  VBUS 5 V or 9 V
  input protection (TVS on VBUS, ESD on CC)
      v
  BQ25895 1S switch-mode charger + NVDC power path
      |                              |
      v BAT                          v SYS
  18650 (Keystone 1043P)      TPS63070 buck-boost -> 5.0 V -> load switch -> ESP32 5V
      |
      +-- MAX17048 fuel gauge (I2C)
      +-- 10k NTC at cell body -> BQ25895 TS
```

Four state-of-charge LEDs and one status LED are driven directly from ESP32 GPIOs.

## Repository layout

```text
docs/         design record, decisions, part validation, bring-up and test plans
hardware/
  kicad/      schematic and PCB source
  lib/        project-local symbols and footprints (parts KiCad does not ship)
  fabrication/  gerbers, drill, fab drawing
  assembly/   BOM, CPL, assembly drawings, schematic PDF
  mechanical/ board STEP/DXF and YD-ESP32-S3 reference drawings
firmware/     ESP32 battery-monitor support module
spec/         original V1.1 requirements specification
tools/        build and export scripts
```

## Safety

This board charges a lithium-ion cell. Nothing here is manufacturing-ready until every
item in the quality gate passes — see [docs/STATUS.md](docs/STATUS.md). Do not order
assembled boards against an unverified revision of this design.
