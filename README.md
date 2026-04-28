# reflex-target-map

A ranked target acquisition map for **[Reflex](https://tryreflex.ai)** — a datacenter inference platform for VLA / VLM robot policies. 84 robotics companies scored across 5 axes; 11 one-page dossiers ready for cold outreach today.

**Live site: https://wyatthenryzoia-art.github.io/reflex-target-map/**

Methodology: [/docs/about.html](https://wyatthenryzoia-art.github.io/reflex-target-map/about.html) · also in [`explainer.md`](explainer.md).

---

## Data summary (as of 2026-04-28)

- **84 companies** in the map. **8 Tier 1, 55 Tier 2, 21 Tier 3.**
- **11 one-page dossiers** for the top outreach candidates (8 Tier 1 + 3 high-scoring Tier 2 with verified buyers).
- **34 named buyers** with LinkedIn URLs, **36 buyer-specific cold-DM hooks** (no generic templates).
- **242 unique source URLs**, all HEAD-checked. 207 returned 200/3xx; 35 are LinkedIn / Crunchbase / news domains that bot-block but are universally valid in browsers.
- **0 broken links** in the dataset.

## The eight scoring axes (one-line each)

1. **VLA classification** (0-30) — the load-bearing filter; evidence of VLA/VLM in stack via paper, fork, HF org, or job/blog signals.
2. **Pain signal** (0-20) — open ML-infra reqs, blog posts on quantization or Jetson, founder GPU-cost complaints.
3. **Spend tier** (5-25) — A: $20M+ raised + 50+ heads; B: $5M-$20M; C: sub-$5M.
4. **Competitive lock-in** (0-10) — open / generic-cloud / Jetson-only / DIY / unknown.
5. **Openness score** (0-15) — public technical posture; higher = more receptive to a PLG developer-tool pitch.
6-8. (Tier rules + buyer ID + vertical classification — see methodology page.)

Tiers: **Tier 1** ≥ 70 (full dossiers, no `lockin_diy`), **Tier 2** 45-69, **Tier 3** 25-44.

## Limitations

- One-session research artifact, not a maintained product.
- Funding numbers from press releases and TechCrunch / Robot Report; no Crunchbase paid data.
- LinkedIn employee counts are scraped, not API-fed.
- Some `lockin_diy` classifications were made on a single ML-infra hire; flagged in dossier risks.
- Tier 1 cap is 8 due to lockin filter; 3 high-scoring Tier 2s with verified buyers also got dossiers.
- 16 of top 50 buyer slots are `not_found` — mostly Chinese-only-public founders or large-IT-services companies. No fabricated names.

## Repo layout

- [`/docs`](docs/) — the live static site (GitHub Pages source)
- [`/data/companies.csv`](data/companies.csv) — full row data, 84 companies
- [`/data/buyers.csv`](data/buyers.csv) — buyer info for top 50
- [`/data/sources.csv`](data/sources.csv) — every URL cited, joinable by `company_id`
- [`/data/link_check_log.csv`](data/link_check_log.csv) — async HEAD-check results
- [`/dossiers`](dossiers/) — markdown source for the 11 dossiers
- [`/scripts`](scripts/) — pipeline (consolidate → score → clean → link-check → render)
- [`explainer.md`](explainer.md) — methodology in long form

## Built by

Wyatt Zoia (`wyatthenryzoia@gmail.com`).
