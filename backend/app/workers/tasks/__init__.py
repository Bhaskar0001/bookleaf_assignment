from app.workers.tasks.ticket_tasks import (
    process_ticket_support_assist_task,
    process_ticket_background_task,
    dispatch_ticket_support_assist,
)

# Backwards compatibility alias
classify_and_prioritize_task = process_ticket_support_assist_task

__all__ = [
    "process_ticket_support_assist_task",
    "process_ticket_background_task",
    "dispatch_ticket_support_assist",
    "classify_and_prioritize_task",
]
