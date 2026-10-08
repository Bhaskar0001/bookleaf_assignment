from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.models import Ticket, TicketRelationship, User
from app.modules.relationships.repository import RelationshipRepository
from app.modules.relationships.detector import score_candidate
from app.modules.relationships.schemas import (
    DuplicateCandidateOut,
    DuplicateSignals,
    ConfirmedRelationshipOut,
)
from app.modules.timeline.service import TicketEventService
from app.core.errors import NotFoundException, ConflictException, ValidationException


class RelationshipService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = RelationshipRepository(db)
        self.event_service = TicketEventService(db)

    async def get_duplicate_candidates_and_confirmed(
        self,
        ticket: Ticket,
    ) -> Dict[str, Any]:
        """
        Calculates duplicate candidates deterministically and fetches confirmed relationships.
        """
        # 1. Fetch confirmed relationships
        rels = await self.repository.get_relationships_for_ticket(ticket.id)
        confirmed_list: List[ConfirmedRelationshipOut] = []
        linked_ticket_ids = set()

        for r in rels:
            s_num = r.source_ticket.ticket_number if r.source_ticket else None
            t_num = r.target_ticket.ticket_number if r.target_ticket else None
            c_name = r.confirmer.full_name if r.confirmer else None
            confirmed_list.append(
                ConfirmedRelationshipOut(
                    id=r.id,
                    source_ticket_id=r.source_ticket_id,
                    source_ticket_number=s_num,
                    target_ticket_id=r.target_ticket_id,
                    target_ticket_number=t_num,
                    relationship_type=r.relationship_type,
                    detected_by=r.detected_by,
                    confirmed_by_name=c_name,
                    created_at=r.created_at,
                )
            )
            linked_ticket_ids.add(r.source_ticket_id)
            linked_ticket_ids.add(r.target_ticket_id)

        # 2. Find candidate pool: same author, different ticket ID
        query = (
            select(Ticket)
            .where(
                Ticket.author_id == ticket.author_id,
                Ticket.id != ticket.id,
            )
            .order_by(Ticket.created_at.desc())
            .limit(25)
        )
        res = await self.db.execute(query)
        other_tickets = list(res.scalars().all())

        candidates: List[DuplicateCandidateOut] = []
        for other in other_tickets:
            # Skip if already formally linked
            if other.id in linked_ticket_ids:
                continue

            score, reason, signals = score_candidate(
                new_subject=ticket.subject,
                new_description=ticket.description,
                new_book_id=str(ticket.book_id) if ticket.book_id else None,
                cand_subject=other.subject,
                cand_description=other.description,
                cand_book_id=str(other.book_id) if other.book_id else None,
                cand_status=other.status,
                cand_created_at=other.created_at,
            )

            # Keep candidates with meaningful similarity signal
            if score >= 0.40 or (signals["same_book"] and score >= 0.35):
                candidates.append(
                    DuplicateCandidateOut(
                        ticket_id=other.id,
                        ticket_number=other.ticket_number,
                        subject=other.subject,
                        status=other.status,
                        similarity=score,
                        reason=reason,
                        signals=DuplicateSignals(**signals),
                    )
                )

        # Sort candidates descending by similarity score
        candidates.sort(key=lambda c: c.similarity, reverse=True)

        return {
            "candidates": candidates,
            "confirmedRelationships": confirmed_list,
        }

    async def link_duplicate(
        self,
        source_ticket: Ticket,
        target_ticket: Ticket,
        admin_user: User,
    ) -> TicketRelationship:
        if source_ticket.id == target_ticket.id:
            raise ValidationException("A ticket cannot be linked as a duplicate of itself", code="SELF_LINK_INVALID")

        existing = await self.repository.find_existing(source_ticket.id, target_ticket.id, "DUPLICATE")
        if not existing:
            # Also check reverse link
            existing = await self.repository.find_existing(target_ticket.id, source_ticket.id, "DUPLICATE")

        if existing:
            raise ConflictException("A duplicate relationship already exists between these tickets", code="DUPLICATE_RELATION_EXISTS")

        rel = await self.repository.create_relationship(
            source_id=source_ticket.id,
            target_id=target_ticket.id,
            detected_by="SYSTEM",
            confirmed_by=admin_user.id,
            rel_type="DUPLICATE",
        )

        # Record atomic event on source ticket
        await self.event_service.record_event(
            ticket_id=source_ticket.id,
            event_type="DUPLICATE_LINKED",
            actor_user_id=admin_user.id,
            metadata={
                "target_ticket_id": str(target_ticket.id),
                "target_ticket_number": target_ticket.ticket_number,
                "role": "duplicate_of",
            },
        )

        # Record atomic event on target ticket
        await self.event_service.record_event(
            ticket_id=target_ticket.id,
            event_type="DUPLICATE_LINKED",
            actor_user_id=admin_user.id,
            metadata={
                "source_ticket_id": str(source_ticket.id),
                "source_ticket_number": source_ticket.ticket_number,
                "role": "authoritative_for",
            },
        )

        await self.db.commit()
        return rel

    async def unlink_duplicate(
        self,
        source_ticket: Ticket,
        target_ticket: Ticket,
        admin_user: User,
    ) -> None:
        rel = await self.repository.find_existing(source_ticket.id, target_ticket.id, "DUPLICATE")
        if not rel:
            rel = await self.repository.find_existing(target_ticket.id, source_ticket.id, "DUPLICATE")

        if not rel:
            raise NotFoundException("No duplicate relationship exists between these tickets", code="RELATION_NOT_FOUND")

        await self.repository.delete_relationship(rel)

        # Record atomic event on both tickets
        await self.event_service.record_event(
            ticket_id=source_ticket.id,
            event_type="DUPLICATE_UNLINKED",
            actor_user_id=admin_user.id,
            metadata={
                "target_ticket_id": str(target_ticket.id),
                "target_ticket_number": target_ticket.ticket_number,
            },
        )

        await self.event_service.record_event(
            ticket_id=target_ticket.id,
            event_type="DUPLICATE_UNLINKED",
            actor_user_id=admin_user.id,
            metadata={
                "source_ticket_id": str(source_ticket.id),
                "source_ticket_number": source_ticket.ticket_number,
            },
        )

        await self.db.commit()

    async def confirm_not_duplicate(
        self,
        source_ticket: Ticket,
        target_ticket: Ticket,
        admin_user: User,
    ) -> None:
        await self.event_service.record_event(
            ticket_id=source_ticket.id,
            event_type="DUPLICATE_DISMISSED",
            actor_user_id=admin_user.id,
            metadata={
                "candidate_ticket_id": str(target_ticket.id),
                "candidate_ticket_number": target_ticket.ticket_number,
                "note": "Admin confirmed this is not a duplicate issue",
            },
        )
        await self.db.commit()
