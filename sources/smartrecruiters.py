"""SmartRecruiters fetcher."""
from __future__ import annotations

import asyncio
import logging

from core.gate import passes_gate
from core.models import Job
from core.normalise import _is_nl, _norm, _valid_url
from sources._http import HEADERS_JSON, get_sem, safe_get

log = logging.getLogger(__name__)

TARGETS = [
    ("Airbus", "Airbus"), ("AirFranceKLM", "Air France-KLM"),
    ("GEAviation", "GE Aerospace"), ("Deloitte", "Deloitte"),
    ("KPMG", "KPMG"), ("PricewaterhouseCoopers", "PwC"),
    ("ErnstYoung", "EY"),
    ("Capgemini", "Capgemini"), ("SITAAeroIT", "SITA"),
    ("OliverWyman", "Oliver Wyman"), ("McKinseyAndCompany", "McKinsey"),
    ("CollinsAerospace", "Collins Aerospace"), ("Maersk", "Maersk"),
    ("DSVRoadAS", "DSV"), ("Achmea", "Achmea"),
    ("QuantumBlackMcKinsey", "QuantumBlack by McKinsey"),
]

KEYWORDS = [
    "data analyst", "data scientist", "revenue management", "operations research",
    "pricing analyst", "machine learning", "business analyst", "yield analyst",
    "quantitative analyst", "business intelligence", "supply chain analytics",
]


async def _fetch_company(session, cid: str, company: str) -> list[Job]:
    sem = get_sem("api.smartrecruiters.com")
    jobs: list[Job] = []
    seen_urls: set[str] = set()

    for kw in KEYWORDS:
        url = f"https://api.smartrecruiters.com/v1/companies/{cid}/postings"
        params = {"keyword": kw, "country": "nl", "limit": "20"}
        status, data = await safe_get(session, url, sem, params=params, headers=HEADERS_JSON)

        if status != 200 or not isinstance(data, dict):
            log.debug("SmartRecruiters %s kw=%s: status=%s", cid, kw, status)
            continue

        for j in data.get("content", []):
            title = j.get("name", "")
            loc_obj = j.get("location", {})
            loc = loc_obj.get("city", "") + ", " + loc_obj.get("country", "")
            job_url = j.get("ref", "") or j.get("company", {}).get("identifier", "")
            # Build a proper URL
            job_id = j.get("id", "")
            if job_id:
                job_url = f"https://jobs.smartrecruiters.com/{cid}/{job_id}"

            if not _valid_url(job_url) or job_url in seen_urls:
                continue
            seen_urls.add(job_url)

            ok, _ = passes_gate(_norm(title), company=company)
            if not ok:
                continue

            jobs.append(Job(
                title=title, company=company, location=loc,
                url=job_url, source="smartrecruiters",
            ))

    return jobs


async def fetch_smartrecruiters(session) -> list[Job]:
    tasks = [_fetch_company(session, c, n) for c, n in TARGETS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("SmartRecruiters error: %s", r)
    return jobs
