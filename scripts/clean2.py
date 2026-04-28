#!/usr/bin/env python3
"""Second cleanup pass: drop hyperscaler-corporates and promote weak-evidence
lockin_diy classifications to lockin_unknown where the evidence was a single
infra hire or an inferred ex-FAANG team composition.
"""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

DROP_NAMES = {
    "Tencent": "hyperscaler — self-serves, not Reflex ICP",
    "TeleAI / TeleHuman": "China Telecom corporate research arm, not commercial",
    "TeleAI": "China Telecom corporate research arm, not commercial",
    "Xiaomi Robotics": "Xiaomi-owned, parent runs own GPUs; not external-buyer ICP",
    "GigaAI": "Huawei Habo-funded PRC research lab; outreach friction high",
}

# Promote lockin_diy → lockin_unknown for these (evidence was inferential,
# not a direct DIY commitment) — opens them up for Tier 1 if score qualifies.
LOCKIN_PROMOTIONS = {
    "X Square Robot": "open-source model release ≠ DIY serving",
    "Flexion": "single ML-Infra hire is team buildout, not committed DIY",
    "Sereact": "agent had no signal — should be unknown not diy",
    "Genesis AI": "ex-FAANG team composition is inferential",
    "Galbot": "Genie Studio is product platform, no direct serving-stack signal",
    "Pollen Robotics": "HF-owned but openness signal — already lockin_open, leave",
}


def main() -> None:
    rows = list(csv.DictReader(open(DATA / "companies.csv")))
    fieldnames = list(rows[0].keys())
    kept = []
    dropped = []
    promoted = []

    for r in rows:
        if r["company_name"] in DROP_NAMES:
            dropped.append((r["company_name"], DROP_NAMES[r["company_name"]]))
            continue
        if r["company_name"] in LOCKIN_PROMOTIONS and r["lockin_status"] == "lockin_diy":
            r["lockin_status"] = "lockin_unknown"
            r["notes"] = (r["notes"] or "")[:200]
            r["notes"] += f" | lockin reclass: {LOCKIN_PROMOTIONS[r['company_name']]}"
            promoted.append(r["company_name"])
        kept.append(r)

    with open(DATA / "companies.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in kept:
            w.writerow(r)

    print(f"dropped {len(dropped)}:")
    for n, reason in dropped:
        print(f"  - {n}: {reason}")
    print(f"\npromoted lockin_diy → lockin_unknown: {len(promoted)}")
    for n in promoted:
        print(f"  - {n}")


if __name__ == "__main__":
    main()
