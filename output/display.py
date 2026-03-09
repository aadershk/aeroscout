"""Rich console display for job results."""
from __future__ import annotations

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from core.models import Job

console = Console()


def display_results(jobs: list[Job]) -> None:
    """Display jobs in a Rich table with score breakdown."""
    if not jobs:
        console.print("[bold red]No qualifying jobs found.[/bold red]")
        return

    width = console.width or 120

    # Main table
    table = Table(show_header=True, header_style="bold", expand=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Score", width=6)
    table.add_column("Seniority", width=10)
    table.add_column("Title", min_width=25)
    table.add_column("Company", min_width=15)
    table.add_column("Location", min_width=12)

    for i, job in enumerate(jobs, 1):
        # Score color
        if job.score > 75:
            score_str = f"[bright_green]{job.score}[/bright_green]"
        elif job.score >= 50:
            score_str = f"[yellow]{job.score}[/yellow]"
        else:
            score_str = f"[white]{job.score}[/white]"

        # Seniority color
        sen = job.seniority
        if sen == "Junior":
            sen_str = f"[cyan]{sen}[/cyan]"
        elif sen == "Senior":
            sen_str = f"[red]{sen}[/red]"
        else:
            sen_str = f"[yellow]{sen}[/yellow]"

        table.add_row(
            str(i),
            score_str,
            sen_str,
            escape(job.title),
            escape(job.company),
            escape(job.location),
        )

    console.print(table)

    # URL list
    console.print("\n[bold]Job URLs:[/bold]")
    for i, job in enumerate(jobs, 1):
        console.print(f"  {i}. [link={job.url}]{escape(job.url)}[/link]")

    # Score breakdown
    console.print("\n[bold]Score Breakdown:[/bold]")
    for i, job in enumerate(jobs, 1):
        if job.score_detail:
            parts = ", ".join(f"{k}={v:+d}" for k, v in job.score_detail.items())
            console.print(f"  {i}. {escape(job.title[:50])}: {parts}")
