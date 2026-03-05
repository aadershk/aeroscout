"""Rich terminal display for AeroScout results."""
from __future__ import annotations

from rich import print as rprint
from rich.markup import escape
from rich.table import Table
from rich.console import Console
from rich.text import Text

from core.models import Job

console = Console(force_terminal=True, highlight=False)


def _tier_colour(score: int) -> str:
    if score >= 90:
        return "bold green"
    if score >= 65:
        return "green"
    if score >= 45:
        return "yellow"
    return "dim"


def render_table(jobs: list[Job], min_score: int = 40) -> None:
    """Print sorted job table to terminal."""
    qualifying = [j for j in jobs if j.score >= min_score]
    qualifying.sort(key=lambda j: j.score, reverse=True)

    if not qualifying:
        rprint(f"[yellow]No jobs scored >= {min_score}[/yellow]")
        return

    table = Table(
        title=f"AeroScout — {len(qualifying)} qualifying roles (score >= {min_score})",
        show_lines=False,
        expand=True,
    )
    table.add_column("#", style="dim", width=3, no_wrap=True)
    table.add_column("Score", width=6, no_wrap=True)
    table.add_column("Title", min_width=28)
    table.add_column("Company", min_width=18)
    table.add_column("Location", min_width=14)
    table.add_column("Source", width=14, no_wrap=True)

    for i, job in enumerate(qualifying, 1):
        colour = _tier_colour(job.score)
        table.add_row(
            str(i),
            f"[{colour}]{job.score}[/{colour}]",
            escape(job.title),
            escape(job.company),
            escape(job.location or "—"),
            escape(job.source),
        )

    console.print(table)
    console.print()

    # URL list for copy-paste
    console.print("[bold]Job URLs:[/bold]")
    for i, job in enumerate(qualifying, 1):
        console.print(f"  [{i}] {escape(job.url)}")
    console.print()


def render_score_detail(job: Job) -> None:
    """Print score breakdown for a single job (for debugging)."""
    rprint(f"\n[bold]{escape(job.title)}[/bold] @ [cyan]{escape(job.company)}[/cyan]")
    rprint(f"  Total score: [bold]{job.score}[/bold]")
    for k, v in job.score_detail.items():
        if k == "total":
            continue
        sign = "+" if v > 0 else ""
        colour = "green" if v > 0 else "red"
        rprint(f"  [{colour}]{sign}{v}[/{colour}]  {k}")


def render_summary(
    raw: int,
    after_dedup: int,
    after_gate: int,
    qualifying: int,
    zero_sources: list[str],
    elapsed: float,
) -> None:
    """Print run summary stats."""
    console.print(
        f"[dim]Raw fetched:[/dim] {raw}  "
        f"[dim]After dedup:[/dim] {after_dedup}  "
        f"[dim]After gate:[/dim] {after_gate}  "
        f"[bold]Qualifying (>= min_score):[/bold] {qualifying}  "
        f"[dim]Elapsed:[/dim] {elapsed:.1f}s"
    )
    if zero_sources:
        console.print(f"[dim]Zero-result sources:[/dim] {', '.join(zero_sources)}")
