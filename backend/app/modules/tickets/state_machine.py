from typing import Dict, Set
from app.core.errors import InvalidTransitionException

VALID_TRANSITIONS: Dict[str, Set[str]] = {
    "OPEN": {"IN_PROGRESS", "RESOLVED", "CLOSED"},
    "IN_PROGRESS": {"RESOLVED", "CLOSED"},
    "RESOLVED": {"IN_PROGRESS", "CLOSED"},
    "CLOSED": {"IN_PROGRESS"},  # Reopening
}


def validate_status_transition(current_status: str, new_status: str) -> None:
    if current_status == new_status:
        return

    allowed = VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise InvalidTransitionException(
            f"Cannot transition ticket from '{current_status}' to '{new_status}'. Allowed transitions: {list(allowed)}",
            code="INVALID_STATUS_TRANSITION",
        )
