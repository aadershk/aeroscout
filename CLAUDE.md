# AeroScout — Project Memory
# Auto-loaded by Claude Code at the start of every session.
# Do NOT delete. Edit freely as the project evolves.

## What this project is
Autonomous job-hunting tool for Aadersh Kalyanasundaram.
Scrapes Netherlands job market, filters, scores, and ranks roles.
Single command: `python main.py` — no GUI, no database, no auth.

## Owner profile
- MSc Data Science & Business Analytics, UvA, graduating June 2026
- Skills: Python, SQL, ML, operations research, statistics, data visualisation
- Language: English only — Dutch fluency requirement = hard disqualify
- Location target: Netherlands (Amsterdam/Schiphol area primarily)
- NOT available for: internships, PhD positions, senior roles (5+ yrs exp required)

## Target roles (score these highest)
TIER 1 — Aviation-specific analytics (ideal):
  Revenue Management Analyst, Yield Analyst, Pricing Analyst (airline),
  Operations Research Analyst/Scientist, Network Planning Analyst,
  Demand Forecasting Analyst, MRO Analytics Engineer, Fleet Optimisation Analyst,
  Capacity Planning Analyst, Schedule Optimisation Analyst,
  Aviation Data Scientist, Commercial Analyst (airline)

TIER 2 — Quantitative / DS (strong):
  Data Scientist, ML Engineer, Quantitative Analyst, Decision Scientist,
  Supply Chain Data Scientist, Logistics Analytics Analyst,
  Transport Economics Analyst, Management Consultant (analytics practice),
  Simulation Analyst, Statistical Analyst/Modeller

TIER 3 — BI / Data (acceptable fallback):
  Data Analyst, Analytics Engineer, BI Analyst/Developer,
  Data Engineer (aviation/consulting companies ONLY), Insights Analyst,
  Performance Analyst, Commercial Analytics Analyst

## Target companies (score by tier)
TIER A +45 (aviation ecosystem):
  KLM, Air France-KLM, Transavia, Corendon, TUI fly NL,
  Amadeus, Sabre, Navitaire, SITA, IBS Software, FLYR Labs, Aviobook,
  Cirium, OAG, NAVBLUE, Lufthansa Systems,
  Schiphol Group, Eurocontrol, EASA, LVNL,
  NACO, To70, Seabury Consulting, Aevean, NLR,
  AerCap, Fokker Services, Menzies Aviation, Swissport, dnata,
  Travix, Kiwi.com, Booking.com

TIER B +30 (consulting / transport / logistics):
  McKinsey, BCG, Bain, Oliver Wyman, Roland Berger, Kearney, Strategy&,
  Deloitte, KPMG, PwC, EY, Accenture, Capgemini, IBM,
  Steer, Jacobs, Mott MacDonald, Arcadis, Royal HaskoningDHV, Goudappel,
  NS, ProRail, Port of Rotterdam, Port of Amsterdam, LVNL,
  DHL, Maersk, DSV, PostNL, Kuehne+Nagel

TIER C +15 (finance/tech MNCs):
  ING, ABN AMRO, Rabobank, NN Group, Aegon, Achmea,
  ASML, Philips, Shell, NXP, Wolters Kluwer, Heineken, Adyen,
  Microsoft NL, Google Amsterdam, Amazon NL, Uber Amsterdam, TomTom

TIER D +8 (mid tech):
  Databricks, Snowflake, Palantir, Elastic, Spotify Amsterdam,
  Atlassian, Catawiki, Sendcloud, Bunq, Miro, Picnic, Bol.com, Coolblue

## Hard rejection rules (non-negotiable)
ALWAYS reject these — never appear in output:
  - Internship / stage / meewerkstage / afstudeerstage / \bintern\b
  - PhD / doctoral position / student assistant
  - Pilots, cabin crew, aircraft mechanics, NDT inspectors
  - EMC/RF/radar/wind tunnel/structural/composites engineers
  - Sysadmins, DevOps, cloud/security engineers (non-data)
  - HR, recruitment, talent acquisition (non-data)
  - Sales, account managers, BDMs (non-data)
  - Product Manager (UNLESS "Data Product Manager")
  - Dutch fluency required (vloeiend Nederlands, moedertaal, C1 Dutch, etc.)
  - Temp/staffing agency (Hays, Randstad, Manpower, Hinttech, Fitura, etc.)
  - Senior role with 5+ years experience required

## Project structure
aeroscout/
  CLAUDE.md          ← this file
  main.py            ← entry point, CLI flags
  core/
    gate.py          ← two-stage relevance filter
    scorer.py        ← aviation-first scoring model
    normalise.py     ← title normalisation, URL validation
    dedup.py         ← two-level deduplication
  sources/
    workday.py
    greenhouse.py
    lever.py
    recruitee.py
    smartrecruiters.py
    ashby.py
    teamtailor.py
    workable.py
    personio.py
    adzuna.py
    stepstone.py
    linkedin.py
    indeed.py
    direct.py
  output/
    display.py       ← Rich terminal table, URL list, score breakdown
    save.py          ← timestamped .txt file writer

## Key technical constraints
- Python 3.11.9, Windows 11, PowerShell
- Dependencies: aiohttp, rich, beautifulsoup4[lxml], lxml, certifi ONLY
- asyncio pipeline — never blocking calls
- Per-domain semaphore(3) to prevent IP bans
- ClientTimeout(connect=8, sock_read=18) — NOT total= only
- certifi SSL — never ssl=False globally
- _norm(title) applied EVERYWHERE before any regex/hash/display
- rich.markup.escape() on ALL untrusted API strings before Rich rendering
- _valid_url() check before every enrichment HTTP call
- Workday ext paths start with "/" — f"{base_root}{ext}" NOT f"{base_root}/{ext}"

## Scoring model (quick reference)
Dutch language required          → -200
English environment detected     → +15
Title T1 (RM/OR/pricing/MRO)    → +55
Title T2 (DS/ML/consulting)     → +30
Title T2b (DA/BI/data eng)      → +20
Description hits T1             → +15
Aviation domain hits            → +8 each, max +48
Tool stack hits                 → +4 each, max +16
Junior/graduate signal          → +20
Senior signal in title          → -90
Company tier A/B/C/D            → +45/+30/+15/+8
NL location unconfirmed         → -40
Temp/staffing agency            → -50
Domain mismatch (non-av co + 0 aviation hits) → -25
MIN_SCORE default               → 40

## Session workflow
- Use /plan (Shift+Tab x2) for research and planning — read-only, no side effects
- Use /compact when context approaches 75% full
- Use /cost after each major phase to track spend
- Reference files with @ syntax: @core/scorer.py instead of describing it
- One change per message in build phase — never bundle multiple fixes
- Run `python -m pytest tests/ -v` after every significant change

## Known issues to fix (update this list as issues are resolved)
- LinkedIn: needs rate limiting + User-Agent rotation to avoid soft blocks
- Indeed NL: pagination not yet implemented
- Some Teamtailor slugs unverified — mark dead ones here when found
- SmartRecruiters: some company IDs may be stale
