"""Workday ATS source.

Endpoint: POST https://{tenant}.wd3.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
Response: {"jobPostings": [...]}  — each item has externalPath starting with "/"
Full job URL: f"{base_root}{ext}"  where base_root = https://{tenant}.wd3.myworkdayjobs.com
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Confirmed tenants (from research report)
# ---------------------------------------------------------------------------
TARGETS = [
    # (tenant, site, company_display_name)
    ("amadeus",     "jobs",                       "Amadeus"),
    ("accenture",   "AccentureCareers",            "Accenture"),
    ("ing",         "ICSNLDGEN",                   "ING"),          # NL-specific
    ("philips",     "jobs-and-careers",            "Philips"),
    ("shell",       "ShellCareers",                "Shell"),
    ("vanderlande", "careers",                     "Vanderlande"),
    ("wk",          "External",                    "Wolters Kluwer"),
    ("nxp",         "careers",                     "NXP Semiconductors"),
    ("maersk",      "PT_Careers",                  "Maersk"),
    ("relx",        "ciriumcareers",               "Cirium"),
    ("pwc",         "Global_Campus_Careers",       "PwC"),
    ("pwc",         "Global_Experienced_Careers",  "PwC"),
]

# Search terms — multiple passes to catch different role types
SEARCH_TERMS = [
    "data analyst",
    "data scientist",
    "revenue management",
    "operations research",
    "analytics",
]

PAGE_SIZE = 20


async def _fetch_tenant(
    session: aiohttp.ClientSession,
    tenant: str,
    site: str,
    company: str,
    search: str,
) -> list[dict[str, Any]]:
    """Fetch one page of results for one tenant+search combination."""
    base_root = f"https://{tenant}.wd3.myworkdayjobs.com"
    api_url = f"{base_root}/wday/cxs/{tenant}/{site}/jobs"
    host = f"{tenant}.wd3.myworkdayjobs.com"
    sem = get_semaphore(host)

    payload = {"limit": PAGE_SIZE, "offset": 0, "searchText": search, "appliedFacets": {}}

    async with sem:
        try:
            async with session.post(
                api_url,
                json=payload,
                headers=HEADERS_JSON,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status != 200:
                    log.debug("%s/%s [%s] → HTTP %s", tenant, site, search, resp.status)
                    return []
                data = await resp.json(content_type=None)
                postings = data.get("jobPostings", [])
                # Attach base_root so caller can build full URL
                for p in postings:
                    p["_base_root"] = base_root
                    p["_company"] = company
                return postings
        except Exception as exc:
            log.warning("Workday %s/%s [%s] error: %s", tenant, site, search, exc)
            return []


def _posting_to_job(p: dict[str, Any]) -> Job | None:
    """Convert a Workday posting dict to a Job."""
    ext = p.get("externalPath", "")
    if not ext.startswith("/"):
        return None
    base_root = p.get("_base_root", "")
    url = f"{base_root}{ext}"
    if not _valid_url(url):
        return None

    title = _norm(p.get("title", ""))
    if not title:
        return None

    location_data = p.get("locationsText", "") or p.get("primaryLocation", {})
    if isinstance(location_data, dict):
        location = location_data.get("name", "")
    else:
        location = str(location_data)

    return Job(
        title=title,
        company=p.get("_company", ""),
        location=location,
        url=url,
        source="workday",
    )


async def fetch_workday(
    session: aiohttp.ClientSession,
) -> list[Job]:
    """Fetch all Workday targets across all search terms."""
    tasks = []
    for tenant, site, company in TARGETS:
        for search in SEARCH_TERMS:
            tasks.append(
                asyncio.wait_for(
                    _fetch_tenant(session, tenant, site, company, search),
                    timeout=TASK_TIMEOUT,
                )
            )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    seen_ext: set[str] = set()  # deduplicate within workday before returning
    for batch in results:
        if isinstance(batch, BaseException):
            log.warning("Workday task exception: %s", batch)
            continue
        for p in batch:
            ext = p.get("externalPath", "")
            if ext in seen_ext:
                continue
            seen_ext.add(ext)
            job = _posting_to_job(p)
            if job:
                jobs.append(job)

    log.debug("Workday: %d raw jobs", len(jobs))
    return jobs
