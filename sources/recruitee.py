"""Recruitee ATS fetcher."""
from __future__ import annotations

import asyncio
import logging

from bs4 import BeautifulSoup as _BS

from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, get_sem, safe_get

log = logging.getLogger(__name__)

TARGETS = [
    ("nlr", "NLR"), ("transavia", "Transavia"),
    ("royalhaskoningdhv", "Royal HaskoningDHV"),
    ("fokker", "Fokker Services"), ("menzies", "Menzies Aviation"),
    ("swissport", "Swissport"), ("aercap", "AerCap"),
    ("vanderlande", "Vanderlande"), ("lvnl", "LVNL"),
    ("portofrotterdam", "Port of Rotterdam"),
]


async def _fetch_slug(session, slug: str, company: str) -> list[Job]:
    url = f"https://{slug}.recruitee.com/api/offers/"
    sem = get_sem(f"{slug}.recruitee.com")
    status, data = await safe_get(session, url, sem, headers=HEADERS_JSON)

    if status == 404:
        log.debug("Recruitee %s: 404", slug)
        return []
    if status != 200 or not isinstance(data, dict):
        log.debug("Recruitee %s: status=%s", slug, status)
        return []

    jobs: list[Job] = []
    for offer in data.get("offers", []):
        title = offer.get("title", "")
        desc = _BS(offer.get("description", "") or "", "lxml").get_text(" ", strip=True)
        offer_slug = offer.get("slug", "")
        loc = offer.get("location", "")
        job_url = f"https://{slug}.recruitee.com/o/{offer_slug}"

        if not _valid_url(job_url):
            continue

        ok, _ = passes_gate(_norm(title), company=company)
        if not ok:
            continue

        jobs.append(Job(
            title=title, company=company, location=loc,
            url=job_url, description=desc, source="recruitee",
        ))

    return jobs


async def fetch_recruitee(session) -> list[Job]:
    tasks = [_fetch_slug(session, s, c) for s, c in TARGETS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("Recruitee error: %s", r)
    return jobs
