"""Shared HTTP helpers with rate limiting and retries."""
from __future__ import annotations

import asyncio
import logging
import ssl
from collections import defaultdict
from typing import Any

import aiohttp
import certifi

from core.normalise import _jitter

log = logging.getLogger(__name__)

CONNECT_TIMEOUT = 8
READ_TIMEOUT = 20
TASK_TIMEOUT = 60

_SSL = ssl.create_default_context(cafile=certifi.where())

_SEMS: dict[str, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(3))
_SEMS_STRICT: dict[str, asyncio.Semaphore] = {
    "www.linkedin.com": asyncio.Semaphore(1),
    "nl.indeed.com": asyncio.Semaphore(1),
    "www.nationalevacaturebank.nl": asyncio.Semaphore(2),
    "www.intermediair.nl": asyncio.Semaphore(2),
}

HEADERS_JSON = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

HEADERS_HTML = {
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
    "Accept-Language": "en-US,en;q=0.9,nl;q=0.7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}


def get_sem(host: str) -> asyncio.Semaphore:
    return _SEMS_STRICT.get(host, _SEMS[host])


def make_timeout() -> aiohttp.ClientTimeout:
    return aiohttp.ClientTimeout(connect=CONNECT_TIMEOUT, sock_read=READ_TIMEOUT)


async def safe_get(
    session: aiohttp.ClientSession,
    url: str,
    sem: asyncio.Semaphore,
    params: dict | None = None,
    headers: dict | None = None,
    retries: int = 3,
) -> tuple[int, Any]:
    """GET with jitter backoff on 429/503/502. Returns (status, json_or_text_or_None)."""
    for attempt in range(retries):
        try:
            async with sem:
                async with session.get(
                    url, params=params, headers=headers or HEADERS_HTML, ssl=_SSL,
                    timeout=make_timeout(),
                ) as resp:
                    if resp.status in (429, 502, 503):
                        if attempt < retries - 1:
                            await asyncio.sleep(_jitter(attempt))
                            continue
                        return resp.status, None
                    ct = resp.headers.get("Content-Type", "")
                    if "json" in ct:
                        return resp.status, await resp.json(content_type=None)
                    return resp.status, await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.debug("GET %s attempt %d: %s", url, attempt, e)
            if attempt < retries - 1:
                await asyncio.sleep(_jitter(attempt))
            else:
                return 0, None
    return 0, None


async def safe_post(
    session: aiohttp.ClientSession,
    url: str,
    sem: asyncio.Semaphore,
    payload: dict | None = None,
    headers: dict | None = None,
    retries: int = 3,
) -> tuple[int, Any]:
    """POST with jitter backoff on 429/503/502. Returns (status, json_or_text_or_None)."""
    for attempt in range(retries):
        try:
            async with sem:
                async with session.post(
                    url, json=payload, headers=headers or HEADERS_JSON, ssl=_SSL,
                    timeout=make_timeout(),
                ) as resp:
                    if resp.status in (429, 502, 503):
                        if attempt < retries - 1:
                            await asyncio.sleep(_jitter(attempt))
                            continue
                        return resp.status, None
                    ct = resp.headers.get("Content-Type", "")
                    if "json" in ct:
                        return resp.status, await resp.json(content_type=None)
                    return resp.status, await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.debug("POST %s attempt %d: %s", url, attempt, e)
            if attempt < retries - 1:
                await asyncio.sleep(_jitter(attempt))
            else:
                return 0, None
    return 0, None
