"""AeroScout — job aggregator for aviation analytics roles in the Netherlands."""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time

import aiohttp

from core.dedup import dedup
from core.gate import passes_gate
from core.models import Job
from core.normalise import _norm
from core.scorer import infer_seniority, score
from output.display import display_results
from output.save import save_results
from sources._http import TASK_TIMEOUT, make_timeout, _SSL
from sources.enrichment import enrich_batch

# Windows UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

log = logging.getLogger("aeroscout")

# ── Source registry ─────────────────────────────────────────────────────────

_SOURCES = {
    "workday": ("sources.workday", "fetch_workday"),
    "greenhouse": ("sources.greenhouse", "fetch_greenhouse"),
    "lever": ("sources.lever", "fetch_lever"),
    "recruitee": ("sources.recruitee", "fetch_recruitee"),
    "smartrecruiters": ("sources.smartrecruiters", "fetch_smartrecruiters"),
    "ashby": ("sources.ashby", "fetch_ashby"),
    "teamtailor": ("sources.teamtailor", "fetch_teamtailor"),
    "workable": ("sources.workable", "fetch_workable"),
    "personio": ("sources.personio", "fetch_personio"),
    "linkedin": ("sources.linkedin", "fetch_linkedin"),
    "adzuna": ("sources.adzuna", "fetch_adzuna"),
    "stepstone": ("sources.stepstone", "fetch_stepstone"),
    "direct": ("sources.direct", "fetch_direct"),
    "nvb": ("sources.nvb", "fetch_nvb"),
    "intermediair": ("sources.intermediair", "fetch_intermediair"),
}


def _import_fetcher(module_path: str, func_name: str):
    """Lazy import a fetcher function."""
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, func_name)


async def _fetch_source(session, name: str, mod_path: str, func_name: str) -> tuple[str, list[Job]]:
    """Fetch from a single source with timeout."""
    try:
        fetcher = _import_fetcher(mod_path, func_name)
        jobs = await asyncio.wait_for(fetcher(session), timeout=TASK_TIMEOUT * 3)
        return name, jobs
    except asyncio.TimeoutError:
        log.warning("%s: timeout", name)
        return name, []
    except Exception as e:
        log.warning("%s: %s", name, e)
        return name, []


async def run(min_score: int = 40, dry_run: bool = False, test_sources: bool = False,
              output_dir: str = ".") -> None:
    """Main pipeline."""
    t0 = time.time()

    connector = aiohttp.TCPConnector(limit=30, ssl=_SSL)
    async with aiohttp.ClientSession(connector=connector, timeout=make_timeout()) as session:

        # ── Test sources mode ──────────────────────────────────────────
        if test_sources:
            print("Testing sources...")
            for name, (mod_path, func_name) in _SOURCES.items():
                try:
                    fetcher = _import_fetcher(mod_path, func_name)
                    jobs = await asyncio.wait_for(fetcher(session), timeout=TASK_TIMEOUT * 2)
                    status = f"LIVE ({len(jobs)} jobs)" if jobs else "DEAD (0 jobs)"
                except Exception as e:
                    status = f"ERROR: {e}"
                print(f"  {name:20s} {status}")
            return

        # ── Fetch all sources ──────────────────────────────────────────
        print("Fetching from all sources...")
        tasks = [
            _fetch_source(session, name, mod_path, func_name)
            for name, (mod_path, func_name) in _SOURCES.items()
        ]
        results = await asyncio.gather(*tasks)

        raw_jobs: list[Job] = []
        source_counts: dict[str, int] = {}
        for name, jobs in results:
            source_counts[name] = len(jobs)
            raw_jobs.extend(jobs)

        raw_count = len(raw_jobs)
        print(f"Raw jobs fetched: {raw_count}")

        # ── Dedup ──────────────────────────────────────────────────────
        jobs = dedup(raw_jobs)
        dedup_count = len(jobs)
        print(f"After dedup: {dedup_count}")

        # ── Quick gate (title only) ───────────────────────────────────
        gated: list[Job] = []
        for j in jobs:
            ok, _ = passes_gate(_norm(j.title), company=j.company)
            if ok:
                gated.append(j)
        quick_gate_count = len(gated)
        print(f"After quick gate: {quick_gate_count}")

        if dry_run:
            print(f"\n[DRY RUN] Would enrich {quick_gate_count} jobs. Stopping.")
            return

        # ── Enrich ─────────────────────────────────────────────────────
        print(f"Enriching {quick_gate_count} jobs...")
        enriched = await enrich_batch(session, gated)

        # ── Full gate (title + description) ────────────────────────────
        full_gated: list[Job] = []
        for j in enriched:
            ok, _ = passes_gate(_norm(j.title), j.description, j.company)
            if ok:
                full_gated.append(j)
        full_gate_count = len(full_gated)
        print(f"After full gate: {full_gate_count}")

        # ── Score + seniority ──────────────────────────────────────────
        for j in full_gated:
            j.score, j.score_detail = score(j.title, j.company, j.location, j.description)
            j.seniority = infer_seniority(j.title, j.description)

        # ── Filter + sort ──────────────────────────────────────────────
        qualifying = [j for j in full_gated if j.score >= min_score]
        qualifying.sort(key=lambda j: j.score, reverse=True)

    # ── Display + save ─────────────────────────────────────────────────
    elapsed = time.time() - t0
    print(f"\nQualifying jobs (score >= {min_score}): {len(qualifying)}")
    print(f"Runtime: {elapsed:.1f}s\n")

    display_results(qualifying)
    filepath = save_results(qualifying, output_dir)
    print(f"\nResults saved to: {filepath}")

    # ── Summary ────────────────────────────────────────────────────────
    print(f"\n--- Summary ---")
    print(f"Raw: {raw_count} | Dedup: {dedup_count} | Quick gate: {quick_gate_count} "
          f"| Full gate: {full_gate_count} | Qualifying: {len(qualifying)}")
    print(f"Per source:")
    for name, count in sorted(source_counts.items()):
        status = "ZERO" if count == 0 else str(count)
        print(f"  {name:20s} {status}")


def main():
    parser = argparse.ArgumentParser(description="AeroScout — Aviation Analytics Job Aggregator")
    parser.add_argument("--min-score", type=int, default=40, help="Minimum score threshold (default: 40)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--test-sources", action="store_true", help="Test each source for LIVE/DEAD status")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and gate, but skip enrichment")
    parser.add_argument("--output-dir", default=".", help="Directory for output files")
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=level, format="%(name)s %(levelname)s %(message)s")

    asyncio.run(run(
        min_score=args.min_score,
        dry_run=args.dry_run,
        test_sources=args.test_sources,
        output_dir=args.output_dir,
    ))


if __name__ == "__main__":
    main()
