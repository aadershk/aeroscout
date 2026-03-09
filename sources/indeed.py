"""Indeed NL fetcher — placeholder, Indeed blocks most scraping."""
from __future__ import annotations

import logging

from core.models import Job

log = logging.getLogger(__name__)


async def fetch_indeed(session) -> list[Job]:
    """Indeed aggressively blocks scraping; returns empty for now."""
    log.debug("Indeed: skipped (anti-scraping)")
    return []
