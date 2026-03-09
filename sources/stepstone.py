"""Stepstone NL fetcher — JSON-LD only."""
from __future__ import annotations

import asyncio
import json
import logging

from bs4 import BeautifulSoup

from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_HTML, get_sem, safe_get

log = logging.getLogger(__name__)

QUERIES = [
    "revenue management analyst", "yield analyst", "operations research analyst",
    "aviation data scientist", "pricing analyst", "quantitative analyst",
    "demand forecasting analyst", "business analyst aviation", "data analyst schiphol",
    "junior data analyst", "supply chain data scientist", "transport analytics",
]


async def fetch_stepstone(session) -> list[Job]:
    sem = get_sem("www.stepstone.nl")
    jobs: list[Job] = []
    seen_urls: set[str] = set()

    for q in QUERIES:
        url = "https://www.stepstone.nl/vacatures/"
        params = {"q": q, "where": "Netherlands"}
        status, text = await safe_get(session, url, sem, params=params, headers=HEADERS_HTML)

        if status != 200 or not text or not isinstance(text, str):
            log.debug("Stepstone q=%s: status=%s", q, status)
            continue

        soup = BeautifulSoup(text, "lxml")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                ld = json.loads(script.string or "")
                items = ld if isinstance(ld, list) else ld.get("itemListElement", [ld])
                for item in items:
                    posting = item.get("item", item) if isinstance(item, dict) else item
                    if not isinstance(posting, dict):
                        continue
                    if posting.get("@type") not in ("JobPosting", None):
                        continue

                    title = posting.get("title", "")
                    company = ""
                    ho = posting.get("hiringOrganization", {})
                    if isinstance(ho, dict):
                        company = ho.get("name", "")
                    loc_obj = posting.get("jobLocation", {})
                    loc = ""
                    if isinstance(loc_obj, dict):
                        addr = loc_obj.get("address", {})
                        if isinstance(addr, dict):
                            loc = addr.get("addressLocality", "")
                    elif isinstance(loc_obj, list) and loc_obj:
                        addr = loc_obj[0].get("address", {})
                        if isinstance(addr, dict):
                            loc = addr.get("addressLocality", "")
                    job_url = posting.get("url", "")

                    if not title or not _valid_url(job_url) or job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    ok, _ = passes_gate(_norm(title), company=company)
                    if not ok:
                        continue

                    jobs.append(Job(
                        title=title, company=company, location=loc,
                        url=job_url, source="stepstone",
                    ))
            except (json.JSONDecodeError, AttributeError):
                continue

    return jobs
