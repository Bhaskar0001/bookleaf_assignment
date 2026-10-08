from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.db.models import TicketRelationship, Ticket


class RelationshipRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_relationships_for_ticket(self, ticket_id: uuid.UUID) -> List[TicketRelationship]:
        query = (
            select(TicketRelationship)
            .where(
                or_(
                    TicketRelationship.source_ticket_id == ticket_id,
                    TicketRelationship.target_ticket_id == ticket_id,
                )
            )
            .options(
                selectinload(TicketRelationship.source_ticket),
                selectinload(TicketRelationship.target_ticket),
                selectinload(TicketRelationship.confirmer),
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_existing(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        rel_type: str = "DUPLICATE",
    ) -> Optional[TicketRelationship]:
        query = select(TicketRelationship).where(
            TicketRelationship.source_ticket_id == source_id,
            TicketRelationship.target_ticket_id == target_id,
            TicketRelationship.relationship_type == rel_type,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_relationship(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        detected_by: str = "SYSTEM",
        confirmed_by: Optional[uuid.UUID] = None,
        rel_type: str = "DUPLICATE",
    ) -> TicketRelationship:
        rel = TicketRelationship(
            source_ticket_id=source_id,
            target_ticket_id=target_id,
            relationship_type=rel_type,
            detected_by=detected_by,
            confirmed_by=confirmed_by,
        )
        self.db.add(rel)
        return rel

    async def delete_relationship(self, rel: TicketRelationship) -> None:
        await self.db.delete(rel)
