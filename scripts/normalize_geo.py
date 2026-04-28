#!/usr/bin/env python3
"""Normalize hq_country variants and add a `region` column to companies.csv.

region values: california | us_other | international
"""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

COUNTRY_NORMALIZE = {
    "USA": "USA",
    "United States": "USA",
    "United States of America": "USA",
    "U.S.A.": "USA",
    "US": "USA",
    "U.K.": "United Kingdom",
    "UK": "United Kingdom",
    "S. Korea": "South Korea",
    "Korea": "South Korea",
    "PRC": "China",
}

CA_CITIES = {
    "san francisco", "sf", "berkeley", "oakland", "palo alto", "mountain view",
    "san jose", "sunnyvale", "san mateo", "menlo park", "redwood city",
    "los angeles", "la", "pasadena", "santa monica", "irvine", "santa clara",
    "san diego", "fremont", "burlingame", "emeryville", "cupertino",
    "milpitas", "south san francisco",
}


def region_for(country: str, city: str) -> str:
    if not country:
        return ""
    if country == "USA":
        if city.strip().lower() in CA_CITIES:
            return "california"
        return "us_other"
    return "international"


def main() -> None:
    rows = list(csv.DictReader(open(DATA / "companies.csv")))
    fieldnames = list(rows[0].keys())
    if "region" not in fieldnames:
        # insert region right after hq_city
        i = fieldnames.index("hq_city") + 1
        fieldnames.insert(i, "region")

    cnt_ca = 0
    cnt_us = 0
    cnt_intl = 0
    cnt_blank = 0
    for r in rows:
        c = (r.get("hq_country") or "").strip()
        c = COUNTRY_NORMALIZE.get(c, c)
        r["hq_country"] = c
        city = (r.get("hq_city") or "").strip()
        r["region"] = region_for(c, city)
        if r["region"] == "california":
            cnt_ca += 1
        elif r["region"] == "us_other":
            cnt_us += 1
        elif r["region"] == "international":
            cnt_intl += 1
        else:
            cnt_blank += 1

    with open(DATA / "companies.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"normalized {len(rows)} rows: california={cnt_ca}  us_other={cnt_us}  international={cnt_intl}  blank={cnt_blank}")


if __name__ == "__main__":
    main()
