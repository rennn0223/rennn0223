#!/usr/bin/env python3
"""Convert source-prepped.png into a self-typing monochrome ASCII SVG.

Each pixel of a ~100-wide character grid picks a glyph from a density
ramp; every row wipes in left-to-right with a block cursor riding the
edge, staggered top to bottom. Prints once and freezes — no looping.

Usage: python scripts/make_ascii_svg.py
Writes: ren-ascii.svg at the repo root.
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "ren-ascii.svg"

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)

COLS = 100
CHAR_W, CHAR_H = 6.0, 10.0  # 10px monospace cell
PAD = 18
FG = "#c9d1d9"  # one light-gray fill: monochrome on purpose
BG = "#0d1117"
BORDER = "#30363d"

ROW_DUR = 0.35   # seconds for one row's wipe
STAGGER = 0.055  # delay between rows


def image_to_grid(path: Path) -> list[str]:
    img = Image.open(path).convert("L")
    rows = round(COLS * (img.height / img.width) * (CHAR_W / CHAR_H))
    img = img.resize((COLS, rows), Image.LANCZOS)
    px = np.asarray(img, dtype=np.float32) / 255.0
    idx = ((1.0 - px) * (len(RAMP) - 1)).round().astype(int)
    return ["".join(RAMP[i] for i in row).rstrip() for row in idx]


def main() -> None:
    grid = image_to_grid(SRC)
    rows = len(grid)
    width = round(COLS * CHAR_W + 2 * PAD)
    height = round(rows * CHAR_H + 2 * PAD)
    full_w = COLS * CHAR_W

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="ASCII portrait of rennn0223">',
        f'<rect width="{width}" height="{height}" rx="12" fill="{BG}"/>',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" '
        f'fill="none" stroke="{BORDER}"/>',
        '<defs>',
    ]

    for i, line in enumerate(grid):
        if not line:
            continue
        y = PAD + i * CHAR_H
        begin = i * STAGGER
        parts.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{y}" width="0" height="{CHAR_H}">'
            f'<animate attributeName="width" from="0" to="{full_w}" '
            f'dur="{ROW_DUR}s" begin="{begin:.3f}s" fill="freeze"/></rect></clipPath>'
        )
    parts.append('</defs>')

    parts.append(
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="{CHAR_H}px" fill="{FG}" xml:space="preserve">'
    )
    for i, line in enumerate(grid):
        if not line:
            continue
        y_text = PAD + i * CHAR_H + CHAR_H - 2
        text = (line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        parts.append(
            f'<g clip-path="url(#r{i})">'
            f'<text x="{PAD}" y="{y_text}" textLength="{len(line) * CHAR_W}">{text}</text>'
            f'</g>'
        )
    parts.append('</g>')

    # block cursor riding each row's wipe edge
    for i, line in enumerate(grid):
        if not line:
            continue
        y = PAD + i * CHAR_H
        begin = i * STAGGER
        end = begin + ROW_DUR
        parts.append(
            f'<rect x="{PAD}" y="{y}" width="{CHAR_W}" height="{CHAR_H}" fill="{FG}" opacity="0">'
            f'<set attributeName="opacity" to="0.85" begin="{begin:.3f}s"/>'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + full_w}" '
            f'dur="{ROW_DUR}s" begin="{begin:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.3f}s"/></rect>'
        )

    parts.append('</svg>')
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({rows} rows)")


if __name__ == "__main__":
    main()
