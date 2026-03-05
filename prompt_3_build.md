PROMPT 3 — BUILD PHASE
Use this prompt in normal mode (Plan Mode OFF).
Give this AFTER you have reviewed and approved plan.md.
=========================================================================

Read @CLAUDE.md and @plan.md before starting.

Execute the approved plan. Work through the task checklist in plan.md
in exact order. Do not skip steps. Do not bundle multiple tasks into one.

EXECUTION RULES:
1. Complete one task from the checklist, then run its tests, then move on.
2. After writing any Python file, immediately run:
   python -m py_compile {filename} && echo "SYNTAX OK"
3. After all core/ modules are written, run:
   python -m pytest tests/test_gate.py tests/test_scorer.py -v
   Fix all failures before touching sources/.
4. After writing sources/, run a connectivity test:
   python main.py --test-sources
   This should attempt one request per source and print LIVE/DEAD status.
   Write this --test-sources flag into main.py from the start.
5. Final integration test: python main.py --dry-run --limit 3
   (fetches real data but only processes 3 jobs through the full pipeline)
   Confirm the output renders cleanly in the terminal.
6. Full run: python main.py
   Report what you see.

WRITE tests/ AS YOU GO:
- tests/test_normalise.py — test _norm() on the CamelCase cases, code prefixes, etc.
- tests/test_gate.py — all 15 test cases from plan.md
- tests/test_scorer.py — score verification for KLM aviation role vs NXP chip role
- tests/test_dedup.py — confirm URL-exact and uid-based dedup both work

QUALITY GATES (do not proceed past these without passing):
- Zero syntax errors across all files
- All tests in tests/ pass
- --test-sources shows at least 8 sources LIVE
- Terminal output renders without Rich markup errors
- Output file is created and contains full URLs

AFTER THE FULL RUN:
Report:
  - Raw count fetched
  - After dedup count
  - After gate count
  - Qualifying count (score >= 40)
  - Top 5 results with scores
  - Any sources that returned 0 results
  - Runtime in seconds
  - Any errors or warnings that appeared

Then stop and wait for my feedback before making any changes.

---

CODING STANDARDS TO FOLLOW THROUGHOUT:

Async:
  - Every fetcher is async def fetch_X(session, sem, target) -> list[Job]
  - Every fetcher wrapped with asyncio.wait_for(..., timeout=TASK_TIMEOUT)
  - Never asyncio.sleep with fixed values — always _jitter(attempt)

HTTP:
  - ClientTimeout(connect=CONNECT_TIMEOUT, sock_read=READ_TIMEOUT)
  - Per-domain semaphore via _domain_sems.get(url)
  - ssl=_SSL (certifi context or system bundle — never False globally)
  - _parse_ct() to extract MIME type before deciding json vs text parse

Safety:
  - _norm(title) called on EVERY title before ANY processing
  - rich.markup.escape() on ALL untrusted strings in display.py
  - _valid_url() called before EVERY enrichment fetch
  - try/except around every fetcher body — one source failing != crash

Dedup:
  - uid = hashlib.md5(f"{_norm(title).lower()[:40]}|{company.lower()[:20]}".encode()).hexdigest()[:14]
  - This must be computed in Job.__post_init__, not at dedup time

CLI flags in main.py:
  --min-score N      default 40
  --debug            show DEBUG level logs
  --test-sources     test one request per source, report LIVE/DEAD
  --dry-run          run full pipeline, limit output to first 3 qualifying jobs
  --output-dir PATH  where to save .txt file (default: next to main.py)

Logging:
  - Expected 404s / empty API responses → log.debug(), not log.warning()
  - Genuine unexpected errors → log.warning()
  - Never log.warning for a company slug that simply has no open roles

Comments:
  - One-line comment per non-obvious decision
  - No paragraph-length docstrings — keep them to one line
  - No commented-out dead code

---

TOKEN EFFICIENCY DURING BUILD:
- Use @filename syntax when referencing existing files
- After finishing each module, type /compact to keep context lean
- If I ask "why did you do X", answer in 2 sentences max
- Do not summarise what you just wrote — I can read it
