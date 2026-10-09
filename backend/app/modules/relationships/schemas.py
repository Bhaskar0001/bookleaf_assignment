from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, ConfigDict


class DuplicateSignals(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    same_author: bool
    same_book: bool
    subject_similarity: float
    description_similarity: float
    existing_status: str
    recency_days: int


class DuplicateCandidateOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ticket_id: uuid.UUID
    ticket_number: str
    subject: str
    status: str
    similarity: float
    reason: str
    signals: DuplicateSignals


class ConfirmedRelationshipOut(BaseModel):
    id: uuid.UUID
    source_ticket_id: uuid.UUID
    source_ticket_number: Optional[str] = None
    target_ticket_id: uuid.UUID
    target_ticket_number: Optional[str] = None
    relationship_type: str
    detected_by: str
    confirmed_by_name: Optional[str] = None
    created_at: datetime


class DuplicateRelationshipsResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]  # contains "candidates" and "confirmedRelationships"


class LinkDuplicateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    target_ticket_id: str = Field(..., alias="targetTicketId")


class UnlinkDuplicateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    target_ticket_id: str = Field(..., alias="targetTicketId")
