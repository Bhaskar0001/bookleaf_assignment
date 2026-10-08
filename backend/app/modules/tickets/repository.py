from typing import List, Optional, Tuple
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from app.db.models import Ticket, Author, Book, User, TicketMessage, TicketInternalNote


class TicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_ticket_number(self) -> str:
        # Atomic counter generation for human-readable BL-10001
        count_res = await self.db.execute(select(func.count(Ticket.id)))
        count = count_res.scalar() or 0
        return f"BL-{10001 + count}"

    async def create_ticket(
        self,
        author_id: uuid.UUID,
        subject: str,
        description: str,
        book_id: Optional[uuid.UUID] = None,
    ) -> Ticket:
        ticket_number = await self.generate_ticket_number()
        ticket = Ticket(
            ticket_number=ticket_number,
            author_id=author_id,
            book_id=book_id,
            subject=subject,
            description=description,
            status="OPEN",
        )
        self.db.add(ticket)
        return ticket

    async def get_by_identifier(self, identifier: str) -> Optional[Ticket]:
        query = (
            select(Ticket)
            .options(
                selectinload(Ticket.author).selectinload(Author.user),
                selectinload(Ticket.book),
                selectinload(Ticket.assigned_admin),
                selectinload(Ticket.messages).selectinload(TicketMessage.sender),
                selectinload(Ticket.internal_notes).selectinload(TicketInternalNote.admin),
            )
        )
        try:
            val_uuid = uuid.UUID(identifier)
            query = query.where(Ticket.id == val_uuid)
        except ValueError:
            query = query.where(Ticket.ticket_number == identifier)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_author_tickets(self, author_id: uuid.UUID) -> List[Ticket]:
        query = (
            select(Ticket)
            .where(Ticket.author_id == author_id)
            .options(
                selectinload(Ticket.book),
                selectinload(Ticket.messages).selectinload(TicketMessage.sender),
            )
            .order_by(Ticket.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_admin_queue(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[uuid.UUID] = None,
        author_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        sort_by: str = "recent",  # oldest_unresolved, highest_priority, recent
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Ticket], int]:
        query = select(Ticket).options(
            selectinload(Ticket.author).selectinload(Author.user),
            selectinload(Ticket.book),
            selectinload(Ticket.assigned_admin),
        )

        conditions = []
        if status:
            conditions.append(Ticket.status == status)
        if category:
            conditions.append(Ticket.category == category)
        if priority:
            conditions.append(Ticket.priority == priority)
        if assignee_id:
            conditions.append(Ticket.assigned_admin_id == assignee_id)
        if author_id:
            conditions.append(Ticket.author_id == author_id)
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    Ticket.ticket_number.ilike(search_pattern),
                    Ticket.subject.ilike(search_pattern),
                    Ticket.description.ilike(search_pattern),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Total count query
        count_q = select(func.count(Ticket.id))
        if conditions:
            count_q = count_q.where(and_(*conditions))
        total_res = await self.db.execute(count_q)
        total_count = total_res.scalar() or 0

        # Sort order
        if sort_by == "oldest_unresolved":
            query = query.where(Ticket.status.in_(["OPEN", "IN_PROGRESS"])).order_by(asc(Ticket.created_at))
        elif sort_by == "highest_priority":
            # Priority order: CRITICAL > HIGH > MEDIUM > LOW
            priority_order = func.case(
                (Ticket.priority == "CRITICAL", 1),
                (Ticket.priority == "HIGH", 2),
                (Ticket.priority == "MEDIUM", 3),
                (Ticket.priority == "LOW", 4),
                else_=5,
            )
            query = query.order_by(priority_order, desc(Ticket.created_at))
        else:
            query = query.order_by(desc(Ticket.updated_at))

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total_count

    async def add_message(
        self,
        ticket_id: uuid.UUID,
        sender_user_id: uuid.UUID,
        sender_role: str,
        message: str,
    ) -> TicketMessage:
        msg = TicketMessage(
            ticket_id=ticket_id,
            sender_user_id=sender_user_id,
            sender_role=sender_role,
            message=message,
        )
        self.db.add(msg)
        return msg

    async def add_internal_note(
        self,
        ticket_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        note: str,
    ) -> TicketInternalNote:
        internal_note = TicketInternalNote(
            ticket_id=ticket_id,
            admin_user_id=admin_user_id,
            note=note,
        )
        self.db.add(internal_note)
        return internal_note
