"""AeroScout — autonomous job-hunting tool.

Usage:
  python main.py                          # full run, default min-score 40
  python main.py --min-score 50           # raise qualifying threshold
  python main.py --debug                  # verbose logging
  python main.py --test-sources           # probe one request per source
  python main.py --dry-run --limit 3      # full pipeline, show first 3 jobs
  python main.py --output-dir ./results   # save .txt to custom path
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import time
from collections import defaultdict
from pathlib import Path

import aiohttp

from core.dedup import dedup
from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm
from core.scorer import score
from output.display import render_summary, render_table
from output.save import save_results
from sources._http import _SSL, make_timeout
from sources.ashby import fetch_ashby
from sources.adzuna import fetch_adzuna
from sources.direct import fetch_direct
from sources.greenhouse import fetch_greenhouse
from sources.indeed import fetch_indeed
from sources.lever import fetch_lever
from sources.linkedin import fetch_linkedin
from sources.personio import fetch_personio
from sources.recruitee import fetch_recruitee
from sources.smartrecruiters import fetch_smartrecruiters
from sources.stepstone import fetch_stepstone
from sources.teamtailor import fetch_teamtailor
from sources.workable import fetch_workable
from sources.workday import fetch_workday

log = logging.getLogger("aeroscout")

ALL_FETCHERS = {
    "workday":        fetch_workday,
    "greenhouse":     fetch_greenhouse,
    "smartrecruiters": fetch_smartrecruiters,
    "recruitee":      fetch_recruitee,
    "lever":          fetch_lever,
    "teamtailor":     fetch_teamtailor,
    "workable":       fetch_workable,
    "personio":       fetch_personio,
    "ashby":          fetch_ashby,
    "linkedin":       fetch_linkedin,
    "adzuna":         fetch_adzuna,
    "direct":         fetch_direct,
    "indeed":         fetch_indeed,
    "stepstone":      fetch_stepstone,
}


def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s [%(name)s] %(message)s",
        level=level,
    )
    # Suppress noisy third-party loggers
    for noisy in ("aiohttp", "asyncio", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.ERROR)


async def _test_sources(session: aiohttp.ClientSession) -> None:
    """Run one request per source and report LIVE / DEAD / EMPTY."""
    print("\nTesting sources...\n")
    for name, fetcher in ALL_FETCHERS.items():
        try:
            jobs = await asyncio.wait_for(fetcher(session), timeout=30)
            status = f"LIVE   ({len(jobs)} jobs)"
        except asyncio.TimeoutError:
            status = "TIMEOUT"
        except Exception as exc:
            status = f"ERROR  {exc}"
        print(f"  {name:<20} {status}")
    print()


async def _run_pipeline(
    session: aiohttp.ClientSession,
    min_score: int,
    dry_run: bool,
    limit: int,
    output_dir: Path,
) -> None:
    t0 = time.perf_counter()

    # ── Fetch ────────────────────────────────────────────────────────────
    tasks = [fetcher(session) for fetcher in ALL_FETCHERS.values()]
    source_names = list(ALL_FETCHERS.keys())
    results = await asyncio.gather(*tasks, return_exceptions=True)

    raw_jobs: list[Job] = []
    source_counts: dict[str, int] = defaultdict(int)
    for name, result in zip(source_names, results):
        if isinstance(result, BaseException):
            log.warning("Source '%s' failed: %s", name, result)
            continue
        source_counts[name] = len(result)
        raw_jobs.extend(result)

    raw_count = len(raw_jobs)

    # ── Dedup ────────────────────────────────────────────────────────────
    deduped = dedup(raw_jobs)
    dedup_count = len(deduped)

    # ── Gate ─────────────────────────────────────────────────────────────
    passed: list[Job] = []
    for job in deduped:
        ok, reason = passes_gate(job.title, job.description, job.company)
        if ok:
            passed.append(job)
        else:
            log.debug("GATE REJECT [%s]: %s @ %s", reason, job.title, job.company)

    gate_count = len(passed)

    # ── Score ─────────────────────────────────────────────────────────────
    for job in passed:
        job.score, job.score_detail = score(
            job.title, job.company, job.location, job.description
        )

    # ── Output ───────────────────────────────────────────────────────────
    qualifying = [j for j in passed if j.score >= min_score]
    qualifying_count = len(qualifying)

    if dry_run:
        qualifying = qualifying[:limit]

    elapsed = time.perf_counter() - t0

    zero_sources = [n for n, c in source_counts.items() if c == 0]
    render_summary(raw_count, dedup_count, gate_count, qualifying_count, zero_sources, elapsed)
    render_table(passed, min_score=min_score)

    if not dry_run:
        out_path = save_results(passed, min_score=min_score, output_dir=output_dir)
        print(f"Saved → {out_path}")


async def _main(args: argparse.Namespace) -> None:
    timeout = make_timeout()
    connector = aiohttp.TCPConnector(ssl=_SSL, limit=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        if args.test_sources:
            await _test_sources(session)
        else:
            await _run_pipeline(
                session=session,
                min_score=args.min_score,
                dry_run=args.dry_run,
                limit=args.limit,
                output_dir=Path(args.output_dir),
            )


def main() -> None:
    # Ensure UTF-8 output on Windows — job titles may contain non-ASCII chars
    import sys
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="AeroScout — autonomous aviation job hunter"
    )
    parser.add_argument("--min-score", type=int, default=40, metavar="N",
                        help="Minimum score threshold (default: 40)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable DEBUG logging")
    parser.add_argument("--test-sources", action="store_true",
                        help="Test one request per source, print LIVE/DEAD")
    parser.add_argument("--dry-run", action="store_true",
                        help="Full pipeline but only show first --limit jobs")
    parser.add_argument("--limit", type=int, default=3, metavar="N",
                        help="Number of jobs shown in --dry-run (default: 3)")
    parser.add_argument("--output-dir", default=".",
                        help="Directory for output .txt file (default: .)")
    args = parser.parse_args()

    _setup_logging(args.debug)
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()
