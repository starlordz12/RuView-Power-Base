#!/usr/bin/env python3
"""Verify hardware/lib/RuView.kicad_sym.

Three checks, in increasing strength:

1. KiCad itself can load the library (kicad-cli sym export svg).
2. Every pin declared in tools/gen_symbols.py appears exactly once.
3. No two pins of a symbol occupy the same coordinate — a silent killer,
   because KiCad renders overlapping pins on top of each other and ERC will
   happily net them together.

Each check has been watched to FAIL against a deliberately broken control.

    python tools/check_symbols.py
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_symbols  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "hardware", "lib", "RuView.kicad_sym")


def find_cli():
    for c in (
        os.environ.get("KICAD_CLI"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\KiCad\10.0\bin\kicad-cli.exe"),
        shutil.which("kicad-cli"),
    ):
        if c and os.path.exists(c):
            return c
    return None


def split_symbols(text):
    """Return {symbol_name: body} for top-level symbols only."""
    out = {}
    for m in re.finditer(r'\(symbol "([^"]+)"', text):
        name = m.group(1)
        if name.endswith("_1_1"):
            continue
        i, depth = m.start(), 0
        j = i
        while True:
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out[name] = text[i : j + 1]
    return out


def main():
    fails = []

    if not os.path.exists(LIB):
        print(f"FAIL  library missing: {LIB}")
        return 1
    text = io.open(LIB, encoding="utf-8", newline="").read()

    # --- 1. KiCad can load it -------------------------------------------------
    cli = find_cli()
    if not cli:
        print("WARN  kicad-cli not found; skipping the load check")
    else:
        tmp = tempfile.mkdtemp()
        try:
            r = subprocess.run(
                [cli, "sym", "export", "svg", "--output", tmp, LIB],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                fails.append(f"kicad-cli could not load the library: {r.stdout.strip()} {r.stderr.strip()}")
            else:
                print(f"PASS  kicad-cli loaded and plotted the library")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # --- 2 & 3. per-symbol pin checks ----------------------------------------
    bodies = split_symbols(text)
    for part in gen_symbols.PARTS:
        name = part["name"]
        if name not in bodies:
            fails.append(f"{name}: symbol missing from library")
            continue
        body = bodies[name]

        numbers = re.findall(r'\(number "([^"]+)"', body)
        expected = [p[0] for p in part["pins"]]
        missing = sorted(set(expected) - set(numbers))
        dupes = sorted({n for n in numbers if numbers.count(n) > 1})
        if missing:
            fails.append(f"{name}: pins absent from library: {missing}")
        if dupes:
            fails.append(f"{name}: duplicate pin numbers: {dupes}")
        if not missing and not dupes:
            print(f"PASS  {name}: all {len(expected)} pins present, none duplicated")

        coords = re.findall(r"\(pin [a-z_]+ line\s*\n\s*\(at ([-\d.]+) ([-\d.]+)", body)
        seen = {}
        for x, y in coords:
            seen.setdefault((x, y), 0)
            seen[(x, y)] += 1
        stacked = [k for k, v in seen.items() if v > 1]
        if stacked:
            fails.append(f"{name}: pins stacked at identical coordinates: {stacked}")
        else:
            print(f"PASS  {name}: no two pins share a coordinate")

    print()
    if fails:
        for f in fails:
            print(f"FAIL  {f}")
        return 1
    print("All symbol checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
