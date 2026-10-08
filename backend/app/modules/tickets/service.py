import asyncio
from typing import List, Optional, Tuple
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.tickets.repository import TicketRepository
from app.modules.tickets.state_machine import validate_status_transition
from app.modules.tickets.schemas import (
    CreateTicketRequest,
    TicketOut,
    TicketMessageOut,
    TicketInternalNoteOut,
    TicketBookSummary,
    TicketAuthorSummary,
    AuthorTicketDetailOut,
)
from app.modules.timeline.service import TicketEventService
from app.modules.books.repository import BookRepository
from app.modules.support_assist.service import SupportAssistService
from app.db.models import Ticket, Author, User, TicketAssignment, TicketMessage, TicketInternalNote
from app.core.errors import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
)
from app.core.logging import logger


class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = TicketRepository(db)
        self.event_service = TicketEventService(db)
        self.book_repo = BookRepository(db)

    async def create_author_ticket(
        self,
        author: Author,
        req: CreateTicketRequest,
    ) -> Ticket:
        # Validate book if provided
        book_id: Optional[uuid.UUID] = None
        if req.book_id:
            book = await self.book_repo.get_book_by_id_and_author(req.book_id, author.id)
            if not book:
                # Check if book exists belonging to another author
                other_book = await self.book_repo.get_book_by_id(req.book_id)
                if other_book:
                    raise ForbiddenException(
                        "The requested book is not available for this account.",
                        code="BOOK_NOT_ACCESSIBLE",
                    )
                raise NotFoundException("Referenced book not found", code="BOOK_NOT_FOUND")
            book_id = book.id

        # 1. Persist ticket
        ticket = await self.repository.create_ticket(
            author_id=author.id,
            subject=req.subject,
            description=req.description,
            book_id=book_id,
        )
        await self.db.flush()

        # 2. Record TICKET_CREATED event atomically in same transaction
        await self.event_service.record_event(
            ticket_id=ticket.id,
            event_type="TICKET_CREATED",
            actor_user_id=author.user_id,
            metadata={
                "subject": ticket.subject,
                "book_id": str(book_id) if book_id else None,
            },
        )

        # 3. Commit transaction
        await self.db.commit()
        await self.db.refresh(ticket)

        # 4. Trigger asynchronous background classification & prioritization with independent session
        async def _run_assist_bg(t_id: uuid.UUID):
            try:
                from app.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as bg_session:
                    svc = SupportAssistService(bg_session)
                    await svc.process_ticket_async(t_id)
            except Exception as bg_err:
                logger.warning(f"Background assist processing failed for ticket {t_id}: {bg_err}")

        try:
            asyncio.create_task(_run_assist_bg(ticket.id))
        except Exception as e:
            logger.warning(f"Could not trigger background assist task: {e}")

        return ticket

    async def get_author_ticket_detail(self, identifier: str, author_id: uuid.UUID) -> AuthorTicketDetailOut:
        ticket = await self.repository.get_by_identifier(identifier)
        if not ticket:
            raise NotFoundException("Ticket not found", code="TICKET_NOT_FOUND")

        # Strict Author Isolation
        if ticket.author_id != author_id:
            raise ForbiddenException(
                "You are not authorized to view this ticket.",
                code="TICKET_NOT_ACCESSIBLE",
            )

        # Build clean AuthorTicketDetailOut (INTERNAL NOTES ARE COMPLETELY EXCLUDED)
        book_summary = None
        if ticket.book:
            book_summary = TicketBookSummary(
                id=ticket.book.id,
                book_id=ticket.book.book_id,
                title=ticket.book.title,
                isbn=ticket.book.isbn,
                status=ticket.book.status,
            )

        messages_out = []
        for m in ticket.messages:
            sender_name = m.sender.full_name if m.sender else None
            messages_out.append(
                TicketMessageOut(
                    id=m.id,
                    sender_user_id=m.sender_user_id,
                    sender_name=sender_name,
                    sender_role=m.sender_role,
                    message=m.message,
                    created_at=m.created_at,
                )
            )

        # Fetch author-visible timeline events
        timeline_events = await self.event_service.get_ticket_timeline(ticket.id, include_internal=False)

        # Fetch confirmed related tickets
        from app.modules.relationships.repository import RelationshipRepository
        rel_repo = RelationshipRepository(self.db)
        rels = await rel_repo.get_relationships_for_ticket(ticket.id)
        related_list = []
        for r in rels:
            other = r.target_ticket if r.source_ticket_id == ticket.id else r.source_ticket
            if other and other.author_id == author_id:
                related_list.append({
                    "ticket_id": str(other.id),
                    "ticket_number": other.ticket_number,
                    "subject": other.subject,
                    "status": other.status,
                    "relationship_type": r.relationship_type,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                })

        return AuthorTicketDetailOut(
            ticket_number=ticket.ticket_number,
            subject=ticket.subject,
            description=ticket.description,
            status=ticket.status,
            category=ticket.category,
            priority=ticket.priority,
            created_at=ticket.created_at,
            book=book_summary,
            messages=messages_out,
            timeline=timeline_events,
            related_tickets=related_list,
        )

    async def get_admin_ticket_detail(self, identifier: str) -> Ticket:
        ticket = await self.repository.get_by_identifier(identifier)
        if not ticket:
            raise NotFoundException("Ticket not found", code="TICKET_NOT_FOUND")
        return ticket

    async def add_message(
        self,
        identifier: str,
        current_user: User,
        message_text: str,
        author_id: Optional[uuid.UUID] = None,
    ) -> TicketMessage:
        ticket = await self.repository.get_by_identifier(identifier)
        if not ticket:
            raise NotFoundException("Ticket not found", code="TICKET_NOT_FOUND")

        # If user is author, check ownership
        if current_user.role == "AUTHOR":
            if ticket.author_id != author_id:
                raise ForbiddenException("You cannot send messages to this ticket", code="TICKET_NOT_ACCESSIBLE")

        if ticket.status == "CLOSED":
            raise ValidationException("Cannot reply to a closed ticket. Please contact support to reopen.", code="TICKET_CLOSED")

        # Add message
        msg = await self.repository.add_message(
            ticket_id=ticket.id,
            sender_user_id=current_user.id,
            sender_role=current_user.role,
            message=message_text,
        )
        await self.db.flush()

        # Record MESSAGE_ADDED event
        await self.event_service.record_event(
            ticket_id=ticket.id,
            event_type="MESSAGE_ADDED",
            actor_user_id=current_user.id,
            metadata={
                "message_id": str(msg.id),
                "sender_role": current_user.role,
            },
        )

        # If admin replied and ticket was OPEN, transition to IN_PROGRESS
        if current_user.role == "ADMIN":
            await self.event_service.record_event(
                ticket_id=ticket.id,
                event_type="RESPONSE_SENT",
                actor_user_id=current_user.id,
                metadata={"message_id": str(msg.id)},
            )
            if ticket.status == "OPEN":
                ticket.status = "IN_PROGRESS"
                await self.event_service.record_event(
                    ticket_id=ticket.id,
                    event_type="STATUS_CHANGED",
                    actor_user_id=current_user.id,
                    metadata={"old_status": "OPEN", "new_status": "IN_PROGRESS"},
                )

        ticket.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def add_internal_note(
        self,
        identifier: str,
        admin_user: User,
        note_text: str,
    ) -> TicketInternalNote:
        ticket = await self.repository.get_by_identifier(identifier)
        if not ticket:
            raise NotFoundException("Ticket not found", code="TICKET_NOT_FOUND")

        note = await self.repository.add_internal_note(
            ticket_id=ticket.id,
            admin_user_id=admin_user.id,
            note=note_text,
        )
        await self.db.flush()

        await self.event_service.record_event(
            ticket_id=ticket.id,
            event_type="INTERNAL_NOTE_ADDED",
            actor_user_id=admin_user.id,
            metadata={"note_id": str(note.id)},
        )

        ticket.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def update_status(
        self,
        identifier: str,
        new_status: str,
        actor_user: User,
    ) -> Ticket:
        ticket = await self.repository.get_by_identifier(identifier)
        if not ticket:
            raise NotFoundException("Ticket not found", code="TICKET_NOT_FOUND")

        old_status = ticket.status
        validate_status_transition(old_status, new_status)

        ticket.status = new_status
        now = datetime.now(timezone.utc)
        ticket.updated_at = now

        if new_status == "RESOLVED":
            ticket.resolved_at = now
        elif new_status == "CLOSED":
            ticket.closed_at = now

        # Record STATUS_CHANGED
        await self.event_service.record_event(
            ticket_id=ticket.id,
            event_type="STATUS_CHANGED",
            actor_user_id=actor_user.id,
            metadata={"old_status": old_status, "new_status": new_status},
        )

        # Additional specific events
        if new_status == "RESOLVED":
            await self.event_service.record_event(
                ticket_id=ticket.id,
                event_type="RESOLVED",
                actor_user_id=actor_user.id,
                metadata={},
            )
        elif new_status == "CLOSED":
            await self.event_service.record_event(
                ticket_id=ticket.id,
                event_type="CLOSED",
                actor_user_id=actor_user.id,
                metadata={},
            )

        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def update_category(
        self,
        identifier: str,
        category: str,
        actor_user: User,
    ) -> Ticket:
        ticket = await self.repository.get_by_identifier(identifier)
        if not ticket:
            raise NotFoundException("Ticket not found", code="TICKET_NOT_FOUND")

        old_cat = ticket.category
        ticket.category = category
        ticket.category_source = "ADMIN"
        ticket.updated_at = datetime.now(timezone.utc)

        await self.event_service.record_event(
            ticket_id=ticket.id,
            event_type="CATEGORY_CHANGED",
            actor_user_id=actor_user.id,
            metadata={"old_category": old_cat, "new_category": category, "source": "ADMIN"},
        )

        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def update_priority(
        self,
        identifier: str,
        priority: str,
        actor_user: User,
    ) -> Ticket:
        ticket = await self.repository.get_by_identifier(identifier)
        if not ticket:
            raise NotFoundException("Ticket not found", code="TICKET_NOT_FOUND")

        old_prio = ticket.priority
        ticket.priority = priority
        ticket.priority_source = "ADMIN"
        ticket.updated_at = datetime.now(timezone.utc)

        await self.event_service.record_event(
            ticket_id=ticket.id,
            event_type="PRIORITY_CHANGED",
            actor_user_id=actor_user.id,
            metadata={"old_priority": old_prio, "new_priority": priority, "source": "ADMIN"},
        )

        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def update_assignment(
        self,
        identifier: str,
        assigned_admin_id: uuid.UUID,
        assigned_by: User,
    ) -> Ticket:
        ticket = await self.repository.get_by_identifier(identifier)
        if not ticket:
            raise NotFoundException("Ticket not found", code="TICKET_NOT_FOUND")

        ticket.assigned_admin_id = assigned_admin_id
        ticket.updated_at = datetime.now(timezone.utc)

        assignment = TicketAssignment(
            ticket_id=ticket.id,
            admin_user_id=assigned_admin_id,
            assigned_by_user_id=assigned_by.id,
        )
        self.db.add(assignment)

        await self.event_service.record_event(
            ticket_id=ticket.id,
            event_type="ASSIGNED",
            actor_user_id=assigned_by.id,
            metadata={"assigned_admin_id": str(assigned_admin_id)},
        )

        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    def to_ticket_out(self, t: Ticket) -> TicketOut:
        author_summary = None
        if t.author:
            author_summary = TicketAuthorSummary(
                id=t.author.id,
                author_id=t.author.author_id,
                pen_name=t.author.pen_name,
                email=t.author.user.email if t.author.user else None,
            )

        book_summary = None
        if t.book:
            book_summary = TicketBookSummary(
                id=t.book.id,
                book_id=t.book.book_id,
                title=t.book.title,
                isbn=t.book.isbn,
                status=t.book.status,
            )

        msgs = []
        for m in getattr(t, "messages", []):
            sender_name = m.sender.full_name if m.sender else None
            msgs.append(
                TicketMessageOut(
                    id=m.id,
                    sender_user_id=m.sender_user_id,
                    sender_name=sender_name,
                    sender_role=m.sender_role,
                    message=m.message,
                    created_at=m.created_at,
                )
            )

        return TicketOut(
            id=t.id,
            ticket_number=t.ticket_number,
            author_id=t.author_id,
            author=author_summary,
            book_id=t.book_id,
            book=book_summary,
            subject=t.subject,
            description=t.description,
            status=t.status,
            category=t.category,
            priority=t.priority,
            system_category=t.system_category,
            system_category_confidence=float(t.system_category_confidence) if t.system_category_confidence else None,
            category_source=t.category_source,
            system_priority=t.system_priority,
            system_priority_confidence=float(t.system_priority_confidence) if t.system_priority_confidence else None,
            priority_source=t.priority_source,
            assigned_admin_id=t.assigned_admin_id,
            assigned_admin_name=t.assigned_admin.full_name if t.assigned_admin else None,
            created_at=t.created_at,
            updated_at=t.updated_at,
            resolved_at=t.resolved_at,
            closed_at=t.closed_at,
            messages=msgs,
        )
