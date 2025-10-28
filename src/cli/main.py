"""CLI for podcast content management agent."""
import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..agents import PodcastOrchestrator
from ..config.paths import generate_run_directory
from ..llm import LLMGateway
from ..models import AggregateReport

# Load environment variables
load_dotenv()

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="Podcast Content Management Agent")
def cli():
    """Podcast Content Management Agent - AI-powered podcast content processing."""
    pass


@cli.command()
@click.option(
    "--episode",
    "-e",
    type=click.Path(exists=True, path_type=Path),
    help="Path to single episode JSON file",
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Process all episodes in sample_inputs/ directory",
)
@click.option(
    "--model",
    "-m",
    default="anthropic/claude-4.5-sonnet",
    help="LLM model to use (default: anthropic/claude-4.5-sonnet)",
)
@click.option(
    "--api-key",
    help="OpenRouter API key (overrides OPENROUTER_API_KEY env var)",
)
@click.option(
    "--no-reasoning",
    is_flag=True,
    help="Disable reasoning logs",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def process(
    episode: Optional[Path],
    all: bool,
    model: str,
    api_key: Optional[str],
    no_reasoning: bool,
    verbose: bool,
):
    """Process podcast episodes through the content management pipeline."""

    # Validate inputs
    if not episode and not all:
        console.print("[red]Error: Must specify either --episode or --all[/red]")
        sys.exit(1)

    if episode and all:
        console.print("[red]Error: Cannot use both --episode and --all[/red]")
        sys.exit(1)

    # Get API key
    api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]Error: OpenRouter API key required.[/red]")
        console.print("Set OPENROUTER_API_KEY environment variable or use --api-key flag")
        sys.exit(1)

    # Determine episodes to process
    episodes_to_process = []
    if episode:
        episodes_to_process = [episode]
    else:
        # Process all in sample_inputs/
        sample_dir = Path("sample_inputs")
        if not sample_dir.exists():
            console.print(f"[red]Error: sample_inputs/ directory not found[/red]")
            sys.exit(1)
        episodes_to_process = sorted(sample_dir.glob("*.json"))

    if not episodes_to_process:
        console.print("[red]Error: No episodes found to process[/red]")
        sys.exit(1)

    # Generate timestamped run directory
    run_timestamp, reports_dir, logs_dir = generate_run_directory()

    console.print("\n[bold cyan]Podcast Content Management Agent[/bold cyan]")
    console.print(f"Model: {model}")
    console.print(f"Episodes to process: {len(episodes_to_process)}")
    console.print(f"Run directory: outputs/run_{run_timestamp}/")
    console.print("")

    # Initialize LLM gateway
    try:
        llm = LLMGateway(
            api_key=api_key,
            default_model=model,
        )
    except Exception as e:
        console.print(f"[red]Error initializing LLM gateway: {e}[/red]")
        sys.exit(1)

    # Initialize orchestrator
    orchestrator = PodcastOrchestrator(
        llm_gateway=llm,
        reports_dir=reports_dir,
        logs_dir=logs_dir,
        enable_reasoning_logs=not no_reasoning,
    )

    # Display fact-checking API configuration status
    console.print("[bold]Fact-Checking Configuration:[/bold]")

    fact_check_available = []
    fact_check_unavailable = []

    if os.getenv("PERPLEXITY_API_KEY"):
        fact_check_available.append("Perplexity")
    else:
        fact_check_unavailable.append("Perplexity")

    if os.getenv("TAVILY_API_KEY"):
        fact_check_available.append("Tavily")
    else:
        fact_check_unavailable.append("Tavily")

    if os.getenv("GOOGLE_FACT_CHECK_API_KEY"):
        fact_check_available.append("Google Fact Check")
    else:
        fact_check_unavailable.append("Google Fact Check")

    if os.getenv("SERPAPI_KEY"):
        fact_check_available.append("SerpAPI")
    else:
        fact_check_unavailable.append("SerpAPI")

    if fact_check_available:
        console.print(f"  ✓ APIs available: [green]{', '.join(fact_check_available)}[/green]")
    if fact_check_unavailable:
        console.print(f"  ✗ APIs not configured: [dim]{', '.join(fact_check_unavailable)}[/dim]")
    if not fact_check_available:
        console.print("  [yellow]⚠ No fact-checking APIs configured - claims will not be verified[/yellow]")

    console.print("")

    # Process episodes
    reports = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for ep_path in episodes_to_process:
            task = progress.add_task(f"Processing {ep_path.name}...", total=None)

            try:
                # Process episode
                report = orchestrator.process_episode(ep_path, model=model)

                # Save report
                json_path, md_path = orchestrator.save_report(report)

                reports.append(report)

                progress.update(task, description=f"✓ {ep_path.name}")

                if verbose:
                    console.print(f"\n[green]✓ Processed {ep_path.name}[/green]")
                    console.print(f"  Summary: {report.summary.word_count} words")
                    console.print(f"  Takeaways: {len(report.key_notes.takeaways)}")
                    console.print(f"  Quotes: {len(report.key_notes.quotes)}")
                    console.print(f"  Fact checks: {report.fact_checks.total_claims}")
                    console.print(f"  Processing time: {report.metrics.processing_time_seconds:.2f}s")
                    console.print(f"  Tokens used: {report.metrics.total_tokens_used:,}")
                    console.print("")

            except Exception as e:
                progress.update(task, description=f"✗ {ep_path.name}")
                console.print(f"[red]✗ Error processing {ep_path.name}: {e}[/red]")
                if verbose:
                    import traceback
                    console.print(traceback.format_exc())

    # Create aggregate report if multiple episodes
    if len(reports) > 1:
        console.print("\n[cyan]Creating aggregate report...[/cyan]")

        # Calculate common themes
        all_topics = []
        for report in reports:
            all_topics.extend(report.key_notes.topics)

        # Find most common topics
        from collections import Counter
        topic_counts = Counter(all_topics)
        common_themes = [topic for topic, count in topic_counts.most_common(5)]

        aggregate = AggregateReport(
            episode_reports=reports,
            total_episodes=len(reports),
            total_processing_time=sum(r.metrics.processing_time_seconds for r in reports),
            total_tokens=sum(r.metrics.total_tokens_used for r in reports),
            common_themes=common_themes,
        )

        # Save aggregate report
        agg_json_path = reports_dir / "aggregate_report.json"
        with open(agg_json_path, "w") as f:
            f.write(aggregate.model_dump_json(indent=2))

        agg_md_path = reports_dir / "aggregate_report.md"
        with open(agg_md_path, "w") as f:
            f.write(aggregate.to_markdown())

        console.print(f"[green]✓ Aggregate report saved[/green]")

    # Finalize and save reasoning logs
    orchestrator.finalize()

    # Print summary
    console.print("\n[bold green]✓ Processing complete![/bold green]")
    console.print(f"\nProcessed {len(reports)} episode(s)")
    console.print(f"Total tokens used: {sum(r.metrics.total_tokens_used for r in reports):,}")
    console.print(f"Total time: {sum(r.metrics.processing_time_seconds for r in reports):.2f}s")
    console.print(f"\nOutputs saved to: outputs/run_{run_timestamp}/")


