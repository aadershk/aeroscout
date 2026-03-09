"""Save results to text file."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from core.models import Job


def save_results(jobs: list[Job], output_dir: str = ".") -> str:
    """Save jobs to aeroscout_YYYYMMDD_HHMMSS.txt. Returns the file path."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    filepath = out_path / f"aeroscout_{ts}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"AeroScout Results — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Total qualifying jobs: {len(jobs)}\n")
        f.write("=" * 80 + "\n\n")

        for i, job in enumerate(jobs, 1):
            f.write(f"#{i}  Score: {job.score}  Seniority: {job.seniority}\n")
            f.write(f"Title:    {job.title}\n")
            f.write(f"Company:  {job.company}\n")
            f.write(f"Location: {job.location}\n")
            f.write(f"Source:   {job.source}\n")
            f.write(f"URL:      {job.url}\n")
            if job.score_detail:
                parts = ", ".join(f"{k}={v:+d}" for k, v in job.score_detail.items())
                f.write(f"Scoring:  {parts}\n")
            if job.description:
                f.write(f"Description: {job.description[:300]}\n")
            f.write("-" * 80 + "\n\n")

    return str(filepath)
