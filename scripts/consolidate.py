#!/usr/bin/env python3
"""Merge cache/universe_1a.csv, 1b.csv, 1c.csv into data/universe.csv.

Dedup keys (in priority order):
  1. normalized domain (lowercased, strip www., strip trailing slash)
  2. normalized company name (lowercased, strip punctuation, strip suffixes)

Apply spec 3.3 exclusion list. Apply manual review additions.

Each kept row carries a list of (source_type, source_url) tuples for traceability.
"""
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / "cache"
DATA = REPO / "data"

# Spec 3.3 exclusions + manual review additions (Apptronik per founder review;
# name-clash "Reflex Robotics" — different company, drop to avoid confusion).
EXCLUDE_NAMES = {
    "tesla", "google deepmind", "deepmind", "meta", "apple", "amazon robotics", "amazon",
    "figure", "figure ai", "1x", "1x technologies", "skild", "skild ai",
    "physical intelligence", "sanctuary ai", "sanctuary", "boston dynamics",
    "agility", "agility robotics", "apptronik",
    # name clashes
    "reflex robotics",
    # generic / non-company artifacts that snuck in
    "openai", "nvidia", "intuitive surgical",  # already public, not target
}

EXCLUDE_DOMAINS = {
    "tesla.com", "deepmind.google", "deepmind.com", "meta.com", "apple.com",
    "amazon.science", "figure.ai", "1x.tech", "skild.ai", "physicalintelligence.company",
    "sanctuary.ai", "bostondynamics.com", "agilityrobotics.com",
    "apptronik.com",
    "reflexrobotics.com",
    "openai.com", "nvidia.com",
}

ACADEMIC_KEYWORDS = (
    "stanford", "mit ", "harvard", "kaist", "tsinghua", " eth ", "epfl",
    "carnegie mellon", "uc berkeley", "u of", "university", "research institute",
    "national lab", "fraunhofer",
)

NAME_SUFFIX_STRIP = re.compile(r"\s+(inc|llc|corp|co|ltd|gmbh|ag|sa|s\.a\.|s\.l\.|ai|robotics|technologies|technology|labs|lab)\.?$", re.I)
NAME_PUNCT = re.compile(r"[^\w\s]")


def norm_name(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    s = NAME_PUNCT.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    # iteratively strip suffixes
    prev = None
    while prev != s:
        prev = s
        s = NAME_SUFFIX_STRIP.sub("", s).strip()
    return s


def norm_domain(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r"^https?://", "", s)
    s = re.sub(r"^www\.", "", s)
    s = s.rstrip("/")
    s = s.split("/")[0]
    return s


def is_academic(name: str, notes: str = "") -> bool:
    blob = (name + " " + notes).lower()
    return any(k in blob for k in ACADEMIC_KEYWORDS)


def is_excluded(name: str, domain: str) -> bool:
    n = norm_name(name)
    d = norm_domain(domain)
    if n in EXCLUDE_NAMES:
        return True
    if d and d in EXCLUDE_DOMAINS:
        return True
    return False


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
    raw = (
        load(CACHE / "universe_1a.csv", "1a")
        + load(CACHE / "universe_1b.csv", "1b")
        + load(CACHE / "universe_1c.csv", "1c")
    )
    print(f"raw rows in: {len(raw)}")

    # group by best key
    groups: dict[str, dict] = {}
    skipped_excluded = 0
    skipped_academic = 0
    skipped_blank = 0
    for r in raw:
        name = r["company_name"]
        if not name:
            skipped_blank += 1
            continue
        if is_excluded(name, r["domain"]):
            skipped_excluded += 1
            continue
        if is_academic(name, r["notes"]):
            skipped_academic += 1
            continue

        d = norm_domain(r["domain"])
        n = norm_name(name)
        key = d or n
        if not key:
            skipped_blank += 1
            continue

        g = groups.get(key)
        if g is None:
            g = {
                "company_name": name,
                "domain": d,
                "norm_name": n,
                "sources": [],
                "notes": [],
                "origins": set(),
            }
            groups[key] = g
        else:
            # prefer longest non-empty domain, prefer name with mixed case
            if not g["domain"] and d:
                g["domain"] = d
            if len(name) > len(g["company_name"]) and name[0].isupper():
                g["company_name"] = name
        g["sources"].append({
            "type": r["source_type"],
            "url": r["source_url"],
            "quote": r["source_quote"],
        })
        if r["notes"]:
            g["notes"].append(r["notes"])
        g["origins"].add(r["_origin"])

    # second pass: merge groups whose normalized names match (handles cases where
    # one row had a domain and another did not)
    by_name: dict[str, str] = {}
    merged_keys = set()
    for key, g in list(groups.items()):
        n = g["norm_name"]
        if n in by_name and by_name[n] != key:
            target_key = by_name[n]
            target = groups[target_key]
            target["sources"].extend(g["sources"])
            target["notes"].extend(g["notes"])
            target["origins"].update(g["origins"])
            if not target["domain"] and g["domain"]:
                target["domain"] = g["domain"]
            merged_keys.add(key)
        else:
            by_name[n] = key
    for k in merged_keys:
        groups.pop(k, None)

    # build output
    out_rows = []
    company_id = 0
    for key, g in groups.items():
        company_id += 1
        cid = f"c{company_id:03d}"
        # dedupe sources by url
        seen = set()
        unique_sources = []
        for s in g["sources"]:
            u = s["url"]
            if u and u not in seen:
                seen.add(u)
                unique_sources.append(s)
        out_rows.append({
            "company_id": cid,
            "company_name": g["company_name"],
            "domain": g["domain"],
            "origins": "|".join(sorted(g["origins"])),
            "source_count": len(unique_sources),
            "primary_source_type": unique_sources[0]["type"] if unique_sources else "",
            "primary_source_url": unique_sources[0]["url"] if unique_sources else "",
            "primary_source_quote": unique_sources[0]["quote"] if unique_sources else "",
            "all_sources": ";".join(s["url"] for s in unique_sources if s["url"]),
            "notes": " | ".join(g["notes"][:3]),
        })

    # sort by source count desc (rows seen by multiple lists are higher signal)
    out_rows.sort(key=lambda r: (-r["source_count"], r["company_name"].lower()))

    DATA.mkdir(parents=True, exist_ok=True)
    out_path = DATA / "universe.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        for r in out_rows:
            w.writerow(r)

    # also a sources flat file for the link checker
    sources_path = DATA / "sources_universe.csv"
    with open(sources_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company_id", "field", "url"])
        for key, g in groups.items():
            cid = next(r["company_id"] for r in out_rows if r["company_name"] == g["company_name"])
            for s in g["sources"]:
                if s["url"]:
                    w.writerow([cid, "universe_source", s["url"]])

    multi = [r for r in out_rows if r["source_count"] >= 2]
    print(f"unique companies: {len(out_rows)}")
    print(f"  with >=2 sources (cross-list overlap): {len(multi)}")
    print(f"skipped excluded: {skipped_excluded}")
    print(f"skipped academic: {skipped_academic}")
    print(f"skipped blank: {skipped_blank}")
    print(f"out: {out_path}")
    print(f"out: {sources_path}")


if __name__ == "__main__":
    main()
