#!/usr/bin/env python3
"""Render docs/index.html, docs/about.html, docs/dossiers/*.html, and docs/assets/data.json
from data/companies.csv (+ buyers.csv + sources.csv) and dossiers/*.md.

Idempotent: safe to re-run.
"""
import csv
import json
import re
from datetime import date
from pathlib import Path

import markdown as md

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
DOSS_MD = REPO / "dossiers"
DOCS = REPO / "docs"
ASSETS = DOCS / "assets"
DOSS_HTML = DOCS / "dossiers"

LIVE_BASE = "https://wyatthenryzoia-art.github.io/reflex-target-map"

import subprocess
import time
try:
    CACHEBUST = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True, cwd=REPO).strip() or str(int(time.time()))
except Exception:
    CACHEBUST = str(int(time.time()))


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return s


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def to_int(x, default=0):
    try:
        return int(float(x))
    except Exception:
        return default


def site_header(active: str, depth: int = 0) -> str:
    prefix = "../" * depth
    nav = [
        ("Map", f"{prefix}index.html", "map"),
        ("About", f"{prefix}about.html", "about"),
        ("GitHub", "https://github.com/wyatthenryzoia-art/reflex-target-map", "github"),
    ]
    nav_html = " ".join(
        f'<a href="{u}"{"" if k != active else " style=color:#fff"}>{n}</a>' for n, u, k in nav
    )
    return f"""<header class="site">
  <h1><a href="{prefix}index.html">REFLEX TARGETS</a></h1>
  <nav>{nav_html}</nav>
</header>"""


def site_footer() -> str:
    today = date.today().isoformat()
    return f"""<footer class="site">
  Built by Wyatt Zoia. Data as of {today}. <a href="about.html">Methodology</a>.
</footer>"""


def render_index(rows: list[dict], total_count: int, dossier_count: int, metrics: dict, lead_cards: list = None) -> str:
    leads_html = ""
    if lead_cards:
        cards = "".join(
            f'''<a class="lead-card" href="{c['url']}">
              <div class="lead-name">{c['name']}</div>
              <div class="lead-meta">{c['buyer']} · {c['hq']}</div>
              <div class="lead-reason">{c['reason']}</div>
              <div class="lead-cta">view dossier →</div>
            </a>''' for c in lead_cards
        )
        leads_html = f'''<div class="leads">
          <div class="leads-label">START HERE — strongest cold-DM hooks</div>
          <div class="lead-cards">{cards}</div>
        </div>'''
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>REFLEX TARGETS</title>
  <meta name="description" content="155 robotics companies running or building toward VLA / VLM policies — the workload Reflex serves. 20 cold-DM-ready dossiers. Every claim sourced.">
  <meta property="og:title" content="REFLEX TARGETS">
  <meta property="og:description" content="155 robotics companies that should be paying Reflex. 20 dossiers ready for cold outreach.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://wyatthenryzoia-art.github.io/reflex-target-map/">
  <meta name="twitter:card" content="summary">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23000'/%3E%3Ccircle cx='16' cy='16' r='5' fill='%23f97316'/%3E%3Ccircle cx='16' cy='16' r='10' fill='none' stroke='%23f97316' stroke-opacity='0.4' stroke-width='2'/%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap">
  <link rel="stylesheet" href="assets/vendor/leaflet.css">
  <link rel="stylesheet" href="assets/vendor/markercluster.css">
  <link rel="stylesheet" href="assets/vendor/markercluster-default.css">
  <link rel="stylesheet" href="assets/styles.css?v={CACHEBUST}">
</head>
<body>
{site_header("map")}
<div class="container">
  <div class="hero">
    <h2>Robotics companies that should be paying Reflex.</h2>
    <p>
      Where in the world the VLA / VLM robotics shops are. Click a marker for who they are, what they're building, and who to talk to. <a href="about.html">methodology →</a>
    </p>
    <div class="metrics-mini">
      <span><b>{metrics['total']}</b> companies</span>
      <span><b>{metrics['dossiers']}</b> dossiers</span>
      <span><b>{metrics['vla_active']}</b> running VLAs today</span>
      <span><b>{metrics['buyers']}</b> named buyers</span>
    </div>
  </div>

