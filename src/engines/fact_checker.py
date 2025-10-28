"""Fact-checking engine using multiple search APIs."""
from typing import Optional

from ..llm import LLMGateway, PromptTemplates
from ..models import ClaimType, EpisodeFactChecks, FactualClaim, PodcastEpisode
from .multi_source_verifier import MultiSourceVerifier


class FactCheckEngine:
    """Engine for identifying and verifying factual claims using multiple APIs."""

    def __init__(
        self,
        llm_gateway: LLMGateway,
        perplexity_key: Optional[str] = None,
        tavily_key: Optional[str] = None,
        google_key: Optional[str] = None,
        serpapi_key: Optional[str] = None,
    ):
        """
        Initialize fact-checking engine.

        Args:
            llm_gateway: LLM gateway instance
            perplexity_key: Perplexity API key
            tavily_key: Tavily API key
            google_key: Google Fact Check API key
            serpapi_key: SerpAPI key (optional)
        """
        self.llm = llm_gateway

        # Initialize multi-source verifier
        self.verifier = MultiSourceVerifier(
            llm_gateway=llm_gateway,
            perplexity_key=perplexity_key,
            tavily_key=tavily_key,
            google_key=google_key,
            serpapi_key=serpapi_key,
        )

    def fact_check_episode(
        self,
        episode: PodcastEpisode,
        model: Optional[str] = None,
    ) -> EpisodeFactChecks:
        """
        Identify and fact-check claims in an episode.

        Args:
            episode: Episode to fact-check
            model: Optional model override

        Returns:
            EpisodeFactChecks with all verification results
        """
        # Step 1: Identify claims (no minimum threshold)
        claims = self._identify_claims(episode, model)

        # Step 2: Verify each claim using multiple sources
        fact_checks = []
        for claim in claims:
            result = self.verifier.verify_claim(claim)
            fact_checks.append(result)

        return EpisodeFactChecks(
            episode_id=episode.episode_id,
            fact_checks=fact_checks,
        )

    def _identify_claims(
        self,
        episode: PodcastEpisode,
        model: Optional[str] = None,
    ) -> list[FactualClaim]:
        """
        Identify factual claims from episode transcript.

        NO MINIMUM THRESHOLD - Returns whatever claims are found.

        Args:
            episode: Episode to analyze
            model: Optional model override

        Returns:
            List of factual claims (can be empty)
        """
        # Build transcript with speaker and timestamp
        transcript_with_meta = "\n".join([
            f"[{seg.timestamp}] {seg.speaker}: {seg.text}"
            for seg in episode.transcript
        ])

        system_prompt, user_prompt = PromptTemplates.claim_identification(
            episode_title=episode.title,
            transcript_text=transcript_with_meta,
        )

        try:
            response_json = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model,
            )

            # Parse claims
            claims_data = response_json.get("claims", [])
            claims = []

            for item in claims_data:
                claim_type_str = item.get("claim_type", "other")
                # Map string to enum
                try:
                    claim_type = ClaimType(claim_type_str.lower())
                except ValueError:
                    claim_type = ClaimType.OTHER

                claims.append(
                    FactualClaim(
                        claim_text=item.get("claim_text", ""),
                        claim_type=claim_type,
                        speaker=item.get("speaker", "Unknown"),
                        timestamp=item.get("timestamp"),
                        context=item.get("context"),
                    )
                )

            # Return whatever was found - NO minimum threshold
            return claims

        except Exception as e:
            print("Claim identification error:", str(e))
            # Return empty list on error - no placeholders
            return []

    def close(self):
        """Close all API clients."""
        self.verifier.close()
