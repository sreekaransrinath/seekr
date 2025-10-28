"""Transcript parser for loading and validating podcast episodes."""
import json
from pathlib import Path
from typing import Union

from pydantic import ValidationError

from ..models import PodcastEpisode, TranscriptSegment


class TranscriptParsingError(Exception):
    """Raised when transcript parsing fails."""

    pass


class TranscriptParser:
    """Parser for podcast transcript JSON files."""

    def __init__(self):
        """Initialize the transcript parser."""
        self.episodes_parsed = 0
        self.errors = []

    def parse_file(self, file_path: Union[str, Path]) -> PodcastEpisode:
        """
        Parse a transcript JSON file into a PodcastEpisode.

        Args:
            file_path: Path to the JSON transcript file

        Returns:
            Parsed and validated PodcastEpisode

        Raises:
            TranscriptParsingError: If parsing or validation fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise TranscriptParsingError(f"File not found: {file_path}")

        if not file_path.suffix == ".json":
            raise TranscriptParsingError(f"File must be JSON format: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise TranscriptParsingError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise TranscriptParsingError(f"Error reading {file_path}: {e}")

        return self._validate_and_parse(raw_data, file_path)

    def _validate_and_parse(self, raw_data: dict, source_file: Path) -> PodcastEpisode:
        """
        Validate raw JSON data and parse into PodcastEpisode.

        Args:
            raw_data: Raw dictionary from JSON
            source_file: Source file path for error messages

        Returns:
            Validated PodcastEpisode

        Raises:
            TranscriptParsingError: If validation fails
        """
        # Check required top-level fields
        required_fields = ["episode_id", "title", "host", "transcript"]
        missing_fields = [field for field in required_fields if field not in raw_data]
        if missing_fields:
            raise TranscriptParsingError(
                f"Missing required fields in {source_file}: {', '.join(missing_fields)}"
            )

        # Validate transcript is a non-empty list
        if not isinstance(raw_data.get("transcript"), list):
            raise TranscriptParsingError(
                f"'transcript' must be a list in {source_file}"
            )

        if len(raw_data["transcript"]) == 0:
            raise TranscriptParsingError(
                f"'transcript' cannot be empty in {source_file}"
            )

        # Check each transcript segment has required fields
        segment_required = ["timestamp", "speaker", "section", "text"]
        for i, segment in enumerate(raw_data["transcript"]):
            missing = [field for field in segment_required if field not in segment]
            if missing:
                raise TranscriptParsingError(
                    f"Segment {i} in {source_file} missing fields: {', '.join(missing)}"
                )

        # Parse with Pydantic validation
        try:
            episode = PodcastEpisode(**raw_data)
            self.episodes_parsed += 1
            return episode
        except ValidationError as e:
            error_msg = f"Validation failed for {source_file}:\n"
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                error_msg += f"  - {loc}: {error['msg']}\n"
            raise TranscriptParsingError(error_msg)

    def parse_multiple(self, file_paths: list[Union[str, Path]]) -> list[PodcastEpisode]:
        """
        Parse multiple transcript files.

        Args:
            file_paths: List of file paths to parse

        Returns:
            List of parsed PodcastEpisodes

        Note:
            Errors are collected in self.errors but don't stop processing
        """
        episodes = []
        self.errors = []

        for file_path in file_paths:
            try:
                episode = self.parse_file(file_path)
                episodes.append(episode)
            except TranscriptParsingError as e:
                self.errors.append({"file": str(file_path), "error": str(e)})

        return episodes

    def get_validation_report(self, episode: PodcastEpisode) -> dict:
        """
        Generate a validation report for an episode.

        Args:
            episode: The parsed episode

        Returns:
            Dictionary with validation statistics
        """
        return {
            "episode_id": episode.episode_id,
            "title": episode.title,
            "segment_count": len(episode.transcript),
            "word_count": episode.word_count,
            "section_count": episode.section_count,
            "speaker_count": episode.speaker_count,
            "sections": episode.get_sections(),
            "speakers": episode.get_speakers(),
            "duration_estimate": episode.duration_estimate,
            "validation_status": "passed",
        }
