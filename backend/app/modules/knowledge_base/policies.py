"""BookLeaf Publishing Operational Policy Knowledge Base & Guidelines.
Directly aligns with BookLeaf Technical Assignment Brief pages 5-7.
"""

COMPANY_OVERVIEW = """
BookLeaf Company Overview:
- BookLeaf Publishing is a self-publishing company operating in India and the US.
- Packages offered: Standard Free (no upfront cost) and Bestseller Breakthrough (premium, paid package with marketing and distribution add-ons).
- Services: Cover design, typesetting, ISBN assignment, printing, distribution, and royalty management.
- Printing Facility: In-house printing facility and warehouse are located in Delhi. Also works with print partners including Repro India and Epitome Books.
"""

ROYALTY_POLICY = """
BookLeaf Royalty Policy:
- 80/20 Royalty Split: 80% of net profit per book goes to author, 20% to BookLeaf.
- Net Profit Calculation: Net profit = MRP minus printing cost, platform commission (Amazon/Flipkart), and shipping charges.
- Payout Schedule: Royalties are calculated quarterly and paid within 45 days of the quarter ending.
- Minimum Threshold: Minimum payout threshold is ₹1,000. Accumulated royalties below this roll over to the next quarter.
- Payment Mode: Payouts are made via bank transfer to the account linked in the author dashboard.
- Royalty Breakdown: Authors can view a detailed breakdown in their dashboard showing sales per platform.
"""

ISBN_POLICY = """
BookLeaf ISBN Policy:
- Every book published through BookLeaf receives a unique ISBN assigned by BookLeaf registered under BookLeaf's publisher imprint.
- If an author wants an ISBN under their own imprint, they must obtain it independently.
- If an author reports an ISBN error (duplicate, wrong book linked), treat as HIGH PRIORITY and escalate to the production team immediately with a 48-hour resolution timeline.
"""

PRINTING_QUALITY_POLICY = """
BookLeaf Printing & Quality Policy:
- In-house Delhi printing handles most orders; overflow or specific formats go to Repro India or Epitome Books.
- Standard turnaround: 5–7 business days from order confirmation.
- Quality issues (misprints, binding defects, color inconsistency): Apologize sincerely, ask for photos of the defective copies, and arrange a free reprint once verified (5–7 business days).
"""

DISTRIBUTION_POLICY = """
BookLeaf Distribution & Availability Policy:
- Channels: Amazon India, Flipkart, Amazon US, Amazon UK, and BookLeaf Store.
- Listing Turnaround: New listings typically go live within 7–10 business days after publication is complete.
- Stock Sync: If a book shows "Currently Unavailable" on a platform, it usually indicates a stock sync issue. BookLeaf operations can trigger a re-sync within 24–48 hours.
"""

PRODUCTION_STAGES_POLICY = """
BookLeaf Production Stages & Lifecycle:
- Exact Stages: Manuscript Received -> Editing (if opted) -> Cover Design -> Typesetting -> Proofreading -> ISBN Assignment -> Printing -> Distribution Setup -> Published & Live.
- Authors are updated at each stage via email. Delays typically happen at Cover Design (waiting for author approval) or Proofreading (revision rounds).
- If delayed, be transparent without blaming the author; frame it collaboratively with specific updated timelines.
"""

COMMUNICATION_TONE_GUIDELINES = """
BookLeaf Communication Tone Guidelines:
1. Empathetic and professional: Authors are our partners, not customers to be managed.
2. Acknowledge the author's concern before jumping to solutions.
3. Be specific: Include actual numbers, dates, and statuses wherever possible rather than vague reassurances.
4. Own mistakes directly: If something is BookLeaf's fault (delayed royalties, ISBN error), own it directly. No corporate deflection.
5. Escalation timelines: If the issue requires investigation, give a clear timeline ("Our team will look into this and get back to you within 48 hours").
6. Next step: Always end with a clear next step for the author and/or BookLeaf team.
"""

POLICIES = {
    "ROYALTY_PAYMENT": f"{ROYALTY_POLICY}\n{COMMUNICATION_TONE_GUIDELINES}",
    "ISBN_METADATA": f"{ISBN_POLICY}\n{COMMUNICATION_TONE_GUIDELINES}",
    "PRINTING_QUALITY": f"{PRINTING_QUALITY_POLICY}\n{COMMUNICATION_TONE_GUIDELINES}",
    "DISTRIBUTION_AVAILABILITY": f"{DISTRIBUTION_POLICY}\n{COMMUNICATION_TONE_GUIDELINES}",
    "BOOK_STATUS": f"{PRODUCTION_STAGES_POLICY}\n{COMMUNICATION_TONE_GUIDELINES}",
    "GENERAL": f"{COMPANY_OVERVIEW}\n{COMMUNICATION_TONE_GUIDELINES}",
}


def get_relevant_policies(category: str = None) -> str:
    if category and category in POLICIES:
        return POLICIES[category]
    return "\n\n".join([
        COMPANY_OVERVIEW,
        ROYALTY_POLICY,
        ISBN_POLICY,
        PRINTING_QUALITY_POLICY,
        DISTRIBUTION_POLICY,
        PRODUCTION_STAGES_POLICY,
        COMMUNICATION_TONE_GUIDELINES,
    ])
