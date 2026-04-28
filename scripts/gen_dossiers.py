#!/usr/bin/env python3
"""Generate Tier 1 dossier markdown from data/companies.csv + data/buyers.csv + data/sources.csv.

Each Tier 1 row gets a markdown file at dossiers/<slug>.md following the spec section 10
template. Skips dossier if required fields are missing — flags those rows in stderr.
"""
import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
DOSS = REPO / "dossiers"

VERTICAL_LABELS = {
    "humanoid_general": "Humanoid (general)",
    "humanoid_industrial": "Humanoid (industrial)",
    "mobile_manipulator_warehouse": "Mobile manipulator (warehouse)",
    "mobile_manipulator_other": "Mobile manipulator (other)",
    "drone_aerial": "Drone / aerial",
    "agriculture": "Agriculture",
    "defense_dual_use": "Defense (dual-use)",
    "surgical_medical": "Surgical / medical",
    "last_mile_delivery": "Last-mile delivery",
    "cleaning_janitorial": "Cleaning / janitorial",
    "consumer_home": "Consumer / home",
    "research_only": "Research only",
}

CLASS_LABELS = {
    "vla_active": "vla_active",
    "vla_likely": "vla_likely",
    "vla_possible": "vla_possible",
}

LOCKIN_LABELS = {
    "lockin_open": "open to vendor solutions",
    "lockin_generic_cloud": "generic cloud (Modal/Together/Fireworks/Replicate/Baseten)",
    "lockin_jetson_only": "Jetson edge only",
    "lockin_diy": "in-house infra build",
    "lockin_unknown": "no public signal",
}

REQUIRED = ["company_name", "vla_classification", "pain_score", "spend_tier", "vertical"]


def fmt_money(s: str) -> str:
    if not s:
        return "—"
    try:
        n = int(float(s))
        if n >= 1_000_000:
            return f"${n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"${n/1_000:.0f}k"
        return f"${n}"
    except Exception:
        return s


def render(company: dict, buyer: dict, urls: list[str]) -> str:
    name = company["company_name"]
    score = company.get("score", "")
    tier = company.get("tier", "")
    vertical = VERTICAL_LABELS.get(company.get("vertical", ""), company.get("vertical", "—"))
    stage = company.get("last_round_stage", "—") or "—"
    hq = ", ".join(filter(None, [company.get("hq_city", ""), company.get("hq_country", "")])) or "—"
    desc = company.get("one_line_description", "")

    vla_class = company.get("vla_classification", "")
    vla_url = company.get("vla_evidence_url", "")
    vla_quote = company.get("vla_evidence_quote", "")
    models = company.get("models_used", "")

    pain_score = company.get("pain_score", "0")
    pain_url = company.get("pain_signal_url", "")
    pain_quote = company.get("pain_signal_quote", "")
    pain_summary = company.get("pain_summary", "")

    raised = fmt_money(company.get("total_raised_usd", ""))
    round_size = fmt_money(company.get("last_round_size_usd", ""))
    round_date = company.get("last_round_date", "—") or "—"
    round_stage = company.get("last_round_stage", "—") or "—"
    headcount = company.get("headcount", "—") or "—"
    growth = company.get("headcount_growth_6mo", "")
    growth_str = f"{growth}%" if growth else "—"
    spend = (company.get("spend_tier", "") or "—").upper()
    spend_rat = company.get("spend_rationale", "")

    lockin_label = LOCKIN_LABELS.get(company.get("lockin_status", ""), "—")
    lockin_url = company.get("lockin_evidence_url", "")
    openness = company.get("openness_score", "—")

    buyer_name = (buyer.get("buyer_name", "") if buyer else "") or "(not yet identified)"
    buyer_title = (buyer.get("buyer_title", "") if buyer else "") or ""
    buyer_li = (buyer.get("buyer_linkedin_url", "") if buyer else "") or ""
    buyer_x = (buyer.get("buyer_x_handle", "") if buyer else "") or "—"
    buyer_signal = (buyer.get("buyer_recent_signal", "") if buyer else "") or "—"
    intro = (buyer.get("warm_intro_path", "") if buyer else "") or "cold"
    hook = (buyer.get("suggested_first_dm_hook", "") if buyer else "") or "(no specific hook found, recommend warm intro path only)"
    # filter internal scoring notes out of user-facing Risks section
    raw_notes = company.get("notes", "") or ""
    risk_parts = []
    for part in raw_notes.split(" | "):
        p = part.strip()
        if not p:
            continue
        if p.lower().startswith("lockin reclass"):
            continue
        risk_parts.append(p)
    risks = " | ".join(risk_parts) or "—"

    # Why argument: lead with VLA, follow with pain
    why_lines = []
    if vla_class == "vla_active":
        why_lines.append(f"Active VLA usage ({models or 'undisclosed model'}) — direct evidence in their public stack.")
    elif vla_class == "vla_likely":
        why_lines.append(f"Strong VLA signal from public posture (job posts, blog, demos) — likely fine-tuning or running VLAs.")
    else:
        why_lines.append(f"Vertical fit (humanoid / dexterous manipulation) puts them on the VLA adoption curve.")
    if int(pain_score or 0) >= 2:
        why_lines.append(f"Pain signal {pain_score}/3: {pain_summary or 'multiple infra reqs / public infra discussion'}.")
    elif int(pain_score or 0) == 1:
        why_lines.append(f"Modest pain signal: {pain_summary or 'one infra-relevant indicator'}.")
    else:
        why_lines.append("Pain signal is quiet — sales motion will lean on PLG / developer-experience rather than urgency.")
    why = " ".join(why_lines)

    # Render
    md = []
    md.append(f"# {name}\n")
    md.append(f"**Tier {tier} — Score: {score}/100**  ")
    md.append(f"**Vertical: {vertical} | Stage: {round_stage} | HQ: {hq}**\n")

    md.append("## What they do\n")
    md.append(f"{desc or '(description pending)'}\n")

    md.append("## Why they're a Reflex prospect\n")
    md.append(f"{why}\n")

    md.append("## Model usage\n")
    md.append(f"- Classification: `{vla_class}`")
    if models:
        md.append(f"- Models used: {models.replace('|', ', ')}")
    if vla_url:
        if vla_quote:
            md.append(f'- Evidence: [{vla_url}]({vla_url}) — "{vla_quote}"')
        else:
            md.append(f"- Evidence: [{vla_url}]({vla_url})")
    md.append("")

    md.append("## Pain signal\n")
    md.append(f"- Score: {pain_score}/3")
    if pain_url:
        md.append(f"- Top signal: [{pain_url}]({pain_url}) — {pain_summary or pain_quote}")
    elif pain_summary:
        md.append(f"- Top signal: {pain_summary}")
    md.append("")

    md.append("## Spend snapshot\n")
    md.append(f"- Total raised: {raised}")
    md.append(f"- Last round: {round_size}, {round_date}, {round_stage}")
    md.append(f"- Headcount: {headcount}, growth 6mo: {growth_str}")
    md.append(f"- Spend tier: {spend} — {spend_rat or '(rationale pending)'}\n")

    md.append("## Lock-in & openness\n")
    md.append(f"- Current inference posture: {lockin_label}")
    if lockin_url:
        md.append(f"  - Evidence: [{lockin_url}]({lockin_url})")
    md.append(f"- Openness score: {openness}/3 (higher = more receptive to a developer-tool pitch)\n")

    md.append("## Buyer\n")
    md.append(f"- Name: **{buyer_name}**, {buyer_title}".rstrip(", "))
    if buyer_li:
        md.append(f"- LinkedIn: [{buyer_li}]({buyer_li})")
    md.append(f"- X: {buyer_x}")
    md.append(f"- Recent signal: {buyer_signal}")
    md.append(f"- Warm intro path: {intro}\n")

    md.append("## First-touch hook\n")
    md.append(f"{hook}\n")

    md.append("## Risks / disqualifiers\n")
    md.append(f"{risks}\n")

    md.append("## Sources\n")
    if urls:
        for u in urls:
            md.append(f"- [{u}]({u})")
    else:
        md.append("- (no external sources recorded)")
    md.append("")
    return "\n".join(md)


