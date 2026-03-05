"""Utility helpers used across all modules."""
from __future__ import annotations

import random
import re
from urllib.parse import urlparse


# Strip leading ATS job codes like "REQ-1234: " or "(NL) " etc.
_CODE_PREFIX = re.compile(r"^[\[\(][^\]\)]{1,20}[\]\)]\s*")
_ATS_ID = re.compile(r"^\w{2,8}-\d{3,}\s*[:\-–]\s*")
_HTML_TAGS = re.compile(r"<[^>]+>")
_MULTI_SPACE = re.compile(r"\s+")


def _norm(title: str) -> str:
    """Normalise a job title: strip HTML, remove ATS prefixes, collapse whitespace."""
    t = _HTML_TAGS.sub(" ", title)
    t = _CODE_PREFIX.sub("", t)
    t = _ATS_ID.sub("", t)
    t = _MULTI_SPACE.sub(" ", t).strip()
    return t


def _valid_url(url: str) -> bool:
    """Return True only if url is http/https with a real host."""
    if not url:
        return False
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _parse_ct(headers: dict) -> str:
    """Extract bare MIME type from Content-Type header."""
    ct = headers.get("Content-Type", headers.get("content-type", ""))
    return ct.split(";")[0].strip().lower()


def _jitter(attempt: int) -> float:
    """Exponential backoff with jitter: 1-2s, 2-4s, 4-8s..."""
    base = 2 ** attempt
    return base + random.uniform(0, base)