{leads_html}

  <div class="controls">
    <label>Vertical
      <select id="f-vertical"><option value="">All</option></select>
    </label>
    <label>Region
      <select id="f-region">
        <option value="">All</option>
        <option value="california">California</option>
        <option value="us_other">US (other)</option>
        <option value="international">International</option>
      </select>
    </label>
    <label>Signal
      <select id="f-vla">
        <option value="">All</option>
        <option value="vla_active">Running VLAs today</option>
        <option value="vla_likely">Building toward VLAs</option>
        <option value="vla_possible">Adjacent / possible</option>
      </select>
    </label>
    <label>Search
      <input type="search" id="f-search" placeholder="company, buyer, vertical">
    </label>
    <button type="button" class="chip-toggle" id="f-priority" aria-pressed="false">★ Dossiered only</button>
    <span class="count" id="count"></span>
  </div>

  <div class="map-wrap">
    <div id="map"></div>
    <div class="legend">
      <span class="lk pin-vla-active"><span class="dot"></span> running VLAs today</span>
      <span class="lk pin-vla-likely"><span class="dot"></span> building toward</span>
      <span class="lk pin-vla-possible"><span class="dot"></span> adjacent</span>
      <span class="lk priority-key"><span class="dot"></span> has a dossier</span>
    </div>
  </div>
</div>

{site_footer()}
<script src="assets/vendor/leaflet.js"></script>
<script src="assets/vendor/markercluster.js"></script>
<script src="assets/map.js?v={CACHEBUST}"></script>
</body>
</html>"""




def render_about(text_md: str) -> str:
    body = md.markdown(text_md, extensions=["extra"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>METHODOLOGY — REFLEX TARGETS</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap">
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
{site_header("about")}
<div class="prose">
{body}
</div>
{site_footer()}
</body>
</html>"""


