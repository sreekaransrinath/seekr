"""Extraction engine for key notes (takeaways, quotes, topics)."""
from typing import Optional

from ..llm import LLMGateway, PromptTemplates
from ..models import KeyNotes, PodcastEpisode, Quote, Takeaway


class ExtractionEngine:
    """Engine for extracting key notes from episodes."""

    def __init__(self, llm_gateway: LLMGateway):
        """
        Initialize extraction engine.

        Args:
            llm_gateway: LLM gateway instance
        """
        self.llm = llm_gateway

    def extract_key_notes(
        self,
        episode: PodcastEpisode,
        summary: str,
        model: Optional[str] = None,
    ) -> KeyNotes:
        """
        Extract key notes (takeaways, quotes, topics) from episode.

        Args:
            episode: Episode to extract from
            summary: Episode summary (used for topics)
            model: Optional model override

        Returns:
            KeyNotes with all extracted information

        Raises:
            Exception: If extraction fails
        """
        # Extract takeaways
        takeaways = self._extract_takeaways(episode, model)

        # Extract quotes
        quotes = self._extract_quotes(episode, model)

        # Extract topic tags
        topics = self._extract_topics(episode, summary, model)

        return KeyNotes(
            episode_id=episode.episode_id,
            takeaways=takeaways,
            quotes=quotes,
            topics=topics,
        )

    def _extract_takeaways(
        self,
        episode: PodcastEpisode,
        model: Optional[str] = None,
    ) -> list[Takeaway]:
        """Extract top 5 takeaways from episode."""
        transcript_text = episode.get_full_text()

        system_prompt, user_prompt = PromptTemplates.takeaway_extraction(
            episode_title=episode.title,
            transcript_text=transcript_text,
        )

        response_json = self.llm.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
        )

        # Parse takeaways
        takeaways_data = response_json.get("takeaways", [])
        takeaways = []

        for item in takeaways_data[:5]:  # Ensure max 5
            takeaways.append(
                Takeaway(
                    text=item.get("text", ""),
                    relevance_score=item.get("relevance_score", 1.0),
                )
            )

        # Ensure we have exactly 5
        while len(takeaways) < 5:
            takeaways.append(
                Takeaway(
                    text="Additional insights discussed in the episode",
                    relevance_score=0.5,
                )
            )

        return takeaways[:5]

    def _extract_quotes(
        self,
        episode: PodcastEpisode,
        model: Optional[str] = None,
    ) -> list[Quote]:
        """Extract 3-10 notable quotes from episode."""
        # Build transcript with timestamps
        transcript_with_ts = "\n".join([
            f"[{seg.timestamp}] {seg.speaker}: {seg.text}"
            for seg in episode.transcript
        ])

        system_prompt, user_prompt = PromptTemplates.quote_extraction(
            episode_title=episode.title,
            transcript_with_timestamps=transcript_with_ts,
        )

        response_json = self.llm.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
        )

        # Parse quotes
        quotes_data = response_json.get("quotes", [])
        quotes = []

        for item in quotes_data:
            quotes.append(
                Quote(
                    timestamp=item.get("timestamp", "00:00"),
                    speaker=item.get("speaker", "Unknown"),
                    text=item.get("text", ""),
                    context=item.get("context"),
                    engagement_score=item.get("engagement_score", 1.0),
                )
            )

        # Ensure we have at least 3
        if len(quotes) < 3:
            # Fall back to extracting from transcript segments
            for seg in episode.transcript[:3]:
                if len(quotes) >= 3:
                    break
                quotes.append(
                    Quote(
                        timestamp=seg.timestamp,
                        speaker=seg.speaker,
                        text=seg.text,
                        engagement_score=0.5,
                    )
                )

        return quotes[:10]  # Max 10

    def _extract_topics(
        self,
        episode: PodcastEpisode,
        summary: str,
        model: Optional[str] = None,
    ) -> list[str]:
        """Extract 5-10 topic tags from episode."""
        transcript_text = episode.get_full_text()

        system_prompt, user_prompt = PromptTemplates.topic_tagging(
            episode_title=episode.title,
            summary=summary,
            transcript_text=transcript_text,
        )

        response_json = self.llm.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
        )

        # Parse topics
        topics = response_json.get("topics", [])

        # Normalize topics
        topics = [
            topic.lower().strip().replace(" ", "-")
            for topic in topics
        ]

        # Ensure we have 5-10 topics
        if len(topics) < 5:
            # Add default topics based on episode
            default_topics = ["podcast", "conversation", "insights", "discussion", "interview"]
            topics.extend(default_topics[:5 - len(topics)])

        return topics[:10]  # Max 10
