"""Personio ATS source.

Endpoint: GET https://{slug}.jobs.personio.de/api/v1/jobs
          or GET https://{slug}.jobs.personio.de/api/v1/recruiting/jobs
Response: JSON array of job objects
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# Unverified slugs — need runtime confirmation
TARGETS = [
    ("lufthansa-technik",  "Lufthansa Technik"),
    ("dnata",              "dnata"),
    ("aviapartner",        "Aviapartner"),
    ("safran",             "Safran"),
    ("collins-aerospace",  "Collins Aerospace"),
]

HOST = "jobs.personio.de"


async def _fetch_slug(
    session: aiohttp.ClientSession,
    slug: str,
    company: str,
) -> list[Job]:
    # Try primary endpoint first, fall back to alternate path
    url = f"https://{slug}.jobs.personio.de/api/v1/jobs"
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
                    # Try alternate path
                    url2 = f"https://{slug}.jobs.personio.de/api/v1/recruiting/jobs"
                    async with session.get(
                        url2,
                        headers=HEADERS_JSON,
                        ssl=_SSL,
                        timeout=make_timeout(),
                    ) as resp2:
                        if resp2.status != 200:
                            log.debug("Personio '%s' → 404 on both paths", slug)
                            return []
                        data = await resp2.json(content_type=None)
                elif resp.status == 429:
                    log.debug("Personio '%s' → 429 rate limited", slug)
                    return []
                elif resp.status != 200:
                    log.warning("Personio '%s' → HTTP %s", slug, resp.status)
                    return []
                else:
                    data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Personio '%s' error: %s", slug, exc)
            return []

    # Personio can return list or {"data": [...]}
    items = data if isinstance(data, list) else data.get("data", [])

    jobs = []
    for item in items:
        title = _norm(item.get("name", "") or item.get("title", ""))
        if not title:
            continue

        job_id = item.get("id", "")
        job_url = f"https://{slug}.jobs.personio.de/job/{job_id}"
        if not _valid_url(job_url):
            continue

        office = item.get("office", "") or ""
        department = item.get("department", "") or ""

        jobs.append(Job(
            title=title,
            company=company,
            location=office,
            url=job_url,
            source="personio",
        ))

    log.debug("Personio '%s': %d jobs", slug, len(jobs))
    return jobs


async def fetch_personio(session: aiohttp.ClientSession) -> list[Job]:
    tasks = [
        asyncio.wait_for(_fetch_slug(session, slug, company), timeout=TASK_TIMEOUT)
        for slug, company in TARGETS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("Personio task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("Personio total: %d jobs", len(jobs))
    return jobs
