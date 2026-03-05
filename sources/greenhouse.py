"""Greenhouse ATS source.

Endpoint: GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
Response: {"jobs": [...], "meta": {...}}
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# (token, display_name) — verified live from research
TARGETS = [
    ("databricks",          "Databricks"),
    ("catawiki",            "Catawiki"),
    ("sendcloud",           "Sendcloud"),
    ("elastic",             "Elastic"),
    ("realtimeboardglobal", "Miro"),       # former name: RealtimeBoard
    ("flyr",                "FLYR Labs"),  # NOT "flyrlabs" — confirmed correct
]

BASE = "https://boards-api.greenhouse.io/v1/boards"
HOST = "boards-api.greenhouse.io"


async def _fetch_board(
    session: aiohttp.ClientSession,
    token: str,
    company: str,
) -> list[Job]:
    """Fetch all jobs for one Greenhouse board."""
    url = f"{BASE}/{token}/jobs?content=true"
    sem = get_semaphore(HOST)

    async with sem:
        try:
            async with session.get(
                url,
                headers=HEADERS_JSON,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status == 404:
                    log.debug("Greenhouse token '%s' → 404 (dead)", token)
                    return []
                if resp.status != 200:
                    log.warning("Greenhouse '%s' → HTTP %s", token, resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Greenhouse '%s' error: %s", token, exc)
            return []

    jobs = []
    for item in data.get("jobs", []):
        title = _norm(item.get("title", ""))
        if not title:
            continue
        job_url = item.get("absolute_url", "")
        if not _valid_url(job_url):
            continue

        loc = item.get("location", {})
        location = loc.get("name", "") if isinstance(loc, dict) else str(loc)

        # content is HTML job description
        description = item.get("content", "") or ""

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=job_url,
            description=description[:3000],
            source="greenhouse",
        ))

    log.debug("Greenhouse '%s': %d jobs", token, len(jobs))
    return jobs


async def fetch_greenhouse(session: aiohttp.ClientSession) -> list[Job]:
    tasks = [
        asyncio.wait_for(_fetch_board(session, token, company), timeout=TASK_TIMEOUT)
        for token, company in TARGETS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("Greenhouse task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("Greenhouse total: %d jobs", len(jobs))
    return jobs
