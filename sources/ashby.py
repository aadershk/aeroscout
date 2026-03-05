"""Ashby ATS source.

Endpoint: POST https://api.ashbyhq.com/posting-api/job-board
Body: {"organizationHostedJobsPageName": "{name}"}
Response: {"jobs": [...]}

Note: FLYR confirmed on Greenhouse (token: "flyr"), NOT Ashby.
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# Unverified org names — need runtime confirmation
TARGETS = [
    ("aevean",  "Aevean"),
    ("picnic",  "Picnic"),
]

BASE = "https://api.ashbyhq.com/posting-api/job-board"
HOST = "api.ashbyhq.com"


async def _fetch_org(
    session: aiohttp.ClientSession,
    org_name: str,
    company: str,
) -> list[Job]:
    sem = get_semaphore(HOST)
    payload = {"organizationHostedJobsPageName": org_name}

    async with sem:
        try:
            async with session.post(
                BASE,
                json=payload,
                headers=HEADERS_JSON,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status in (401, 403, 404):
                    log.debug("Ashby org '%s' → HTTP %s (not found or auth required)", org_name, resp.status)
                    return []
                if resp.status != 200:
                    log.warning("Ashby '%s' → HTTP %s", org_name, resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Ashby '%s' error: %s", org_name, exc)
            return []

    jobs = []
    for item in data.get("jobs", []):
        title = _norm(item.get("title", ""))
        if not title:
            continue
        job_url = item.get("jobUrl", "") or item.get("applyUrl", "")
        if not _valid_url(job_url):
            continue

        location = item.get("location", "") or ""
        description = item.get("descriptionHtml", "") or item.get("description", "") or ""

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=job_url,
            description=description[:3000],
            source="ashby",
        ))

    log.debug("Ashby '%s': %d jobs", org_name, len(jobs))
    return jobs


async def fetch_ashby(session: aiohttp.ClientSession) -> list[Job]:
    tasks = [
        asyncio.wait_for(_fetch_org(session, org_name, company), timeout=TASK_TIMEOUT)
        for org_name, company in TARGETS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("Ashby task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("Ashby total: %d jobs", len(jobs))
    return jobs
