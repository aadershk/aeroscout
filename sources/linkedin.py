"""LinkedIn guest job search scraper."""
from __future__ import annotations

import asyncio
import logging
import random

from bs4 import BeautifulSoup

from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm, _valid_url
from sources._http import HEADERS_HTML, get_sem, safe_get

log = logging.getLogger(__name__)

QUERIES = [
    "revenue management analyst", "yield analyst netherlands",
    "operations research analyst", "aviation data scientist",
    "pricing analyst", "data scientist aviation",
    "mro analytics", "quantitative analyst netherlands",
    "demand forecasting analyst", "supply chain data scientist",
    "transport analytics netherlands", "data analyst KLM",
    "data analyst Schiphol", "data analyst aviation amsterdam",
    "management consultant analytics", "junior data scientist netherlands",
    "graduate data analyst netherlands", "business analyst aviation",
    "junior revenue management analyst", "entry level operations research",
    "business analyst schiphol", "data analyst dnata",
    "graduate pricing analyst netherlands", "MSc graduate data analyst amsterdam",
]

PAGES_PER_QUERY = 2
_BASE = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


async def fetch_linkedin(session) -> list[Job]:
    sem = get_sem("www.linkedin.com")
    jobs: list[Job] = []
    seen_urls: set[str] = set()

    for q in QUERIES:
        skip_remaining = False
        for page in range(PAGES_PER_QUERY):
            if skip_remaining:
                break

            start = page * 25
            params = {"keywords": q, "location": "Netherlands", "start": str(start)}

            async with sem:
                await asyncio.sleep(random.uniform(2.0, 4.0))
                status, text = await safe_get(
                    session, _BASE, sem=asyncio.Semaphore(1),  # already in sem
                    params=params, headers=HEADERS_HTML,
                )

            if status == 429:
                log.warning("LinkedIn 429 on query=%s, skipping remaining pages", q)
                skip_remaining = True
                continue

            if status != 200 or not text or not isinstance(text, str):
                continue

            soup = BeautifulSoup(text, "lxml")
            cards = soup.find_all("li")

            for card in cards:
                title_el = card.select_one("h3.base-search-card__title")
                company_el = card.select_one("h4.base-search-card__subtitle")
                loc_el = card.select_one("span.job-search-card__location")
                link_el = card.select_one("a.base-card__full-link[href]")

                if not title_el or not link_el:
                    continue

                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else ""
                loc = loc_el.get_text(strip=True) if loc_el else ""
                raw_url = link_el.get("href", "")
                url = raw_url.split("?")[0] if raw_url else ""

                if not _valid_url(url) or url in seen_urls:
                    continue
                seen_urls.add(url)

                ok, _ = passes_gate(_norm(title), company=company)
                if not ok:
                    continue

                jobs.append(Job(
                    title=title, company=company, location=loc,
                    url=url, source="linkedin",
                ))

    return jobs
