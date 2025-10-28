"""Search and fact-checking API clients."""
import os
from typing import List, Optional

import httpx
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single search result from an API."""

    title: str = Field(..., description="Result title")
    url: Optional[str] = Field(None, description="Source URL")
    snippet: str = Field(..., description="Text snippet/excerpt")
    score: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance score")
    source_api: str = Field(..., description="Which API provided this result")


class PerplexityClient:
    """Client for Perplexity AI search API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Perplexity client.

        Args:
            api_key: Perplexity API key
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"
        self.client = httpx.Client(timeout=30.0)

    def search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """
        Search using Perplexity API.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        if not self.api_key:
            return []

        try:
            # Perplexity uses chat completion API with search
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Be precise and concise. Provide factual information with sources.",
                        },
                        {
                            "role": "user",
                            "content": f"Fact-check this claim: {query}. Provide verification status and sources.",
                        },
                    ],
                    "return_citations": True,
                    "return_related_questions": False,
                },
            )
            response.raise_for_status()
            data = response.json()

            # Extract response and citations
            content = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])

            results = []
            for i, citation in enumerate(citations[:max_results]):
                results.append(
                    SearchResult(
                        title=f"Source {i+1}",
                        url=citation if isinstance(citation, str) else None,
                        snippet=content[:500],  # First 500 chars of analysis
                        score=1.0 - (i * 0.1),  # Decreasing relevance
                        source_api="perplexity",
                    )
                )

            # If no citations, create result from response
            if not results and content:
                results.append(
                    SearchResult(
                        title="Perplexity Analysis",
                        snippet=content[:500],
                        score=0.8,
                        source_api="perplexity",
                    )
                )

            return results

        except Exception as e:
            print("Perplexity search error:", str(e))
            return []

    def close(self):
        """Close HTTP client."""
        self.client.close()


class TavilyClient:
    """Client for Tavily AI search API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client.

        Args:
            api_key: Tavily API key
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

        # Initialize Tavily client if available
        self.client = None
        if self.api_key:
            try:
                from tavily import TavilyClient as Tavily

                self.client = Tavily(api_key=self.api_key)
            except ImportError:
                print("Warning: tavily-python not installed")

    def search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """
        Search using Tavily API.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        if not self.client:
            return []

        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
                include_answer=True,
            )

            results = []
            for item in response.get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", "Unknown"),
                        url=item.get("url"),
                        snippet=item.get("content", ""),
                        score=item.get("score", 0.5),
                        source_api="tavily",
                    )
                )

            return results

        except Exception as e:
            print("Tavily search error:", str(e))
            return []


class GoogleFactCheckClient:
    """Client for Google Fact Check Tools API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Fact Check client.

        Args:
            api_key: Google API key
        """
        self.api_key = api_key or os.getenv("GOOGLE_FACT_CHECK_API_KEY")
        self.client = httpx.Client(timeout=30.0)

    def search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """
        Search using Google Fact Check API.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        if not self.api_key:
            return []

        try:
            response = self.client.get(
                "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                params={
                    "query": query,
                    "key": self.api_key,
                    "languageCode": "en",
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for claim in data.get("claims", [])[:max_results]:
                # Get first review
                reviews = claim.get("claimReview", [])
                if reviews:
                    review = reviews[0]
                    results.append(
                        SearchResult(
                            title=claim.get("text", "Unknown claim"),
                            url=review.get("url"),
                            snippet=f"{review.get('textualRating', 'Unknown')} - {review.get('publisher', {}).get('name', 'Unknown publisher')}",
                            score=0.9,  # High score for fact-check databases
                            source_api="google_factcheck",
                        )
                    )

            return results

        except Exception as e:
            print("Google Fact Check search error:", str(e))
            return []

    def close(self):
        """Close HTTP client."""
        self.client.close()


class SerpAPIClient:
    """Client for SerpAPI (Google Search) - Optional."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpAPI client.

        Args:
            api_key: SerpAPI key
        """
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        self.client = httpx.Client(timeout=30.0)

    def search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """
        Search using SerpAPI.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        if not self.api_key:
            return []

        try:
            response = self.client.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "api_key": self.api_key,
                    "num": max_results,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("organic_results", [])[:max_results]:
                results.append(
                    SearchResult(
                        title=item.get("title", "Unknown"),
                        url=item.get("link"),
                        snippet=item.get("snippet", ""),
                        score=0.7,
                        source_api="serpapi",
                    )
                )

            return results

        except Exception as e:
            print("SerpAPI search error:", str(e))
            return []

    def close(self):
        """Close HTTP client."""
        self.client.close()