def render_dossier(name: str, body_md: str) -> str:
    body = md.markdown(body_md, extensions=["extra"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{name} — REFLEX TARGETS</title>
  <link rel="stylesheet" href="../assets/styles.css">
</head>
<body>
{site_header("map", depth=1)}
<div class="dossier">
  <p class="back"><a href="../index.html">← back to map</a></p>
  {body}
</div>
{site_footer()}
</body>
</html>"""


def main() -> None:
    companies = read_csv(DATA / "companies.csv")
    buyers = read_csv(DATA / "buyers.csv")
    sources = read_csv(DATA / "sources.csv")

    by_co = {c["company_id"]: c for c in companies}
    buyers_by_co = {b["company_id"]: b for b in buyers}
    sources_by_co: dict[str, list[str]] = {}
    for s in sources:
        sources_by_co.setdefault(s["company_id"], []).append(s["url"])

    DOSS_HTML.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    json_rows = []
    dossier_count = 0
    for c in companies:
        cid = c["company_id"]
        b = buyers_by_co.get(cid, {})
        score = to_int(c.get("score"))
        tier = to_int(c.get("tier"))
        slug = c.get("slug") or slugify(c["company_name"])
        has_dossier = (DOSS_MD / f"{slug}.md").exists()
        if has_dossier:
            dossier_count += 1
        dossier_url = f"dossiers/{slug}.html" if has_dossier else ""
        urls = sorted(set(filter(None, sources_by_co.get(cid, []))))
        city = (c.get("hq_city") or "").strip()
        country = (c.get("hq_country") or "").strip()
        if city and country:
            hq_display = f"{city}, {country}"
        else:
            hq_display = city or country or "—"
        json_rows.append({
            "id": cid,
            "company_name": c["company_name"],
            "domain": c.get("domain", ""),
            "vertical": c.get("vertical", ""),
            "hq_city": city,
            "hq_country": country,
            "hq_display": hq_display,
            "region": c.get("region", ""),
            "tier": tier,
            "score": score,
            "vla_classification": c.get("vla_classification", ""),
            "pain_score": to_int(c.get("pain_score")),
            "spend_tier": c.get("spend_tier", ""),
            "buyer_name": b.get("buyer_name", ""),
            "buyer_linkedin_url": b.get("buyer_linkedin_url", ""),
            "one_line_description": c.get("one_line_description", ""),
            "dossier_url": dossier_url,
            "has_dossier": has_dossier,
            "source_urls": urls,
        })

    # Sort: California first, then US-other, then international, then unknown — score-desc within each
    REGION_RANK = {"california": 0, "us_other": 1, "international": 2, "": 3}
    json_rows.sort(key=lambda r: (REGION_RANK.get(r["region"], 9), -r["score"], r["company_name"]))

    (ASSETS / "data.json").write_text(json.dumps(json_rows, indent=2))

    # geo.json — lat/lon by (city, country) for the map renderer
    geo_rows = []
    geo_path = DATA / "geocoded.csv"
    if geo_path.exists():
        with open(geo_path) as f:
            for r in csv.DictReader(f):
                try:
                    geo_rows.append({
                        "hq_city": r["hq_city"],
                        "hq_country": r["hq_country"],
                        "lat": float(r["lat"]),
                        "lon": float(r["lon"]),
                        "source": r.get("source", ""),
                    })
                except Exception:
                    continue
    (ASSETS / "geo.json").write_text(json.dumps(geo_rows, indent=2))

    # build metrics block from the actual data
    buyers_list = []
    if (DATA / "buyers.csv").exists():
        buyers_list = list(csv.DictReader(open(DATA / "buyers.csv")))
    sources_list = []
    if (DATA / "sources.csv").exists():
        sources_list = list(csv.DictReader(open(DATA / "sources.csv")))
    metrics = {
        "total": len(json_rows),
        "dossiers": dossier_count,
        "vla_active": sum(1 for r in json_rows if r["vla_classification"] == "vla_active"),
        "buyers": sum(1 for b in buyers_list if b.get("buyer_linkedin_url")),
        "hooks": sum(1 for b in buyers_list if b.get("suggested_first_dm_hook") and "no specific hook" not in b.get("suggested_first_dm_hook", "").lower()),
        "urls": len({s["url"] for s in sources_list}),
    }

    # Pick top 3 cold-DM-ready leads (hand-tuned: strongest specific hooks).
    LEAD_SLUGS = ["sereact", "periodic-labs", "telexistence"]
    buyers_idx = {b["company_id"]: b for b in buyers_list}
    lead_cards = []
    for slug in LEAD_SLUGS:
        c = next((r for r in json_rows if (r.get("dossier_url") or "").endswith(f"{slug}.html")), None)
        if not c:
            continue
        b = buyers_idx.get(c["id"], {})
        # short, concrete reason — pull from the hook if reasonable, else from desc
        hook = (b.get("suggested_first_dm_hook") or "").strip()
        reason = hook if hook and "no specific hook" not in hook.lower() else c.get("one_line_description", "")
        # trim the reason to ~180 chars
        if len(reason) > 200:
            reason = reason[:197].rstrip() + "…"
        lead_cards.append({
            "name": c["company_name"],
            "vertical": c["vertical"],
            "hq": c["hq_display"],
            "buyer": b.get("buyer_name", ""),
            "reason": reason,
            "url": c["dossier_url"],
        })

    (DOCS / "index.html").write_text(render_index(json_rows, len(json_rows), dossier_count, metrics, lead_cards))

    about_md_path = REPO / "explainer.md"
    about_md = about_md_path.read_text() if about_md_path.exists() else "# About\n\nMethodology coming."
    (DOCS / "about.html").write_text(render_about(about_md))

    for md_file in DOSS_MD.glob("*.md"):
        slug = md_file.stem
        body = md_file.read_text()
        title_match = re.search(r"^#\s+(.+)$", body, re.M)
        title = title_match.group(1).strip() if title_match else slug
        (DOSS_HTML / f"{slug}.html").write_text(render_dossier(title, body))

    print(f"rendered {len(companies)} companies, {dossier_count} dossiers")


if __name__ == "__main__":
    main()
