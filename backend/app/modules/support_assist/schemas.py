from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    category: str = Field(description="One of: ROYALTY_PAYMENT, ISBN_METADATA, PRINTING_QUALITY, DISTRIBUTION_AVAILABILITY, BOOK_STATUS, GENERAL")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class PrioritizationResult(BaseModel):
    priority: str = Field(description="One of: CRITICAL, HIGH, MEDIUM, LOW")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class DraftResponseResult(BaseModel):
    draft_response: str
    suggested_action: Optional[str] = None
    requires_manual_verification: bool = False
    verification_notes: Optional[str] = None


class DraftResponseRequest(BaseModel):
    ticket_id: Optional[str] = None
