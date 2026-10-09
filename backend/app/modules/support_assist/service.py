import time
from typing import Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models import Ticket, Book, Author, User, TicketMessage, SupportAssistRun
from app.modules.support_assist.provider import get_ai_provider, AIProvider, MockFallbackProvider
from app.modules.support_assist.schemas import (
    ClassificationResult,
    PrioritizationResult,
    DraftResponseResult,
)
from app.modules.knowledge_base.policies import get_relevant_policies
from app.modules.timeline.service import TicketEventService
from app.core.logging import logger


class SupportAssistService:
    def __init__(self, db: AsyncSession, provider: Optional[AIProvider] = None):
        self.db = db
        self.provider = provider or get_ai_provider()
        self.event_service = TicketEventService(db)

    async def process_ticket_async(self, ticket_id: uuid.UUID) -> None:
        """
        Background task helper: classifies and prioritizes ticket without blocking ticket creation.
        """
        query = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(selectinload(Ticket.book), selectinload(Ticket.author))
        )
        res = await self.db.execute(query)
        ticket = res.scalar_one_or_none()
        if not ticket:
            return

        book_title = ticket.book.title if ticket.book else None

        # 1. Classification
        start_time = time.time()
        try:
            class_res = await self.provider.classify_ticket(ticket.subject, ticket.description, book_title)
            latency = int((time.time() - start_time) * 1000)

            # Store in ticket if not overridden by admin
            if ticket.category_source != "ADMIN":
                ticket.system_category = class_res.category
                ticket.system_category_confidence = class_res.confidence
                ticket.category_source = "SYSTEM"
                if not ticket.category:
                    ticket.category = class_res.category

            # Record SupportAssistRun
            run = SupportAssistRun(
                ticket_id=ticket.id,
                task_type="CLASSIFICATION",
                provider=self.provider.__class__.__name__,
                model=getattr(self.provider, "model_name", "local-rules"),
                input_payload={"subject": ticket.subject, "description": ticket.description, "book": book_title},
                output_payload=class_res.model_dump(),
                status="SUCCESS",
                latency_ms=latency,
            )
            self.db.add(run)

            # Record timeline event
            await self.event_service.record_event(
                ticket_id=ticket.id,
                event_type="CATEGORY_CHANGED",
                actor_user_id=None,
                metadata={
                    "category": class_res.category,
                    "confidence": class_res.confidence,
                    "source": "SYSTEM",
                },
            )
        except Exception as e:
            logger.error(f"SupportAssist classification failed for ticket {ticket_id}: {e}")
            run = SupportAssistRun(
                ticket_id=ticket.id,
                task_type="CLASSIFICATION",
                provider=self.provider.__class__.__name__,
                model=getattr(self.provider, "model_name", "local-rules"),
                input_payload={"subject": ticket.subject},
                status="FAILED",
                error_message=str(e),
            )
            self.db.add(run)

        # 2. Prioritization
        start_time = time.time()
        try:
            prio_res = await self.provider.prioritize_ticket(ticket.subject, ticket.description, ticket.category)
            latency = int((time.time() - start_time) * 1000)

            if ticket.priority_source != "ADMIN":
                ticket.system_priority = prio_res.priority
                ticket.system_priority_confidence = prio_res.confidence
                ticket.priority_source = "SYSTEM"
                if not ticket.priority:
                    ticket.priority = prio_res.priority

            run_prio = SupportAssistRun(
                ticket_id=ticket.id,
                task_type="PRIORITIZATION",
                provider=self.provider.__class__.__name__,
                model=getattr(self.provider, "model_name", "local-rules"),
                input_payload={"subject": ticket.subject, "category": ticket.category},
                output_payload=prio_res.model_dump(),
                status="SUCCESS",
                latency_ms=latency,
            )
            self.db.add(run_prio)

            await self.event_service.record_event(
                ticket_id=ticket.id,
                event_type="PRIORITY_CHANGED",
                actor_user_id=None,
                metadata={
                    "priority": prio_res.priority,
                    "confidence": prio_res.confidence,
                    "source": "SYSTEM",
                },
            )
        except Exception as e:
            logger.error(f"SupportAssist prioritization failed for ticket {ticket_id}: {e}")
            run_prio = SupportAssistRun(
                ticket_id=ticket.id,
                task_type="PRIORITIZATION",
                provider=self.provider.__class__.__name__,
                model=getattr(self.provider, "model_name", "local-rules"),
                input_payload={"subject": ticket.subject},
                status="FAILED",
                error_message=str(e),
            )
            self.db.add(run_prio)
        # 3. Deterministic Duplicate Detection & Event Logging
        try:
            from app.modules.relationships.service import RelationshipService
            rel_svc = RelationshipService(self.db)
            rel_data = await rel_svc.get_duplicate_candidates_and_confirmed(ticket)
            candidates = rel_data.get("candidates", [])
            if candidates:
                top_cand = candidates[0]
                if top_cand.similarity >= 0.65:
                    await self.event_service.record_event(
                        ticket_id=ticket.id,
                        event_type="DUPLICATE_DETECTED",
                        actor_user_id=None,
                        metadata={
                            "candidate_ticket_id": str(top_cand.ticket_id),
                            "candidate_ticket_number": top_cand.ticket_number,
                            "score": top_cand.similarity,
                            "signals": top_cand.signals.model_dump(),
                        },
                    )
        except Exception as e:
            logger.warning(f"Duplicate candidate event generation skipped for ticket {ticket_id}: {e}")

        await self.db.commit()

    async def generate_response_draft(self, ticket: Ticket) -> DraftResponseResult:
        """
        Generates an assistive draft response for an admin reviewing the ticket workspace.
        """
        # Load related book and author details
        query = (
            select(Ticket)
            .where(Ticket.id == ticket.id)
            .options(
                selectinload(Ticket.book),
                selectinload(Ticket.author).selectinload(Author.user),
                selectinload(Ticket.messages),
            )
        )
        res = await self.db.execute(query)
        full_ticket = res.scalar_one_or_none() or ticket

        author_name = full_ticket.author.pen_name if full_ticket.author else "Author"
        book_info = {}
        if full_ticket.book:
            book_info = {
                "title": full_ticket.book.title,
                "isbn": full_ticket.book.isbn,
                "status": full_ticket.book.status,
                "royalty_pending": str(full_ticket.book.royalty_pending),
                "print_partner": full_ticket.book.print_partner,
            }

        recent_msgs = []
        for m in (full_ticket.messages or [])[-5:]:
            recent_msgs.append({"sender": m.sender_role, "text": m.message})

        policy_text = get_relevant_policies(full_ticket.category)

        start_time = time.time()
        try:
            draft_res = await self.provider.generate_response_draft(
                ticket_subject=full_ticket.subject,
                ticket_description=full_ticket.description,
                author_name=author_name,
                book_info=book_info,
                recent_messages=recent_msgs,
                policy_context=policy_text,
            )
            latency = int((time.time() - start_time) * 1000)

            run = SupportAssistRun(
                ticket_id=full_ticket.id,
                task_type="RESPONSE_DRAFT",
                provider=self.provider.__class__.__name__,
                model=getattr(self.provider, "model_name", "local-rules"),
                input_payload={"subject": full_ticket.subject, "author": author_name},
                output_payload=draft_res.model_dump(),
                status="SUCCESS",
                latency_ms=latency,
            )
            self.db.add(run)
            await self.db.commit()
            return draft_res
        except Exception as e:
            logger.error(f"SupportAssist response draft generation error: {e}")
            fallback = MockFallbackProvider()
            draft_res = await fallback.generate_response_draft(
                ticket_subject=full_ticket.subject,
                ticket_description=full_ticket.description,
                author_name=author_name,
                book_info=book_info,
                recent_messages=recent_msgs,
                policy_context=policy_text,
            )
            return draft_res