@cli.command()
@click.argument("episode_file", type=click.Path(exists=True, path_type=Path))
def validate(episode_file: Path):
    """Validate an episode transcript file without processing."""
    from ..engines import TranscriptParser

    console.print(f"\n[cyan]Validating {episode_file.name}...[/cyan]\n")

    parser = TranscriptParser()

    try:
        episode = parser.parse_file(episode_file)
        report = parser.get_validation_report(episode)

        console.print("[green]✓ Validation successful![/green]\n")
        console.print(f"Episode ID: {report['episode_id']}")
        console.print(f"Title: {report['title']}")
        console.print(f"Segments: {report['segment_count']}")
        console.print(f"Word count: {report['word_count']:,}")
        console.print(f"Sections: {report['section_count']}")
        console.print(f"Speakers: {report['speaker_count']}")
        console.print(f"Duration: {report['duration_estimate']}")
        console.print(f"\nSections: {', '.join(report['sections'])}")
        console.print(f"Speakers: {', '.join(report['speakers'])}")

    except Exception as e:
        console.print(f"[red]✗ Validation failed: {e}[/red]")
        sys.exit(1)


@cli.command()
def info():
    """Display information about the agent and available models."""
    console.print("\n[bold cyan]Podcast Content Management Agent[/bold cyan]")
    console.print("Version: 1.0.0\n")

    console.print("[bold]Features:[/bold]")
    console.print("  • Automated podcast transcript processing")
    console.print("  • 200-300 word summaries with section awareness")
    console.print("  • Key takeaways and notable quotes extraction")
    console.print("  • Topic tagging for SEO and discovery")
    console.print("  • Fact-checking with knowledge base verification")
    console.print("  • Transparent agent reasoning logs")
    console.print("  • JSON and Markdown output formats\n")

    console.print("[bold]Popular Models (via OpenRouter):[/bold]")
    console.print("  • anthropic/claude-4.5-sonnet (default, recommended)")
    console.print("  • anthropic/claude-3-opus")
    console.print("  • openai/gpt-4o")
    console.print("  • openai/gpt-4-turbo")
    console.print("  • google/gemini-pro-1.5\n")

    console.print("[bold]Environment Variables:[/bold]")
    console.print("  • OPENROUTER_API_KEY (required)\n")


if __name__ == "__main__":
    cli()
