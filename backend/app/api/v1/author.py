from typing import List
from fastapi import APIRouter, Depends, status
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
    author: Author = Depends(require_author),
    db: AsyncSession = Depends(get_db),
):
    service = TicketService(db)
    tickets = await service.repository.get_author_tickets(author.id)
    return {
        "success": True,
        "data": [service.to_ticket_out(t).model_dump() for t in tickets],
    }


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(
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


@router.post("/tickets/{ticket_id}/messages")
async def post_message(
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
