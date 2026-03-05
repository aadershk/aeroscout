"""Recruitee ATS source.

Endpoint: GET https://{slug}.recruitee.com/api/offers/
Response: {"offers": [...]}
"""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

# Verified slugs. NLR slug is "werkenbijnlr" not "nlr" (302 redirect confirmed).
TARGETS = [
    ("werkenbijnlr", "NLR"),
    # Add more verified slugs here as they are confirmed
]


async def _fetch_slug(
    session: aiohttp.ClientSession,
    slug: str,
    company: str,
) -> list[Job]:
    url = f"https://{slug}.recruitee.com/api/offers/"
    host = f"{slug}.recruitee.com"
    sem = get_semaphore(host)

    async with sem:
        try:
            async with session.get(
                url,
                headers=HEADERS_JSON,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status == 404:
                    log.debug("Recruitee '%s' → 404", slug)
                    return []
                if resp.status != 200:
                    log.warning("Recruitee '%s' → HTTP %s", slug, resp.status)
                    return []
                data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Recruitee '%s' error: %s", slug, exc)
            return []

    jobs = []
    for offer in data.get("offers", []):
        title = _norm(offer.get("title", ""))
        if not title:
            continue
        careers_url = offer.get("careers_url", "")
        if not _valid_url(careers_url):
            # Fallback: construct from slug
            offer_slug = offer.get("slug", "")
            careers_url = f"https://{slug}.recruitee.com/o/{offer_slug}"
        if not _valid_url(careers_url):
            continue

        city = offer.get("city", "") or ""
        country = offer.get("country_code", "") or ""
        location = f"{city}, {country}".strip(", ")

        description = offer.get("description", "") or ""

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=careers_url,
            description=description[:3000],
            source="recruitee",
        ))

    log.debug("Recruitee '%s': %d jobs", slug, len(jobs))
    return jobs


async def fetch_recruitee(session: aiohttp.ClientSession) -> list[Job]:
    tasks = [
        asyncio.wait_for(_fetch_slug(session, slug, company), timeout=TASK_TIMEOUT)
        for slug, company in TARGETS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("Recruitee task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("Recruitee total: %d jobs", len(jobs))
    return jobs
