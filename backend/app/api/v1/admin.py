from typing import Optional, List
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.dependencies import require_admin
from app.db.models import User
from app.modules.tickets.service import TicketService
from app.modules.tickets.schemas import (
    UpdateStatusRequest,
    UpdateCategoryRequest,
    UpdatePriorityRequest,
    AssignTicketRequest,
    CreateMessageRequest,
    CreateInternalNoteRequest,
    TicketOut,
    TicketMessageOut,
    TicketInternalNoteOut,
)
from app.modules.timeline.service import TicketEventService
from app.modules.timeline.schemas import TimelineEventOut
from app.modules.relationships.service import RelationshipService
from app.modules.relationships.schemas import (
    DuplicateRelationshipsResponse,
    LinkDuplicateRequest,
    UnlinkDuplicateRequest,
)
from app.modules.support_assist.service import SupportAssistService
from app.modules.notifications.websocket_manager import manager
from app.core.errors import NotFoundException

router = APIRouter(prefix="/admin", tags=["Admin Operations"], dependencies=[Depends(require_admin)])


@router.get("/tickets")
async def get_admin_queue(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[uuid.UUID] = Query(None),
    author_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("recent"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    tickets, total_count = await service.repository.get_admin_queue(
        status=status,
        category=category,
        priority=priority,
        assignee_id=assignee_id,
        author_id=author_id,
        search=search,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    return {
        "success": True,
        "data": {
            "total": total_count,
            "items": [service.to_ticket_out(t).model_dump() for t in tickets],
        },
    }


@router.get("/tickets/{ticket_id}")
async def get_admin_ticket_workspace(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    ticket = await service.get_admin_ticket_detail(ticket_id)

    # Full workspace bundle
    ticket_out = service.to_ticket_out(ticket).model_dump()

    # Internal notes (strictly accessible only here!)
    notes_out = []
    for n in ticket.internal_notes:
        admin_name = n.admin.full_name if n.admin else None
        notes_out.append(
            TicketInternalNoteOut(
                id=n.id,
                admin_user_id=n.admin_user_id,
                admin_name=admin_name,
                note=n.note,
                created_at=n.created_at,
            ).model_dump()
        )
    ticket_out["internalNotes"] = notes_out

    return {"success": True, "data": ticket_out}


@router.get("/tickets/{ticket_id}/timeline")
async def get_ticket_timeline(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    ticket = await service.get_admin_ticket_detail(ticket_id)
    event_service = TicketEventService(db)
    events = await event_service.get_ticket_timeline(ticket.id, include_internal=True)
    return {"success": True, "data": [e.model_dump() for e in events]}


@router.get("/tickets/{ticket_id}/relationships", response_model=DuplicateRelationshipsResponse)
async def get_ticket_relationships(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    ticket = await service.get_admin_ticket_detail(ticket_id)
    rel_service = RelationshipService(db)
    res = await rel_service.get_duplicate_candidates_and_confirmed(ticket)
    return DuplicateRelationshipsResponse(success=True, data=res)


@router.patch("/tickets/{ticket_id}/status")
async def update_status(
    ticket_id: str,
    req: UpdateStatusRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    updated = await service.update_status(ticket_id, req.status, current_admin)

    # Broadcast
    author_user_id = updated.author.user_id if updated.author else None
    await manager.broadcast_event(
        event_name="ticket.status.updated",
        ticket_id=str(updated.id),
        author_user_id=author_user_id,
        payload={"ticketNumber": updated.ticket_number, "status": updated.status},
    )

    return {"success": True, "data": service.to_ticket_out(updated).model_dump()}


@router.patch("/tickets/{ticket_id}/category")
async def update_category(
    ticket_id: str,
    req: UpdateCategoryRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    updated = await service.update_category(ticket_id, req.category, current_admin)

    author_user_id = updated.author.user_id if updated.author else None
    await manager.broadcast_event(
        event_name="ticket.category.updated",
        ticket_id=str(updated.id),
        author_user_id=author_user_id,
        payload={"ticketNumber": updated.ticket_number, "category": updated.category},
    )

    return {"success": True, "data": service.to_ticket_out(updated).model_dump()}


@router.patch("/tickets/{ticket_id}/priority")
async def update_priority(
    ticket_id: str,
    req: UpdatePriorityRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    updated = await service.update_priority(ticket_id, req.priority, current_admin)

    author_user_id = updated.author.user_id if updated.author else None
    await manager.broadcast_event(
        event_name="ticket.priority.updated",
        ticket_id=str(updated.id),
        author_user_id=author_user_id,
        payload={"ticketNumber": updated.ticket_number, "priority": updated.priority},
    )

    return {"success": True, "data": service.to_ticket_out(updated).model_dump()}


@router.patch("/tickets/{ticket_id}/assignment")
async def update_assignment(
    ticket_id: str,
    req: AssignTicketRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    updated = await service.update_assignment(ticket_id, req.admin_id, current_admin)

    author_user_id = updated.author.user_id if updated.author else None
    await manager.broadcast_event(
        event_name="ticket.assignment.updated",
        ticket_id=str(updated.id),
        author_user_id=author_user_id,
        payload={"ticketNumber": updated.ticket_number, "assignedAdminId": str(req.admin_id)},
    )

    return {"success": True, "data": service.to_ticket_out(updated).model_dump()}


@router.post("/tickets/{ticket_id}/messages")
async def post_admin_message(
    ticket_id: str,
    req: CreateMessageRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    msg = await service.add_message(
        identifier=ticket_id,
        current_user=current_admin,
        message_text=req.message,
    )

    ticket = await service.get_admin_ticket_detail(ticket_id)
    author_user_id = ticket.author.user_id if ticket.author else None

    await manager.broadcast_event(
        event_name="ticket.message.created",
        ticket_id=str(ticket.id),
        author_user_id=author_user_id,
        payload={
            "id": str(msg.id),
            "senderRole": "ADMIN",
            "message": msg.message,
            "createdAt": msg.created_at.isoformat(),
        },
    )

    return {
        "success": True,
        "data": {
            "id": str(msg.id),
            "senderRole": msg.sender_role,
            "message": msg.message,
            "createdAt": msg.created_at.isoformat(),
        },
    }


@router.post("/tickets/{ticket_id}/internal-notes")
async def post_internal_note(
    ticket_id: str,
    req: CreateInternalNoteRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    note = await service.add_internal_note(
        identifier=ticket_id,
        admin_user=current_admin,
        note_text=req.note,
    )

    return {
        "success": True,
        "data": {
            "id": str(note.id),
            "adminName": current_admin.full_name,
            "note": note.note,
            "createdAt": note.created_at.isoformat(),
        },
    }


@router.post("/tickets/{ticket_id}/draft-response")
async def generate_draft_response(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    ticket = await service.get_admin_ticket_detail(ticket_id)
    support_service = SupportAssistService(db)
    draft_result = await support_service.generate_response_draft(ticket)
    return {"success": True, "data": draft_result.model_dump()}


@router.post("/tickets/{ticket_id}/link-duplicate")
async def link_duplicate(
    ticket_id: str,
    req: LinkDuplicateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    source_ticket = await service.get_admin_ticket_detail(ticket_id)
    target_ticket = await service.get_admin_ticket_detail(req.target_ticket_id)

    rel_service = RelationshipService(db)
    rel = await rel_service.link_duplicate(source_ticket, target_ticket, current_admin)

    return {
        "success": True,
        "message": f"Linked ticket {source_ticket.ticket_number} as duplicate of {target_ticket.ticket_number}",
        "data": {"relationshipId": str(rel.id)},
    }


@router.post("/tickets/{ticket_id}/unlink-duplicate")
async def unlink_duplicate(
    ticket_id: str,
    req: UnlinkDuplicateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    source_ticket = await service.get_admin_ticket_detail(ticket_id)
    target_ticket = await service.get_admin_ticket_detail(req.target_ticket_id)

    rel_service = RelationshipService(db)
    await rel_service.unlink_duplicate(source_ticket, target_ticket, current_admin)

    return {
        "success": True,
        "message": f"Unlinked duplicate relationship between {source_ticket.ticket_number} and {target_ticket.ticket_number}",
    }


@router.post("/tickets/{ticket_id}/confirm-not-duplicate")
async def confirm_not_duplicate(
    ticket_id: str,
    req: LinkDuplicateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    source_ticket = await service.get_admin_ticket_detail(ticket_id)
    target_ticket = await service.get_admin_ticket_detail(req.target_ticket_id)

    rel_service = RelationshipService(db)
    await rel_service.confirm_not_duplicate(source_ticket, target_ticket, current_admin)

    return {
        "success": True,
        "message": f"Confirmed candidate {target_ticket.ticket_number} is not a duplicate",
    }


@router.get("/authors/{author_id}/timeline")
async def get_admin_author_timeline(
    author_id: str,
    db: AsyncSession = Depends(get_db),
):
    event_service = TicketEventService(db)
    try:
        author_uuid = uuid.UUID(author_id)
    except ValueError:
        raise NotFoundException("Invalid author ID", code="INVALID_AUTHOR_ID")

    events = await event_service.get_admin_author_timeline(author_uuid)
    return {"success": True, "data": [e.model_dump() for e in events]}
