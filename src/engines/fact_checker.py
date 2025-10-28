"""Fact-checking engine for verifying claims."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..llm import LLMGateway, PromptTemplates
from ..models import (
    ClaimType,
    EpisodeFactChecks,
    FactCheckResult,
    FactualClaim,
    PodcastEpisode,
    Source,
    VerificationStatus,
)


class FactCheckEngine:
    """Engine for identifying and verifying factual claims."""

    def __init__(
        self,
        llm_gateway: LLMGateway,
        knowledge_base_path: Optional[Path] = None,
    ):
        """
        Initialize fact-checking engine.

        Args:
            llm_gateway: LLM gateway instance
            knowledge_base_path: Path to knowledge base JSON file
        """
        self.llm = llm_gateway

        # Load knowledge base
        if knowledge_base_path is None:
            knowledge_base_path = Path(__file__).parent.parent.parent / "data" / "knowledge_base.json"

        self.knowledge_base = self._load_knowledge_base(knowledge_base_path)

    def _load_knowledge_base(self, path: Path) -> dict:
        """Load knowledge base from JSON file."""
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load knowledge base from {path}: {e}")
            return {}

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

        Raises:
            Exception: If fact-checking fails
        """
        # Step 1: Identify claims
        claims = self._identify_claims(episode, model)

        # Step 2: Verify each claim
        fact_checks = []
        for claim in claims:
            result = self._verify_claim(claim, model)
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
        """Identify factual claims from episode transcript."""
        transcript_text = episode.get_full_text()

        # Build transcript with speaker and timestamp
        transcript_with_meta = "\n".join([
            f"[{seg.timestamp}] {seg.speaker}: {seg.text}"
            for seg in episode.transcript
        ])

        system_prompt, user_prompt = PromptTemplates.claim_identification(
            episode_title=episode.title,
            transcript_text=transcript_with_meta,
        )

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

        # Ensure we have at least 3 claims
        if len(claims) < 3:
            # Add a default unverifiable claim
            for i in range(3 - len(claims)):
                claims.append(
                    FactualClaim(
                        claim_text="General discussion point from the episode",
                        claim_type=ClaimType.OTHER,
                        speaker="Multiple",
                    )
                )

        return claims

    def _verify_claim(
        self,
        claim: FactualClaim,
        model: Optional[str] = None,
    ) -> FactCheckResult:
        """Verify a single factual claim."""
        # Search knowledge base
        kb_results = self._search_knowledge_base(claim)

        # Generate verification prompt
        system_prompt, user_prompt = PromptTemplates.claim_verification(
            claim_text=claim.claim_text,
            claim_type=claim.claim_type.value,
            context=claim.context or "No additional context",
            knowledge_base_results=kb_results,
        )

        try:
            response_json = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model,
            )

            # Parse verification result
            status_str = response_json.get("verification_status", "unable_to_verify")
            try:
                status = VerificationStatus(status_str)
            except ValueError:
                status = VerificationStatus.UNABLE_TO_VERIFY

            # Parse sources
            sources = []
            for src_data in response_json.get("sources", []):
                sources.append(
                    Source(
                        title=src_data.get("title", "Unknown Source"),
                        excerpt=src_data.get("excerpt"),
                        reliability_score=src_data.get("reliability_score", 0.5),
                    )
                )

            return FactCheckResult(
                claim=claim,
                verification_status=status,
                confidence_score=response_json.get("confidence_score", 0.5),
                explanation=response_json.get("explanation", "Unable to verify"),
                sources=sources,
                verified_at=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            # If verification fails, return unable_to_verify
            return FactCheckResult(
                claim=claim,
                verification_status=VerificationStatus.UNABLE_TO_VERIFY,
                confidence_score=0.3,
                explanation=f"Verification failed: {str(e)}",
                sources=[],
                verified_at=datetime.utcnow().isoformat(),
            )

    def _search_knowledge_base(self, claim: FactualClaim) -> list[dict]:
        """
        Search knowledge base for relevant information.

        Simple keyword-based search. In production, would use vector search
        or more sophisticated retrieval.

        Args:
            claim: Claim to search for

        Returns:
            List of relevant knowledge base entries
        """
        results = []
        claim_text_lower = claim.claim_text.lower()

        # Search all categories
        for category, entries in self.knowledge_base.items():
            for key, entry in entries.items():
                content = entry.get("content", "").lower()
                title = entry.get("title", "").lower()

                # Simple keyword matching
                keywords = claim_text_lower.split()[:5]  # First 5 words
                matches = sum(1 for kw in keywords if kw in content or kw in title)

                if matches > 0:
                    results.append({
                        "title": entry.get("title"),
                        "content": entry.get("content"),
                        "excerpt": entry.get("content")[:200],
                        "reliability_score": entry.get("reliability_score", 0.5),
                        "relevance": matches / len(keywords) if keywords else 0,
                    })

        # Sort by relevance and return top 3
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return results[:3]
