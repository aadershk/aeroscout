"""Stepstone NL — DROPPED source.

Stepstone NL is React-rendered with no static JSON or consistent CSS selectors.
Requires a headless browser. This stub always returns empty and logs once.
"""
from __future__ import annotations

import logging

import aiohttp

from core.models import Job

log = logging.getLogger(__name__)
_WARNED = False


async def fetch_stepstone(session: aiohttp.ClientSession) -> list[Job]:
    global _WARNED
    if not _WARNED:
        log.debug("Stepstone NL skipped — React-rendered, no static selectors")
        _WARNED = True
    return []
