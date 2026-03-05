"""Two-level deduplication for AeroScout.

Level 1: exact URL dedup (normalised to lowercase, strip trailing slash)
Level 2: uid-based semantic dedup (title+company hash from Job.__post_init__)
"""
from __future__ import annotations

from core.models import Job


def dedup(jobs: list[Job]) -> list[Job]:
    """Remove duplicates; keep first occurrence of each URL and uid."""
    seen_urls: set[str] = set()
    seen_uids: set[str] = set()
    result: list[Job] = []

    for job in jobs:
        norm_url = job.url.lower().rstrip("/")
        if norm_url in seen_urls:
            continue
        if job.uid in seen_uids:
            continue
        seen_urls.add(norm_url)
        seen_uids.add(job.uid)
        result.append(job)

    return result
