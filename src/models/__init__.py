"""Data models for podcast content management."""
from .fact_check import (
    ClaimType,
    EpisodeFactChecks,
    FactCheckResult,
    FactualClaim,
    Source,
    VerificationStatus,
)
from .output import AggregateReport, EpisodeReport, ProcessingMetrics
from .summary import EpisodeSummary, KeyNotes, Quote, Takeaway
from .transcript import PodcastEpisode, TranscriptSegment

__all__ = [
    # Transcript models
    "PodcastEpisode",
    "TranscriptSegment",
    # Summary models
    "EpisodeSummary",
    "KeyNotes",
    "Quote",
    "Takeaway",
    # Fact-check models
    "ClaimType",
    "EpisodeFactChecks",
    "FactCheckResult",
    "FactualClaim",
    "Source",
    "VerificationStatus",
    # Output models
    "AggregateReport",
    "EpisodeReport",
    "ProcessingMetrics",
]