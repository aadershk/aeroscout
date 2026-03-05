"""SmartRecruiters ATS source.

Endpoint: GET https://api.smartrecruiters.com/v1/companies/{cid}/postings?country=NL&limit=100
Response: {"totalFound": N, "content": [...]}
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# Verified company IDs (exact case matters)
TARGETS = [
    ("ASML1",          "ASML"),
    ("DeloitteNL",     "Deloitte"),
    ("KPMGNederland",  "KPMG"),
    ("kiwi4",          "Kiwi.com"),
    ("Bookingcom1",    "Booking.com"),
]

BASE = "https://api.smartrecruiters.com/v1/companies"
HOST = "api.smartrecruiters.com"


async def _fetch_company(
    session: aiohttp.ClientSession,
    cid: str,
    company: str,
    country_filter: bool = True,
) -> list[Job]:
    params = {"limit": 100}
    if country_filter:
        params["country"] = "NL"

    url = f"{BASE}/{cid}/postings"
    sem = get_semaphore(HOST)

    async with sem:
        try:
            async with session.get(
                url,
                params=params,
                headers=HEADERS_JSON,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status == 404:
                    log.debug("SmartRecruiters '%s' → 404", cid)
                    return []
                if resp.status != 200:
                    log.warning("SmartRecruiters '%s' → HTTP %s", cid, resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("SmartRecruiters '%s' error: %s", cid, exc)
            return []

    jobs = []
    for item in data.get("content", []):
        title = _norm(item.get("name", ""))
        if not title:
            continue

        # Build apply URL from id
        job_id = item.get("id", "")
        job_url = f"https://careers.smartrecruiters.com/{cid}/{job_id}"
        # Some items have a direct ref URL
        ref = item.get("ref", "")
        if _valid_url(ref):
            job_url = ref

        loc = item.get("location", {})
        city = loc.get("city", "") if isinstance(loc, dict) else ""
        country = loc.get("country", "") if isinstance(loc, dict) else ""
        location = f"{city}, {country}".strip(", ")

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=job_url,
            source="smartrecruiters",
        ))

    log.debug("SmartRecruiters '%s': %d jobs", cid, len(jobs))
    return jobs


async def fetch_smartrecruiters(session: aiohttp.ClientSession) -> list[Job]:
    tasks = []
    for cid, company in TARGETS:
        # ASML1 may have 0 NL-filtered jobs — run once with and once without filter
        if cid == "ASML1":
            tasks.append(asyncio.wait_for(
                _fetch_company(session, cid, company, country_filter=False),
                timeout=TASK_TIMEOUT,
            ))
        else:
            tasks.append(asyncio.wait_for(
                _fetch_company(session, cid, company, country_filter=True),
                timeout=TASK_TIMEOUT,
            ))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("SmartRecruiters task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("SmartRecruiters total: %d jobs", len(jobs))
    return jobs
