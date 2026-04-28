#!/usr/bin/env python3
"""Merge cache/scored_batch_*.csv into data/companies.csv + data/sources.csv.

Output schema for data/companies.csv:
  company_id, slug, company_name, domain, one_line_description,
  founded_year, hq_country, hq_city,
  total_raised_usd, last_round_date, last_round_stage, last_round_size_usd,
  headcount, headcount_growth_6mo,
  vla_classification, vla_evidence_type, vla_evidence_url, vla_evidence_quote, models_used,
  pain_score, pain_signal_url, pain_signal_quote, pain_summary,
  spend_tier, spend_rationale,
  vertical, lockin_status, lockin_evidence_url, openness_score,
  notes,
  score, tier   (filled by score.py later)

data/sources.csv: company_id, field, url
"""
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / "cache"
DATA = REPO / "data"

OUT_FIELDS = [
    "company_id", "slug", "company_name", "domain", "one_line_description",
    "founded_year", "hq_country", "hq_city",
    "total_raised_usd", "last_round_date", "last_round_stage", "last_round_size_usd",
    "headcount", "headcount_growth_6mo",
    "vla_classification", "vla_evidence_type", "vla_evidence_url", "vla_evidence_quote", "models_used",
    "pain_score", "pain_signal_url", "pain_signal_quote", "pain_summary",
    "spend_tier", "spend_rationale",
    "vertical", "lockin_status", "lockin_evidence_url", "openness_score",
    "notes",
    "score", "tier",
]


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return s[:60]


def main() -> None:
    rows = []
    for f in sorted(CACHE.glob("scored_batch_*.csv")):
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                rows.append(r)
        print(f"loaded {f.name}: now {len(rows)} rows")

    # universe sources for each company (carry forward original source URLs)
    uni_sources: dict[str, list[str]] = {}
    if (DATA / "sources_universe.csv").exists():
        with open(DATA / "sources_universe.csv") as f:
            for r in csv.DictReader(f):
                uni_sources.setdefault(r["company_id"], []).append(r["url"])

    # also pull primary_source_url from working_set as a fallback
    if (DATA / "working_set.csv").exists():
        with open(DATA / "working_set.csv") as f:
            for r in csv.DictReader(f):
                cid = r["company_id"]
                ws = r.get("primary_source_url", "")
                if ws and ws not in uni_sources.get(cid, []):
                    uni_sources.setdefault(cid, []).append(ws)
                # all_sources is semicolon-separated
                for u in (r.get("all_sources", "") or "").split(";"):
                    u = u.strip()
                    if u and u not in uni_sources.get(cid, []):
                        uni_sources.setdefault(cid, []).append(u)

    # build companies output, drop any vla_no
    companies = []
    sources_rows = []
    seen = set()
    dropped_vla_no = 0
    for r in rows:
        cid = r.get("company_id", "").strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)

        if (r.get("vla_classification") or "").strip() == "vla_no":
            dropped_vla_no += 1
            continue

        out = {k: (r.get(k, "") or "").strip() for k in OUT_FIELDS}
        out["company_id"] = cid
        out["company_name"] = r.get("company_name", "").strip()
        out["domain"] = (r.get("domain") or "").strip()
        out["slug"] = slugify(out["company_name"])
        out["score"] = ""
        out["tier"] = ""
        companies.append(out)

        # collect every URL field into sources.csv
        url_fields = [
            ("vla_evidence_url", r.get("vla_evidence_url", "")),
            ("pain_signal_url", r.get("pain_signal_url", "")),
            ("lockin_evidence_url", r.get("lockin_evidence_url", "")),
        ]
        for field, u in url_fields:
            u = (u or "").strip()
            if u and u.startswith("http"):
                sources_rows.append({"company_id": cid, "field": field, "url": u})
        for u in (r.get("extra_source_urls", "") or "").split("|"):
            u = u.strip()
            if u and u.startswith("http"):
                sources_rows.append({"company_id": cid, "field": "extra", "url": u})
        for u in uni_sources.get(cid, []):
            u = u.strip()
            if u and u.startswith("http"):
                sources_rows.append({"company_id": cid, "field": "universe", "url": u})

    # dedupe sources
    seen_pairs = set()
    deduped = []
    for r in sources_rows:
        k = (r["company_id"], r["url"])
        if k in seen_pairs:
            continue
        seen_pairs.add(k)
        deduped.append(r)

    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / "companies.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        w.writeheader()
        for r in companies:
            w.writerow(r)

    with open(DATA / "sources.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_id", "field", "url"])
        w.writeheader()
        for r in deduped:
            w.writerow(r)

    # breakdown
    from collections import Counter
    vla = Counter(c["vla_classification"] for c in companies)
    spend = Counter(c["spend_tier"] for c in companies)
    pain = Counter(c["pain_score"] for c in companies)
    print(f"\nmerged: {len(companies)} companies kept, {dropped_vla_no} dropped (vla_no)")
    print(f"sources: {len(deduped)} unique URLs")
    print(f"vla: {dict(vla)}")
    print(f"spend: {dict(spend)}")
    print(f"pain: {dict(pain)}")


if __name__ == "__main__":
    main()
