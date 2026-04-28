#!/usr/bin/env python3
"""Apply spec 9.1 scoring to data/companies.csv. Adds/overwrites `score` and `tier` columns.

Score components (max 100):
- VLA: vla_active=30, vla_likely=20, vla_possible=8
- Pain: 0=0, 1=5, 2=12, 3=20
- Spend: a=25, b=15, c=5
- Lockin: lockin_open=10, lockin_generic_cloud=8, lockin_jetson_only=8, lockin_unknown=4, lockin_diy=0
- Openness: 0=0, 1=5, 2=10, 3=15

Tiers: 1 = 70+, 2 = 45-69, 3 = 25-44, drop = <25
Tier 1 cap = 20 (highest scores).
Tier 1 with lockin_diy is downgraded to Tier 2 (spec 11.4).
"""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

VLA_WEIGHTS = {"vla_active": 30, "vla_likely": 20, "vla_possible": 8, "vla_no": 0, "": 0}
PAIN_WEIGHTS = {0: 0, 1: 5, 2: 12, 3: 20}
SPEND_WEIGHTS = {"a": 25, "b": 15, "c": 5, "": 0}
LOCKIN_WEIGHTS = {
    "lockin_open": 10,
    "lockin_generic_cloud": 8,
    "lockin_jetson_only": 8,
    "lockin_unknown": 4,
    "lockin_diy": 0,
    "": 0,
}
OPENNESS_WEIGHTS = {0: 0, 1: 5, 2: 10, 3: 15}


def to_int(x, default=0):
    try:
        return int(float(x))
    except Exception:
        return default


def score_row(r: dict) -> int:
    s = 0
    s += VLA_WEIGHTS.get(r.get("vla_classification", ""), 0)
    s += PAIN_WEIGHTS.get(to_int(r.get("pain_score")), 0)
    s += SPEND_WEIGHTS.get((r.get("spend_tier") or "").lower(), 0)
    s += LOCKIN_WEIGHTS.get(r.get("lockin_status", ""), 0)
    s += OPENNESS_WEIGHTS.get(to_int(r.get("openness_score")), 0)
    return s


def tier_for(score: int) -> int:
    if score >= 70:
        return 1
    if score >= 45:
        return 2
    if score >= 25:
        return 3
    return 0  # drop


def main() -> None:
    path = DATA / "companies.csv"
    rows = list(csv.DictReader(open(path)))
    if not rows:
        print("no rows")
        return

    fieldnames = list(rows[0].keys())
    for col in ("score", "tier"):
        if col not in fieldnames:
            fieldnames.append(col)

    for r in rows:
        score = score_row(r)
        t = tier_for(score)
        # spec 11.4: no Tier 1 with lockin_diy
        if t == 1 and r.get("lockin_status") == "lockin_diy":
            t = 2
        # vla_no => drop
        if r.get("vla_classification") == "vla_no":
            t = 0
        r["score"] = score
        r["tier"] = t

    # Tier 1 cap = 20
    tier1 = sorted([r for r in rows if r["tier"] == 1], key=lambda x: -x["score"])
    if len(tier1) > 20:
        for r in tier1[20:]:
            r["tier"] = 2

    # Drop tier 0 from output
    kept = [r for r in rows if to_int(r.get("tier")) > 0]

    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in kept:
            w.writerow(r)

    by_tier = {}
    for r in kept:
        by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1
    print(f"scored {len(rows)}, kept {len(kept)}: " + ", ".join(f"T{k}={v}" for k, v in sorted(by_tier.items())))


if __name__ == "__main__":
    main()
