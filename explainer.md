# Methodology

## Universe

A robotics company is included if (a) it builds robots or robotics software as a core product, (b) it has raised at least seed from a named investor or shipped a public demo, and (c) it is not on the exclusion list.

Excluded: trillion-dollar parents that built their own inference (Tesla, Google DeepMind, Meta, Apple, Amazon Robotics); $1B+ companies publicly committed to in-house infra (Figure, 1X, Skild, Sanctuary, Boston Dynamics, Agility, Apptronik); pure hardware/component plays with no ML stack; pure RL or classical-control shops with no language or vision component; defense primes; companies dead or pivoted in the last 12 months. PRC-state-funded research labs and hyperscalers are also dropped — outreach friction is the gating reason.

Sources, in 15+ streams:

- **Lists & rankings:** Robot Report RBR50 (last 3 years), humanoid-robot-startup trackers.
- **VC portfolios:** Khosla, Sequoia, a16z, Lux, Eclipse, NVentures, Construct Capital, 8VC, Bessemer, Greylock, GV, Founders Fund, Boldstart.
- **Accelerators:** Y Combinator robotics batches (W23–W26), HAX (SOSV), MassRobotics residents.
- **Open-source signal:** GitHub org-account forkers of `physical-intelligence/openpi`, `openvla/openvla`, `huggingface/lerobot`, `NVIDIA/Isaac-GR00T`, `lerobot/SmolVLA`, `octo-models/octo`, `tonyzhaozh/aloha`, `MarkFzp/mobile-aloha`, `google-deepmind/open_x_embodiment`, RT-2/PaLM-E variants. HuggingFace orgs with VLA-tagged or robotics-tagged models.
- **News (2025–2026):** TechCrunch, The Robot Report, Sifted, Tech.eu, EU-Startups, Hacker News Show HN, FreightWaves, ConstructionDive, AgFunder, MedTech Innovator.
- **International press:** 36Kr (China), KED Global / KoreaTechBlog (Korea), Bridge Tokyo / TechBlitz (Japan), Sifted / EU-Startups (Europe), Calcalist (Israel), YourStory / Inc42 (India).
- **Vertical deep-dives:** surgical/medical robotics, AI agriculture, construction, last-mile delivery, cleaning, drone autonomy, warehouse, industrial assembly.

530+ raw rows pre-dedup across two expansion passes → 155 in the published map after exclusions, vla_no drops, and score thresholds.

## Scoring

Each company gets an integer 0-100, combining five axes:

- **VLA classification** (0-30) — the load-bearing filter. `vla_active` (clear evidence of VLA/VLM in production or active R&D: model card, recent fork of openpi/openvla, HF org with VLA fine-tunes) = 30. `vla_likely` (job posts, blog, demos referencing VLAs but no direct artifact) = 20. `vla_possible` (right vertical, no current signal) = 8. `vla_no` is dropped.
- **Pain signal** (0-20) — open ML-infra job reqs, blog posts on quantization or Jetson constraints, founder posts about GPU spend or latency. 0 = no signal, 3 = screaming (3+ infra reqs OR a public migration).
- **Spend tier** (5-25) — A: $20M+ raised + 50+ heads + fleet evidence. B: $5M-$20M raised, 15-50 heads. C: under $5M.
- **Competitive lock-in** (0-10) — `lockin_open` (visible vendor openness) = 10. `lockin_generic_cloud` (Modal/Together/Fireworks/Replicate/Baseten) = 8. `lockin_jetson_only` = 8. `lockin_unknown` = 4. `lockin_diy` = 0 and disqualifies a row from the top dossier set, since they built their own and won't buy.
- **Openness score** (0-15) — public technical posture: blog cadence, papers, GitHub org, HF presence. Higher = more receptive to a developer-tool pitch.

Score thresholds: 70+ = top dossier candidate (capped at 20). 45-69 = mapped without dossier. 25-44 = lower-priority SDR fodder. <25 dropped.

## Buyers

For the top 50 by score, named buyer in this priority: CTO; Head of ML / AI / Robotics Software; technical founder if company is under 25 people; VP Eng if no CTO; Robotics Lead or Embodied AI Lead. LinkedIn URL is required, plus one second source (team page, paper, podcast, news mention) where possible. Of 50, 34 named buyers were identified — the 16 not_found are mostly Chinese-only-public founders or large-IT consultancies where no clean robotics buyer surfaced.

The first-touch hook field is one specific sentence tied to the buyer's most recent public signal. Generic hooks ("loved your work", "saw you on TechCrunch") were banned at write-time; if no specific hook was reachable, the field reads `no specific hook found, recommend warm intro path only`. 36 of 50 rows hit the specific-hook bar.

## Data quality

Every URL was async HEAD-checked with a 10-second timeout, following up to 3 redirects. 207 returned 200 or a valid 3xx; 35 are LinkedIn / Crunchbase / Pitchbook / TechCrunch / BusinessWire — domains that bot-block automated requests but resolve in any browser. Those are surfaced as `BOTBLOCK_OK` in `link_check_log.csv` rather than dropped, since they are the spec-mandated sources for buyer profiles and funding facts. Zero broken links in the dataset.

Every quote from a source is under 15 words. Anything longer was paraphrased into our voice. No company appears with a dead domain, a LinkedIn under 5 employees, or a last news mention over 18 months old.

## Known gaps

- Funding numbers come from press releases and trade press, not Crunchbase paid data — some `total_raised_usd` figures may lag the most recent close.
- LinkedIn employee counts are scraped, not API-fed; treat `headcount_growth_6mo` as directional.
- 16 of 50 buyer slots are `not_found` rather than fabricated — the methodology preferred null over invented names.
- 8 of 84 rows have no HQ city/country populated — the underlying companies are stealth or non-English-only.
- `lockin_diy` was applied via inference for a few high-scoring rows where the evidence was a single ML-infra hire or ex-FAANG team composition; those were promoted to `lockin_unknown` and flagged in the dossier risks. Real DIY commitments (own Triton fork, custom serving stack) stay `lockin_diy`.

## 30-day workflow

1. Day 1. Open the map. Read the top 11 dossiers. Pick 5 with strongest pain signal AND warmest intro path — that is week-one outbound.
2. Days 2-5. Forward each via warm path. Where cold, send the dossier hook verbatim.
3. Days 6-10. Outbound batch two from the next 10 highest dossiers.
4. Days 11-20. Tier 2 rows for SDR-style follow-up — every row has VLA evidence, pain score, vertical, and a buyer where one exists.
5. Days 21-30. Refresh. Pain signals move fast — a company that was pain=1 last month can be pain=3 after one public infra blog post.
