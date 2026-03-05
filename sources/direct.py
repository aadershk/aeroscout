"""Direct company career page scraper.

For companies not on a supported ATS. Fetches JSON-LD job postings from
career pages when available. Falls back to parsing <a> tags for job links.

Currently targets companies where ATS was unverified in research.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re

from bs4 import BeautifulSoup
import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_BROWSER, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# (company_name, careers_url)
# Only include pages that are known to have job listings (not login-gated)
TARGETS = [
    ("To70",              "https://to70.com/about/careers/"),
    ("Seabury Consulting", "https://seaburyconsulting.com/careers/"),
    ("NACO",              "https://www.naco.nl/careers"),
    ("Aevean",            "https://aevean.com/careers"),
    ("IBS Software",      "https://www.ibsplc.com/careers"),
    ("NAVBLUE",           "https://www.navblue.aero/en/careers"),
    ("Lufthansa Systems", "https://careers.lhsystems.com/"),
]

_JSONLD_TYPE = re.compile(r'"@type"\s*:\s*"JobPosting"', re.I)


def _extract_jsonld_jobs(html: str, company: str, base_url: str) -> list[Job]:
    """Extract jobs from JSON-LD JobPosting schema blocks."""
    soup = BeautifulSoup(html, "lxml")
    jobs = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        # Handle single object or @graph array
        items = data if isinstance(data, list) else [data]
        for item in items:
            if item.get("@type") != "JobPosting":
                continue
            title = _norm(item.get("title", ""))
            if not title:
                continue
            job_url = item.get("url", "") or base_url
            if not _valid_url(job_url):
                continue
            loc = item.get("jobLocation", {})
            if isinstance(loc, dict):
                addr = loc.get("address", {})
                location = addr.get("addressLocality", "") if isinstance(addr, dict) else ""
            else:
                location = ""
            description = item.get("description", "") or ""
            jobs.append(Job(
                title=title,
                company=company,
                location=location,
                url=job_url,
                description=description[:3000],
                source="direct",
            ))
    return jobs


async def _fetch_page(
    session: aiohttp.ClientSession,
    company: str,
    url: str,
) -> list[Job]:
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    sem = get_semaphore(host)

    async with sem:
        try:
            async with session.get(
                url,
                headers=HEADERS_BROWSER,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status != 200:
                    log.debug("Direct '%s' → HTTP %s", company, resp.status)
                    return []
                html = await resp.text()
        except Exception as exc:
            log.warning("Direct '%s' error: %s", company, exc)
            return []

    # Try JSON-LD first (structured data)
    if _JSONLD_TYPE.search(html):
        jobs = _extract_jsonld_jobs(html, company, url)
        if jobs:
            log.debug("Direct '%s': %d jobs via JSON-LD", company, len(jobs))
            return jobs

    log.debug("Direct '%s': no JSON-LD jobs found on %s", company, url)
    return []


async def fetch_direct(session: aiohttp.ClientSession) -> list[Job]:
    tasks = [
        asyncio.wait_for(_fetch_page(session, company, url), timeout=TASK_TIMEOUT)
        for company, url in TARGETS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("Direct task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("Direct total: %d jobs", len(jobs))
    return jobs
