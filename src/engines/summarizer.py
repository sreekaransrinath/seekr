"""Summarization engine for podcast episodes."""
from typing import Optional

from ..llm import LLMGateway, PromptTemplates
from ..models import EpisodeSummary, PodcastEpisode


class SummarizationEngine:
    """Engine for generating episode summaries."""

    def __init__(self, llm_gateway: LLMGateway):
        """
        Initialize summarization engine.

        Args:
            llm_gateway: LLM gateway instance
        """
        self.llm = llm_gateway

    def summarize(
        self,
        episode: PodcastEpisode,
        model: Optional[str] = None,
    ) -> EpisodeSummary:
        """
        Generate summary for an episode.

        Args:
            episode: Episode to summarize
            model: Optional model override

        Returns:
            EpisodeSummary with generated summary

        Raises:
            Exception: If summarization fails
        """
        # Get sections and transcript
        sections = episode.get_sections()
        transcript_text = episode.get_full_text()

        # Generate prompts
        system_prompt, user_prompt = PromptTemplates.summarization(
            episode_title=episode.title,
            host=episode.host,
            guests=episode.guests,
            sections=sections,
            transcript_text=transcript_text,
        )

        # Generate summary
        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
        )

        # Extract themes from summary (simple keyword extraction)
        key_themes = self._extract_themes(response.content, transcript_text)

        return EpisodeSummary(
            episode_id=episode.episode_id,
            summary_text=response.content.strip(),
            sections_covered=sections,
            key_themes=key_themes,
        )

    def _extract_themes(self, summary: str, transcript: str) -> list[str]:
        """
        Extract key themes from summary and transcript.

        Simple keyword-based extraction. In production, would use more
        sophisticated NLP or have LLM explicitly identify themes.

        Args:
            summary: Episode summary
            transcript: Full transcript

        Returns:
            List of key themes
        """
        # Common theme keywords to look for
        theme_keywords = {
            "remote work": ["remote", "distributed", "work from home", "async"],
            "artificial intelligence": ["ai", "machine learning", "artificial intelligence"],
            "healthcare": ["healthcare", "medical", "health", "clinical"],
            "technology": ["technology", "tech", "digital", "software"],
            "business": ["business", "company", "startup", "enterprise"],
            "innovation": ["innovation", "innovative", "future", "cutting-edge"],
            "leadership": ["leadership", "management", "team", "culture"],
            "regulation": ["regulation", "fda", "compliance", "policy"],
            "entrepreneurship": ["entrepreneur", "founder", "bootstrapping", "venture"],
            "investment": ["investment", "funding", "vc", "capital"],
        }

        # Combine summary and transcript for theme detection
        combined_text = (summary + " " + transcript).lower()

        themes = []
        for theme, keywords in theme_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                themes.append(theme)

        # Limit to top themes
        return themes[:5] if themes else ["general discussion"]
