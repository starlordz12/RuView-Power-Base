# CLAUDE.md — RuView Power Base

Working rules for Claude Code in this repository.

## Reading order

1. This file
2. `docs/STATUS.md` — current stage, blocking gate items, next action
3. `docs/DECISIONS.md` — where we deliberately depart from the V1.1 spec
4. `docs/PART_SELECTION.md` — validated MPNs
5. `spec/RuView_Power_Base_PCBWay_Claude_Code_Spec_V1.1.md` — the requirements baseline,
   read last and only when the above do not answer the question

## This board charges a lithium-ion cell

That constrains how work is done here more than anything else in this file.

- **Never mark the design manufacturing-ready without the spec §39 gate passing.** All 22
  items, individually evidenced. A green ERC and DRC is not that gate — it is two of its
  items.
- **Never infer an electrical limit from a similar part, a reference board, or a trigger
  board schematic found online.** Read the vendor datasheet. Cite the page.
- **The charger's default register state is a real operating state**, not a transient one.
  The board sits in it whenever the ESP32 is absent, held in reset, or crashed. Verify it
  is safe rather than assuming firmware will always be there to fix it.
- Do not raise the charge current above the validated 2.0 A target because a datasheet
  maximum permits it. Spec §30.1 is explicit about this.

## The host board is a YD-ESP32-S3 V1.3, not an Espressif DevKitC-1

The V1.1 spec says to use Espressif's official DXF as mechanical truth. **That instruction
is wrong for this hardware** — see `docs/DECISIONS.md` D1. Use VCC-GND's drawings, and
prefer a measurement of the user's physical board over any published drawing, because
V1.3 is an undocumented intermediate revision.

Do not guess header spacing or pin order from a photograph, a clone listing, or the
official Espressif pinout.

## Verification rules

- **An assertion nobody has watched fail is a guess.** This applies to ERC and DRC rule
  sets too: a rule set that passes a board it should have rejected is worse than none.
- **Visually open every exported gerber before calling an export done.** Spec §24 Stage F
  requires it. A clean `kicad-cli` exit code is not an inspection.
- Re-confirm part lifecycle status immediately before the order, not once at selection.
- State what was *not* checked. An unverified item is an open item, not a passed one.

## Environment

- KiCad 10.0.6 — `%LOCALAPPDATA%\Programs\KiCad\10.0`
- `kicad-cli` — `%LOCALAPPDATA%\Programs\KiCad\10.0\bin\kicad-cli.exe`
- Never hard-code that path into a committed file; resolve it in `tools/`.

## Custom library parts

Project-local symbols and footprints live in `hardware/lib/`. Everything else comes from
KiCad stock. Currently custom: TPS63070 symbol, TPS63070 VQFN-HR-15 footprint, MAX17048
symbol. Adding to this list needs a reason recorded in `docs/DECISIONS.md`.

## Working style

Before editing, report: goal, current stage, files expected to change, acceptance check,
commands to run, known risks.

After editing: run the relevant checks, report exact results **and what was not tested**,
then update `docs/STATUS.md`. Keep commits small and single-purpose.

Commit style: `hw(schematic): ...`, `hw(pcb): ...`, `docs(decisions): ...`,
`fw(monitor): ...`, `tools(export): ...`.

## Authorship

The user is the sole author of record. Never add AI attribution to anything that reaches
GitHub — no `Co-Authored-By:` trailers, no "Generated with" lines in commits or PR bodies.

## Scope control

This is a power carrier board. Do not add: USB data routing, displays, extra sensors,
wireless charging, multi-cell support, or a second board variant — unless the spec calls
for it or the user asks.
