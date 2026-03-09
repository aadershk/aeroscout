"""Greenhouse ATS fetcher."""
from __future__ import annotations

import asyncio
import html as _h
import logging

from bs4 import BeautifulSoup as _BS

from core.gate import passes_gate
from core.models import Job
from core.normalise import _is_nl, _norm, _valid_url
from sources._http import HEADERS_JSON, get_sem, safe_get

log = logging.getLogger(__name__)

BOARDS = [
    ("bookingcom", "Booking.com"), ("travix", "Travix"), ("flyrlabs", "FLYR Labs"),
    ("tomtom", "TomTom"), ("palantir", "Palantir"),
    ("databricks", "Databricks"), ("aviobook", "Aviobook"), ("snowflakecareers", "Snowflake"),
    ("spotify", "Spotify Amsterdam"), ("elastic", "Elastic"), ("miro", "Miro"),
    ("uber", "Uber Amsterdam"), ("atlassian", "Atlassian"), ("kiwi", "Kiwi.com"),
    ("cirium", "Cirium"), ("netflix", "Netflix"), ("catawiki", "Catawiki"),
    ("sendcloud", "Sendcloud"), ("travelperk", "TravelPerk"), ("picnic", "Picnic"),
]


async def _fetch_board(session, token: str, company: str) -> list[Job]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    sem = get_sem("boards-api.greenhouse.io")
    status, data = await safe_get(session, url, sem, headers=HEADERS_JSON)

    if status == 404:
        log.debug("Greenhouse %s: 404", token)
        return []
    if status != 200 or not isinstance(data, dict):
        log.debug("Greenhouse %s: status=%s", token, status)
        return []

    jobs: list[Job] = []
    for j in data.get("jobs", []):
        title = j.get("title", "")
        loc = j.get("location", {}).get("name", "")
        job_url = j.get("absolute_url", "")
        raw = _h.unescape(j.get("content", "") or "")
        desc = _BS(raw, "lxml").get_text(" ", strip=True) if raw else ""

        if loc and not _is_nl(loc):
            continue
        if not _valid_url(job_url):
            continue

        ok, _ = passes_gate(_norm(title), company=company)
        if not ok:
            continue

        jobs.append(Job(
            title=title, company=company, location=loc,
            url=job_url, description=desc, source="greenhouse",
        ))

    return jobs


async def fetch_greenhouse(session) -> list[Job]:
    tasks = [_fetch_board(session, t, c) for t, c in BOARDS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("Greenhouse error: %s", r)
    return jobs
