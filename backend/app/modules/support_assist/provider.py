from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import asyncio
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
    def __init__(self, api_key: str, model_name: str = "gemini-3.8-flash"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def _generate_content_async(self, prompt: str) -> str:
        """Runs the synchronous SDK call in a worker thread with timeout to avoid freezing asyncio loop."""
        def _call():
            resp = self.model.generate_content(prompt)
            return resp.text.strip()

        return await asyncio.wait_for(asyncio.to_thread(_call), timeout=8.0)

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
        text = await self._generate_content_async(prompt)
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
        text = await self._generate_content_async(prompt)
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
        text = await self._generate_content_async(prompt)
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
        book_title = book_info.get("title", "your title")
        text = (ticket_subject + " " + ticket_description).lower()

        if any(w in text for w in ["royalty", "payment", "payout", "paid", "earning", "money", "rupee"]):
            if any(w in text for w in ["low", "less", "wrong amount", "calculation"]):
                draft = (
                    f"Dear {author_name},\n\n"
                    f"Thank you for reaching out regarding the royalties for '{book_title}'.\n\n"
                    "We completely understand why you'd want clarity on this. At BookLeaf, royalties follow an 80/20 split on net profit—"
                    "calculated as MRP minus actual printing cost, platform commission (Amazon/Flipkart), and shipping charges. "
                    "We want to ensure complete transparency with you. Our operations team is pulling your detailed line-by-line royalty breakdown "
                    "for each retail channel so you can see the exact math.\n\n"
                    "We will share the full sales ledger with you within 48 hours right here in this thread.\n\n"
                    "Warm regards,\nBookLeaf Author Operations Desk"
                )
                action = "Pull line-by-line channel ledger (Amazon/Flipkart/BookLeaf Store) and attach breakdown"
            else:
                draft = (
                    f"Dear {author_name},\n\n"
                    f"Thank you for contacting us regarding your royalty payout for '{book_title}'. We acknowledge how important timely payouts are to you.\n\n"
                    "As per BookLeaf policy, royalties are calculated quarterly and disbursed within 45 days of the quarter ending, "
                    "with a minimum payout threshold of ₹1,000 (accumulated balances below this roll over to the subsequent quarter). "
                    "Our finance desk is verifying your linked bank details and sales reconciliation for the latest cycle.\n\n"
                    "If your payout is overdue or your bank credentials require a re-verification, we will escalate this immediately "
                    "and provide a confirmed resolution within 48 hours.\n\n"
                    "Warm regards,\nBookLeaf Author Operations Desk"
                )
                action = "Check author banking ledger, payout threshold status (₹1,000), and recent remittance run"

        elif any(w in text for w in ["isbn", "barcode", "metadata"]):
            draft = (
                f"Dear {author_name},\n\n"
                f"Thank you for flagging this ISBN/metadata discrepancy regarding '{book_title}'.\n\n"
                "We treat ISBN and catalog metadata issues as high-priority operational items. We have immediately escalated this to our senior production team "
                "to cross-verify the ISBN registered under BookLeaf's publisher imprint against the distributor catalog feeds.\n\n"
                "Our team will resolve the catalog mapping and provide an updated confirmation right here within 48 hours.\n\n"
                "Warm regards,\nBookLeaf Production & Operations Team"
            )
            action = "Escalate to production lead; check Raja Rammohun Roy agency registry and Amazon/Flipkart feed mapping"

        elif any(w in text for w in ["print", "quality", "damaged", "misprint", "binding", "blurry", "pages"]):
            draft = (
                f"Dear {author_name},\n\n"
                f"Please accept our sincere apologies for the print quality issues you experienced with your author copies of '{book_title}'. "
                "This is certainly not the standard of craftsmanship we strive for at BookLeaf.\n\n"
                "Could you please share 2–3 clear photographs of the defective copies (showing the misprint, binding, or cover alignment)? "
                "Once our manufacturing desk verifies the batch defect with our printing facility, BookLeaf will immediately arrange a free reprint "
                "and dispatch replacement copies to you within 5–7 business days.\n\n"
                "We look forward to your photos so we can initiate this right away.\n\n"
                "Warm regards,\nBookLeaf Printing & Quality Desk"
            )
            action = "Request photos of defective copies; prepare free reprint order with Delhi in-house / Repro team"

        elif any(w in text for w in ["unavailable", "stock", "out of stock", "amazon", "flipkart"]):
            draft = (
                f"Dear {author_name},\n\n"
                f"Thank you for letting us know about the availability status of '{book_title}'.\n\n"
                "When a published book shows as 'Currently Unavailable' on Amazon or Flipkart, it typically indicates a temporary channel inventory synchronization issue. "
                "Our distribution desk has triggered an inventory re-sync with the respective platform's publisher operations desk.\n\n"
                "These re-syncs typically update and reflect as live in-stock within 24–48 hours. We are monitoring the listing and will update you as soon as it reflects active.\n\n"
                "Warm regards,\nBookLeaf Distribution Support"
            )
            action = "Trigger distributor stock re-sync with Amazon India / Flipkart publisher desk"

        elif any(w in text for w in ["typesetting", "cover", "proof", "production", "stage", "when will", "status"]):
            draft = (
                f"Dear {author_name},\n\n"
                f"Thank you for checking in on the production progress of '{book_title}'.\n\n"
                "At BookLeaf, every title progresses through our 9-stage pipeline: Manuscript Received → Editing → Cover Design → Typesetting → Proofreading → "
                "ISBN Assignment → Printing → Distribution Setup → Published & Live. We want to ensure we take every care while keeping the timeline tight.\n\n"
                "Our production coordinator is reviewing the exact milestone status for your manuscript. We will update your project tracker and provide a confirmed target completion date within 24 hours.\n\n"
                "Warm regards,\nBookLeaf Production Team"
            )
            action = "Check current manufacturing stage in production tracker and update author"

        else:
            draft = (
                f"Dear {author_name},\n\n"
                f"Thank you for contacting BookLeaf Author Support regarding '{ticket_subject}'.\n\n"
                f"We are actively reviewing your query with our operations team regarding '{book_title}'. "
                "Authors are our valued publishing partners, and we are committed to providing you with clear, accurate information. "
                "Our team is investigating the details and will get back to you with a comprehensive update within 24–48 hours.\n\n"
                "Warm regards,\nBookLeaf Author Operations Desk"
            )
            action = "Review author inquiry and respond within 24 business hours"

        return DraftResponseResult(
            draft_response=draft,
            suggested_action=action,
            requires_manual_verification=True,
            verification_notes="Verify author records against live database ledger before sending",
        )


def get_ai_provider() -> AIProvider:
    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
        try:
            return GeminiProvider(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
        except Exception as e:
            logger.warning(f"Failed to initialize GeminiProvider, using fallback provider: {e}")
            return MockFallbackProvider()
    return MockFallbackProvider()
