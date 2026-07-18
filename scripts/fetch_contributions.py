#!/usr/bin/env python3
"""Fetch the public contribution calendar — no token needed.

GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions (the same fragment the
profile page uses). Parse the day cells and write data/contributions.json
with raw days plus derived stats.

Usage: python scripts/fetch_contributions.py
"""
import json
import re
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "rennn0223"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def parse_count(text: str) -> int:
    m = re.match(r"(\d+)", text.strip())
    return int(m.group(1)) if m else 0  # "No contributions on ..." -> 0


def main() -> None:
    resp = requests.get(URL, timeout=30, headers={"User-Agent": "profile-art"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # counts live in <tool-tip for="<cell id>"> elements
    tips = {t.get("for"): parse_count(t.get_text()) for t in soup.find_all("tool-tip")}

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append({
            "date": td["data-date"],
            "level": int(td.get("data-level", 0)),
            "count": tips.get(td.get("id"), 0),
        })
    if not days:
        raise SystemExit("no day cells parsed — GitHub markup may have changed")
    days.sort(key=lambda d: d["date"])

    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    # streaks (current streak ignores today if it's still empty)
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif d["date"] == date.today().isoformat():
            continue
        else:
            break

    monthly: dict[str, int] = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "username": USERNAME,
        "fetched": date.today().isoformat(),
        "total": total,
        "best_day": best,
        "current_streak": current,
        "longest_streak": longest,
        "monthly": monthly,
        "days": days,
    }, indent=1), encoding="utf-8")
    print(f"wrote {OUT}: {total} contributions over {len(days)} days")


if __name__ == "__main__":
    main()
