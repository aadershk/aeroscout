"""Direct career page scraper — JSON-LD only."""
from __future__ import annotations

import asyncio
import json
import logging

from bs4 import BeautifulSoup

from bs4 import BeautifulSoup as _BS

from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_HTML, get_sem, safe_get

log = logging.getLogger(__name__)

TARGETS = [
    ("To70", "https://to70.com/about/careers/"),
    ("Seabury Consulting", "https://seaburyconsulting.com/careers/"),
    ("EASA", "https://www.easa.europa.eu/en/the-agency/working-easa/vacancies"),
    ("OAG", "https://www.oag.com/about/careers"),
    ("Lufthansa Systems", "https://careers.lhsystems.com/"),
    ("AerCap", "https://www.aercap.com/careers"),
    ("Fokker Services", "https://www.fokker.com/en/careers"),
    ("Port of Amsterdam", "https://www.portofamsterdam.com/en/working-at/vacancies"),
    ("NS", "https://werkenbijns.nl/vacatures"),
    ("LVNL", "https://www.lvnl.nl/werken-bij"),
    ("NLR", "https://www.nlr.org/career/vacancies/"),
    ("KLM", "https://careers.klm.com/nl/jobs/"),
]


async def _fetch_site(session, company: str, page_url: str) -> list[Job]:
    from urllib.parse import urlparse
    host = urlparse(page_url).hostname or ""
    sem = get_sem(host)

    status, text = await safe_get(session, page_url, sem, headers=HEADERS_HTML)
    if status != 200 or not text or not isinstance(text, str):
        log.debug("Direct %s: status=%s", company, status)
        return []

    soup = BeautifulSoup(text, "lxml")
    jobs: list[Job] = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            ld = json.loads(script.string or "")
        except (json.JSONDecodeError, AttributeError):
            continue

        # Handle various JSON-LD structures
        postings: list[dict] = []
        if isinstance(ld, list):
            postings = ld
        elif isinstance(ld, dict):
            if ld.get("@type") == "JobPosting":
                postings = [ld]
            elif "itemListElement" in ld:
                for item in ld["itemListElement"]:
                    if isinstance(item, dict):
                        postings.append(item.get("item", item))
            elif "@graph" in ld:
                for item in ld["@graph"]:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        postings.append(item)

        for posting in postings:
            if not isinstance(posting, dict):
                continue
            if posting.get("@type") not in ("JobPosting", None):
                continue

            title = posting.get("title", posting.get("name", ""))
            if not title:
                continue

            job_url = posting.get("url", "")
            raw_desc = posting.get("description", "")
            desc = _BS(raw_desc, "lxml").get_text(" ", strip=True) if raw_desc and "<" in str(raw_desc) else str(raw_desc)

            ho = posting.get("hiringOrganization", {})
            co = ho.get("name", "") if isinstance(ho, dict) else ""
            if not co:
                co = company

            loc_obj = posting.get("jobLocation", {})
            loc = ""
            if isinstance(loc_obj, dict):
                addr = loc_obj.get("address", {})
                if isinstance(addr, dict):
                    loc = addr.get("addressLocality", addr.get("name", ""))
                elif isinstance(addr, str):
                    loc = addr
            elif isinstance(loc_obj, list) and loc_obj:
                addr = loc_obj[0].get("address", {})
                if isinstance(addr, dict):
                    loc = addr.get("addressLocality", "")

            if not _valid_url(job_url):
                continue

            ok, _ = passes_gate(_norm(title), company=co)
            if not ok:
                continue

            jobs.append(Job(
                title=title, company=co, location=loc,
                url=job_url, description=desc, source="direct",
            ))

    if not jobs:
        log.debug("Direct %s: no JSON-LD found", company)
    return jobs


async def fetch_direct(session) -> list[Job]:
    tasks = [_fetch_site(session, c, u) for c, u in TARGETS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("Direct error: %s", r)
    return jobs
