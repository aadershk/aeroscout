"""Title normalisation and utility helpers."""
from __future__ import annotations

import random
import re
from urllib.parse import urlparse


def _norm(title: str) -> str:
    """Normalise a job title: strip HTML, ATS codes, brackets, CamelCase split, collapse ws."""
    t = title
    # 1. Strip HTML tags
    t = re.sub(r'<[^>]+>', ' ', t)
    # 2. Strip ATS codes
    t = re.sub(r'^[A-Z]\d{4,9}-\d{3}\s+', '', t)
    t = re.sub(r'^\w{2,8}-\d{3,}\s*[:\-\u2013]\s*', '', t)
    # 3. Strip bracket prefix
    t = re.sub(r'^[\[\(][^\]\)]{1,25}[\]\)]\s*', '', t)
    # 4. CamelCase split
    t = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', t)
    t = re.sub(r'(?<=[A-Z]{2})(?=[A-Z][a-z])', ' ', t)
    # 5. Collapse whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _valid_url(url: str) -> bool:
    """Return True only for http/https URLs with a netloc, not javascript: or #."""
    if not url or url.startswith('javascript:') or url.strip() == '#':
        return False
    try:
        p = urlparse(url)
        return p.scheme in ('http', 'https') and bool(p.netloc)
    except Exception:
        return False


_NL_PAT = re.compile(
    r'netherlands|nederland|amsterdam|schiphol|hoofddorp|eindhoven|rotterdam'
    r'|den haag|the hague|utrecht|rijswijk|amstelveen|haarlemmermeer'
    r'|north holland|noord-holland|\bnl\b',
    re.I,
)


def _is_nl(text: str) -> bool:
    """Return True if text mentions a Dutch location."""
    return bool(_NL_PAT.search(text))


def _jitter(attempt: int) -> float:
    """Exponential jitter for retries."""
    return random.uniform(0, min(2 ** attempt, 30))


def _parse_ct(headers: dict) -> str:
    """Extract bare MIME type from Content-Type header, stripping charset etc."""
    ct = headers.get('Content-Type', headers.get('content-type', ''))
    return ct.split(';')[0].strip().lower()