def main() -> None:
    if not (DATA / "companies.csv").exists():
        print("no companies.csv yet", file=sys.stderr)
        sys.exit(1)

    companies = list(csv.DictReader(open(DATA / "companies.csv")))
    buyers_by_co: dict[str, dict] = {}
    if (DATA / "buyers.csv").exists():
        for b in csv.DictReader(open(DATA / "buyers.csv")):
            buyers_by_co[b["company_id"]] = b

    sources_by_co: dict[str, list[str]] = {}
    if (DATA / "sources.csv").exists():
        for s in csv.DictReader(open(DATA / "sources.csv")):
            sources_by_co.setdefault(s["company_id"], []).append(s["url"])

    DOSS.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    DOSSIER_CAP = 25

    # Dossier set = all Tier 1 + top Tier 2 (score>=68 with verified buyer), capped at DOSSIER_CAP.
    # Spec section 9.2 caps the dossier set at 20; spec section 0.5.2 floor is 10.
    def is_dossier_candidate(c: dict) -> bool:
        if str(c.get("tier", "")) == "1":
            return True
        if str(c.get("tier", "")) == "2" and int(c.get("score") or 0) >= 68:
            b = buyers_by_co.get(c["company_id"], {})
            verified = b.get("buyer_verified", "")
            if verified and verified != "not_found":
                return True
        return False

    candidates = [c for c in companies if is_dossier_candidate(c)]
    candidates.sort(key=lambda c: -int(c.get("score") or 0))
    candidates = candidates[:DOSSIER_CAP]

    for c in candidates:
        missing = [k for k in REQUIRED if not c.get(k)]
        if missing:
            print(f"  skipping {c.get('company_name')}: missing {missing}", file=sys.stderr)
            skipped += 1
            continue
        slug = c["slug"]
        path = DOSS / f"{slug}.md"
        body = render(c, buyers_by_co.get(c["company_id"], {}), sorted(set(sources_by_co.get(c["company_id"], []))))
        path.write_text(body)
        written += 1

    print(f"wrote {written} dossiers; skipped {skipped} for missing fields")


if __name__ == "__main__":
    main()
