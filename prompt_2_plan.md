PROMPT 2 — PLANNING PHASE
Use this prompt in Plan Mode, AFTER reviewing research.md.
Still read-only. Claude produces plan.md — no code yet.
=========================================================================

Read @CLAUDE.md and @research.md before starting.

Produce plan.md — a complete, numbered implementation blueprint.
Every architectural decision must be documented with rationale.
No code yet. This is the document I will edit before you build anything.

---

PLAN.MD MUST CONTAIN:

## 1. Project structure
Show the exact file tree. Follow the structure in CLAUDE.md unless
research revealed a reason to change it. Explain any deviations.

## 2. Source manifest
A table: source name | type | verified URL | # targets | search terms/queries
Only include sources confirmed live in research.md.
Mark which sources need User-Agent rotation (LinkedIn, Indeed).
Note which sources return description in the initial fetch vs. need enrichment.

## 3. Pipeline design
Exact sequence:
  a. Parallel fetch across all sources
  b. quick_gate on title (before enrichment) — what % of requests does this save?
  c. Parallel enrichment (only gate-passed jobs)
  d. Deduplication (two levels — document exactly how uid is computed)
  e. full_gate (post-enrichment)
  f. Scoring
  g. Output

Concurrency numbers: global semaphore N, per-domain semaphore N, TASK_TIMEOUT.
Justify each number.

## 4. Gate logic design
Two-stage gate. Write out the full regex design:

REJECT_INTERN: every pattern that catches internships/PhD (list all)
REJECT_NON_DATA: every category with example patterns
  - include negative-lookaheads so "Data Security Analyst" is NOT rejected
  - list every role family: flight crew, mechanics, IT infra, HR, sales, PM, etc.

RELEVANCE_TITLE: complete list of positive patterns covering ALL target roles
  - Must cover every role in Tier 1, 2, 3 from CLAUDE.md
  - Include Dutch variants where applicable

RELEVANCE_DESC fallback: lighter pattern set for description-only matches

## 5. Scoring model
Document every signal with score value and rationale.
Note: domain_mismatch triggers when company tier is C/D/unknown AND domain_hits == 0.
Note: senior_pen -90 applies to TITLE only, not description.
Document the exact aviation domain keyword list (justify each inclusion).
Document the tool stack keyword list.

## 6. Normalisation design
_norm(title): exact transformations in order (camelCase, strip codes, strip brackets)
_valid_url(): exact validation logic
_esc(): when and where applied (ALL Rich rendering paths)

## 7. Deduplication design
Level 1: exact URL match (normalised — strip trailing slash, lowercase)
Level 2: uid = MD5(norm_title.lower()[:40] + "|" + company.lower()[:20])
Document why this catches cross-source duplicates from same company.

## 8. Output design
Terminal:
  - Score table (score-coloured rows, no URL column — too wide)
  - Full URL list below table — each URL on its own line, clickable [link=URL]
  - Score breakdown (plain console.print, NOT Rich Table — avoids wrap bug)
  - Zero-result source report
File:
  - aeroscout_YYYYMMDD_HHMMSS.txt next to main.py
  - Contains: rank, score, seniority, title, company, location, url, breakdown, preview

## 9. Module responsibilities
For each file in the project structure:
  - One-line purpose
  - Public functions/classes it exports
  - What it imports from other modules

## 10. Test plan
List 15 specific test cases with expected outcomes. Examples:
  - "Data Science Intern" at NXP → rejected by REJECT_INTERN
  - "SeniorDataEngineer" → _norm → "Senior Data Engineer" → rejected by senior_pen
  - "Revenue Management Analyst" at Transavia → score >= 100
  - "I261217-002 SeniorDataEngineer" → _norm strips code prefix first
  - Job with url "javascript:void(0)" → _valid_url returns False
  - "Vloeiend Nederlands vereist" in description → dutch_penalty -200
  Add 10 more relevant cases based on your research findings.

## 11. Token efficiency strategy
Given the owner wants minimal token usage in future sessions:
  - Which modules change most often → should be kept short
  - Which modules are stable → can be longer
  - Recommended /compact trigger point (% context fill)
  - Which tasks to delegate to sub-agents

## 12. Numbered task checklist
Every implementation step in order. This is what I will approve/annotate
before you write any code. Be specific — not "write gate.py" but:
  "1. Create core/normalise.py — _norm(), _valid_url(), _is_nl(), _esc()"
  "2. Create core/gate.py — REJECT_INTERN, REJECT_NON_DATA, RELEVANCE_TITLE,
      RELEVANCE_DESC, quick_gate(), full_gate()"
  ... and so on through every file and every function.

---

After writing plan.md, stop and tell me it is ready.
List any questions you have before I review it.
Do NOT start building until I explicitly say "proceed with task 1".
