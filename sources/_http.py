"""Shared HTTP configuration and domain semaphore registry."""
from __future__ import annotations

import asyncio
import ssl
from collections import defaultdict
from typing import Any

import aiohttp
import certifi

CONNECT_TIMEOUT = 8
READ_TIMEOUT = 18
TASK_TIMEOUT = 45  # per-fetcher coroutine watchdog

_SSL: ssl.SSLContext = ssl.create_default_context(cafile=certifi.where())

# Per-domain concurrency cap (3 parallel requests max per host)
_SEMAPHORES: dict[str, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(3))
# LinkedIn is extremely aggressive — cap to 1
_SEMAPHORES_STRICT = {"www.linkedin.com": asyncio.Semaphore(1)}


def get_semaphore(host: str) -> asyncio.Semaphore:
    """Return the semaphore for a given hostname."""
    return _SEMAPHORES_STRICT.get(host, _SEMAPHORES[host])


def make_timeout() -> aiohttp.ClientTimeout:
    return aiohttp.ClientTimeout(connect=CONNECT_TIMEOUT, sock_read=READ_TIMEOUT)


HEADERS_BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

HEADERS_JSON = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}
