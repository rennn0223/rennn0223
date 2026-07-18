#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53-week heatmap SVG.

Rounded boxes slide in diagonally (CSS keyframes that play on load,
then freeze — no looping), with a Less→More legend and a stats footer.

Usage: python scripts/render_heatmap_svg.py
Writes: contrib-heatmap.svg at the repo root.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end)

CELL, GAP = 12, 3
STEP = CELL + GAP
LEFT, TOP = 34, 42          # room for day / month labels
PAD = 16
BG, BORDER, DIM, FG = "#0d1117", "#30363d", "#8b949e", "#c9d1d9"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main() -> None:
    data = json.loads(DATA.read_text())
    days = data["days"]

    # column = week; GitHub's calendar starts weeks on Sunday
    weeks: list[list[dict]] = [[]]
    for d in days:
        dow = (date.fromisoformat(d["date"]).weekday() + 1) % 7  # Sun=0
        if dow == 0 and weeks[-1]:
            weeks.append([])
        d["dow"] = dow
        weeks[-1].append(d)

    n_weeks = len(weeks)
    grid_w = n_weeks * STEP - GAP
    width = PAD + LEFT + grid_w + PAD
    height = TOP + 7 * STEP - GAP + 58
    best = data["best_day"]
    neon_cut = max(10, best["count"])  # level 5: only the very best days

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{data["total"]} contributions in the last year">',
        '<style>',
        'text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:11px}',
        '.c{opacity:0;animation:drop .3s ease-out forwards}',
        '@keyframes drop{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}',
        '.f{opacity:0;animation:fade .6s ease-out forwards}',
        '@keyframes fade{from{opacity:0}to{opacity:1}}',
        '</style>',
        f'<rect width="{width}" height="{height}" rx="12" fill="{BG}"/>',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="none" stroke="{BORDER}"/>',
    ]

    # month labels (at each month's first week)
    seen = set()
    for w, week in enumerate(weeks):
        m = date.fromisoformat(week[0]["date"]).month
        if m not in seen:
            seen.add(m)
            if w == 0 and len(week) < 4:
                continue  # partial first column: label would crowd the next one
            parts.append(f'<text class="f" x="{PAD + LEFT + w * STEP}" y="{TOP - 10}" '
                         f'fill="{DIM}">{MONTHS[m - 1]}</text>')

    for label, dow in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        parts.append(f'<text class="f" x="{PAD}" y="{TOP + dow * STEP + CELL - 2}" '
                     f'fill="{DIM}">{label}</text>')

    max_delay = 0.0
    for w, week in enumerate(weeks):
        for d in week:
            level = 5 if d["count"] >= neon_cut and d["count"] > 0 else min(d["level"], 4)
            delay = (w + d["dow"]) * 0.018  # diagonal, line-after-line reveal
            max_delay = max(max_delay, delay)
            x = PAD + LEFT + w * STEP
            y = TOP + d["dow"] * STEP
            parts.append(
                f'<rect class="c" style="animation-delay:{delay:.3f}s" '
                f'x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" '
                f'fill="{PALETTE[level]}"><title>{d["count"]} on {d["date"]}</title></rect>'
            )

    # footer: stats left, legend right — fade in after the reveal
    fy = height - 22
    fstyle = f' style="animation-delay:{max_delay + 0.3:.2f}s"'
    stats = (f'{data["total"]:,} contributions in the last year'
             f' · streak {data["current_streak"]}d (best {data["longest_streak"]}d)'
             f' · best day {best["count"]}')
    parts.append(f'<text class="f"{fstyle} x="{PAD + LEFT}" y="{fy}" fill="{FG}">{stats}</text>')

    lx = width - PAD - 6 * (CELL + 4) - 78
    parts.append(f'<g class="f"{fstyle}><text x="{lx - 34}" y="{fy}" fill="{DIM}">Less</text>')
    for i, c in enumerate(PALETTE):
        parts.append(f'<rect x="{lx + i * (CELL + 4)}" y="{fy - CELL + 2}" '
                     f'width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>')
    parts.append(f'<text x="{lx + 6 * (CELL + 4) + 6}" y="{fy}" fill="{DIM}">More</text></g>')

    parts.append('</svg>')
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({n_weeks} weeks, {width}x{height})")


if __name__ == "__main__":
    main()
