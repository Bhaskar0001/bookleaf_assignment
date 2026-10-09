import uuid
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Numeric,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="AUTHOR", index=True)  # AUTHOR, ADMIN
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    author_profile: Mapped[Optional["Author"]] = relationship("Author", back_populates="user", uselist=False)
    sent_messages: Mapped[List["TicketMessage"]] = relationship("TicketMessage", back_populates="sender")
    internal_notes: Mapped[List["TicketInternalNote"]] = relationship("TicketInternalNote", back_populates="admin")


class Author(Base, TimestampMixin):
    __tablename__ = "authors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    author_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., AUTH001
    pen_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    joined_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_royalties_earned: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_royalties_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_royalties_pending: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="author_profile")
    books: Mapped[List["Book"]] = relationship("Book", back_populates="author", cascade="all, delete-orphan")
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="author")


class Book(Base, TimestampMixin):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., BK001
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("authors.id", ondelete="RESTRICT"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    isbn: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    genre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="In Production")  # "Published & Live", "In Production - Cover Design", etc.
    mrp: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    author_royalty_per_copy: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    copies_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    royalty_earned: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    royalty_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    royalty_pending: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    last_royalty_payout_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    print_partner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    available_on: Mapped[Any] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list, nullable=False)

    # Relationships
    author: Mapped["Author"] = relationship("Author", back_populates="books")
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="book")


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., BL-10001
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("authors.id", ondelete="RESTRICT"), index=True, nullable=False)
    book_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="SET NULL"), index=True, nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True, nullable=False)  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)  # ROYALTY_PAYMENT, ISBN_METADATA, etc.
    priority: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)  # CRITICAL, HIGH, MEDIUM, LOW

    # System vs Admin overrides
    system_category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    system_category_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)
    category_source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # SYSTEM, ADMIN

    system_priority: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    system_priority_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)
    priority_source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # SYSTEM, ADMIN

    assigned_admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    author: Mapped["Author"] = relationship("Author", back_populates="tickets")
    book: Mapped[Optional["Book"]] = relationship("Book", back_populates="tickets")
    assigned_admin: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_admin_id])
    messages: Mapped[List["TicketMessage"]] = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketMessage.created_at")
    internal_notes: Mapped[List["TicketInternalNote"]] = relationship("TicketInternalNote", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketInternalNote.created_at")
    events: Mapped[List["TicketEvent"]] = relationship("TicketEvent", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketEvent.created_at")

    __table_args__ = (
        Index("ix_tickets_author_status", "author_id", "status"),
        Index("ix_tickets_created_at_desc", "created_at"),
    )


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    sender_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    sender_role: Mapped[str] = mapped_column(String(32), nullable=False)  # AUTHOR, ADMIN
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="messages")
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages")


class TicketInternalNote(Base):
    __tablename__ = "ticket_internal_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    admin_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="internal_notes")
    admin: Mapped["User"] = relationship("User", back_populates="internal_notes")


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    metadata_json: Mapped[Any] = mapped_column("metadata", JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="events")
    actor: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_ticket_events_ticket_created", "ticket_id", "created_at"),
    )


class TicketRelationship(Base):
    __tablename__ = "ticket_relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    target_ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(32), default="DUPLICATE", nullable=False)
    detected_by: Mapped[str] = mapped_column(String(32), default="SYSTEM", nullable=False)  # SYSTEM, ADMIN
    confirmed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    source_ticket: Mapped["Ticket"] = relationship("Ticket", foreign_keys=[source_ticket_id])
    target_ticket: Mapped["Ticket"] = relationship("Ticket", foreign_keys=[target_ticket_id])
    confirmer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[confirmed_by])

    __table_args__ = (
        UniqueConstraint("source_ticket_id", "target_ticket_id", "relationship_type", name="uq_ticket_relationship"),
    )


class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    admin_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    assigned_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    ticket: Mapped["Ticket"] = relationship("Ticket")
    admin: Mapped["User"] = relationship("User", foreign_keys=[admin_user_id])
    assigned_by: Mapped["User"] = relationship("User", foreign_keys=[assigned_by_user_id])


class SupportAssistRun(Base):
    __tablename__ = "support_assist_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)  # CLASSIFICATION, PRIORITIZATION, RESPONSE_DRAFT
    provider: Mapped[str] = mapped_column(String(64), nullable=False)  # GEMINI, LOCAL_RULES
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    input_payload: Mapped[Any] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), nullable=False)
    output_payload: Mapped[Optional[Any]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # SUCCESS, FAILED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    ticket: Mapped["Ticket"] = relationship("Ticket")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    details: Mapped[Any] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    actor: Mapped[Optional["User"]] = relationship("User")
