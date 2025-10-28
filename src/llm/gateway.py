"""OpenRouter LLM gateway for model-agnostic API access."""
import json
import os
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Response from LLM API."""

    content: str = Field(..., description="Generated text content")
    model: str = Field(..., description="Model that generated the response")
    tokens_used: int = Field(default=0, description="Total tokens consumed")
    finish_reason: str = Field(default="stop", description="Why generation stopped")


class LLMGateway:
    """Gateway for OpenRouter API - model-agnostic LLM access."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "anthropic/claude-3.5-sonnet",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        """
        Initialize OpenRouter gateway.

        Args:
            api_key: OpenRouter API key (or reads from OPENROUTER_API_KEY env var)
            default_model: Default model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.default_model = default_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.total_tokens_used = 0
        self.total_api_calls = 0

        # HTTP client
        self.client = httpx.Client(timeout=120.0)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close HTTP client."""
        self.client.close()

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """
        Generate text completion from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use (overrides default)
            max_tokens: Max tokens (overrides default)
            temperature: Temperature (overrides default)

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            Exception: If API call fails
        """
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Make API call
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/seekr-ai/podcast-agent",
            "X-Title": "Podcast Content Management Agent",
        }

        try:
            response = self.client.post(
                self.BASE_URL,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            # Parse response
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", "stop")

            # Extract token usage
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)

            # Update stats
            self.total_tokens_used += tokens_used
            self.total_api_calls += 1

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
            )

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
            raise Exception(f"OpenRouter API error: {error_detail}")
        except Exception as e:
            raise Exception(f"LLM generation failed: {e}")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Generate JSON response from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use
            **kwargs: Additional arguments for generate()

        Returns:
            Parsed JSON response

        Raises:
            Exception: If generation fails or response is not valid JSON
        """
        # Add JSON instruction to prompts
        if system_prompt:
            system_prompt += "\n\nYou must respond with valid JSON only, no other text."
        else:
            system_prompt = "You must respond with valid JSON only, no other text."

        prompt += "\n\nRespond with valid JSON only."

        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            **kwargs,
        )

        # Parse JSON
        try:
            # Try to extract JSON from markdown code blocks
            content = response.content.strip()
            if content.startswith("```"):
                # Remove markdown code fences
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines)

            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception("Failed to parse JSON response: " + str(e) + "\nResponse: " + response.content[:500])

    def get_stats(self) -> dict:
        """Get usage statistics."""
        return {
            "total_api_calls": self.total_api_calls,
            "total_tokens_used": self.total_tokens_used,
        }

    def reset_stats(self):
        """Reset usage statistics."""
        self.total_api_calls = 0
        self.total_tokens_used = 0
