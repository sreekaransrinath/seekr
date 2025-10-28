"""Data models for episode summaries."""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class EpisodeSummary(BaseModel):
    """Summary of a podcast episode."""

    episode_id: str = Field(..., description="Episode identifier")
    summary_text: str = Field(..., description="200-300 word summary")
    word_count: int = Field(0, description="Actual word count of summary")
    sections_covered: List[str] = Field(default_factory=list, description="Sections included in summary")
    key_themes: List[str] = Field(default_factory=list, description="Main themes identified")

    def model_post_init(self, __context) -> None:
        """Calculate word count after initialization."""
        self.word_count = len(self.summary_text.split())

    @field_validator('summary_text')
    @classmethod
    def validate_summary_length(cls, v: str) -> str:
        """Validate summary is within word count range."""
        word_count = len(v.split())
        if word_count < 150:
            raise ValueError(f"Summary too short: {word_count} words (minimum 150)")
        if word_count > 350:
            raise ValueError(f"Summary too long: {word_count} words (maximum 350)")
        return v.strip()


class Takeaway(BaseModel):
    """A key takeaway from the episode."""

    text: str = Field(..., description="Takeaway text (1-2 sentences)")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance score")

    @field_validator('text')
    @classmethod
    def validate_takeaway_length(cls, v: str) -> str:
        """Ensure takeaway is concise."""
        if len(v) > 200:
            raise ValueError(f"Takeaway too long: {len(v)} chars (max 200)")
        return v.strip()


class Quote(BaseModel):
    """A notable quote from the episode."""

    timestamp: str = Field(..., description="When quote was said")
    speaker: str = Field(..., description="Who said it")
    text: str = Field(..., description="The quote text")
    context: Optional[str] = Field(None, description="Brief context")
    engagement_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Predicted engagement")


class KeyNotes(BaseModel):
    """Key notes extracted from an episode."""

    episode_id: str = Field(..., description="Episode identifier")
    takeaways: List[Takeaway] = Field(..., description="Top 5 takeaways")
    quotes: List[Quote] = Field(..., description="3-10 notable quotes")
    topics: List[str] = Field(..., description="5-10 topic tags")

    @field_validator('takeaways')
    @classmethod
    def validate_takeaway_count(cls, v: List[Takeaway]) -> List[Takeaway]:
        """Ensure exactly 5 takeaways."""
        if len(v) != 5:
            raise ValueError(f"Must have exactly 5 takeaways, got {len(v)}")
        return v

    @field_validator('quotes')
    @classmethod
    def validate_quote_count(cls, v: List[Quote]) -> List[Quote]:
        """Ensure at least 3 quotes."""
        if len(v) < 3:
            raise ValueError(f"Must have at least 3 quotes, got {len(v)}")
        if len(v) > 10:
            raise ValueError(f"Too many quotes: {len(v)} (max 10)")
        return v

    @field_validator('topics')
    @classmethod
    def validate_topic_count(cls, v: List[str]) -> List[str]:
        """Ensure 5-10 topics."""
        if len(v) < 5:
            raise ValueError(f"Must have at least 5 topics, got {len(v)}")
        if len(v) > 10:
            raise ValueError(f"Too many topics: {len(v)} (max 10)")
        # Normalize to lowercase, hyphenated
        return [topic.lower().strip().replace(' ', '-') for topic in v]
