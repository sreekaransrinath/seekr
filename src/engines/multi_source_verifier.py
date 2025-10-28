"""Multi-source verification engine with reconciliation logic."""
import asyncio
from datetime import datetime
from typing import List, Optional, Tuple

from ..llm import LLMGateway
from ..llm.search_apis import (
    GoogleFactCheckClient,
    PerplexityClient,
    SearchResult,
    SerpAPIClient,
    TavilyClient,
)
from ..models import FactCheckResult, FactualClaim, Source, VerificationStatus


class MultiSourceVerifier:
    """Verifies claims using multiple search APIs and reconciles results."""

    def __init__(
        self,
        llm_gateway: LLMGateway,
        perplexity_key: Optional[str] = None,
        tavily_key: Optional[str] = None,
        google_key: Optional[str] = None,
        serpapi_key: Optional[str] = None,
    ):
        """
        Initialize multi-source verifier.

        Args:
            llm_gateway: LLM gateway for analysis
            perplexity_key: Perplexity API key
            tavily_key: Tavily API key
            google_key: Google Fact Check API key
            serpapi_key: SerpAPI key (optional)
        """
        self.llm = llm_gateway

        # Initialize API clients
        self.perplexity = PerplexityClient(perplexity_key)
        self.tavily = TavilyClient(tavily_key)
        self.google_factcheck = GoogleFactCheckClient(google_key)
        self.serpapi = SerpAPIClient(serpapi_key) if serpapi_key else None

    def verify_claim(self, claim: FactualClaim) -> FactCheckResult:
        """
        Verify a claim using multiple sources and reconcile results.

        Args:
            claim: Claim to verify

        Returns:
            FactCheckResult with verification status, confidence, and sources
        """
        # Step 1: Search all available APIs in parallel
        all_results = self._search_all_apis(claim.claim_text)

        # Step 2: If no results found, mark as unverifiable
        if not all_results:
            return FactCheckResult(
                claim=claim,
                verification_status=VerificationStatus.UNVERIFIABLE,
                confidence_score=0.0,
                explanation="No sources found to verify this claim.",
                sources=[],
                verified_at=datetime.utcnow().isoformat(),
            )

        # Step 3: Analyze results with LLM and reconcile
        verification_status, confidence, explanation = self._reconcile_results(
            claim, all_results
        )

        # Step 4: Convert search results to Source objects
        sources = self._convert_to_sources(all_results)

        return FactCheckResult(
            claim=claim,
            verification_status=verification_status,
            confidence_score=confidence,
            explanation=explanation,
            sources=sources,
            verified_at=datetime.utcnow().isoformat(),
        )

    def _search_all_apis(self, query: str) -> List[SearchResult]:
        """
        Search all available APIs in parallel.

        Args:
            query: Search query

        Returns:
            Combined list of search results from all APIs
        """
        all_results = []

        # Search each API
        perplexity_results = self.perplexity.search(query)
        all_results.extend(perplexity_results)

        tavily_results = self.tavily.search(query)
        all_results.extend(tavily_results)

        google_results = self.google_factcheck.search(query)
        all_results.extend(google_results)

        if self.serpapi:
            serpapi_results = self.serpapi.search(query)
            all_results.extend(serpapi_results)

        return all_results

    def _reconcile_results(
        self,
        claim: FactualClaim,
        search_results: List[SearchResult],
    ) -> Tuple[VerificationStatus, float, str]:
        """
        Reconcile search results from multiple sources using LLM.

        Args:
            claim: Original claim
            search_results: Results from all APIs

        Returns:
            Tuple of (verification_status, confidence_score, explanation)
        """
        # Build context from all search results
        context = self._build_reconciliation_context(search_results)

        # Create prompt for LLM to reconcile
        system_prompt = """You are an expert fact-checker analyzing multiple sources to verify claims.

Your task:
1. Review all provided sources
2. Determine consensus verification status:
   - "verified" (✅) if 3+ sources agree the claim is true
   - "possibly_inaccurate" (⚠️) if sources conflict or claim is time-sensitive/outdated
   - "unverifiable" (❓) if sources don't address the claim or are inconclusive
3. Assign confidence score (0.0-1.0):
   - 0.9-1.0: Strong consensus, high-quality sources
   - 0.7-0.89: Good agreement, reliable sources
   - 0.4-0.69: Mixed evidence or lower-quality sources
   - 0.0-0.39: No clear evidence or contradictory
4. Explain your reasoning (2-3 sentences)

Respond with valid JSON:
{
  "verification_status": "verified" | "possibly_inaccurate" | "unverifiable",
  "confidence_score": 0.0-1.0,
  "explanation": "Your explanation here"
}"""

        user_prompt = f"""Verify this claim using the provided sources:

**Claim**: {claim.claim_text}
**Type**: {claim.claim_type.value}
**Context**: {claim.context or 'No additional context'}

**Sources from Multiple APIs**:
{context}

Analyze all sources and return JSON with verification_status, confidence_score, and explanation."""

        try:
            response_json = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

            # Parse response
            status_str = response_json.get("verification_status", "unverifiable")
            try:
                status = VerificationStatus(status_str)
            except ValueError:
                status = VerificationStatus.UNVERIFIABLE

            confidence = float(response_json.get("confidence_score", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1

            explanation = response_json.get(
                "explanation",
                "Unable to determine verification status from available sources.",
            )

            return status, confidence, explanation

        except Exception as e:
            print(f"Reconciliation error: {e}")
            return (
                VerificationStatus.UNVERIFIABLE,
                0.3,
                f"Error during reconciliation: {str(e)}",
            )

    def _build_reconciliation_context(self, results: List[SearchResult]) -> str:
        """
        Build formatted context from search results.

        Args:
            results: Search results

        Returns:
            Formatted string of all results
        """
        if not results:
            return "No sources found."

        context_lines = []
        for i, result in enumerate(results, 1):
            context_lines.append(f"\n**Source {i}** [{result.source_api.upper()}]")
            context_lines.append(f"Title: {result.title}")
            if result.url:
                context_lines.append(f"URL: {result.url}")
            context_lines.append(f"Content: {result.snippet}")
            context_lines.append(f"Relevance Score: {result.score:.2f}")
            context_lines.append("-" * 60)

        return "\n".join(context_lines)

    def _convert_to_sources(self, search_results: List[SearchResult]) -> List[Source]:
        """
        Convert search results to Source objects.

        Args:
            search_results: Search results

        Returns:
            List of Source objects
        """
        sources = []
        for result in search_results:
            sources.append(
                Source(
                    title=result.title,
                    url=result.url,
                    excerpt=result.snippet[:200] if result.snippet else None,
                    reliability_score=result.score,
                    api_source=result.source_api,
                )
            )

        return sources

    def close(self):
        """Close all API clients."""
        self.perplexity.close()
        self.google_factcheck.close()
        if self.serpapi:
            self.serpapi.close()
