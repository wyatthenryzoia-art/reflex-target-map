#!/usr/bin/env python3
"""Trim the 249-row universe to a working set of ~120-150 high-confidence candidates,
ranked so parallel scoring agents can be batched.

Priority order for inclusion:
  Tier A (always keep): source_count >= 2 (cross-list overlap)
  Tier B (always keep): primary_source_type in {gh_fork, hf_org, hf_model_card}
  Tier C (keep top): rbr50 + vc_portfolio rows in robotics-VLA-relevant verticals
  Tier D (drop): single-source funding_news / industry_news / humanoid_tracker
       rows for companies in non-VLA-relevant verticals
"""
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

VLA_SIGNAL_TYPES = {"gh_fork", "hf_org", "hf_model_card"}

# rough vertical-relevance heuristic from company name and notes
RELEVANT_KEYWORDS = (
    "humanoid", "manipulat", "embodied", "agi", "foundation", "vla", "lerobot",
    "warehouse", "pick", "dexter", "surg", "agri", "harvest", "weeding",
    "drone", "aerial", "construction", "weld", "cleaning", "delivery",
    "kitchen", "chef", "labor",
)

NON_RELEVANT_KEYWORDS = (
    "consulting", "platform", "marketplace", "logistics software",
    "iot", "supply chain",
)


def relevance_score(row: dict) -> int:
    blob = (row["company_name"] + " " + row["notes"]).lower()
    s = 0
    for k in RELEVANT_KEYWORDS:
        if k in blob:
            s += 1
    for k in NON_RELEVANT_KEYWORDS:
        if k in blob:
            s -= 2
    return s


def classify(row: dict) -> str:
    if int(row["source_count"]) >= 2:
        return "A"
    if row["primary_source_type"] in VLA_SIGNAL_TYPES:
        return "B"
    if row["primary_source_type"] in ("rbr50", "vc_portfolio"):
        return "C"
    return "D"


def main() -> None:
    rows = list(csv.DictReader(open(DATA / "universe.csv")))
    for r in rows:
        r["_class"] = classify(r)
        r["_relevance"] = relevance_score(r)

    keep_a = [r for r in rows if r["_class"] == "A"]
    keep_b = [r for r in rows if r["_class"] == "B"]
    cands_c = sorted([r for r in rows if r["_class"] == "C"], key=lambda r: -r["_relevance"])
    cands_d = sorted([r for r in rows if r["_class"] == "D"], key=lambda r: -r["_relevance"])

    # Target ~130 in working set
    target = 130
    have = len(keep_a) + len(keep_b)
    needed = max(0, target - have)
    keep_c = cands_c[: int(needed * 0.7)]
    keep_d = cands_d[: max(0, needed - len(keep_c))]
    # only keep tier D rows whose relevance is positive
    keep_d = [r for r in keep_d if r["_relevance"] > 0]

    keep = keep_a + keep_b + keep_c + keep_d

    # remove the helper cols
    for r in keep:
        r.pop("_class", None)
        r.pop("_relevance", None)

    out_path = DATA / "working_set.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(keep[0].keys()))
        w.writeheader()
        for r in keep:
            w.writerow(r)

    print(f"working set: {len(keep)} ({len(keep_a)}A + {len(keep_b)}B + {len(keep_c)}C + {len(keep_d)}D)")
    print(f"out: {out_path}")


if __name__ == "__main__":
    main()
