#!/usr/bin/env python3
"""Hand-author the neofetch-style info card SVG.

Each line fades and slides in on a short stagger so the panel looks
like it's printing next to the portrait. Plays once and freezes.
Set STATIC=1 to emit a frozen frame for local previews.

Usage: python scripts/make_info_card.py
Writes: info-card.svg at the repo root.
"""
import os
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

# ✏️ 這裡的內容可以自由修改
TITLE = "ren@github"
LINES = [
    ("Name",      "林書任 (Ren)"),
    ("GitHub",    "@rennn0223 · joined 2023"),
    ("Focus",     "always be building"),
    ("Stack",     "Python · JavaScript · Web"),
    ("Learning",  "one commit at a time"),
    ("Contact",   "ren910223@gmail.com"),
    ("Motto",     "一次一個 commit,慢慢變強"),
]

W = 490
BG, BORDER = "#0d1117", "#30363d"
KEY, VAL, DIM = "#7ee787", "#c9d1d9", "#8b949e"
DOTS = ["#ff5f57", "#febc2e", "#28c840"]
PALETTE = ["#ff7b72", "#ffa657", "#d2a8ff", "#79c0ff", "#7ee787", "#f2cc60", "#c9d1d9", "#484f58"]

ROW_H = 30
TOP = 92
STAGGER = 0.18


def main() -> None:
    n_rows = len(LINES) + 2  # separator + palette row
    height = TOP + n_rows * ROW_H + 26

    anim_css = "" if STATIC else (
        ".ln{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}"
        "to{opacity:1;transform:none}}"
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" aria-label="{TITLE} info card">',
        f'<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;'
        f'font-size:15px}}{anim_css}</style>',
        f'<rect width="{W}" height="{height}" rx="12" fill="{BG}"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="12" fill="none" stroke="{BORDER}"/>',
        # title bar
        f'<line x1="0" y1="44" x2="{W}" y2="44" stroke="{BORDER}"/>',
    ]
    for i, c in enumerate(DOTS):
        parts.append(f'<circle cx="{24 + i * 22}" cy="22" r="6.5" fill="{c}"/>')
    parts.append(f'<text x="{W / 2}" y="27" text-anchor="middle" fill="{DIM}">{TITLE}</text>')

    def row(i: int) -> tuple[float, str]:
        y = TOP + i * ROW_H
        style = "" if STATIC else f' style="animation-delay:{i * STAGGER:.2f}s"'
        return y, style

    y, style = row(0)
    parts.append(f'<g class="ln"{style}><text x="28" y="{y - 22}" fill="{VAL}">'
                 f'<tspan fill="{KEY}">{TITLE}</tspan></text>'
                 f'<text x="28" y="{y - 4}" fill="{DIM}">{"-" * len(TITLE)}</text></g>')

    for i, (key, val) in enumerate(LINES, start=1):
        y, style = row(i)
        val = val.replace("&", "&amp;").replace("<", "&lt;")
        parts.append(
            f'<g class="ln"{style}><text x="28" y="{y}">'
            f'<tspan fill="{KEY}">{key}</tspan>'
            f'<tspan fill="{DIM}" x="120">:</tspan>'
            f'<tspan fill="{VAL}" x="136">{val}</tspan></text></g>'
        )

    # neofetch colour swatches
    y, style = row(len(LINES) + 1)
    sw = "".join(
        f'<rect x="{28 + i * 26}" y="{y - 14}" width="26" height="14" fill="{c}"/>'
        for i, c in enumerate(PALETTE)
    )
    parts.append(f'<g class="ln"{style}>{sw}</g>')

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
