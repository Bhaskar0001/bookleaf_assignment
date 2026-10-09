import asyncio
import sys
import uuid
from typing import Optional
from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.modules.support_assist.service import SupportAssistService
from app.modules.notifications.websocket_manager import manager

logger = get_task_logger(__name__)


async def _execute_support_assist_async(ticket_id: uuid.UUID) -> dict:
    """
    Executes Support Assist AI classification, prioritization, and duplicate detection
    for a given ticket within a dedicated asynchronous database session.
    """
    async with AsyncSessionLocal() as session:
        service = SupportAssistService(session)
        await service.process_ticket_async(ticket_id)
        
        # Notify active clients via WebSocket if available
        try:
            await manager.broadcast_event(
                event_name="ticket.classified",
                ticket_id=str(ticket_id),
                payload={"ticketId": str(ticket_id), "source": "celery"},
            )
        except Exception as ws_err:
            logger.debug(f"[Celery] WS broadcast notice skipped: {ws_err}")
            
        return {"ticket_id": str(ticket_id), "status": "COMPLETED"}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=15, name="tasks.process_ticket_support_assist")
def process_ticket_support_assist_task(self, ticket_id_str: str) -> dict:
    """
    Celery task that performs AI SupportAssist for the specified ticket ID.
    Retries up to 3 times on transient failures.
    """
    logger.info(f"[Celery Task] Processing SupportAssist for ticket: {ticket_id_str}")
    try:
        ticket_id = uuid.UUID(ticket_id_str)
        result = asyncio.run(_execute_support_assist_async(ticket_id))
        logger.info(f"[Celery Task] Successfully processed SupportAssist for ticket: {ticket_id_str}")
        return result
    except Exception as exc:
        logger.error(f"[Celery Task] Error running SupportAssist for {ticket_id_str}: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10, name="tasks.process_ticket_background")
def process_ticket_background_task(self, ticket_id_str: str) -> dict:
    """
    Celery task for operational background tasks, ticket metrics, and audit tracking.
    """
    logger.info(f"[Celery Task] Executing background operations for ticket: {ticket_id_str}")
    return {"status": "SUCCESS", "ticket_id": ticket_id_str}


def dispatch_ticket_support_assist(ticket_id: uuid.UUID) -> str:
    """
    Dispatches the SupportAssist job.
    If Celery is enabled and the broker is reachable, sends the job to Celery worker queue.
    Otherwise, quickly falls back to an in-process asyncio task so ticket creation never stalls.
    """
    ticket_id_str = str(ticket_id)
    is_testing = settings.APP_ENV == "testing" or "pytest" in sys.modules

    if settings.USE_CELERY and not is_testing:
        try:
            # Fast check if Redis broker is actively accepting connections
            import redis
            r = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=0.2, socket_timeout=0.2)
            r.ping()
            task = process_ticket_support_assist_task.delay(ticket_id_str)
            logger.info(f"Dispatched Celery task {task.id} for ticket {ticket_id_str}")
            return f"celery:{task.id}"
        except Exception as e:
            logger.info(
                f"Celery broker not reachable ({e}); routing task to in-process async worker."
            )
    
    # In-process asynchronous execution fallback
    async def _in_process_fallback():
        try:
            await _execute_support_assist_async(ticket_id)
        except Exception as err:
            logger.error(f"In-process AI assist failed for ticket {ticket_id_str}: {err}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_in_process_fallback())
        return "in_process:asyncio"
    except RuntimeError:
        # No running event loop in caller thread
        asyncio.run(_in_process_fallback())
        return "in_process:sync"
