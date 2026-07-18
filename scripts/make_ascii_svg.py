#!/usr/bin/env python3
"""Convert source-photo.jpg into a self-typing ASCII-portrait SVG.

Pipeline: crop → CLAHE local contrast → median denoise → tone posterize
(6 levels) + Sobel edge lines, then map onto a short glyph ramp. Dark
glyphs print on a light paper card so the portrait reads like ink —
hair dark, face light. Every row wipes in left-to-right with a block
cursor riding the edge, staggered top to bottom. Plays once, freezes.

Usage: python scripts/make_ascii_svg.py
Writes: ren-ascii.svg at the repo root.
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-photo.jpg"
OUT = ROOT / "ren-ascii.svg"

GLYPHS = " .:=*#"       # tone levels, sparse -> dense (ink on paper)
CROP = (0.08, 0.02, 0.92, 0.86)  # trim edges and the busy collar area
COLS = 110
CLAHE_CLIP = 3.0
MEDIAN = 5
EDGE_AMT = 0.65          # how strongly feature lines darken the tone
THRESHOLDS = [0.15, 0.34, 0.54, 0.74, 0.88]

CHAR_W, CHAR_H = 6.0, 10.0
PAD = 18
FG = "#1f2328"           # ink
BG = "#f6f8fa"           # paper
BORDER = "#d0d7de"

ROW_DUR = 0.35
STAGGER = 0.05


def image_to_grid() -> list[str]:
    img = Image.open(SRC).convert("L")
    w, h = img.size
    l, t, r, b = CROP
    a = np.asarray(img.crop((int(w * l), int(h * t), int(w * r), int(h * b))))

    x = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(8, 8)).apply(a)
    x = cv2.medianBlur(x, MEDIAN)
    gx = cv2.Sobel(x, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(x, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    mag /= max(np.percentile(mag, 99), 1e-6)

    rows = round(COLS * (a.shape[0] / a.shape[1]) * (CHAR_W / CHAR_H))
    v = cv2.resize(x, (COLS, rows), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    e = np.clip(cv2.resize(mag, (COLS, rows), interpolation=cv2.INTER_AREA), 0, 1)
    ink = np.clip((1 - v) + EDGE_AMT * e, 0, 1)

    idx = np.zeros_like(ink, dtype=int)
    for t in THRESHOLDS:
        idx += (ink >= t).astype(int)
    return ["".join(GLYPHS[i] for i in row).rstrip() for row in idx]


def main() -> None:
    grid = image_to_grid()
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
        f'font-size="{CHAR_H + 1}px" font-weight="600" fill="{FG}" xml:space="preserve">'
    )
    for i, line in enumerate(grid):
        if not line:
            continue
        y_text = PAD + i * CHAR_H + CHAR_H - 2
        text = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # non-breaking spaces: some renderers (notably Safari) strip leading
        # regular spaces from <text> even with xml:space="preserve", which
        # shifts and stretches every row
        text = text.replace(" ", "&#160;")
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
            f'<set attributeName="opacity" to="0.7" begin="{begin:.3f}s"/>'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + full_w}" '
            f'dur="{ROW_DUR}s" begin="{begin:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.3f}s"/></rect>'
        )

    parts.append('</svg>')
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({rows} rows)")


if __name__ == "__main__":
    main()
