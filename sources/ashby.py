"""Ashby ATS fetcher."""
from __future__ import annotations

import asyncio
import logging

from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, get_sem, safe_post

log = logging.getLogger(__name__)

BOARDS = [
    ("FLYR", "FLYR Labs"), ("aevean", "Aevean"), ("picnic", "Picnic"),
]


async def _fetch_board(session, name: str, company: str) -> list[Job]:
    url = "https://api.ashbyhq.com/posting-api/job-board"
    sem = get_sem("api.ashbyhq.com")
    payload = {"organizationHostedJobsPageName": name}
    status, data = await safe_post(session, url, sem, payload, HEADERS_JSON)

    if status != 200 or not isinstance(data, dict):
        log.debug("Ashby %s: status=%s", name, status)
        return []

    jobs: list[Job] = []
    for j in data.get("jobs", []):
        title = j.get("title", "")
        job_url = j.get("jobUrl", "")
        desc = j.get("descriptionBody", "") or j.get("descriptionPlain", "")
        loc = j.get("location", "")

        if not _valid_url(job_url):
            continue

        ok, _ = passes_gate(_norm(title), company=company)
        if not ok:
            continue

        jobs.append(Job(
            title=title, company=company, location=loc,
            url=job_url, description=desc, source="ashby",
        ))

    return jobs


async def fetch_ashby(session) -> list[Job]:
    tasks = [_fetch_board(session, n, c) for n, c in BOARDS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("Ashby error: %s", r)
    return jobs
