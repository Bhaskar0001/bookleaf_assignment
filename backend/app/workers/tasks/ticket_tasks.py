import asyncio
import uuid
from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.modules.support_assist.service import SupportAssistService
from app.core.logging import logger


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def classify_and_prioritize_task(self, ticket_id_str: str):
    logger.info(f"[Celery] Processing classification & prioritization for ticket {ticket_id_str}")
    try:
        ticket_id = uuid.UUID(ticket_id_str)

        async def _run():
            async with AsyncSessionLocal() as session:
                service = SupportAssistService(session)
                await service.process_ticket_async(ticket_id)

        asyncio.run(_run())
        logger.info(f"[Celery] Completed classification & prioritization for {ticket_id_str}")
        return {"status": "SUCCESS", "ticket_id": ticket_id_str}
    except Exception as exc:
        logger.error(f"[Celery] Error in classify_and_prioritize_task: {exc}")
        raise self.retry(exc=exc)
