"""Data models for fact-checking results."""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ClaimType(str, Enum):
    """Types of factual claims."""

    STATISTIC = "statistic"
    DATE = "date"
    COMPANY = "company"
    TECHNOLOGY = "technology"
    PREDICTION = "prediction"
    REGULATION = "regulation"
    OTHER = "other"


class VerificationStatus(str, Enum):
    """Verification status of a claim."""

    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    INCORRECT = "incorrect"
    UNABLE_TO_VERIFY = "unable_to_verify"


class FactualClaim(BaseModel):
    """A factual claim extracted from transcript."""

    claim_text: str = Field(..., description="The factual claim")
    claim_type: ClaimType = Field(..., description="Type of claim")
    speaker: str = Field(..., description="Who made the claim")
    timestamp: Optional[str] = Field(None, description="When claim was made")
    context: Optional[str] = Field(None, description="Surrounding context")


class Source(BaseModel):
    """A source used for verification."""

    title: str = Field(..., description="Source title")
    url: Optional[str] = Field(None, description="Source URL")
    excerpt: Optional[str] = Field(None, description="Relevant excerpt")
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0, description="Source reliability")


class FactCheckResult(BaseModel):
    """Result of fact-checking a claim."""

    claim: FactualClaim = Field(..., description="The original claim")
    verification_status: VerificationStatus = Field(..., description="Verification outcome")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in verification")
    explanation: str = Field(..., description="Explanation of verification")
    sources: List[Source] = Field(default_factory=list, description="Sources consulted")
    verified_at: Optional[str] = Field(None, description="ISO timestamp of verification")

    @field_validator('confidence_score')
    @classmethod
    def validate_confidence(cls, v: float, info) -> float:
        """Ensure confidence matches verification status."""
        status = info.data.get('verification_status')
        if status == VerificationStatus.VERIFIED and v < 0.7:
            raise ValueError("Verified claims should have confidence >= 0.7")
        if status == VerificationStatus.INCORRECT and v < 0.7:
            raise ValueError("Incorrect claims should have confidence >= 0.7")
        return v


class EpisodeFactChecks(BaseModel):
    """All fact-check results for an episode."""

    episode_id: str = Field(..., description="Episode identifier")
    fact_checks: List[FactCheckResult] = Field(..., description="All fact-check results")
    total_claims: int = Field(0, description="Total claims identified")
    verified_count: int = Field(0, description="Number of verified claims")
    unverified_count: int = Field(0, description="Number of unverified claims")

    def model_post_init(self, __context) -> None:
        """Calculate statistics after initialization."""
        self.total_claims = len(self.fact_checks)
        self.verified_count = sum(
            1 for fc in self.fact_checks
            if fc.verification_status in [VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_VERIFIED]
        )
        self.unverified_count = self.total_claims - self.verified_count

    @field_validator('fact_checks')
    @classmethod
    def validate_fact_check_count(cls, v: List[FactCheckResult]) -> List[FactCheckResult]:
        """Ensure at least 3 fact checks."""
        if len(v) < 3:
            raise ValueError(f"Must have at least 3 fact checks, got {len(v)}")
        return v
