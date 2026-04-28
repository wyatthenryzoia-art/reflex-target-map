#!/usr/bin/env python3
"""Consolidate v2 universe expansion (cache/universe_2*.csv).

Dedup against:
  - existing data/companies.csv (already-scored)
  - existing data/universe.csv (already-considered)
  - the v2 inputs themselves

Apply the same exclusion + academic filters as scripts/consolidate.py.
Output: data/universe_v2_new.csv (truly new candidates only).
"""
import csv
import re
import sys
from pathlib import Path

# Reuse helpers from consolidate.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from consolidate import (  # type: ignore
    EXCLUDE_DOMAINS, EXCLUDE_NAMES, ACADEMIC_KEYWORDS,
    norm_domain, norm_name, is_academic, is_excluded,
)

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / "cache"
DATA = REPO / "data"


def load_existing_keys() -> set[str]:
    """Return set of {norm_name, norm_domain} keys for everything we already have."""
    keys: set[str] = set()
    for path in (DATA / "companies.csv", DATA / "universe.csv"):
        if not path.exists():
            continue
        with open(path) as f:
            for r in csv.DictReader(f):
                n = norm_name(r.get("company_name", ""))
                d = norm_domain(r.get("domain", ""))
                if n:
                    keys.add(f"name:{n}")
                if d:
                    keys.add(f"dom:{d}")
    return keys


def load(path: Path, source_label: str) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append({
                "company_name": (r.get("company_name") or "").strip(),
                "domain": (r.get("domain") or "").strip(),
                "source_type": (r.get("signal_type") or r.get("source_type") or source_label).strip(),
                "source_url": (r.get("signal_url") or r.get("source_url") or "").strip(),
                "source_quote": (r.get("signal_quote") or r.get("source_quote") or "").strip(),
                "notes": (r.get("notes") or "").strip(),
                "_origin": source_label,
            })
    return rows


def main() -> None:
    existing = load_existing_keys()
    print(f"existing keys: {len(existing)}")

    # also pull up the working_set (the rows we already attempted to score) to avoid re-doing
    seen_attempted = set()
    if (DATA / "working_set.csv").exists():
        for r in csv.DictReader(open(DATA / "working_set.csv")):
            n = norm_name(r["company_name"])
            d = norm_domain(r["domain"])
            if n: seen_attempted.add(f"name:{n}")
            if d: seen_attempted.add(f"dom:{d}")

    raw = []
    for tag in ("2a", "2b", "2c", "2d", "2e"):
        path = CACHE / f"universe_{tag}.csv"
        rows = load(path, tag)
        raw.extend(rows)
        print(f"  {path.name}: {len(rows)} rows")
    print(f"raw new rows in: {len(raw)}")

    groups: dict[str, dict] = {}
    skipped = {"excluded": 0, "academic": 0, "blank": 0, "duplicate": 0}
    for r in raw:
        name = r["company_name"]
        if not name:
            skipped["blank"] += 1
            continue
        if is_excluded(name, r["domain"]):
            skipped["excluded"] += 1
            continue
        if is_academic(name, r["notes"]):
            skipped["academic"] += 1
            continue
        n = norm_name(name)
        d = norm_domain(r["domain"])
        if (n and f"name:{n}" in existing) or (d and f"dom:{d}" in existing) \
           or (n and f"name:{n}" in seen_attempted) or (d and f"dom:{d}" in seen_attempted):
            skipped["duplicate"] += 1
            continue
        key = d or n
        if not key:
            skipped["blank"] += 1
            continue
        g = groups.setdefault(key, {
            "company_name": name, "domain": d, "norm_name": n,
            "sources": [], "notes": [], "origins": set(),
        })
        if not g["domain"] and d: g["domain"] = d
        if len(name) > len(g["company_name"]) and name[0].isupper(): g["company_name"] = name
        g["sources"].append({"type": r["source_type"], "url": r["source_url"], "quote": r["source_quote"]})
        if r["notes"]: g["notes"].append(r["notes"])
        g["origins"].add(r["_origin"])

    # second-pass merge by norm_name
    by_name: dict[str, str] = {}
    merged = set()
    for k, g in list(groups.items()):
        n = g["norm_name"]
        if n in by_name and by_name[n] != k:
            t = groups[by_name[n]]
            t["sources"].extend(g["sources"])
            t["notes"].extend(g["notes"])
            t["origins"].update(g["origins"])
            if not t["domain"] and g["domain"]: t["domain"] = g["domain"]
            merged.add(k)
        else:
            by_name[n] = k
    for k in merged:
        groups.pop(k, None)

    # find max company_id in existing companies.csv to continue numbering
    max_id = 0
    if (DATA / "companies.csv").exists():
        for r in csv.DictReader(open(DATA / "companies.csv")):
            cid = r.get("company_id", "")
            m = re.search(r"\d+", cid)
            if m:
                max_id = max(max_id, int(m.group(0)))
    if (DATA / "universe.csv").exists():
        for r in csv.DictReader(open(DATA / "universe.csv")):
            cid = r.get("company_id", "")
            m = re.search(r"\d+", cid)
            if m:
                max_id = max(max_id, int(m.group(0)))

    next_id = max_id + 1

    out = []
    for k, g in groups.items():
        seen = set()
        unique = []
        for s in g["sources"]:
            if s["url"] and s["url"] not in seen:
                seen.add(s["url"])
                unique.append(s)
        out.append({
            "company_id": f"c{next_id:03d}",
            "company_name": g["company_name"],
            "domain": g["domain"],
            "origins": "|".join(sorted(g["origins"])),
            "source_count": len(unique),
            "primary_source_type": unique[0]["type"] if unique else "",
            "primary_source_url": unique[0]["url"] if unique else "",
            "primary_source_quote": unique[0]["quote"] if unique else "",
            "all_sources": ";".join(s["url"] for s in unique if s["url"]),
            "notes": " | ".join(g["notes"][:3]),
        })
        next_id += 1

    out.sort(key=lambda r: (-r["source_count"], r["company_name"].lower()))

    out_path = DATA / "universe_v2_new.csv"
    if not out:
        print("no new rows after dedup")
        return
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        for r in out:
            w.writerow(r)
    multi = [r for r in out if r["source_count"] >= 2]
    print(f"\nNEW unique candidates: {len(out)}")
    print(f"  cross-list overlap (>=2 src): {len(multi)}")
    print(f"  skipped: {skipped}")
    print(f"  out: {out_path}")


if __name__ == "__main__":
    main()
