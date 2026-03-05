"""Teamtailor ATS source.

Endpoint: GET https://{slug}.teamtailor.com/jobs.json
Response: {"data": [...], "meta": {...}}

Dead slugs confirmed: klm, corendon, bunq
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# Unverified slugs — will hit 404 gracefully if wrong
# Confirmed dead: klm, corendon, bunq
TARGETS = [
    ("transavia-nl",        "Transavia"),
    ("fokker",              "Fokker Services"),
    ("to70",                "To70"),
    ("aevean",              "Aevean"),
    ("naco",                "NACO"),
    ("ibssoftware",         "IBS Software"),
    ("travix",              "Travix"),
    ("nngroup",             "NN Group"),
    ("prorail",             "ProRail"),
    ("ns-nl",               "NS"),
    ("postnl",              "PostNL"),
    ("vanderlande",         "Vanderlande"),
    ("seaburyconsulting",   "Seabury Consulting"),
    ("steer",               "Steer"),
    ("royalhaskoningdhv",   "Royal HaskoningDHV"),
    ("coolblue",            "Coolblue"),
    ("portofrotterdam",     "Port of Rotterdam"),
]


async def _fetch_slug(
    session: aiohttp.ClientSession,
    slug: str,
    company: str,
) -> list[Job]:
    url = f"https://{slug}.teamtailor.com/jobs.json"
    host = f"{slug}.teamtailor.com"
    sem = get_semaphore(host)

    async with sem:
        try:
            async with session.get(
                url,
                headers=HEADERS_JSON,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status in (404, 406):
                    log.debug("Teamtailor '%s' → HTTP %s (slug not found)", slug, resp.status)
                    return []
                if resp.status != 200:
                    log.warning("Teamtailor '%s' → HTTP %s", slug, resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Teamtailor '%s' error: %s", slug, exc)
            return []

    jobs = []
    for item in data.get("data", []):
        attrs = item.get("attributes", {}) if isinstance(item, dict) else {}
        title = _norm(attrs.get("title", ""))
        if not title:
            continue

        # Job URL from links or constructed
        links = item.get("links", {})
        job_url = links.get("careersite-job-url", "") if isinstance(links, dict) else ""
        if not _valid_url(job_url):
            job_slug = attrs.get("slug", "")
            job_url = f"https://{slug}.teamtailor.com/jobs/{job_slug}"
        if not _valid_url(job_url):
            continue

        location = attrs.get("city", "") or ""
        description = attrs.get("body", "") or ""

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=job_url,
            description=description[:3000],
            source="teamtailor",
        ))

    log.debug("Teamtailor '%s': %d jobs", slug, len(jobs))
    return jobs


async def fetch_teamtailor(session: aiohttp.ClientSession) -> list[Job]:
    tasks = [
        asyncio.wait_for(_fetch_slug(session, slug, company), timeout=TASK_TIMEOUT)
        for slug, company in TARGETS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("Teamtailor task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("Teamtailor total: %d jobs", len(jobs))
    return jobs
