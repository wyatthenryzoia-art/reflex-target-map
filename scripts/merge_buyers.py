#!/usr/bin/env python3
"""Merge cache/buyers_*.csv into data/buyers.csv. Add buyer URLs to data/sources.csv."""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / "cache"
DATA = REPO / "data"

BUYER_FIELDS = [
    "company_id", "buyer_name", "buyer_title", "buyer_linkedin_url",
    "buyer_x_handle", "buyer_github", "buyer_recent_signal",
    "buyer_signal_url", "buyer_signal_date", "warm_intro_path",
    "suggested_first_dm_hook", "buyer_verified",
]


def main() -> None:
    rows = []
    for f in sorted(CACHE.glob("buyers_*.csv")):
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                rows.append({k: (r.get(k, "") or "").strip() for k in BUYER_FIELDS})
        print(f"loaded {f.name}: now {len(rows)}")

    # only keep buyers for live company IDs
    live_ids = {c["company_id"] for c in csv.DictReader(open(DATA / "companies.csv"))}
    rows = [r for r in rows if r["company_id"] in live_ids]

    with open(DATA / "buyers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=BUYER_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {len(rows)} buyer rows")

    # add buyer URLs to sources.csv
    src_rows = list(csv.DictReader(open(DATA / "sources.csv")))
    seen = {(s["company_id"], s["url"]) for s in src_rows}
    for b in rows:
        for field in ["buyer_linkedin_url", "buyer_signal_url"]:
            u = b.get(field, "").strip()
            if u and u.startswith("http") and (b["company_id"], u) not in seen:
                seen.add((b["company_id"], u))
                src_rows.append({"company_id": b["company_id"], "field": field, "url": u})

    with open(DATA / "sources.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_id", "field", "url"])
        w.writeheader()
        for s in src_rows:
            w.writerow(s)
    print(f"sources.csv: {len(src_rows)} rows total after adding buyer URLs")

    # quick stats
    from collections import Counter
    verified = Counter(r["buyer_verified"] for r in rows)
    has_hook = sum(1 for r in rows if r["suggested_first_dm_hook"] and "no specific hook" not in r["suggested_first_dm_hook"].lower())
    has_warm = sum(1 for r in rows if r["warm_intro_path"] and r["warm_intro_path"] != "cold")
    has_li = sum(1 for r in rows if r["buyer_linkedin_url"])
    print(f"verified breakdown: {dict(verified)}")
    print(f"  with linkedin_url: {has_li}/{len(rows)}")
    print(f"  with specific hook: {has_hook}/{len(rows)}")
    print(f"  with warm intro path: {has_warm}/{len(rows)}")


if __name__ == "__main__":
    main()
