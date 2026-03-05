"""Shared data model for AeroScout."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    source: str = ""
    score: int = 0
    score_detail: dict = field(default_factory=dict)
    uid: str = field(init=False)

    def __post_init__(self) -> None:
        # Import here to avoid circular; normalise is a leaf module
        from core.normalise import _norm
        self.uid = hashlib.md5(
            f"{_norm(self.title).lower()[:40]}|{self.company.lower()[:20]}".encode()
        ).hexdigest()[:14]
