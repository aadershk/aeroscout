"""Workday ATS fetcher."""
from __future__ import annotations

import asyncio
import logging

from core.gate import passes_gate
from core.models import Job
from core.normalise import _is_nl, _norm, _valid_url
from sources._http import HEADERS_JSON, get_sem, safe_post

log = logging.getLogger(__name__)

TARGETS = [
    ("klm", "KLMCareers", "KLM"),
    ("amadeus", "jobs", "Amadeus"),
    ("accenture", "AccentureCareers", "Accenture"),
    ("ing", "ICSNLDGEN", "ING"),
    ("philips", "jobs-and-careers", "Philips"),
    ("shell", "ShellCareers", "Shell"),
    ("vanderlande", "careers", "Vanderlande"),
    ("wk", "External", "Wolters Kluwer"),
    ("nxp", "careers", "NXP Semiconductors"),
    ("maersk", "PT_Careers", "Maersk"),
    ("relx", "ciriumcareers", "Cirium"),
    ("pwc", "Global_Campus_Careers", "PwC"),
    ("pwc", "Global_Experienced_Careers", "PwC"),
    ("capgemini", "CapgeminiCareers", "Capgemini"),
    ("asml", "ASMLCareers", "ASML"),
    ("heineken", "Heineken_Careers", "Heineken"),
    ("adyen", "Adyen_Careers", "Adyen"),
    ("dhl", "DHLGroupCareers", "DHL"),
    ("postnl", "PostNL_Careers", "PostNL"),
]

SEARCH_TERMS = [
    "revenue management", "operations research", "pricing analyst", "data scientist",
    "data analyst", "analytics engineer", "machine learning", "yield analyst",
    "quantitative analyst", "business intelligence", "demand forecasting",
    "mro analytics", "network planning", "transport analytics", "supply chain analytics",
    "business analyst",
]


async def _fetch_tenant(session, tenant: str, site: str, company: str) -> list[Job]:
    """Fetch jobs from a single Workday tenant."""
    base_url = f"https://{tenant}.wd3.myworkdayjobs.com"
    api_url = f"{base_url}/wday/cxs/{tenant}/{site}/jobs"
    sem = get_sem(f"{tenant}.wd3.myworkdayjobs.com")
    jobs: list[Job] = []
    seen_urls: set[str] = set()

    for term in SEARCH_TERMS:
        payload = {"limit": 20, "offset": 0, "searchText": term, "appliedFacets": {}}
        status, data = await safe_post(session, api_url, sem, payload, HEADERS_JSON)
        if status != 200 or not isinstance(data, dict):
            log.debug("Workday %s/%s term=%s status=%s", tenant, site, term, status)
            continue

        for posting in data.get("jobPostings", []):
            title = posting.get("title", "")
            ext = posting.get("externalPath", "")
            loc = posting.get("locationsText", "")

            if loc and not _is_nl(loc):
                continue

            url = f"{base_url}{ext}"
            if not _valid_url(url) or url in seen_urls:
                continue
            seen_urls.add(url)

            ok, _ = passes_gate(_norm(title), company=company)
            if not ok:
                continue

            jobs.append(Job(
                title=title, company=company, location=loc,
                url=url, source="workday",
            ))

    return jobs


async def fetch_workday(session) -> list[Job]:
    """Fetch from all Workday tenants."""
    tasks = [_fetch_tenant(session, t, s, c) for t, s, c in TARGETS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("Workday error: %s", r)
    return jobs
