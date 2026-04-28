#!/usr/bin/env python3
"""Read data/link_check_log.csv. For each failed URL:
  1. If the URL belongs to a company that no longer exists in companies.csv (orphan), drop from sources.csv.
  2. Else null the referencing field in companies.csv (with note) and drop from sources.csv.
  3. Re-run link check; report.
"""
import csv
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

URL_FIELDS = ["vla_evidence_url", "pain_signal_url", "lockin_evidence_url"]


def is_failure(status: str) -> bool:
    if not status:
        return True
    if status.startswith("2"):
        return False
    if status.startswith("3"):
        return False
    # bot-blocked-but-valid (LinkedIn 999, Crunchbase 403, etc.) — keep
    if status.startswith("BOTBLOCK_OK"):
        return False
    return True


def main() -> None:
    # 1. load failed urls
    failed = set()
    with open(DATA / "link_check_log.csv") as f:
        for r in csv.DictReader(f):
            if is_failure(r["status"]):
                failed.add(r["url"])
    print(f"failed urls: {len(failed)}")

    # 2. live company ids
    companies = list(csv.DictReader(open(DATA / "companies.csv")))
    fieldnames = list(companies[0].keys())
    live_ids = {c["company_id"] for c in companies}

    # 3. update sources.csv: drop rows referencing failed urls + orphans
    sources = list(csv.DictReader(open(DATA / "sources.csv")))
    kept_sources = []
    dropped_orphan = 0
    dropped_failed = 0
    for s in sources:
        if s["company_id"] not in live_ids:
            dropped_orphan += 1
            continue
        if s["url"] in failed:
            dropped_failed += 1
            continue
        kept_sources.append(s)
    with open(DATA / "sources.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_id", "field", "url"])
        w.writeheader()
        for s in kept_sources:
            w.writerow(s)
    print(f"sources.csv: dropped {dropped_orphan} orphans + {dropped_failed} failed = {len(kept_sources)} kept")

    # 4. for each company, null any URL field that points to a failed url
    nulled = 0
    for c in companies:
        for field in URL_FIELDS:
            u = (c.get(field) or "").strip()
            if u and u in failed:
                c[field] = ""
                # also clear the corresponding quote/summary field if it's now orphaned
                if field == "vla_evidence_url":
                    c["vla_evidence_quote"] = ""
                elif field == "pain_signal_url":
                    pass  # keep pain_summary, it's in our voice
                nulled += 1

    with open(DATA / "companies.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for c in companies:
            w.writerow(c)
    print(f"companies.csv: nulled {nulled} broken field references")


if __name__ == "__main__":
    main()
