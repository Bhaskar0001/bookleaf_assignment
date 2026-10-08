from typing import Optional, Dict, Any, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.timeline.repository import TicketEventRepository
from app.modules.timeline.schemas import TimelineEventOut
from app.db.models import TicketEvent


class TicketEventService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = TicketEventRepository(db)

    async def record_event(
        self,
        ticket_id: uuid.UUID,
        event_type: str,
        actor_user_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TicketEvent:
        """Central method for recording all business events atomically inside the caller's transaction."""
        return await self.repository.create_event(
            ticket_id=ticket_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            metadata=metadata,
        )

    def to_event_out(self, event: TicketEvent) -> TimelineEventOut:
        actor_name = None
        actor_role = None
        if event.actor:
            actor_name = event.actor.full_name
            actor_role = event.actor.role

        ticket_number = event.ticket.ticket_number if event.ticket else None
        ticket_subject = event.ticket.subject if event.ticket else None

        return TimelineEventOut(
            id=event.id,
            ticket_id=event.ticket_id,
            ticket_number=ticket_number,
            ticket_subject=ticket_subject,
            actor_user_id=event.actor_user_id,
            actor_name=actor_name,
            actor_role=actor_role,
            event_type=event.event_type,
            metadata=event.metadata_json or {},
            created_at=event.created_at,
        )

    async def get_ticket_timeline(
        self,
        ticket_id: uuid.UUID,
        include_internal: bool = False,
    ) -> List[TimelineEventOut]:
        events = await self.repository.get_ticket_events(ticket_id, include_internal=include_internal)
        return [self.to_event_out(e) for e in events]

    async def get_author_timeline(
        self,
        author_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TimelineEventOut]:
        events = await self.repository.get_author_timeline(author_id, limit=limit, offset=offset)
        return [self.to_event_out(e) for e in events]

    async def get_admin_author_timeline(
        self,
        author_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TimelineEventOut]:
        events = await self.repository.get_admin_author_timeline(author_id, limit=limit, offset=offset)
        return [self.to_event_out(e) for e in events]
