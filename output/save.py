"""Timestamped .txt output file writer."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from core.models import Job


def save_results(
    jobs: list[Job],
    min_score: int = 40,
    output_dir: str | Path = ".",
) -> Path:
    """Write qualifying jobs to a timestamped .txt file. Returns the path."""
    qualifying = [j for j in jobs if j.score >= min_score]
    qualifying.sort(key=lambda j: j.score, reverse=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"aeroscout_{ts}.txt"

    lines = [
        f"AeroScout — Run {ts}",
        f"Qualifying jobs (score >= {min_score}): {len(qualifying)}",
        "=" * 70,
        "",
    ]

    for i, job in enumerate(qualifying, 1):
        lines += [
            f"[{i}] Score: {job.score}",
            f"    Title:    {job.title}",
            f"    Company:  {job.company}",
            f"    Location: {job.location or '—'}",
            f"    Source:   {job.source}",
            f"    URL:      {job.url}",
            "",
        ]

    lines += [
        "=" * 70,
        "URLs only:",
        "",
    ]
    for i, job in enumerate(qualifying, 1):
        lines.append(f"[{i}] {job.url}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
