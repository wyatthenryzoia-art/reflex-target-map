#!/usr/bin/env python3
"""v2 cleanup: drop competitors, acquisitions, defunct, false positives flagged by v2 scorers."""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

DROP_NAMES = {
    # competitors / non-customers
    "Qualia": "competitor — pure VLA cloud infra play",
    # acquisitions / dead
    "Apium Swarm Robotics": "acquired by Red Cat Mar 2026",
    "Apium Swarm": "acquired by Red Cat Mar 2026",
    "Veo Robotics": "defunct — domain redirects to Symbotic",
    "RIVR": "acquired by Amazon Mar 2026",
    "Monarch Tractor": "assets acquired by Caterpillar Apr 2026, in wind-down",
    "Fauna Robotics": "reported acquired by Amazon",
    # not real companies
    "FusionCore": "solo open-source dev, pre-company",
    "ORQA": "research paper / project, not a standalone company",
    "Tokyo Robotics": "Yaskawa subsidiary — corporate exclusion",
    # No Barrier was misclassified — not robotics
    "No Barrier": "medical interpretation SaaS, not robotics",
    # acquired
    "Mentee Robotics": "acquired by Mobileye Jan 2026",
    # already excluded but might have slipped through
    "1X": "excluded mega-player",
    "Skild AI": "excluded mega-player",
    "Sanctuary AI": "excluded mega-player",
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
