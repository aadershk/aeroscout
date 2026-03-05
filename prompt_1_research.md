PROMPT 1 — RESEARCH PHASE
Use this prompt in Plan Mode (Shift+Tab x2 to activate).
Claude will research and produce research.md — READ ONLY, no code written yet.
=========================================================================

We are building AeroScout: an autonomous job-hunting script for a specific
profile. Read @CLAUDE.md for full context before doing anything.

You are in Plan Mode. Use web search and web fetch only. Write everything
you discover to research.md. Do not write any Python yet.

---

TASK: Research and verify every job source we will use. For each source,
confirm it is live, confirm the correct endpoint/format, and note any
changes since 2024.

Work through these sources in order. For each one, actually fetch the
endpoint and record what you find — do not assume anything works.

SECTION 1 — ATS APIs (structured JSON sources)

1. WORKDAY
   For each company below, find the correct Workday subdomain and POST
   endpoint. Test the POST body: {"limit": 5, "offset": 0, "searchText": "data analyst"}
   Verify it returns jobPostings[]. Note the exact base URL.
   Note: the externalPath field starts with "/" — record this.

   Companies to find + verify:
   KLM (try klm.wd3.myworkdayjobs.com), Air France-KLM, Amadeus,
   TUI Netherlands, Accenture NL, Capgemini NL, BCG, Kearney,
   ING Group, ABN AMRO, Rabobank, NN Group, Philips, ASML, Shell NL,
   Heineken, Adyen, DHL, PostNL, Vanderlande, Maersk, Royal HaskoningDHV,
   DSV Netherlands, Aegon, AerCap (PRIORITY — large aviation lessor),
   Wolters Kluwer, NXP Semiconductors

   For each: record {"company": "...", "base": "https://..."}
   Mark DEAD if endpoint returns non-200 or no jobPostings key.

2. GREENHOUSE
   Endpoint: GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
   For each token, fetch and confirm it returns {"jobs": [...]}

   Find + verify tokens for:
   bookingcom, travix, flyrlabs, tomtom, messagebird, palantir, databricks,
   aviobook, snowflakecareers, spotify, elastic, miro, uber, atlassian,
   kiwi, cirium, netflix, catawiki, sendcloud, travelperk, picnic

   Mark DEAD if 404 or empty jobs array.

3. LEVER
   Endpoint: GET https://api.lever.co/v0/postings/{token}?mode=json
   Find + verify tokens for:
   schiphol, transavia, catawiki, sendcloud, seabury, to70, naco,
   corendon, aevean, bunq, coolblue

4. RECRUITEE
   Endpoint: GET https://{slug}.recruitee.com/api/offers/
   Verify: transavia, nlr, royalhaskoningdhv, fokker, menzies, swissport,
   aercap, vanderlande, lvnl, portofrotterdam

5. SMARTRECRUITERS
   Endpoint: GET https://api.smartrecruiters.com/v1/companies/{cid}/postings?country=nl
   Verify these company IDs still work:
   Airbus, AirFranceKLM, GEAviation, Deloitte, KPMG, PricewaterhouseCoopers,
   ErnstYoung, RollsRoyce, Capgemini, SITAAeroIT, OliverWyman,
   McKinseyAndCompany, CollinsAerospace, Maersk, DSVRoadAS, Achmea, APG

6. ASHBY
   Endpoint: POST https://api.ashbyhq.com/posting-api/job-board
   Body: {"organizationHostedJobsPageName": "{name}"}
   Verify: FLYR, aevean, picnic

7. TEAMTAILOR
   Endpoint: GET https://{slug}.teamtailor.com/jobs.json
   This one is critical — many slugs are dead. Test EVERY one:
   klm, transavia-nl, corendon, schiphol, fokker, to70, aevean, naco,
   ibssoftware, flyr, travix, nngroup, prorail, ns, postnl, sendcloud,
   vanderlande, seaburyconsulting, steer, royalhaskoningdhv, coolblue,
   portofrotterdam, bunq, eurocontrol
   
   For each: fetch and check if data.[] array has any items.
   Record which are LIVE and which are DEAD.

