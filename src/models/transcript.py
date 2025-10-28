"""Data models for podcast transcripts."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TranscriptSegment(BaseModel):
    """A single segment of podcast transcript."""

    timestamp: str = Field(..., description="Timestamp in format HH:MM:SS or MM:SS")
    speaker: str = Field(..., description="Name of the speaker")
    section: str = Field(..., description="Section of the episode")
    text: str = Field(..., description="Spoken text content")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp format."""
        parts = v.split(':')
        if len(parts) not in [2, 3]:
            raise ValueError(f"Invalid timestamp format: {v}. Expected MM:SS or HH:MM:SS")
        return v

    @field_validator('text')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not empty."""
        if not v.strip():
            raise ValueError("Transcript text cannot be empty")
        return v.strip()


class PodcastEpisode(BaseModel):
    """Complete podcast episode with metadata and transcript."""

    episode_id: str = Field(..., description="Unique episode identifier")
    title: str = Field(..., description="Episode title")
    host: str = Field(..., description="Host name")
    guests: List[str] = Field(default_factory=list, description="List of guest names")
    transcript: List[TranscriptSegment] = Field(..., description="Full transcript segments")

    # Derived fields
    duration_estimate: Optional[str] = Field(None, description="Estimated duration from last timestamp")
    section_count: int = Field(0, description="Number of unique sections")
    speaker_count: int = Field(0, description="Number of unique speakers")
    word_count: int = Field(0, description="Total word count")

    def model_post_init(self, __context) -> None:
        """Calculate derived fields after initialization."""
        if self.transcript:
            # Calculate unique sections and speakers
            self.section_count = len(set(seg.section for seg in self.transcript))
            self.speaker_count = len(set(seg.speaker for seg in self.transcript))

            # Calculate total word count
            self.word_count = sum(len(seg.text.split()) for seg in self.transcript)

            # Estimate duration from last timestamp
            if self.transcript:
                self.duration_estimate = self.transcript[-1].timestamp

    @field_validator('episode_id')
    @classmethod
    def validate_episode_id(cls, v: str) -> str:
        """Validate episode ID format."""
        if not v.strip():
            raise ValueError("Episode ID cannot be empty")
        return v.strip()

    def get_sections(self) -> List[str]:
        """Get list of unique section names in order of appearance."""
        seen = set()
        sections = []
        for seg in self.transcript:
            if seg.section not in seen:
                seen.add(seg.section)
                sections.append(seg.section)
        return sections

    def get_speakers(self) -> List[str]:
        """Get list of unique speaker names."""
        return list(set(seg.speaker for seg in self.transcript))

    def get_text_by_section(self, section: str) -> str:
        """Get all transcript text for a specific section."""
        segments = [seg.text for seg in self.transcript if seg.section == section]
        return " ".join(segments)

    def get_full_text(self) -> str:
        """Get complete transcript as single text."""
        return " ".join(seg.text for seg in self.transcript)
