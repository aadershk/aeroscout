"""Teamtailor fetcher."""
from __future__ import annotations

import asyncio
import logging

from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_JSON, get_sem, safe_get

log = logging.getLogger(__name__)

TARGETS = [
    ("transavia-nl", "Transavia"), ("fokker", "Fokker Services"),
    ("to70", "To70"), ("aevean", "Aevean"), ("naco", "NACO"),
    ("ibssoftware", "IBS Software"), ("travix", "Travix"),
    ("nngroup", "NN Group"), ("prorail", "ProRail"), ("ns-nl", "NS"),
    ("postnl", "PostNL"), ("vanderlande", "Vanderlande"),
    ("seaburyconsulting", "Seabury Consulting"), ("steer", "Steer"),
    ("royalhaskoningdhv", "Royal HaskoningDHV"), ("coolblue", "Coolblue"),
    ("portofrotterdam", "Port of Rotterdam"), ("eurocontrol", "Eurocontrol"),
    ("schiphol", "Schiphol Group"),
]


async def _fetch_slug(session, slug: str, company: str) -> list[Job]:
    sem = get_sem(f"{slug}.teamtailor.com")
    jobs: list[Job] = []
    seen_urls: set[str] = set()

    for page in range(1, 4):  # up to 3 pages
        url = f"https://{slug}.teamtailor.com/jobs.json"
        params = {"page[number]": str(page)} if page > 1 else None
        status, data = await safe_get(session, url, sem, params=params, headers=HEADERS_JSON)

        if status == 404:
            log.debug("Teamtailor %s: 404", slug)
            return []
        if status != 200 or not isinstance(data, dict):
            log.debug("Teamtailor %s page=%d: status=%s", slug, page, status)
            break

        for j in data.get("data", []):
            attrs = j.get("attributes", {})
            title = attrs.get("title", "")
            desc = attrs.get("body", "")
            loc = attrs.get("location", "") or ""
            # Build URL from links or slug
            job_links = j.get("links", {})
            job_url = job_links.get("careersite-job-url", "") or job_links.get("self", "")

            if not _valid_url(job_url) or job_url in seen_urls:
                continue
            seen_urls.add(job_url)

            ok, _ = passes_gate(_norm(title), company=company)
            if not ok:
                continue

            jobs.append(Job(
                title=title, company=company, location=loc,
                url=job_url, description=desc, source="teamtailor",
            ))

        # Check pagination
        meta = data.get("meta", {})
        total = meta.get("total-count", meta.get("total_count", 0))
        page_size = meta.get("page-size", meta.get("page_size", 20))
        if page * page_size >= total:
            break

    return jobs


async def fetch_teamtailor(session) -> list[Job]:
    tasks = [_fetch_slug(session, s, c) for s, c in TARGETS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[Job] = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
        elif isinstance(r, Exception):
            log.warning("Teamtailor error: %s", r)
    return jobs
