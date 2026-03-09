"""Adzuna NL fetcher."""
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


async def fetch_adzuna(session) -> list[Job]:
    sem = get_sem("www.adzuna.nl")
    jobs: list[Job] = []
    seen_urls: set[str] = set()

    for q in QUERIES:
        url = "https://www.adzuna.nl/search"
        params = {"q": q, "results_per_page": "20", "sort_by": "date"}
        status, text = await safe_get(session, url, sem, params=params, headers=HEADERS_HTML)

        if status != 200 or not text or not isinstance(text, str):
            log.debug("Adzuna q=%s: status=%s", q, status)
            continue

        soup = BeautifulSoup(text, "lxml")

        # Try JSON-LD first
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                ld = json.loads(script.string or "")
                items = ld if isinstance(ld, list) else ld.get("itemListElement", [ld])
                for item in items:
                    posting = item.get("item", item) if isinstance(item, dict) else item
                    if not isinstance(posting, dict):
                        continue
                    if posting.get("@type") not in ("JobPosting", "jobPosting", None):
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
                        url=job_url, source="adzuna",
                    ))
            except (json.JSONDecodeError, AttributeError):
                continue

        # Fallback: parse article cards
        for card in soup.select("article[data-aid]"):
            title_el = card.select_one("h2 a, .title a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://www.adzuna.nl" + job_url

            company_el = card.select_one(".company, [data-company]")
            company = company_el.get_text(strip=True) if company_el else ""
            loc_el = card.select_one(".location, [data-location]")
            loc = loc_el.get_text(strip=True) if loc_el else ""

            if not _valid_url(job_url) or job_url in seen_urls:
                continue
            seen_urls.add(job_url)

            ok, _ = passes_gate(_norm(title), company=company)
            if not ok:
                continue

            jobs.append(Job(
                title=title, company=company, location=loc,
                url=job_url, source="adzuna",
            ))

    return jobs
