"""
CLI entry point for knowledge-engine.

All commands are exposed under the `ke` binary (see pyproject.toml scripts).

Usage:
    ke research "topic"          Run a research session
    ke search "query"            Search existing knowledge
    ke schedule                  Run scheduled heartbeat tasks
    ke export                    Export a knowledge package
    ke status                    Show knowledge store stats
    ke benchmark                 Run DRB benchmark suite
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=False, path_type=Path),
    default=None,
    help="Path to ke.yaml config file (default: ./ke.yaml)",
)
@click.pass_context
def main(ctx: click.Context, config: Path | None) -> None:
    """knowledge-engine: continuous knowledge accumulation with structured evaluation."""
    from knowledge_engine.config.settings import Settings

    ctx.ensure_object(dict)
    ctx.obj["settings"] = Settings(_config_file=config)  # type: ignore[call-arg]


@main.command()
@click.argument("topic")
@click.option("--waves", default=2, show_default=True, help="Number of research waves")
@click.option("--skeptic/--no-skeptic", default=True, show_default=True, help="Run adversarial skeptic pass")
@click.option("--dry-run", is_flag=True, help="Run pipeline without persisting output")
@click.pass_context
def research(ctx: click.Context, topic: str, waves: int, skeptic: bool, dry_run: bool) -> None:
    """Run a research session on TOPIC."""
    from knowledge_engine.research.pipeline import ResearchPipeline

    settings = ctx.obj["settings"]
    pipeline = ResearchPipeline(settings=settings)

    console.print(f"[bold green]Researching:[/] {topic}")
    with console.status("Running pipeline..."):
        result = pipeline.run(topic=topic, waves=waves, with_skeptic=skeptic, dry_run=dry_run)

    console.print(f"[bold]Gate result:[/] {result.gate_outcome}")
    if result.persisted_path:
        console.print(f"[bold]Saved:[/] {result.persisted_path}")


@main.command()
@click.argument("query")
@click.option("--top-k", default=5, show_default=True, help="Number of results to return")
@click.option("--rerank/--no-rerank", default=True, show_default=True)
@click.option("--intent", default=None, help='Domain intent hint (e.g. "ml", "finance")')
@click.pass_context
def search(ctx: click.Context, query: str, top_k: int, rerank: bool, intent: str | None) -> None:
    """Search existing knowledge for QUERY."""
    from knowledge_engine.search.hybrid import HybridSearch

    settings = ctx.obj["settings"]
    searcher = HybridSearch(settings=settings)

    results = searcher.search(query=query, top_k=top_k, rerank=rerank, intent=intent)
    for i, r in enumerate(results, 1):
        console.print(f"[bold]{i}.[/] [cyan]{r.title}[/] (score={r.score:.3f})")
        console.print(f"   {r.excerpt}")


@main.command()
@click.option("--once", is_flag=True, help="Run all due tasks once and exit")
@click.option("--task", default=None, help="Run a specific named task")
@click.pass_context
def schedule(ctx: click.Context, once: bool, task: str | None) -> None:
    """Run scheduled heartbeat tasks."""
    from knowledge_engine.scheduler.heartbeat import Heartbeat

    settings = ctx.obj["settings"]
    hb = Heartbeat(settings=settings)

    if task:
        hb.run_task(task)
    elif once:
        hb.run_due()
    else:
        console.print("[yellow]Use --once to run due tasks, or --task NAME to run a specific task.[/]")
        hb.list_tasks()


@main.command()
@click.option("--output", "-o", type=click.Path(path_type=Path), default=Path("./export"))
@click.option("--format", "fmt", type=click.Choice(["jsonl", "markdown", "parquet"]), default="jsonl")
@click.pass_context
def export(ctx: click.Context, output: Path, fmt: str) -> None:
    """Export knowledge package for sharing or fine-tuning."""
    from knowledge_engine.knowledge.package import KnowledgePackage

    settings = ctx.obj["settings"]
    pkg = KnowledgePackage(settings=settings)
    pkg.export(output_dir=output, format=fmt)
    console.print(f"[green]Exported to[/] {output}")


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show knowledge store stats and recent activity."""
    from knowledge_engine.knowledge.store import KnowledgeStore

    settings = ctx.obj["settings"]
    store = KnowledgeStore(settings=settings)
    stats = store.stats()

    console.print("[bold]Knowledge Store[/]")
    console.print(f"  Notes:     {stats['note_count']}")
    console.print(f"  Lessons:   {stats['lesson_count']}")
    console.print(f"  Rules:     {stats['rule_count']}")
    console.print(f"  Last run:  {stats['last_run']}")
    console.print(f"  Dir:       {settings.knowledge_dir}")


@main.command()
@click.option("--suite", type=click.Choice(["drb"]), default="drb")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=Path("./results"))
@click.pass_context
def benchmark(ctx: click.Context, suite: str, output: Path) -> None:
    """Run evaluation benchmark (default: DRB — Deep Research Bench)."""
    console.print(f"[yellow]Benchmark suite '{suite}' — not yet implemented.[/]")
    sys.exit(1)


if __name__ == "__main__":
    main()
