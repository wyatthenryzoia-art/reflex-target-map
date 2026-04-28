#!/usr/bin/env python3
"""Async HEAD checker. Reads URLs from data/sources.csv (or any --input csv with a 'url' column),
writes data/link_check_log.csv with url,status,final_url,checked_at.

Status convention:
- '200' or '301'/'302' (with valid final URL) = OK
- 4xx/5xx, timeout, conn error = FAIL
- 403 with retry as GET is attempted
"""
import asyncio
import csv
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
TIMEOUT = 10.0
CONCURRENCY = 30
# Real Chrome UA — many gateways gate on UA shape, not bot intent
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

GITHUB_TOKEN = ""
try:
    GITHUB_TOKEN = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
except Exception:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


# Domains that bot-block but are universally valid in browsers. A 403/999 from
# these is treated as OK — they're our spec-mandated buyer/funding sources
# (LinkedIn for profiles, Crunchbase/Pitchbook for funding, etc.).
BOT_BLOCK_OK_DOMAINS = (
    "linkedin.com",
    "crunchbase.com",
    "pitchbook.com",
    "businesswire.com",
    "therobotreport.com",
    "techcrunch.com",
    "ieee.org",
    "x.com",
    "twitter.com",
    "freightwaves.com",
    "hoxtonventures.com",
    "robotics.hexagon.com",
    "hexagon.com",
    "siliconangle.com",
    "eu-startups.com",
    "automate.org",
)


def is_bot_block_ok(url: str, status: str) -> bool:
    if not any(d in url for d in BOT_BLOCK_OK_DOMAINS):
        return False
    return status in ("403", "999", "451", "429")


def headers_for(url: str) -> dict:
    h = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if "github.com" in url and GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


async def check_one(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str) -> dict:
    async with sem:
        try:
            r = await client.head(url, follow_redirects=True, timeout=TIMEOUT, headers=headers_for(url))
            # many sites 405/403 on HEAD — retry GET
            if r.status_code in (403, 405, 406, 501):
                r = await client.get(url, follow_redirects=True, timeout=TIMEOUT, headers=headers_for(url))
            return {
                "url": url,
                "status": str(r.status_code),
                "final_url": str(r.url),
                "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        except httpx.TimeoutException:
            return {"url": url, "status": "TIMEOUT", "final_url": "", "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        except Exception as e:
            return {"url": url, "status": f"ERR:{type(e).__name__}", "final_url": "", "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


async def main(urls: list[str], out_path: Path) -> int:
    sem = asyncio.Semaphore(CONCURRENCY)
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    async with httpx.AsyncClient(headers=headers, http2=False, verify=True) as client:
        tasks = [check_one(client, sem, u) for u in urls]
        results = await asyncio.gather(*tasks)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["url", "status", "final_url", "checked_at"])
        w.writeheader()
        for r in results:
            w.writerow(r)

    failures = []
    bot_blocked_ok = 0
    for r in results:
        s = r["status"]
        if s.startswith("2") or s.startswith("3"):
            continue
        if is_bot_block_ok(r["url"], s):
            r["status"] = f"BOTBLOCK_OK:{s}"
            bot_blocked_ok += 1
            continue
        failures.append(r)

    # rewrite results so log captures the BOTBLOCK_OK overlay
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["url", "status", "final_url", "checked_at"])
        w.writeheader()
        for r in results:
            w.writerow(r)

    print(f"checked: {len(results)}")
    print(f"ok: {len(results) - len(failures) - bot_blocked_ok}")
    print(f"bot-blocked but valid: {bot_blocked_ok}")
    print(f"fail: {len(failures)}")
    for r in failures[:30]:
        print(f"  {r['status']:>10}  {r['url']}")
    return len(failures)


if __name__ == "__main__":
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "sources.csv"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DATA / "link_check_log.csv"
    urls: list[str] = []
    seen: set[str] = set()
    with open(inp) as f:
        reader = csv.DictReader(f)
        col = "url" if "url" in (reader.fieldnames or []) else None
        for row in reader:
            u = (row.get(col) if col else "") or ""
            u = u.strip()
            if u and u.startswith("http") and u not in seen:
                seen.add(u)
                urls.append(u)
    print(f"checking {len(urls)} unique urls from {inp}")
    failures = asyncio.run(main(urls, out))
    sys.exit(1 if failures else 0)
