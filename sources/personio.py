"""Personio ATS fetcher."""
from __future__ import annotations

import asyncio
import logging

from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, get_sem, safe_get

log = logging.getLogger(__name__)

TARGETS = [
    ("lufthansa-technik", "Lufthansa Technik"),
    ("safran-group", "Safran"),
    ("collins-aerospace", "Collins Aerospace"),
    ("dnata", "dnata"),
    ("aviapartner", "Aviapartner"),
]

_ENDPOINTS = ["/api/v1/jobs", "/api/v1/recruiting/jobs"]


async def _fetch_slug(session, slug: str, company: str) -> list[Job]:
    sem = get_sem(f"{slug}.jobs.personio.de")
    base = f"https://{slug}.jobs.personio.de"

    for endpoint in _ENDPOINTS:
        url = f"{base}{endpoint}"
        status, data = await safe_get(session, url, sem, headers=HEADERS_JSON)

        if status != 200 or not isinstance(data, (dict, list)):
            continue

        # Normalize to list
        items = data if isinstance(data, list) else data.get("data", data.get("jobs", []))
        if not isinstance(items, list) or not items:
            continue

        jobs: list[Job] = []
        for j in items:
            attrs = j.get("attributes", j) if isinstance(j, dict) else {}
            title = attrs.get("name", attrs.get("title", ""))
            job_id = attrs.get("id", j.get("id", ""))
            loc = attrs.get("office", attrs.get("location", ""))
            if isinstance(loc, dict):
                loc = loc.get("name", "")
            job_url = f"https://{slug}.jobs.personio.de/job/{job_id}" if job_id else ""

            if not title or not _valid_url(job_url):
                continue

            ok, _ = passes_gate(_norm(title), company=company)
            if not ok:
                continue

            jobs.append(Job(
                title=title, company=company, location=str(loc),
                url=job_url, source="personio",
            ))

        return jobs  # Stop at first successful endpoint

    log.debug("Personio %s: no data from any endpoint", slug)
    return []


async def fetch_personio(session) -> list[Job]:
    tasks = [_fetch_slug(session, s, c) for s, c in TARGETS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("Personio error: %s", r)
    return jobs
