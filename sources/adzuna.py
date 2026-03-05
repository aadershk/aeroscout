"""Adzuna NL source.

Requires API key registration at developer.adzuna.com (free tier).
Set environment variables: ADZUNA_APP_ID and ADZUNA_APP_KEY.

Endpoint: GET https://api.adzuna.com/v1/api/jobs/nl/search/{page}
Params: app_id, app_key, results_per_page=50, what=...
"""
from __future__ import annotations

import asyncio
import logging
import os

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

BASE = "https://api.adzuna.com/v1/api/jobs/nl/search"
HOST = "api.adzuna.com"

SEARCH_TERMS = [
    "data analyst",
    "data scientist",
    "revenue management",
    "operations research",
]


async def _fetch_page(
    session: aiohttp.ClientSession,
    app_id: str,
    app_key: str,
    what: str,
    page: int = 1,
) -> list[Job]:
    url = f"{BASE}/{page}"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 50,
        "what": what,
        "content-type": "application/json",
    }
    sem = get_semaphore(HOST)

    async with sem:
        try:
            async with session.get(
                url,
                params=params,
                headers=HEADERS_JSON,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status == 401:
                    log.warning("Adzuna: invalid API credentials")
                    return []
                if resp.status != 200:
                    log.warning("Adzuna '%s' p%s → HTTP %s", what, page, resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Adzuna '%s' error: %s", what, exc)
            return []

    jobs = []
    for item in data.get("results", []):
        title = _norm(item.get("title", ""))
        if not title:
            continue
        job_url = item.get("redirect_url", "")
        if not _valid_url(job_url):
            continue

        company = item.get("company", {}).get("display_name", "") or ""
        location = item.get("location", {}).get("display_name", "") or ""
        description = item.get("description", "") or ""

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=job_url,
            description=description[:3000],
            source="adzuna",
        ))

    return jobs


async def fetch_adzuna(session: aiohttp.ClientSession) -> list[Job]:
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    app_key = os.environ.get("ADZUNA_APP_KEY", "")

    if not app_id or not app_key:
        log.debug("Adzuna skipped — ADZUNA_APP_ID / ADZUNA_APP_KEY not set")
        return []

    tasks = [
        asyncio.wait_for(
            _fetch_page(session, app_id, app_key, what=term),
            timeout=TASK_TIMEOUT,
        )
        for term in SEARCH_TERMS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("Adzuna task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("Adzuna total: %d jobs", len(jobs))
    return jobs
