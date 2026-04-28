# reflex-target-map

A ranked target acquisition map for **[Reflex](https://tryreflex.ai)** — a datacenter inference platform for VLA / VLM robot policies. 155 robotics companies scored across 5 axes; 20 one-page dossiers ready for cold outreach.

**Live site: https://wyatthenryzoia-art.github.io/reflex-target-map/**

Methodology: [/about](https://wyatthenryzoia-art.github.io/reflex-target-map/about.html) · also in [`explainer.md`](explainer.md).

---

## Data summary (as of 2026-04-28)

- **155 companies** in the map. **10 Tier 1, 86 Tier 2, 59 Tier 3.**
- **60 VLA-active**, 72 VLA-likely, 23 VLA-possible.
- **20 one-page dossiers** for the top outreach candidates (T1 + top-scoring T2 with verified buyers, capped at 20).
- **52 named buyers** with LinkedIn URLs across 77 buyer rows; **56 buyer-specific cold-DM hooks** (no generic templates); 6 warm intro paths surfaced.
- **424 unique source URLs**, all HEAD-checked. 362 returned 200/3xx; 62 are LinkedIn / Crunchbase / news domains that bot-block automated requests but are valid in browsers.
- **0 broken links**.
- Region split: **21 California, 45 US-other, 78 international, 11 unknown.** Default sort surfaces California first.

## Sources mined

Robotics universe pulled from 15+ source streams:
- **Lists & rankings:** Robot Report RBR50 (last 3 years), humanoid-robot-startup trackers, RBR50 2024/2025 winners.
- **VC portfolios:** Khosla, Sequoia, a16z, Lux, Eclipse, NVentures, Construct Capital, 8VC, Bessemer, Greylock, GV, Founders Fund, Boldstart.
- **Accelerators:** Y Combinator (W23–W26 robotics batches), HAX (SOSV), MassRobotics residents.
- **Open-source signal:** GitHub org-account forkers of `physical-intelligence/openpi`, `openvla/openvla`, `huggingface/lerobot`, `NVIDIA/Isaac-GR00T`, `lerobot/SmolVLA`, `octo-models/octo`, `tonyzhaozh/aloha`, `MarkFzp/mobile-aloha`, `google-deepmind/open_x_embodiment`, RT-2/PaLM-E variants. HuggingFace orgs with VLA/robotics-tagged models.
- **News (2025–2026):** TechCrunch, The Robot Report, Sifted, Tech.eu, EU-Startups, Hacker News Show HN, FreightWaves, ConstructionDive, AgFunder, MedTech Innovator.
- **International press:** 36Kr (China), KED Global / KoreaTechBlog (Korea), Bridge Tokyo / TechBlitz (Japan), Sifted / EU-Startups (Europe), Calcalist (Israel), YourStory (India).
- **Vertical deep-dives:** surgical/medical (Caresyntax-tier), agriculture, construction, last-mile delivery, cleaning/janitorial, drone autonomy, warehouse, industrial assembly.

## The five scoring axes

1. **VLA classification** (0–30) — the load-bearing filter. Active = direct evidence (model card, recent fork, HF org); Likely = job/blog/demo signals; Possible = right vertical, no signal yet.
2. **Pain signal** (0–20) — open ML-infra reqs, blog posts on quantization or Jetson constraints, founder posts on GPU spend or latency.
3. **Spend tier** (5–25) — A: $20M+ raised + 50+ heads. B: $5M–$20M, 15–50 heads. C: under $5M.
4. **Competitive lock-in** (0–10) — open / generic-cloud / Jetson-only / DIY / unknown. DIY disqualifies a row from Tier 1.
5. **Openness score** (0–15) — public technical posture (blog, papers, GitHub, HuggingFace presence).

## Limitations

- One-session research artifact, not a maintained product.
- Funding figures from press releases and trade press, not Crunchbase paid data.
- LinkedIn employee counts are scraped, not API-fed.
- 25 of 77 buyer slots are `not_found` rather than fabricated — mostly Chinese-only-public founders, large IT consultancies, or very-early stealth.
- 11 of 155 rows have no HQ city/country populated (stealth or non-English-only sites).
- `lockin_diy` was applied via inference where the evidence was a single ML-infra hire or ex-FAANG team composition; promoted to `lockin_unknown` for those and flagged in dossier risks. Real DIY commitments (own Triton fork, custom serving stack) stay `lockin_diy`.

## Repo layout

- [`/docs`](docs/) — the live static site (GitHub Pages source)
- [`/data/companies.csv`](data/companies.csv) — full row data, 155 companies
- [`/data/buyers.csv`](data/buyers.csv) — buyer info, 77 rows
- [`/data/sources.csv`](data/sources.csv) — every URL cited, 424 unique
- [`/data/link_check_log.csv`](data/link_check_log.csv) — async HEAD-check results
- [`/dossiers`](dossiers/) — markdown source for the 20 dossiers
- [`/scripts`](scripts/) — pipeline (consolidate → score → clean → link-check → render)
- [`explainer.md`](explainer.md) — methodology in long form
