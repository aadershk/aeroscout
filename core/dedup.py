"""Deduplication: URL-level then UID-level."""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from core.models import Job

_STRIP_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                 "gclid", "fbclid"}


def _clean_url(url: str) -> str:
    """Normalise URL for dedup: lowercase, strip trailing slash, strip tracking params."""
    url = url.strip().lower().rstrip("/")
    try:
        p = urlparse(url)
        qs = parse_qs(p.query, keep_blank_values=False)
        filtered = {k: v for k, v in qs.items() if k not in _STRIP_PARAMS}
        clean_query = urlencode(filtered, doseq=True) if filtered else ""
        return urlunparse((p.scheme, p.netloc, p.path, p.params, clean_query, ""))
    except Exception:
        return url


def dedup(jobs: list[Job]) -> list[Job]:
    """Remove duplicates: Level 1 = URL exact, Level 2 = uid match. Keep first."""
    seen_urls: set[str] = set()
    seen_uids: set[str] = set()
    result: list[Job] = []
    for job in jobs:
        clean = _clean_url(job.url)
        if clean in seen_urls:
            continue
        seen_urls.add(clean)
        if job.uid in seen_uids:
            continue
        seen_uids.add(job.uid)
        result.append(job)
    return result
