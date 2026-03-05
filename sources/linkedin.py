"""LinkedIn jobs-guest scraper.

Endpoint: GET https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
Params: keywords=..., location=Netherlands, start=0/25/50...
Response: HTML fragment with <li> job card elements.

CSS selectors (confirmed 2024-2025):
  title:    h3.base-search-card__title
  company:  h4.base-search-card__subtitle
  location: span.job-search-card__location
  url:      a.base-card__full-link[href]
  date:     time.job-search-card__listdate

Rate limiting: semaphore(1), random delay between requests.
"""
from __future__ import annotations

import asyncio
import logging
import random

from bs4 import BeautifulSoup
import aiohttp

from core.models import Job
from core.normalise import _norm, _valid_url, _jitter
from sources._http import HEADERS_BROWSER, TASK_TIMEOUT, _SSL, get_semaphore, make_timeout

log = logging.getLogger(__name__)

BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
HOST = "www.linkedin.com"

# Multiple keyword passes to catch different role types
KEYWORD_PASSES = [
    "revenue management analyst",
    "data scientist netherlands",
    "operations research analyst",
    "aviation analytics",
    "yield analyst",
    "pricing analyst",
    "data analyst aviation",
]

PAGES_PER_KEYWORD = 2  # 0 and 25 = 50 results per keyword


async def _fetch_page(
    session: aiohttp.ClientSession,
    keywords: str,
    start: int,
) -> list[Job]:
    sem = get_semaphore(HOST)
    params = {
        "keywords": keywords,
        "location": "Netherlands",
        "start": start,
    }

    async with sem:
        # Polite delay — LinkedIn is aggressive with rate limiting
        await asyncio.sleep(random.uniform(1.5, 3.5))
        try:
            async with session.get(
                BASE_URL,
                params=params,
                headers=HEADERS_BROWSER,
                ssl=_SSL,
                timeout=make_timeout(),
            ) as resp:
                if resp.status == 429:
                    log.warning("LinkedIn rate limited (429) on '%s' start=%s", keywords, start)
                    return []
                if resp.status != 200:
                    log.debug("LinkedIn '%s' start=%s → HTTP %s", keywords, start, resp.status)
                    return []
                html = await resp.text()
        except Exception as exc:
            log.warning("LinkedIn '%s' start=%s error: %s", keywords, start, exc)
            return []

    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("li")

    jobs = []
    for card in cards:
        title_el = card.select_one("h3.base-search-card__title")
        company_el = card.select_one("h4.base-search-card__subtitle")
        location_el = card.select_one("span.job-search-card__location")
        url_el = card.select_one("a.base-card__full-link")

        if not (title_el and url_el):
            continue

        title = _norm(title_el.get_text(strip=True))
        company = company_el.get_text(strip=True) if company_el else ""
        location = location_el.get_text(strip=True) if location_el else ""
        url = url_el.get("href", "")

        # LinkedIn URLs often have tracking params — keep as-is, they're valid
        if not _valid_url(url):
            continue
        # Strip query params to get clean URL for dedup
        url = url.split("?")[0]

        if not title:
            continue

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=url,
            source="linkedin",
        ))

    log.debug("LinkedIn '%s' start=%s: %d cards parsed", keywords, start, len(jobs))
    return jobs


async def fetch_linkedin(session: aiohttp.ClientSession) -> list[Job]:
    tasks = []
    for keywords in KEYWORD_PASSES:
        for page in range(PAGES_PER_KEYWORD):
            tasks.append(
                asyncio.wait_for(
                    _fetch_page(session, keywords, start=page * 25),
                    timeout=TASK_TIMEOUT,
                )
            )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: list[Job] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("LinkedIn task exception: %s", r)
            continue
        jobs.extend(r)

    log.debug("LinkedIn total: %d jobs", len(jobs))
    return jobs
