"""Indeed NL — DROPPED source.

Indeed NL returns HTTP 403 (Cloudflare) on all aiohttp requests.
Not recoverable without a headless browser or residential proxies.
This stub exists so main.py can import it without error; it always
returns an empty list and logs a one-time debug message.
"""
from __future__ import annotations

import logging

import aiohttp

from core.models import Job

log = logging.getLogger(__name__)
_WARNED = False


async def fetch_indeed(session: aiohttp.ClientSession) -> list[Job]:
    global _WARNED
    if not _WARNED:
        log.debug("Indeed NL skipped — 403 Cloudflare wall (aiohttp not supported)")
        _WARNED = True
    return []