8. WORKABLE
   Endpoint: POST https://apply.workable.com/api/v3/accounts/{slug}/jobs
   Verify: eurocontrol, navblue, sabre, arcadis, mottmacdonaldgroup,
   jacobs, rolandberger, portofrotterdam, goudappel, steer, wsp

9. PERSONIO
   Two possible paths — test BOTH for each company:
   GET https://{slug}.jobs.personio.de/api/v1/jobs
   GET https://{slug}.jobs.personio.de/api/v1/recruiting/jobs
   Companies: lufthansa-technik, safran-group, collins-aerospace,
   thales-group, dnata, aviapartner

SECTION 2 — Job Boards

10. ADZUNA NL
    Fetch: https://www.adzuna.nl/search?q=revenue+management+analyst&results_per_page=5
    Confirm: does it return JSON-LD in the HTML? Or job cards with selectors?
    Record the exact CSS selectors for title, company, location, URL in 2025.
    Note any changes in HTML structure vs. a year ago.

11. STEPSTONE NL
    Fetch: https://www.stepstone.nl/vacatures/?q=data+analyst&where=Netherlands
    Same — confirm JSON-LD exists or record current card selectors.

12. LINKEDIN (PUBLIC — no auth)
    This is the most important board. Find the correct public search URL.
    Test: https://www.linkedin.com/jobs/search/?keywords=data+analyst&location=Netherlands
    Confirm: does it return JSON-LD job postings in the HTML source?
    If not JSON-LD, what structured data is available?
    Note: rate limiting behaviour — what happens after 5 rapid requests?
    Find the correct User-Agent and request headers to avoid soft blocks.
    Record the exact pagination parameter (start=0, start=25, etc.)

13. INDEED NL
    Test: https://nl.indeed.com/jobs?q=data+analyst&l=Netherlands&radius=50&sort=date
    Confirm JSON-LD availability or card selectors.
    Note: Indeed heavily blocks scrapers — find the current working approach
    (JSON-LD is usually more stable than card scraping).

14. WERKZOEKEN NL
    Test: https://www.werkzoeken.nl/?q=data+analyst&p=amsterdam
    Confirm structure. This is a Dutch aggregator — may have good coverage
    of companies not on the big boards.

SECTION 3 — Direct career pages (JSON-LD only)
For each company below, find their careers URL and check if it serves
JSON-LD JobPosting schema in the HTML source.
Only include if JSON-LD is confirmed — anchor scraping is too noisy.

To70: https://to70.com/about/careers/
Seabury: https://seaburyconsulting.com/careers/
NACO: https://www.naco.nl/careers
Steer: https://www.steergroup.com/careers
Schiphol: https://www.schiphol.nl/en/job-seeker/
Eurocontrol: https://www.eurocontrol.int/careers
EASA: https://www.easa.europa.eu/en/the-agency/working-easa/vacancies
NLR: https://www.nlr.org/career/vacancies/
Fokker: https://www.fokker.com/en/careers
Aevean: https://aevean.com/careers
IBS Software: https://www.ibsplc.com/careers
NAVBLUE: https://www.navblue.aero/en/careers
OAG: https://www.oag.com/about/careers
Cirium: https://www.cirium.com/company/careers/
Lufthansa Systems: https://careers.lhsystems.com/
NS: https://werkenbijns.nl/vacatures
ProRail: https://www.prorail.nl/werken-bij/vacatures
Port of Rotterdam: https://www.portofrotterdam.com/en/working-at/vacancies
AerCap: https://www.aercap.com/careers
LVNL: https://www.lvnl.nl/werken-bij

SECTION 4 — Research notes to record

After testing all sources, write to research.md:

A. VERIFIED SOURCES — full list of confirmed-live endpoints with exact URLs
B. DEAD SOURCES — what failed and why (404, changed URL, no data returned)
C. LINKEDIN FINDINGS — exact approach that works for public scraping in 2025
D. INDEED FINDINGS — same
E. SURPRISES — anything that changed, moved, or works differently than expected
F. RECOMMENDED SOURCE COUNT — how many total company instances across all ATS
G. QUERY STRATEGY — recommended search terms per source to maximise aviation hits

Be precise. Record exact URLs, not descriptions.
When in doubt, fetch and check — do not assume.

---

When done: write research.md and tell me it is ready for review.
Do NOT proceed to planning until I say so.
