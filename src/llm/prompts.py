"""Prompt templates for different LLM tasks."""
from typing import List


class PromptTemplates:
    """Collection of prompt templates for podcast processing tasks."""

    @staticmethod
    def summarization(
        episode_title: str,
        host: str,
        guests: List[str],
        sections: List[str],
        transcript_text: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for episode summarization.

        Args:
            episode_title: Episode title
            host: Host name
            guests: List of guest names
            sections: List of section names
            transcript_text: Full transcript text

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert podcast content analyst specializing in creating concise, engaging summaries for marketing and content distribution.

Your task is to create a 200-300 word summary that:
1. Captures the main themes and key insights
2. Covers all major sections of the episode
3. Highlights unique perspectives from guests
4. Is engaging and compelling for potential listeners
5. Uses clear, professional language"""

        guests_str = ", ".join(guests) if guests else "No guests"
        sections_str = ", ".join(sections)

        user_prompt = f"""Please create a summary for this podcast episode.

**Episode Title**: {episode_title}
**Host**: {host}
**Guests**: {guests_str}
**Sections**: {sections_str}

**Full Transcript**:
{transcript_text}

Create a 200-300 word summary that covers all sections and captures the key insights and themes. The summary should be engaging and informative."""

        return system_prompt, user_prompt

    @staticmethod
    def takeaway_extraction(
        episode_title: str,
        transcript_text: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for extracting key takeaways.

        Args:
            episode_title: Episode title
            transcript_text: Full transcript text

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert at distilling actionable insights from podcast conversations.

Your task is to extract exactly 5 key takeaways that:
1. Are actionable or thought-provoking
2. Represent the most valuable insights
3. Are concise (1-2 sentences each, max 200 characters)
4. Don't overlap or repeat
5. Are ordered by importance/impact

Respond with valid JSON in this format:
{
  "takeaways": [
    {"text": "Takeaway 1 here", "relevance_score": 1.0},
    {"text": "Takeaway 2 here", "relevance_score": 0.9},
    ...
  ]
}"""

        user_prompt = f"""Extract exactly 5 key takeaways from this episode: "{episode_title}"

**Transcript**:
{transcript_text}

Return JSON with 5 takeaways, ordered by importance."""

        return system_prompt, user_prompt

    @staticmethod
    def quote_extraction(
        episode_title: str,
        transcript_with_timestamps: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for extracting notable quotes.

        Args:
            episode_title: Episode title
            transcript_with_timestamps: Transcript with timestamps and speakers

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert at identifying compelling, shareable quotes from podcast conversations.

Select 3-10 notable quotes that:
1. Are insightful, memorable, or thought-provoking
2. Stand alone without much context
3. Are likely to generate engagement on social media
4. Come from different parts of the episode
5. Include the exact timestamp and speaker

Respond with valid JSON in this format:
{
  "quotes": [
    {
      "timestamp": "HH:MM:SS",
      "speaker": "Speaker Name",
      "text": "The exact quote",
      "context": "Brief context if needed",
      "engagement_score": 0.95
    },
    ...
  ]
}"""

        user_prompt = f"""Extract 3-10 notable quotes from this episode: "{episode_title}"

**Transcript with Timestamps**:
{transcript_with_timestamps}

Return JSON with quotes that are memorable and shareable."""

        return system_prompt, user_prompt

    @staticmethod
    def topic_tagging(
        episode_title: str,
        summary: str,
        transcript_text: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for topic tag extraction.

        Args:
            episode_title: Episode title
            summary: Episode summary
            transcript_text: Full transcript text

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert content categorizer and SEO specialist.

Your task is to generate 5-10 topic tags that:
1. Accurately represent the main topics discussed
2. Use standard, searchable terminology
3. Are formatted as lowercase, hyphenated (e.g., "remote-work", "ai-ethics")
4. Include a mix of broad and specific topics
5. Are useful for content discovery and SEO

Respond with valid JSON in this format:
{
  "topics": ["topic-1", "topic-2", "topic-3", ...]
}"""

        user_prompt = f"""Generate 5-10 topic tags for this episode.

**Title**: {episode_title}

**Summary**: {summary}

**Transcript** (first 1000 chars):
{transcript_text[:1000]}...

Return JSON with 5-10 topic tags, lowercase and hyphenated."""

        return system_prompt, user_prompt

    @staticmethod
    def claim_identification(
        episode_title: str,
        transcript_text: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for identifying factual claims.

        Args:
            episode_title: Episode title
            transcript_text: Full transcript text

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert fact-checker specializing in identifying verifiable claims in podcast content.

Your task is to identify factual claims that:
1. Are specific and verifiable (not opinions)
2. Include statistics, dates, company names, regulations, or predictions
3. Were stated as facts by the speakers
4. Could be fact-checked against external sources

Categorize each claim by type: statistic, date, company, technology, prediction, regulation, or other.

Respond with valid JSON in this format:
{
  "claims": [
    {
      "claim_text": "The specific claim",
      "claim_type": "statistic",
      "speaker": "Speaker Name",
      "timestamp": "HH:MM:SS",
      "context": "Brief surrounding context"
    },
    ...
  ]
}"""

        user_prompt = f"""Identify 5-10 factual claims from this episode that can be fact-checked: "{episode_title}"

**Transcript**:
{transcript_text}

Return JSON with verifiable factual claims."""

        return system_prompt, user_prompt

    @staticmethod
    def claim_verification(
        claim_text: str,
        claim_type: str,
        context: str,
        knowledge_base_results: List[dict],
    ) -> tuple[str, str]:
        """
        Generate prompts for verifying a factual claim.

        Args:
            claim_text: The claim to verify
            claim_type: Type of claim
            context: Context around the claim
            knowledge_base_results: Results from knowledge base search

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert fact-checker with access to a knowledge base.

Your task is to verify a factual claim by:
1. Analyzing the claim carefully
2. Comparing it against provided knowledge base information
3. Determining verification status: verified, partially_verified, unverified, incorrect, or unable_to_verify
4. Assigning a confidence score (0.0-1.0)
5. Explaining your reasoning

Respond with valid JSON in this format:
{
  "verification_status": "verified",
  "confidence_score": 0.95,
  "explanation": "Detailed explanation of verification",
  "sources": [
    {
      "title": "Source title",
      "excerpt": "Relevant excerpt",
      "reliability_score": 0.9
    }
  ]
}"""

        kb_str = "\n".join([
            f"- {item.get('title', 'Unknown')}: {item.get('excerpt', item.get('content', ''))}"
            for item in knowledge_base_results
        ]) if knowledge_base_results else "No knowledge base results found"

        user_prompt = f"""Verify this factual claim:

**Claim**: {claim_text}
**Type**: {claim_type}
**Context**: {context}

**Knowledge Base Results**:
{kb_str}

Analyze the claim against the knowledge base and return JSON with verification status, confidence, explanation, and sources."""

        return system_prompt, user_prompt

    @staticmethod
    def reasoning_decision(
        task_description: str,
        context: dict,
    ) -> tuple[str, str]:
        """
        Generate prompts for agent reasoning about task execution.

        Args:
            task_description: Description of the task
            context: Context information

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are a planning and reasoning agent that makes decisions about how to process podcast content.

Your task is to analyze the given context and decide:
1. What processing strategy to use
2. Which tasks can run in parallel
3. What order tasks should execute
4. Any special considerations

Respond with valid JSON explaining your reasoning and decisions."""

        context_str = "\n".join([f"- {k}: {v}" for k, v in context.items()])

        user_prompt = f"""Make processing decisions for this task:

**Task**: {task_description}

**Context**:
{context_str}

Explain your reasoning and decisions in JSON format."""

        return system_prompt, user_prompt
