from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import json
import re
import google.generativeai as genai
from app.core.config import settings
from app.core.logging import logger
from app.modules.support_assist.schemas import (
    ClassificationResult,
    PrioritizationResult,
    DraftResponseResult,
)


class AIProvider(ABC):
    @abstractmethod
    async def classify_ticket(self, subject: str, description: str, book_title: Optional[str]) -> ClassificationResult:
        pass

    @abstractmethod
    async def prioritize_ticket(self, subject: str, description: str, category: Optional[str]) -> PrioritizationResult:
        pass

    @abstractmethod
    async def generate_response_draft(
        self,
        ticket_subject: str,
        ticket_description: str,
        author_name: str,
        book_info: Dict[str, Any],
        recent_messages: list,
        policy_context: str,
    ) -> DraftResponseResult:
        pass


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def classify_ticket(self, subject: str, description: str, book_title: Optional[str]) -> ClassificationResult:
        prompt = f"""
You are an operational assistant for BookLeaf Publishing. Classify this support ticket into exactly one category:
ROYALTY_PAYMENT, ISBN_METADATA, PRINTING_QUALITY, DISTRIBUTION_AVAILABILITY, BOOK_STATUS, GENERAL.

Ticket Subject: {subject}
Ticket Description: {description}
Referenced Book: {book_title or 'None'}

Return ONLY a valid JSON object with keys:
- "category": (one of the 6 exact names above)
- "confidence": (float between 0.0 and 1.0)
- "reasoning": (short explanation)
"""
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return ClassificationResult(**data)
        raise ValueError("Could not parse JSON response from Gemini")

    async def prioritize_ticket(self, subject: str, description: str, category: Optional[str]) -> PrioritizationResult:
        prompt = f"""
You are an operational assistant for BookLeaf Publishing. Determine the operational priority for this ticket:
CRITICAL, HIGH, MEDIUM, LOW.

Guidelines:
- CRITICAL: Severe printing batch errors, missing urgent publication deadlines, major unresolved disputes.
- HIGH: Pending overdue royalties, missing sales records, author blocked.
- MEDIUM: Standard timeline queries, metadata update requests.
- LOW: General compliments, non-urgent information requests.

Ticket Subject: {subject}
Ticket Description: {description}
Category: {category or 'GENERAL'}

Return ONLY a valid JSON object with keys:
- "priority": (one of CRITICAL, HIGH, MEDIUM, LOW)
- "confidence": (float between 0.0 and 1.0)
- "reasoning": (short explanation)
"""
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return PrioritizationResult(**data)
        raise ValueError("Could not parse JSON response from Gemini")

    async def generate_response_draft(
        self,
        ticket_subject: str,
        ticket_description: str,
        author_name: str,
        book_info: Dict[str, Any],
        recent_messages: list,
        policy_context: str,
    ) -> DraftResponseResult:
        prompt = f"""
You are drafting an internal support response for BookLeaf Publishing operations team.
CRITICAL SAFETY RULES:
1. NEVER invent payment dates, refund amounts, or unverified operational statuses.
2. If data is unknown or requires internal finance check, explicitly note that manual verification is needed.
3. Adhere strictly to BookLeaf publishing policies.
4. Maintain a warm, respectful, professional publishing tone.

Author Name: {author_name}
Subject: {ticket_subject}
Description: {ticket_description}
Book Details: {json.dumps(book_info, default=str)}
Relevant Policy Context:
{policy_context}

Recent Messages:
{json.dumps(recent_messages, default=str)}

Return ONLY a valid JSON object with keys:
- "draft_response": "Polite draft addressed to {author_name}...",
- "suggested_action": "Check finance ledger / escalate to printing coordinator / etc.",
- "requires_manual_verification": boolean,
- "verification_notes": "Note what the admin must verify before sending, if any"
"""
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return DraftResponseResult(**data)
        raise ValueError("Could not parse JSON response from Gemini")


class MockFallbackProvider(AIProvider):
    """
    Deterministic rule-based fallback provider when Gemini API key is unconfigured or offline.
    Guarantees that the support portal never halts or errors out.
    """
    async def classify_ticket(self, subject: str, description: str, book_title: Optional[str]) -> ClassificationResult:
        text = (subject + " " + description).lower()
        if any(w in text for w in ["royalty", "payment", "payout", "paid", "earning", "money", "rupee", "bank"]):
            return ClassificationResult(category="ROYALTY_PAYMENT", confidence=0.88, reasoning="Matched royalty/payment keywords")
        elif any(w in text for w in ["isbn", "barcode", "metadata", "title change", "synopsis"]):
            return ClassificationResult(category="ISBN_METADATA", confidence=0.85, reasoning="Matched ISBN/metadata keywords")
        elif any(w in text for w in ["print", "binding", "paper", "quality", "damaged", "cover page", "misprint"]):
            return ClassificationResult(category="PRINTING_QUALITY", confidence=0.87, reasoning="Matched print/quality keywords")
        elif any(w in text for w in ["amazon", "flipkart", "distribution", "stock", "out of stock", "availability"]):
            return ClassificationResult(category="DISTRIBUTION_AVAILABILITY", confidence=0.84, reasoning="Matched distribution keywords")
        elif any(w in text for w in ["status", "production", "stage", "proof", "typesetting"]):
            return ClassificationResult(category="BOOK_STATUS", confidence=0.82, reasoning="Matched book production status keywords")
        else:
            return ClassificationResult(category="GENERAL", confidence=0.75, reasoning="Default general inquiry")

    async def prioritize_ticket(self, subject: str, description: str, category: Optional[str]) -> PrioritizationResult:
        text = (subject + " " + description).lower()
        if any(w in text for w in ["urgent", "immediately", "severe", "legal", "wrong print", "damaged copies"]):
            return PrioritizationResult(priority="HIGH", confidence=0.85, reasoning="Contains urgency or severe issue markers")
        elif category in ("ROYALTY_PAYMENT", "PRINTING_QUALITY"):
            return PrioritizationResult(priority="HIGH", confidence=0.80, reasoning="Financial or manufacturing issue")
        elif category in ("DISTRIBUTION_AVAILABILITY", "BOOK_STATUS"):
            return PrioritizationResult(priority="MEDIUM", confidence=0.75, reasoning="Operational inquiry")
        else:
            return PrioritizationResult(priority="LOW", confidence=0.70, reasoning="Standard inquiry")

    async def generate_response_draft(
        self,
        ticket_subject: str,
        ticket_description: str,
        author_name: str,
        book_info: Dict[str, Any],
        recent_messages: list,
        policy_context: str,
    ) -> DraftResponseResult:
        book_title = book_info.get("title", "your book")
        return DraftResponseResult(
            draft_response=(
                f"Dear {author_name},\n\n"
                f"Thank you for contacting BookLeaf Author Support regarding '{ticket_subject}'.\n\n"
                f"We are actively reviewing this with our operations team concerning '{book_title}'. "
                "Per BookLeaf policy, our team is cross-referencing your records to provide an accurate update. "
                "We appreciate your patience and will keep you informed right here.\n\n"
                "Warm regards,\nBookLeaf Author Operations"
            ),
            suggested_action="Review author ledger or production dashboard before replying",
            requires_manual_verification=True,
            verification_notes="Verify bank status or manufacturing queue before finalizing response",
        )


def get_ai_provider() -> AIProvider:
    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
        try:
            return GeminiProvider(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
        except Exception as e:
            logger.warning(f"Failed to initialize GeminiProvider, using fallback provider: {e}")
            return MockFallbackProvider()
    return MockFallbackProvider()
