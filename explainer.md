# About this map

## What this is

A target acquisition map for [Reflex](https://tryreflex.ai) — a datacenter-scale inference platform for vision-language-action (VLA) and vision-language model (VLM) robot policies.

The output is a ranked list of robotics companies that look like Reflex prospects, plus one-page dossiers for the top tier. Every row has a source URL behind every non-obvious claim. Every external link in the dataset was HEAD-checked against a 200/3xx response on the day of publish.

## What this is not

Not a CRM. Not a list of "robotics companies in general." Not built from training-data recall — every signal traces to a fetched page. Not a marketing artifact: the explainer page you are reading is the methodology, not the pitch.

## Who it's for

A Reflex founder or BD lead who wants to start an outbound conversation today. Open the live URL on a call, click a Tier 1 dossier, get every sentence you need for a cold DM in 60 seconds.

## Universe definition

A company is on the candidate list if it (a) builds robots or robotics software as a core product, (b) has raised at least seed funding from a named investor or shipped a public demo, and (c) is not on the exclusion list.

**Excluded:** trillion-dollar parents that built their own inference (Tesla, Google DeepMind, Meta, Apple, Amazon Robotics); $1B+ companies publicly committed to in-house infra (Figure, 1X, Skild, Sanctuary, Boston Dynamics, Agility); pure hardware/component plays with no ML stack; pure RL or classical-control shops with no language or vision component; defense primes; companies dead or pivoted in the last 12 months.

**Sources:** Robot Report RBR50 lists; VC robotics portfolios (Khosla, Sequoia, a16z, Lux, Eclipse, NVentures, Construct, 8VC); HuggingFace organizations with VLA-tagged models; GitHub org-account forkers of canonical VLA repos (openpi, openvla, lerobot, Isaac-GR00T, SmolVLA); humanoid robot startup trackers; recent (2025-2026) robotics funding news.

## The eight scoring axes

Each company gets a single integer score 0-100, then a tier (1/2/3/drop). The score combines:

- **VLA classification** (0-30) — the load-bearing filter. `vla_active` (clear evidence of VLA/VLM in production or active R&D, e.g., a model card, a recent fork of openpi or openvla, an HF org with VLA fine-tunes) = 30. `vla_likely` (job posts, blog posts, demo videos referencing VLAs, but no direct artifact) = 20. `vla_possible` (right vertical but no current signal) = 8. `vla_no` is dropped.
- **Pain signal** (0-20) — evidence the company is hurting on inference cost, latency, or edge constraints today. Sources: open ML infra job reqs, engineering blog posts on quantization or Jetson constraints, founder posts complaining about GPU spend.
- **Spend tier** (5-25) — A ($25k+/mo plausible, Series A or later, $20M+ raised, 50+ heads, fleet evidence), B ($5k-$25k/mo, seed+ to small Series A), C (sub-$5k/mo).
- **Competitive lock-in** (0-10) — `lockin_open` (visible openness to vendor solutions) = 10. `lockin_generic_cloud` (Modal/Together/Fireworks/Replicate/Baseten) = 8. `lockin_jetson_only` (visible Jetson edge commitment, no cloud) = 8. `lockin_unknown` = 4. `lockin_diy` (visible custom infra build) = 0, and disqualifies a row from Tier 1.
- **Openness score** (0-15) — public technical posture: blog cadence, papers, GitHub org activity, HF presence. Higher openness means more receptive to a developer-tool PLG pitch.

Tiers: **Tier 1** ≥ 70 (full dossiers, capped at 20), **Tier 2** 45-69, **Tier 3** 25-44, **drop** < 25.

## Buyer identification

For Tier 1 and Tier 2 rows, we identify a named buyer in this order: CTO; Head of ML / AI / Robotics Software; technical founder if the company is under 25 people; VP Eng if no CTO; Robotics Lead or Embodied AI Lead.

For each buyer we record LinkedIn (always), X handle and GitHub (if findable), the most recent public signal about robotics inference (with URL and date), a warm intro path (shared investor with Reflex, mutual connection, alumni overlap; null if cold), and a specific first-touch hook — one sentence that names the actual thing in their last public signal. Generic hooks are banned. A null hook is better than a generic one.

## Data quality bar

Every URL in the dataset was HEAD-checked with a 5-second timeout, following up to 3 redirects. Any 4xx, 5xx, timeout, or login-wall redirect was either replaced with a working source or set to null with a reason. The link-check log is at `/data/link_check_log.csv` in the repo.

Every quote from a source is under 15 words. Anything longer is paraphrased into our own voice with attribution.

No company appears with a domain that 404s, a LinkedIn under 5 employees, or a last news mention over 18 months old.

## Known gaps

- **No Crunchbase paid data.** Funding numbers come from press releases, the Robot Report, TechCrunch, and company announcements. Some `total_raised_usd` figures may lag a recent round we did not catch.
- **LinkedIn employee counts are scraped, not API-fed.** They reflect the public-facing number on the day of pull. Growth-rate estimates (`headcount_growth_6mo`) are best-effort from Wayback or visible profile counts and should be treated as directional, not exact.
- **Buyer identification is verified twice (LinkedIn plus one other public source) where possible**, but for stealth-ish companies the second verification source can be thin. Those rows are flagged `buyer_verified: linkedin_only`.
- **Spend-tier rationale is rough.** It is an order-of-magnitude estimate, not a quoted price.
- **No primary research with the companies.** Everything here is from public sources. Treat the map as a high-quality starting point for outbound, not a closed deal pipeline.

## Suggested 30-day workflow

1. **Day 1.** Open the map. Read the top 10 dossiers. Pick the 5 with the strongest pain signal AND the warmest intro path. These are your week-one outbound batch.
2. **Days 2-5.** For each of those 5, ask the warm intro contact for a forward. If no warm path, send the cold DM hook from the dossier verbatim or as a starting point.
3. **Days 6-10.** Use the second-tier picks (next 10 dossiers) for a second outbound batch. By now you have at least 1-2 calls booked from week one.
4. **Days 11-20.** Layer in Tier 2 rows from the map (no dossier, but the row has VLA classification, pain score, spend tier, vertical). These are SDR fodder — a templated cold email mentioning the specific VLA evidence cited in their row will outperform a generic one 3-5x.
5. **Days 21-30.** Refresh the data. The pain signals (job posts, blog posts) move. A company that was pain-1 last month can be pain-3 this month after a public post about inference cost.

## Limitations

This is a one-session research artifact, not a maintained product. The scoring is opinionated and trades recall for precision. There are real prospects this map will miss because they have no public technical posture (openness=0). Conversely, a company with a screaming public posture but quiet revenue may rank higher than its actual budget warrants — the spend tier is the corrective.

If a row is wrong, the spec is "drop the row, do not fix and ship." There may be rows you would have kept that were dropped on a single weak signal. That is by design.
