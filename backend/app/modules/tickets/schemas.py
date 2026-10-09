from typing import Optional, List, Any
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, ConfigDict


class CreateTicketRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    book_id: Optional[str] = Field(None, alias="bookId")
    category: Optional[str] = "GENERAL"
    subject: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    attachment_name: Optional[str] = None


class TicketBookSummary(BaseModel):
    id: uuid.UUID
    book_id: str
    title: str
    isbn: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class TicketAuthorSummary(BaseModel):
    id: uuid.UUID
    author_id: str
    pen_name: str
    email: Optional[str] = None

    class Config:
        from_attributes = True


class TicketMessageOut(BaseModel):
    id: uuid.UUID
    sender_user_id: uuid.UUID
    sender_name: Optional[str] = None
    sender_role: str  # AUTHOR, ADMIN
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketInternalNoteOut(BaseModel):
    id: uuid.UUID
    admin_user_id: uuid.UUID
    admin_name: Optional[str] = None
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    id: uuid.UUID
    ticket_number: str
    author_id: uuid.UUID
    author: Optional[TicketAuthorSummary] = None
    book_id: Optional[uuid.UUID] = None
    book: Optional[TicketBookSummary] = None
    subject: str
    description: str
    status: str
    category: Optional[str] = None
    priority: Optional[str] = None
    system_category: Optional[str] = None
    system_category_confidence: Optional[float] = None
    category_source: Optional[str] = None
    system_priority: Optional[str] = None
    system_priority_confidence: Optional[float] = None
    priority_source: Optional[str] = None
    assigned_admin_id: Optional[uuid.UUID] = None
    assigned_admin_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    messages: List[TicketMessageOut] = []

    class Config:
        from_attributes = True


from app.modules.timeline.schemas import TimelineEventOut


class AuthorTicketDetailOut(BaseModel):
    ticket_number: str
    subject: str
    description: str
    status: str
    category: Optional[str] = None
    priority: Optional[str] = None
    created_at: datetime
    book: Optional[TicketBookSummary] = None
    messages: List[TicketMessageOut] = []
    timeline: List[TimelineEventOut] = []
    related_tickets: List[dict] = []


class CreateMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class CreateInternalNoteRequest(BaseModel):
    note: str = Field(..., min_length=1)


class UpdateStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(OPEN|IN_PROGRESS|RESOLVED|CLOSED)$")


class UpdateCategoryRequest(BaseModel):
    category: str = Field(..., pattern="^(ROYALTY_PAYMENT|ISBN_METADATA|PRINTING_QUALITY|DISTRIBUTION_AVAILABILITY|BOOK_STATUS|GENERAL)$")


class UpdatePriorityRequest(BaseModel):
    priority: str = Field(..., pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$")


class AssignTicketRequest(BaseModel):
    admin_id: uuid.UUID


class TicketResponse(BaseModel):
    success: bool = True
    data: Any
