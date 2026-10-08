from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.db.models import TicketEvent, Ticket, User


class TicketEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(
        self,
        ticket_id: uuid.UUID,
        event_type: str,
        actor_user_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TicketEvent:
        event = TicketEvent(
            ticket_id=ticket_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            metadata_json=metadata or {},
        )
        self.db.add(event)
        # We don't commit here; caller transaction commits
        return event

    async def get_ticket_events(
        self,
        ticket_id: uuid.UUID,
        include_internal: bool = False,
    ) -> List[TicketEvent]:
        query = (
            select(TicketEvent)
            .where(TicketEvent.ticket_id == ticket_id)
            .options(selectinload(TicketEvent.actor), selectinload(TicketEvent.ticket))
            .order_by(TicketEvent.created_at.asc())
        )
        if not include_internal:
            # Authors must never see internal admin note events
            query = query.where(TicketEvent.event_type != "INTERNAL_NOTE_ADDED")

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_author_timeline(
        self,
        author_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TicketEvent]:
        # Events across all tickets of this author, excluding internal notes
        query = (
            select(TicketEvent)
            .join(Ticket, Ticket.id == TicketEvent.ticket_id)
            .where(Ticket.author_id == author_id)
            .where(TicketEvent.event_type != "INTERNAL_NOTE_ADDED")
            .options(selectinload(TicketEvent.actor), selectinload(TicketEvent.ticket))
            .order_by(desc(TicketEvent.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_admin_author_timeline(
        self,
        author_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TicketEvent]:
        # Full operational history including internal notes
        query = (
            select(TicketEvent)
            .join(Ticket, Ticket.id == TicketEvent.ticket_id)
            .where(Ticket.author_id == author_id)
            .options(selectinload(TicketEvent.actor), selectinload(TicketEvent.ticket))
            .order_by(desc(TicketEvent.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
