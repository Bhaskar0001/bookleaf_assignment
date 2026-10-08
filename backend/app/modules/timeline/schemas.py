from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class TimelineEventOut(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    ticket_number: Optional[str] = None
    ticket_subject: Optional[str] = None
    actor_user_id: Optional[uuid.UUID] = None
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    event_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class AuthorTimelineResponse(BaseModel):
    success: bool = True
    data: List[TimelineEventOut]
