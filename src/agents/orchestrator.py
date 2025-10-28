"""Orchestrator for coordinating all processing agents and engines."""
import os
import time
from pathlib import Path
from typing import Optional

from ..engines import (
    ExtractionEngine,
    FactCheckEngine,
    SummarizationEngine,
    TranscriptParser,
)
from ..llm import LLMGateway
from ..models import EpisodeReport, PodcastEpisode, ProcessingMetrics
from .reasoning import ReasoningLogger


class PodcastOrchestrator:
    """Main orchestrator coordinating all agents and engines."""

    def __init__(
        self,
        llm_gateway: LLMGateway,
        reports_dir: Optional[Path] = None,
        logs_dir: Optional[Path] = None,
        enable_reasoning_logs: bool = True,
        perplexity_key: Optional[str] = None,
        tavily_key: Optional[str] = None,
        google_key: Optional[str] = None,
        serpapi_key: Optional[str] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            llm_gateway: LLM gateway instance
            reports_dir: Directory for report outputs
            logs_dir: Directory for log outputs
            enable_reasoning_logs: Whether to enable reasoning logs
            perplexity_key: Perplexity API key for fact-checking
            tavily_key: Tavily API key for fact-checking
            google_key: Google Fact Check API key
            serpapi_key: SerpAPI key (optional)
        """
        self.llm = llm_gateway
        self.reports_dir = reports_dir or Path("outputs")
        self.logs_dir = logs_dir or Path("outputs")

        # Initialize engines
        self.parser = TranscriptParser()
        self.summarizer = SummarizationEngine(llm_gateway)
        self.extractor = ExtractionEngine(llm_gateway)
        self.fact_checker = FactCheckEngine(
            llm_gateway,
            perplexity_key=perplexity_key or os.getenv("PERPLEXITY_API_KEY"),
            tavily_key=tavily_key or os.getenv("TAVILY_API_KEY"),
            google_key=google_key or os.getenv("GOOGLE_FACT_CHECK_API_KEY"),
            serpapi_key=serpapi_key or os.getenv("SERPAPI_KEY"),
        )

        # Initialize reasoning logger
        self.reasoning = ReasoningLogger(logs_dir) if enable_reasoning_logs else None

    def process_episode(
        self,
        episode_path: Path,
        model: Optional[str] = None,
    ) -> EpisodeReport:
        """
        Process a single podcast episode through the full pipeline.

        Args:
            episode_path: Path to episode JSON file
            model: Optional model override

        Returns:
            Complete EpisodeReport

        Raises:
            Exception: If processing fails
        """
        start_time = time.time()

        # Log planning
        if self.reasoning:
            self.reasoning.log_planning(
                task="Episode Processing Pipeline",
                reasoning=(
                    f"Processing episode from {episode_path.name}. "
                    "Will execute: Parse → Summarize → Extract → Fact-check → Format. "
                    "Summarization and extraction can theoretically run in parallel after parsing, "
                    "but for simplicity and token management, running sequentially."
                ),
                context={"episode_file": str(episode_path), "model": model or self.llm.default_model},
            )

        # Step 1: Parse transcript
        if self.reasoning:
            self.reasoning.log_execution(
                task="Parse Transcript",
                reasoning="Loading and validating episode transcript JSON file",
            )

        episode = self.parser.parse_file(episode_path)

        if self.reasoning:
            validation_report = self.parser.get_validation_report(episode)
            self.reasoning.log_validation(
                task="Parse Transcript",
                reasoning="Transcript successfully parsed and validated",
                outcome=f"Loaded {len(episode.transcript)} segments, {episode.word_count} words",
                context=validation_report,
            )

        # Step 2: Generate summary
        if self.reasoning:
            self.reasoning.log_execution(
                task="Generate Summary",
                reasoning=(
                    f"Generating 200-300 word summary covering all {episode.section_count} sections. "
                    "Using LLM to create engaging, informative summary."
                ),
            )

        summary = self.summarizer.summarize(episode, model=model)

        if self.reasoning:
            self.reasoning.log_validation(
                task="Generate Summary",
                reasoning="Summary generated and validated against word count requirements",
                outcome=f"Generated {summary.word_count} word summary",
                context={"themes": summary.key_themes, "sections": summary.sections_covered},
            )

        # Step 3: Extract key notes
        if self.reasoning:
            self.reasoning.log_execution(
                task="Extract Key Notes",
                reasoning=(
                    "Extractingtakeaways, quotes, and topic tags. "
                    "Using LLM to identify most valuable and engaging content."
                ),
            )

        key_notes = self.extractor.extract_key_notes(episode, summary.summary_text, model=model)

        if self.reasoning:
            self.reasoning.log_validation(
                task="Extract Key Notes",
                reasoning="Key notes extracted and validated",
                outcome=(
                    f"Extracted {len(key_notes.takeaways)} takeaways, "
                    f"{len(key_notes.quotes)} quotes, {len(key_notes.topics)} topics"
                ),
                context={"topics": key_notes.topics},
            )

        # Step 4: Fact-check claims
        if self.reasoning:
            self.reasoning.log_execution(
                task="Fact-Check Claims",
                reasoning=(
                    "Identifying factual claims and verifying using multiple search APIs. "
                    "Will extract verifiable claims, query Perplexity/Tavily/Google Fact Check, "
                    "and reconcile results across sources to determine consensus verification status."
                ),
            )

        fact_checks = self.fact_checker.fact_check_episode(episode, model=model)

        if self.reasoning:
            if fact_checks.total_claims > 0:
                verification_rate = f"{fact_checks.verified_count / fact_checks.total_claims * 100:.1f}%"
                self.reasoning.log_validation(
                    task="Fact-Check Claims",
                    reasoning="Claims identified and verified using multi-source reconciliation",
                    outcome=(
                        f"Fact-checked {fact_checks.total_claims} claims: "
                        f"{fact_checks.verified_count} verified, {fact_checks.unverified_count} unverified/uncertain"
                    ),
                    context={"verification_rate": verification_rate},
                )
            else:
                self.reasoning.log_validation(
                    task="Fact-Check Claims",
                    reasoning="No factual claims identified in this episode",
                    outcome="0 claims found - episode may focus on opinions/discussion rather than facts",
                )

        # Calculate metrics
        processing_time = time.time() - start_time
        stats = self.llm.get_stats()

        metrics = ProcessingMetrics(
            total_tokens_used=stats["total_tokens_used"],
            api_calls_made=stats["total_api_calls"],
            processing_time_seconds=processing_time,
            model_used=model or self.llm.default_model,
        )

        # Create report
        report = EpisodeReport(
            episode=episode,
            summary=summary,
            key_notes=key_notes,
            fact_checks=fact_checks,
            metrics=metrics,
        )

        if self.reasoning:
            self.reasoning.log_decision(
                task="Episode Processing Complete",
                reasoning="All processing stages completed successfully",
                outcome=f"Processed episode in {processing_time:.2f}s using {metrics.total_tokens_used} tokens",
                context={
                    "episode_id": episode.episode_id,
                    "summary_words": summary.word_count,
                    "fact_checks": fact_checks.total_claims,
                },
            )

        return report

    def save_report(
        self,
        report: EpisodeReport,
        output_prefix: Optional[str] = None,
    ) -> tuple[Path, Path]:
        """
        Save episode report to JSON and Markdown files.

        Args:
            report: Episode report to save
            output_prefix: Optional prefix for output files

        Returns:
            Tuple of (json_path, markdown_path)
        """
        if output_prefix is None:
            output_prefix = report.episode.episode_id

        # Save JSON
        json_path = self.reports_dir / f"{output_prefix}_report.json"
        with open(json_path, "w") as f:
            f.write(report.model_dump_json(indent=2))

        # Save Markdown
        md_path = self.reports_dir / f"{output_prefix}_report.md"
        with open(md_path, "w") as f:
            f.write(report.to_markdown())

        if self.reasoning:
            self.reasoning.log_execution(
                task="Save Report",
                reasoning="Saving episode report in JSON and Markdown formats",
                outcome=f"Saved to {json_path.name} and {md_path.name}",
            )

        return json_path, md_path

    def finalize(self):
        """Finalize processing and save reasoning logs."""
        if self.reasoning:
            self.reasoning.save_to_file()
            self.reasoning.save_to_json()

            # Print summary
            summary = self.reasoning.get_summary()
            print("\n" + "=" * 80)
            print("REASONING LOG SUMMARY")
            print("=" * 80)
            print(f"Total entries: {summary['total_entries']}")
            print("\nBy level:")
            for level, count in summary['by_level'].items():
                print(f"  - {level}: {count}")
            print("\nTasks performed:")
            for task in summary['tasks']:
                print(f"  - {task}")
            print("=" * 80)
