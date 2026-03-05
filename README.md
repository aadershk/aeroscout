# AeroScout

Autonomous job aggregator for the Netherlands market. Fetches listings from ATS and job boards, filters by relevance, scores and ranks them, and prints a terminal table plus an optional timestamped `.txt` file. No GUI, database, or auth.

**Focus:** Aviation and analytics roles (revenue management, operations research, data science, BI) in the Netherlands; English-only environments. Internships, PhDs, senior-only and Dutch-fluency-required roles are excluded.

---

## Requirements

- **Python 3.11+**
- Dependencies: `aiohttp`, `rich`, `beautifulsoup4`, `lxml`, `certifi`

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Usage

| Command | Description |
|--------|-------------|
| `python main.py` | Full run; min score 40 |
| `python main.py --min-score 50` | Raise qualifying threshold |
| `python main.py --debug` | Verbose logging |
| `python main.py --test-sources` | One request per source (LIVE/DEAD) |
| `python main.py --dry-run --limit 5` | Full pipeline, show first 5 jobs only |
| `python main.py --output-dir ./results` | Write `.txt` to custom directory |

---

## Pipeline

1. **Fetch** — 14 sources (Workday, Greenhouse, Lever, LinkedIn, Adzuna, Indeed, StepStone, etc.) in parallel with per-domain rate limits.
2. **Dedup** — Title+company normalisation and URL-level deduplication.
3. **Gate** — Hard filters (internships, Dutch-only, senior-only, non-data roles, agencies).
4. **Score** — Title tier, company tier, aviation/description signals, location.
5. **Output** — Rich table to terminal; optionally save scored list to `aeroscout_YYYYMMDD_HHMMSS.txt`.

---

## Layout

```
aeroscout/
  main.py           # Entry point, CLI
  core/             # Gate, scorer, normalise, dedup, models
  sources/          # Per-source fetchers (workday, greenhouse, …)
  output/           # Display (Rich), save (.txt)
  tests/            # pytest
```

---

## Tests

```bash
python -m pytest tests/ -v
```

---

## License

Private use. No warranty.
