from typing import List, Optional
from fastapi import APIRouter, Depends, status, Request, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.dependencies import require_author, get_current_user
from app.db.models import Author, User
from app.modules.authors.service import AuthorService
from app.modules.authors.schemas import AuthorProfileResponse
from app.modules.books.service import BookService
from app.modules.books.schemas import BookListResponse, BookDetailResponse, BookOut
from app.modules.tickets.service import TicketService
from app.modules.tickets.schemas import (
    CreateTicketRequest,
    CreateMessageRequest,
    TicketResponse,
)
from app.modules.timeline.service import TicketEventService
from app.modules.timeline.schemas import AuthorTimelineResponse
from app.modules.notifications.websocket_manager import manager
from app.workers.tasks.ticket_tasks import dispatch_ticket_support_assist
from app.core.rate_limit import limiter
from app.core.errors import NotFoundException, ForbiddenException
from app.core.logging import logger

router = APIRouter(prefix="/author", tags=["Author Operations"])


@router.get("/profile", response_model=AuthorProfileResponse)
async def get_profile(
    author: Author = Depends(require_author),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthorService(db)
    profile = await service.get_author_dashboard_profile(author, current_user)
    return AuthorProfileResponse(success=True, data=profile)


@router.get("/books", response_model=BookListResponse)
async def get_books(
    author: Author = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    service = BookService(db)
    books = await service.get_my_books(author.id)
    return BookListResponse(success=True, data=[BookOut.model_validate(b) for b in books])


@router.get("/books/{book_id}", response_model=BookDetailResponse)
async def get_book_detail(
    book_id: str,
    author: Author = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    service = BookService(db)
    book = await service.get_my_book_detail(book_id, author.id)
    return BookDetailResponse(success=True, data=BookOut.model_validate(book))


@router.get("/tickets")
async def get_tickets(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    author: Author = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    tickets = await service.repository.get_author_tickets(author.id)
    paged = tickets[offset : offset + limit]
    return {
        "success": True,
        "data": [service.to_ticket_out(t).model_dump() for t in paged],
        "total": len(tickets),
        "limit": limit,
        "offset": offset,
    }


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_ticket(
    request: Request,
    response: Response,
    req: CreateTicketRequest,
    author: Author = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    ticket = await service.create_author_ticket(author, req)

    # Real-time notification broadcast
    await manager.broadcast_event(
        event_name="ticket.created",
        ticket_id=str(ticket.id),
        author_user_id=author.user_id,
        payload={
            "ticketNumber": ticket.ticket_number,
            "subject": ticket.subject,
            "status": ticket.status,
            "authorName": author.pen_name,
            "createdAt": ticket.created_at.isoformat(),
        },
    )

    # Dispatch to Celery background queue (with resilient fallback to async in-process)
    dispatch_ticket_support_assist(ticket.id)

    return {
        "success": True,
        "data": {
            "id": str(ticket.id),
            "ticketNumber": ticket.ticket_number,
            "status": ticket.status,
            "category": ticket.category,
            "priority": ticket.priority,
            "createdAt": ticket.created_at.isoformat(),
        },
    }


@router.get("/tickets/{ticket_id}")
async def get_ticket_detail(
    ticket_id: str,
    author: Author = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    detail = await service.get_author_ticket_detail(ticket_id, author.id)
    return {"success": True, "data": detail.model_dump()}


@router.get("/tickets/{ticket_id}/timeline")
async def get_ticket_timeline(
    ticket_id: str,
    author: Author = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    ticket = await ticket_service.repository.get_by_identifier(ticket_id)
    if not ticket:
        raise NotFoundException("Ticket not found", code="TICKET_NOT_FOUND")
    if ticket.author_id != author.id:
        raise ForbiddenException("You are not authorized to view this ticket.", code="TICKET_NOT_ACCESSIBLE")

    event_service = TicketEventService(db)
    events = await event_service.get_ticket_timeline(ticket.id, include_internal=False)
    return {"success": True, "data": events}



@router.post("/tickets/{ticket_id}/messages")
@limiter.limit("40/minute")
async def post_message(
    request: Request,
    response: Response,
    ticket_id: str,
    req: CreateMessageRequest,
    author: Author = Depends(require_author),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    msg = await service.add_message(
        identifier=ticket_id,
        current_user=current_user,
        message_text=req.message,
        author_id=author.id,
    )

    await manager.broadcast_event(
        event_name="ticket.message.created",
        ticket_id=ticket_id,
        author_user_id=author.user_id,
        payload={
            "id": str(msg.id),
            "senderRole": "AUTHOR",
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


@router.get("/timeline", response_model=AuthorTimelineResponse)
async def get_author_timeline(
    author: Author = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    event_service = TicketEventService(db)
    events = await event_service.get_author_timeline(author.id)
    return AuthorTimelineResponse(success=True, data=events)
