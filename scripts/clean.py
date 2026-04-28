#!/usr/bin/env python3
"""Manual cleanup pass: drop rows flagged by scoring agents as
acquisitions, dead companies, false positives, competitors, or non-commercial.
"""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

DROP_NAMES = {
    "Aurorain": "abandoned (GH activity stopped 2024)",
    "BAAI": "gov-backed research non-profit, not commercial ICP",
    "K-Scale Labs": "founder shut down Nov 2025, IP open-sourced",
    "Covariant": "Amazon acquihired founders + 25% staff Aug 2024",
    "Vayu Robotics": "acquired by Serve Robotics",
    "Hebbian Robotics": "builds own openpi-flash inference — likely competitor, not customer",
    "Robust.AI": "founder publicly anti-foundation-model — wrong fit",
    # also catch any false positives that slipped through
    "Astria": "image-generation SaaS, not robotics",
    "Codeflash": "Python/JS code-optimization SaaS, not robotics",
    "Forerunner.ai": "3D reconstruction iOS app, not robotics",
}


def main() -> None:
    rows = list(csv.DictReader(open(DATA / "companies.csv")))
    fieldnames = list(rows[0].keys())
    kept = []
    dropped = []
    for r in rows:
        if r["company_name"] in DROP_NAMES:
            dropped.append((r["company_name"], DROP_NAMES[r["company_name"]]))
            continue
        kept.append(r)

    with open(DATA / "companies.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in kept:
            w.writerow(r)

    print(f"dropped {len(dropped)}, kept {len(kept)}")
    for n, reason in dropped:
        print(f"  - {n}: {reason}")


if __name__ == "__main__":
    main()
