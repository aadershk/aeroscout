"""Workable fetcher."""
from __future__ import annotations

import asyncio
import logging

from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, get_sem, safe_get, safe_post

log = logging.getLogger(__name__)

TARGETS = [
    ("eurocontrol", "Eurocontrol"), ("navblue", "NAVBLUE"),
    ("sabre", "Sabre"), ("arcadis", "Arcadis"),
    ("mottmacdonaldgroup", "Mott MacDonald"), ("jacobs", "Jacobs"),
    ("rolandberger", "Roland Berger"),
    ("portofrotterdam", "Port of Rotterdam"),
    ("goudappel", "Goudappel"), ("steer", "Steer"), ("wsp", "WSP"),
]


async def _fetch_slug(session, slug: str, company: str) -> list[Job]:
    sem = get_sem("apply.workable.com")
    url = f"https://apply.workable.com/api/v3/accounts/{slug}/jobs"
    payload = {"limit": 100, "offset": 0}

    # Try POST first
    status, data = await safe_post(session, url, sem, payload, HEADERS_JSON)
    if status != 200 or not isinstance(data, dict):
        # Fallback to GET
        status, data = await safe_get(session, url, sem, headers=HEADERS_JSON)
    if status != 200 or not isinstance(data, dict):
        log.debug("Workable %s: status=%s", slug, status)
        return []

    jobs: list[Job] = []
    for j in data.get("results", []):
        title = j.get("title", "")
        loc = j.get("location", {})
        if isinstance(loc, dict):
            loc = loc.get("city", "") + ", " + loc.get("country", "")
        elif not isinstance(loc, str):
            loc = ""
        shortcode = j.get("shortcode", "")
        job_url = f"https://apply.workable.com/{slug}/j/{shortcode}/" if shortcode else ""

        if not _valid_url(job_url):
            continue

        ok, _ = passes_gate(_norm(title), company=company)
        if not ok:
            continue

        jobs.append(Job(
            title=title, company=company, location=loc,
            url=job_url, source="workable",
        ))

    return jobs


async def fetch_workable(session) -> list[Job]:
    tasks = [_fetch_slug(session, s, c) for s, c in TARGETS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("Workable error: %s", r)
    return jobs
