# AeroScout Claude Code — Quick Reference
# Print this or keep it open in a second window during each session.

═══════════════════════════════════════════════════════════
 SETUP (one-time, ~5 minutes)
═══════════════════════════════════════════════════════════

1. Create the project folder:
   mkdir C:\Users\Aader\aeroscout
   cd C:\Users\Aader\aeroscout

2. Copy CLAUDE.md into this folder.

3. Install dependencies (if not already):
   pip install aiohttp rich "beautifulsoup4[lxml]" lxml certifi pytest

4. Launch Claude Code:
   claude

5. On first launch, run:
   /init
   (This reads CLAUDE.md and sets up project memory)


═══════════════════════════════════════════════════════════
 SESSION 1 — RESEARCH  (Plan Mode)
═══════════════════════════════════════════════════════════

Step 1. Activate Plan Mode:
  Press Shift+Tab twice
  Look for "⏸ plan mode on" at the bottom

Step 2. Paste the full contents of prompt_1_research.md

Step 3. Let it run. It will browse, fetch, and write research.md.
  This takes 15-30 minutes. Do not interrupt.

Step 4. When it stops and says "research.md is ready":
  - Open research.md in any text editor
  - Review DEAD SOURCES and LINKEDIN FINDINGS especially
  - Add any corrections or notes directly into research.md
  - Type: "research.md reviewed. Proceed to planning."

Step 5. Paste the full contents of prompt_2_plan.md

Step 6. Let it produce plan.md. Review it carefully.
  Open plan.md in a text editor.
  Annotate with any changes you want (add a company, change a score, etc.)
  Type: "plan.md reviewed and annotated. I approve the plan. Proceed."

Step 7. Type /compact before ending session 1.
  This compresses history, saves tokens in session 2.


═══════════════════════════════════════════════════════════
 SESSION 2 — BUILD  (Normal Mode)
═══════════════════════════════════════════════════════════

Step 1. Launch Claude Code in the same folder:
  cd C:\Users\Aader\aeroscout
  claude -c   ← continues last session with full context

Step 2. Confirm Plan Mode is OFF (should be off by default on launch).

Step 3. Paste the full contents of prompt_3_build.md

Step 4. Let it build. Do not interrupt mid-task.
  If it asks a clarifying question, answer with one sentence.
  If it shows you code to review, type "looks good, continue" or
  give a specific correction.

Step 5. After each module is written, it runs tests automatically.
  Watch for test failures — Claude will fix them itself.

Step 6. After the first full run:
  - Review the terminal output carefully
  - Check the aeroscout_*.txt file it created
  - Note any false positives (wrong roles appearing) or false negatives
    (a KLM role you expected that is missing)

Step 7. For each issue, open a NEW targeted message:
  "Job #7 is 'Data Science Intern' — it should be rejected.
   Show me which gate rule should catch it and why it didn't."


═══════════════════════════════════════════════════════════
 ONGOING ITERATION SESSIONS
═══════════════════════════════════════════════════════════

Every future session:
  cd C:\Users\Aader\aeroscout
  claude -c   ← continues with memory

One issue per message. Never bundle.
Reference files with @: "@core/gate.py needs a fix..."
Run /compact every ~20 messages.
Run /cost to check spend — aim for under $2 per session.

For scoring adjustments:
  "In @core/scorer.py, Transavia is Tier A but it scored 35 on
   'Commercial Analyst'. Why? Show me the score_detail for that job."

For new sources:
  "Add Goudappel (transport consultancy) to sources/workable.py.
   Their Workable slug is 'goudappel'. Follow the exact pattern
   of the other Workable targets."

For dead slugs found during a run:
  "The zero-results report showed 'ibssoftware' on Teamtailor.
   Find the correct Teamtailor slug for IBS Software and update
   sources/teamtailor.py."


═══════════════════════════════════════════════════════════
 KEY COMMANDS TO KNOW
═══════════════════════════════════════════════════════════

Shift+Tab x2    Toggle Plan Mode on/off
/compact        Compress conversation history (use at 75% context)
/cost           Show tokens used + cost this session
/clear          Start fresh (loses session history — use carefully)
claude -c       Resume last session from terminal
@filename       Inject file contents into your message
!command        Run a shell command directly (e.g., !python main.py)


═══════════════════════════════════════════════════════════
 WHAT "GOOD OUTPUT" LOOKS LIKE
═══════════════════════════════════════════════════════════

After a full run, the output should have:
  - 15-30 qualifying roles (score >= 40)
  - Top roles scoring 80-120 (KLM/Amadeus/Transavia revenue mgmt roles)
  - Mid roles scoring 50-75 (DS roles at Tier B consulting firms)
  - Lower roles scoring 40-49 (DA roles at Tier C finance companies)
  - ZERO interns, ZERO senior roles, ZERO PM roles, ZERO Dutch-required roles
  - Every URL in the link list opening to an actual job posting
  - aeroscout_YYYYMMDD_HHMMSS.txt created next to main.py

If you see temp agency companies or intern roles — that is a gate bug.
Report the exact job title and company to Claude Code for a fix.


═══════════════════════════════════════════════════════════
 FILES IN THIS PROJECT
═══════════════════════════════════════════════════════════

CLAUDE.md             ← project memory (auto-loaded every session)
prompt_1_research.md  ← paste this in Session 1 Plan Mode
prompt_2_plan.md      ← paste this after reviewing research.md
prompt_3_build.md     ← paste this in Session 2 Normal Mode
quick_reference.md    ← this file

After Session 1:
  research.md         ← Claude's verified source findings (review + annotate)
  plan.md             ← Claude's implementation blueprint (review + annotate)

After Session 2:
  main.py             ← run this
  core/               ← gate, scorer, normalise, dedup
  sources/            ← one file per data source
  output/             ← display and file writer
  tests/              ← pytest suite
  aeroscout_*.txt     ← your job results (one per run)
