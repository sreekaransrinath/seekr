"""Data models for final output reports."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .fact_check import EpisodeFactChecks
from .summary import EpisodeSummary, KeyNotes
from .transcript import PodcastEpisode


class ProcessingMetrics(BaseModel):
    """Metrics about the processing run."""

    total_tokens_used: int = Field(default=0, description="Total LLM tokens consumed")
    api_calls_made: int = Field(default=0, description="Total API calls")
    processing_time_seconds: float = Field(default=0.0, description="Total processing time")
    model_used: str = Field(..., description="LLM model identifier")


class EpisodeReport(BaseModel):
    """Complete report for a single episode."""

    episode: PodcastEpisode = Field(..., description="Original episode data")
    summary: EpisodeSummary = Field(..., description="Episode summary")
    key_notes: KeyNotes = Field(..., description="Extracted key notes")
    fact_checks: EpisodeFactChecks = Field(..., description="Fact-check results")
    metrics: ProcessingMetrics = Field(..., description="Processing metrics")
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp of report generation"
    )

    def to_markdown(self) -> str:
        """Convert report to Markdown format."""
        md = f"# Episode Report: {self.episode.title}\n\n"

        # Metadata
        md += "## Metadata\n"
        md += f"- **Episode ID**: {self.episode.episode_id}\n"
        md += f"- **Host**: {self.episode.host}\n"
        if self.episode.guests:
            md += f"- **Guests**: {', '.join(self.episode.guests)}\n"
        md += f"- **Duration**: {self.episode.duration_estimate}\n"
        md += f"- **Word Count**: {self.episode.word_count:,}\n"
        md += f"- **Sections**: {self.episode.section_count}\n\n"

        # Summary
        md += "## Summary\n"
        md += f"{self.summary.summary_text}\n\n"
        if self.summary.key_themes:
            md += f"**Key Themes**: {', '.join(self.summary.key_themes)}\n\n"

        # Key Takeaways
        md += "## 🔹 Key Takeaways\n"
        for i, takeaway in enumerate(self.key_notes.takeaways, 1):
            md += f"{i}. {takeaway.text}\n"
        md += "\n"

        # Notable Quotes
        md += "## 💬 Notable Quotes\n"
        for quote in self.key_notes.quotes:
            md += f"- **[{quote.timestamp}] {quote.speaker}**: \"{quote.text}\"\n"
            if quote.context:
                md += f"  _{quote.context}_\n"
        md += "\n"

        # Topic Tags
        md += "## 🧭 Topics\n"
        md += ", ".join(f"`{tag}`" for tag in self.key_notes.topics)
        md += "\n\n"

        # Fact Checks
        md += "## ✓ Fact Checks\n"
        md += f"**Summary**: {self.fact_checks.verified_count}/{self.fact_checks.total_claims} claims verified\n\n"
        md += "| Claim | Status | Confidence | Explanation |\n"
        md += "|-------|--------|------------|-------------|\n"
        for fc in self.fact_checks.fact_checks:
            status_emoji = {
                "verified": "✅",
                "partially_verified": "⚠️",
                "incorrect": "❌",
                "unverified": "❓",
                "unable_to_verify": "❓"
            }.get(fc.verification_status.value, "❓")
            claim_short = fc.claim.claim_text[:50] + "..." if len(fc.claim.claim_text) > 50 else fc.claim.claim_text
            md += f"| {claim_short} | {status_emoji} {fc.verification_status.value} | {fc.confidence_score:.2f} | {fc.explanation[:80]}... |\n"
        md += "\n"

        # Processing Metrics
        md += "## 📊 Processing Metrics\n"
        md += f"- **Model**: {self.metrics.model_used}\n"
        md += f"- **Processing Time**: {self.metrics.processing_time_seconds:.2f}s\n"
        md += f"- **API Calls**: {self.metrics.api_calls_made}\n"
        md += f"- **Tokens Used**: {self.metrics.total_tokens_used:,}\n"
        md += f"- **Generated**: {self.generated_at}\n\n"

        return md


class AggregateReport(BaseModel):
    """Aggregate report across all episodes."""

    episode_reports: list[EpisodeReport] = Field(..., description="All episode reports")
    total_episodes: int = Field(..., description="Total number of episodes processed")
    total_processing_time: float = Field(..., description="Total processing time")
    total_tokens: int = Field(..., description="Total tokens used")
    common_themes: list[str] = Field(default_factory=list, description="Common themes across episodes")
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp"
    )

    def to_markdown(self) -> str:
        """Convert aggregate report to Markdown."""
        md = "# Aggregate Podcast Processing Report\n\n"

        # Executive Summary
        md += "## Executive Summary\n"
        md += f"Processed **{self.total_episodes}** podcast episodes in **{self.total_processing_time:.2f}** seconds.\n\n"

        # Episode List
        md += "## Episodes Processed\n"
        for i, report in enumerate(self.episode_reports, 1):
            md += f"{i}. **{report.episode.title}** ({report.episode.episode_id})\n"
            md += f"   - Host: {report.episode.host}\n"
            md += f"   - Duration: {report.episode.duration_estimate}\n"
            md += f"   - Fact Checks: {report.fact_checks.verified_count}/{report.fact_checks.total_claims} verified\n"
        md += "\n"

        # Common Themes
        if self.common_themes:
            md += "## Common Themes\n"
            for theme in self.common_themes:
                md += f"- {theme}\n"
            md += "\n"

        # Aggregate Statistics
        md += "## Aggregate Statistics\n"
        md += f"- **Total Tokens Used**: {self.total_tokens:,}\n"
        md += f"- **Total API Calls**: {sum(r.metrics.api_calls_made for r in self.episode_reports)}\n"
        md += f"- **Average Processing Time**: {self.total_processing_time / self.total_episodes:.2f}s per episode\n"
        md += f"- **Total Fact Checks**: {sum(r.fact_checks.total_claims for r in self.episode_reports)}\n"
        md += f"- **Verified Claims**: {sum(r.fact_checks.verified_count for r in self.episode_reports)}\n\n"

        md += f"_Generated at {self.generated_at}_\n"

        return md
