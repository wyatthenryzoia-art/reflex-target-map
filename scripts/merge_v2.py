#!/usr/bin/env python3
"""Append v2 scored batches to existing data/companies.csv (don't overwrite v1 rows).

Drops vla_no rows. Carries source URLs from data/universe_v2_new.csv into
data/sources.csv via field=universe_v2.
"""
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / "cache"
DATA = REPO / "data"

OUT_FIELDS = list(csv.DictReader(open(DATA / "companies.csv")).fieldnames)


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return s[:60]


def main() -> None:
    # load existing companies — these stay untouched
    existing = list(csv.DictReader(open(DATA / "companies.csv")))
    existing_ids = {r["company_id"] for r in existing}
    existing_names = {r["company_name"].lower().strip() for r in existing}
    print(f"existing companies (v1): {len(existing)}")

    # universe_v2_new gives us the canonical company_id mapping for each new row
    uv2 = {}
    if (DATA / "universe_v2_new.csv").exists():
        uv2 = {r["company_id"]: r for r in csv.DictReader(open(DATA / "universe_v2_new.csv"))}

    new_rows = []
    seen = set(existing_ids)
    dropped_vla_no = 0
    for f in sorted(CACHE.glob("scored_v2_batch_*.csv")):
        for r in csv.DictReader(open(f)):
            cid = (r.get("company_id") or "").strip()
            if not cid or cid in seen:
                continue
            seen.add(cid)
            if (r.get("vla_classification") or "").strip() == "vla_no":
                dropped_vla_no += 1
                continue
            # also drop if name collision with an existing company
            if r["company_name"].lower().strip() in existing_names:
                continue
            out = {k: (r.get(k, "") or "").strip() for k in OUT_FIELDS}
            out["company_id"] = cid
            out["company_name"] = r["company_name"].strip()
            out["domain"] = (r.get("domain") or "").strip()
            out["slug"] = slugify(out["company_name"])
            out["score"] = ""
            out["tier"] = ""
            new_rows.append(out)

    # write merged
    with open(DATA / "companies.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        w.writeheader()
        for r in existing:
            w.writerow(r)
        for r in new_rows:
            w.writerow(r)

    print(f"new (v2) rows added: {len(new_rows)}")
    print(f"dropped (vla_no): {dropped_vla_no}")
    print(f"total now: {len(existing) + len(new_rows)}")

    # add v2 source urls into sources.csv
    src_rows = list(csv.DictReader(open(DATA / "sources.csv")))
    seen_pairs = {(s["company_id"], s["url"]) for s in src_rows}
    added_urls = 0

    new_cids = {r["company_id"] for r in new_rows}
    # universe_v2_new has all_sources;
    for cid in new_cids:
        u = uv2.get(cid, {})
        urls = []
        if u.get("primary_source_url"):
            urls.append(u["primary_source_url"])
        for x in (u.get("all_sources", "") or "").split(";"):
            x = x.strip()
            if x:
                urls.append(x)
        for x in urls:
            if (cid, x) in seen_pairs:
                continue
            if x.startswith("http"):
                src_rows.append({"company_id": cid, "field": "universe_v2", "url": x})
                seen_pairs.add((cid, x))
                added_urls += 1

    # also collect URL fields from the scored CSV
    URL_FIELDS = [("vla_evidence_url", "vla_evidence_url"), ("pain_signal_url", "pain_signal_url"), ("lockin_evidence_url", "lockin_evidence_url")]
    for f in sorted(CACHE.glob("scored_v2_batch_*.csv")):
        for r in csv.DictReader(open(f)):
            cid = r.get("company_id", "")
            if cid not in new_cids:
                continue
            for field, key in URL_FIELDS:
                u = (r.get(key) or "").strip()
                if u and u.startswith("http") and (cid, u) not in seen_pairs:
                    src_rows.append({"company_id": cid, "field": field, "url": u})
                    seen_pairs.add((cid, u))
                    added_urls += 1
            for u in (r.get("extra_source_urls", "") or "").split("|"):
                u = u.strip()
                if u and u.startswith("http") and (cid, u) not in seen_pairs:
                    src_rows.append({"company_id": cid, "field": "extra", "url": u})
                    seen_pairs.add((cid, u))
                    added_urls += 1

    with open(DATA / "sources.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_id", "field", "url"])
        w.writeheader()
        for r in src_rows:
            w.writerow(r)
    print(f"added URLs to sources.csv: {added_urls}")


if __name__ == "__main__":
    main()
