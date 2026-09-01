# YD-ESP32-S3 vendor reference

Source: [vcc-gnd/YD-ESP32-S3](https://github.com/vcc-gnd/YD-ESP32-S3), path
`5-public-YD-ESP32-S3-Hardware info/`.

Fetched 2026-08-31:

| File | Size | Use |
|---|---|---|
| `ESP32-S3-Metric.pdf` | 116 KB | dimensioned mechanical drawing — the mechanical source of truth |
| `YD-ESP32-S3-SCH-V1.4.pdf` | 429 KB | board schematic (V1.4; user's board is V1.3) |

**These files are not committed.** They are VCC-GND's, redistribution terms are unstated,
and they are one `gh api` call away. Everything this project needs from them is extracted
into [`docs/MECHANICAL.md`](../../../docs/MECHANICAL.md).

To re-fetch:

```bash
D="5-public-YD-ESP32-S3-Hardware%20info"
for f in ESP32-S3-Metric.pdf YD-ESP32-S3-SCH-V1.4.pdf; do
  gh api "repos/vcc-gnd/YD-ESP32-S3/contents/$D/$(python -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$f")" \
    -H "Accept: application/vnd.github.raw" > "$f"
done
```
