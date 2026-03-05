"""Workable ATS source.

Endpoint: POST https://apply.workable.com/api/v3/accounts/{slug}/jobs
Body: {"query":"","location":"","limit":100}
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# Unverified slugs — need runtime testing to confirm
TARGETS = [
    ("navblue",             "NAVBLUE"),
    ("arcadis",             "Arcadis"),
    ("mottmacdonaldgroup",  "Mott MacDonald"),
    ("jacobs",              "Jacobs"),
    ("rolandberger",        "Roland Berger"),
    ("portofrotterdam",     "Port of Rotterdam"),
    ("goudappel",           "Goudappel"),
    ("steer",               "Steer"),
]

BASE = "https://apply.workable.com/api/v3/accounts"
HOST = "apply.workable.com"


async def _fetch_slug(
    session: aiohttp.ClientSession,
    slug: str,
    company: str,
) -> list[Job]:
    url = f"{BASE}/{slug}/jobs"
    sem = get_semaphore(HOST)

    payload = {"query": "", "location": "", "limit": 100}

    async with sem:
        try:
            async with session.post(
                url,
                json=payload,
                headers=HEADERS_JSON,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status in (400, 404):
                    log.debug("Workable '%s' → HTTP %s (slug not found)", slug, resp.status)
                    return []
                if resp.status != 200:
                    log.warning("Workable '%s' → HTTP %s", slug, resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Workable '%s' error: %s", slug, exc)
            return []

    jobs = []
    for item in data.get("results", []):
        title = _norm(item.get("title", ""))
        if not title:
            continue

        shortcode = item.get("shortcode", "")
        job_url = f"https://apply.workable.com/{slug}/j/{shortcode}/"
        if not _valid_url(job_url):
            continue

        location = item.get("city", "") or ""
        country = item.get("country", "") or ""
        if country:
            location = f"{location}, {country}".strip(", ")

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=job_url,
            source="workable",
        ))

    log.debug("Workable '%s': %d jobs", slug, len(jobs))
    return jobs


async def fetch_workable(session: aiohttp.ClientSession) -> list[Job]:
    tasks = [
        asyncio.wait_for(_fetch_slug(session, slug, company), timeout=TASK_TIMEOUT)
        for slug, company in TARGETS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("Workable task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("Workable total: %d jobs", len(jobs))
    return jobs
