# Methodology

## Universe

A robotics company is included if it builds robots or robotics software as a core product, has shipped a public demo or raised at least seed from a named investor, and is not on the exclusion list.

Excluded: trillion-dollar parents that built their own inference (Tesla, Google DeepMind, Meta, Apple, Amazon Robotics); $1B+ companies publicly committed to in-house infra (Figure, 1X, Skild, Sanctuary, Boston Dynamics, Agility, Apptronik); pure hardware/component plays with no ML stack; pure RL or classical-control shops with no language or vision component; defense primes; PRC-state-funded research labs and hyperscalers; companies dead, acquired, or pivoted in the last 12 months.

## Sources

- Robot Report RBR50 (last 3 years), humanoid-robot-startup trackers
- VC portfolios: Khosla, Sequoia, a16z, Lux, Eclipse, NVentures, Construct, 8VC, Bessemer, Greylock, GV, Founders Fund, Boldstart
- Y Combinator W23-W26 robotics, HAX (SOSV), MassRobotics
- GitHub org-account forkers of openpi, openvla, lerobot, Isaac-GR00T, SmolVLA, Octo, ALOHA, Mobile-ALOHA, RT-X
- HuggingFace organizations with VLA / robotics-tagged models
- 2025-2026 robotics news: TechCrunch, Robot Report, Sifted, Tech.eu, FreightWaves, ConstructionDive, AgFunder, MedTech Innovator
- International press: 36Kr, KED Global, Bridge Tokyo, EU-Startups, Calcalist, YourStory

530+ raw rows pre-dedup → 155 in the published map.

## Signal

Each company gets a VLA classification — the load-bearing filter:

- **Running VLAs today** — direct evidence in their public stack: model card, recent fork of openpi or openvla, HuggingFace organization with VLA fine-tunes
- **Building toward VLAs** — job posts, blog posts, demos, or founder posts referencing VLAs, but no direct artifact yet
- **Adjacent / possible** — right vertical (humanoid, dexterous manipulation) but no current signal

Companies with no robotics ML stack are dropped.

## Buyers

For the top scorers, we identify a named buyer in this priority: CTO; Head of ML / AI / Robotics Software; technical founder if the company is under 25 people; VP Eng if no CTO; Robotics Lead. LinkedIn URL is required, plus one second source where possible. Where no clean buyer surfaced (mostly Chinese-only-public founders or large IT consultancies), the field is `not_found` rather than fabricated.

Each dossier carries one specific first-touch hook tied to the buyer's most recent public signal. Generic hooks were banned; if no specific signal was reachable, the field reads `no specific hook found`.

## Data quality

Every URL was async HEAD-checked. LinkedIn, Crunchbase, Pitchbook, and a handful of news domains return 403 / 999 to bots but resolve in any browser — those are flagged `BOTBLOCK_OK` rather than dropped. Zero genuinely broken links.

Every quote from a source is under 15 words. No company appears with a dead domain, a LinkedIn under 5 employees, or a last news mention over 18 months old.

## Known gaps

- Funding figures from press releases and trade press, not paid Crunchbase data
- LinkedIn employee counts are scraped, not API-fed
- A quarter of buyer slots are `not_found` rather than fabricated names
- Some HQ rows are blank (stealth or non-English-only sites)
- Edge-deployed companies with strong DIY commitments are flagged but kept on the map for context — they are not near-term Reflex customers

## Suggested workflow

Click any orange marker. The brightest dots are running VLAs in production; the lit ones with a white ring have a full dossier. Filter by region or vertical to narrow down. Read the dossier, send the hook, talk to the buyer.
