"""Lever ATS source.

Endpoint: GET https://api.lever.co/v0/postings/{token}?mode=json
Response: JSON array of postings
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# Confirmed live: spotify (16 jobs, no Amsterdam currently but monitor)
# Others need runtime verification
TARGETS = [
    ("spotify",           "Spotify"),
    ("seaburyconsulting", "Seabury Consulting"),
    ("to70",              "To70"),
    ("naco",              "NACO"),
    ("corendon",          "Corendon"),
    ("aevean",            "Aevean"),
]

BASE = "https://api.lever.co/v0/postings"
HOST = "api.lever.co"


async def _fetch_token(
    session: aiohttp.ClientSession,
    token: str,
    company: str,
) -> list[Job]:
    url = f"{BASE}/{token}?mode=json"
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
                    log.debug("Lever token '%s' → 404", token)
                    return []
                if resp.status != 200:
                    log.warning("Lever '%s' → HTTP %s", token, resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Lever '%s' error: %s", token, exc)
            return []

    if not isinstance(data, list):
        log.debug("Lever '%s' unexpected response type", token)
        return []

    jobs = []
    for item in data:
        title = _norm(item.get("text", ""))
        if not title:
            continue
        job_url = item.get("hostedUrl", "") or item.get("applyUrl", "")
        if not _valid_url(job_url):
            continue

        categories = item.get("categories", {})
        location = categories.get("location", "") if isinstance(categories, dict) else ""
        commitment = categories.get("commitment", "") if isinstance(categories, dict) else ""

        # Description is in item["descriptionPlain"] or nested lists
        description = item.get("descriptionPlain", "") or ""

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=job_url,
            description=description[:3000],
            source="lever",
        ))

    log.debug("Lever '%s': %d jobs", token, len(jobs))
    return jobs


async def fetch_lever(session: aiohttp.ClientSession) -> list[Job]:
    tasks = [
        asyncio.wait_for(_fetch_token(session, token, company), timeout=TASK_TIMEOUT)
        for token, company in TARGETS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("Lever task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("Lever total: %d jobs", len(jobs))
    return jobs
