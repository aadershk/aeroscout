"""Lever ATS fetcher."""
from __future__ import annotations

import asyncio
import logging

from core.gate import passes_gate
from core.models import Job
from core.normalise import _is_nl, _norm, _valid_url
from sources._http import HEADERS_JSON, get_sem, safe_get

log = logging.getLogger(__name__)

BOARDS = [
    ("schiphol", "Schiphol Group"), ("transavia", "Transavia"),
    ("catawiki", "Catawiki"), ("sendcloud", "Sendcloud"),
    ("seabury", "Seabury Consulting"), ("to70", "To70"),
    ("naco", "NACO"), ("corendon", "Corendon Airlines"),
    ("aevean", "Aevean"), ("bunq", "Bunq"), ("coolblue", "Coolblue"),
]


async def _fetch_board(session, token: str, company: str) -> list[Job]:
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    sem = get_sem("api.lever.co")
    status, data = await safe_get(session, url, sem, headers=HEADERS_JSON)

    if status == 404:
        log.debug("Lever %s: 404", token)
        return []
    if status != 200 or not isinstance(data, list):
        log.debug("Lever %s: status=%s", token, status)
        return []

    jobs: list[Job] = []
    for j in data:
        title = j.get("text", "")
        loc = j.get("categories", {}).get("location", "")
        job_url = j.get("hostedUrl", "")
        desc = j.get("descriptionBody", "") or j.get("descriptionPlain", "")

        if loc and not _is_nl(loc):
            continue
        if not _valid_url(job_url):
            continue

        ok, _ = passes_gate(_norm(title), company=company)
        if not ok:
            continue

        jobs.append(Job(
            title=title, company=company, location=loc,
            url=job_url, description=desc, source="lever",
        ))

    return jobs


async def fetch_lever(session) -> list[Job]:
    tasks = [_fetch_board(session, t, c) for t, c in BOARDS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("Lever error: %s", r)
    return jobs
