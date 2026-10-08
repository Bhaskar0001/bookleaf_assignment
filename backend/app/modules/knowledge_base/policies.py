"""BookLeaf Publishing Operational Policy Knowledge Base."""

POLICIES = {
    "ROYALTY_PAYMENT": """
BookLeaf Royalty & Payment Policies:
1. Royalty Calculation: Royalties are computed on Net Received Price (MRP minus retailer discount and printing cost).
2. Payout Cycle: Royalty disbursements occur between the 10th and 15th of each calendar month for sales reconciled in the preceding quarter.
3. Minimum Payout Threshold: The minimum payout threshold is INR 1,000. Balances below INR 1,000 roll over to the subsequent cycle.
4. Payment Verification: Bank details (account number, IFSC, PAN) must be verified in the author portal.
5. Pending Balances: Pending royalties represent reconciled channel sales currently scheduled for the upcoming disbursement run.
Operational Rule: Never promise exact instant payment dates or immediate wire transfers. Direct author to verify banking credentials if payout was returned.
""",
    "ISBN_METADATA": """
BookLeaf ISBN & Metadata Policies:
1. Allocation: A unique 13-digit ISBN is allocated during Stage 4 of production following final manuscript sign-off.
2. Immutability: Once registered with Raja Rammohun Roy National Agency for ISBN, the ISBN, book title, and subtitle cannot be altered.
3. Edition Policy: Substantial revisions (exceeding 25% content change or trim size alteration) require a new edition and separate ISBN registration.
4. Metadata Updates: Minor synopsis, author biography, and category tags can be updated across distributor portals within 3-5 business days.
""",
    "PRINTING_QUALITY": """
BookLeaf Printing & Manufacturing Policies:
1. Print-on-Demand (POD): BookLeaf operates on a high-precision POD model in partnership with Thomson Press, Replika Press, and Manipal Technologies.
2. Turnaround Time: Standard printing turnaround is 5-7 working days from order placement.
3. Quality Standards: Paper stock is 70 GSM natural shade / bond; cover is 300 GSM Art Card with matte or gloss lamination.
4. Defects & Replacements: Any damaged or misprinted copies reported within 7 days of delivery with photographic evidence are replaced free of charge.
""",
    "DISTRIBUTION_AVAILABILITY": """
BookLeaf Distribution & Sales Channels:
1. Retail Platforms: Books are distributed across Amazon India, Flipkart, BookLeaf Direct Bookstore, and international Kindle networks.
2. In-Stock Status: New listings reflect 'Active/In Stock' within 5-10 business days after production completion.
3. Buy Box & Third-Party Sellers: Marketplaces use algorithmic Buy Box rotation; BookLeaf Direct ensures 100% fulfillment guarantee.
4. Out-of-Stock Glitches: Channel inventory synchronization anomalies are escalated directly to platform publisher desks.
""",
    "BOOK_STATUS": """
BookLeaf Production Stages & Lifecycle:
1. Stage 1: Manuscript Submission & Editorial Review (Days 1-7).
2. Stage 2: Typesetting & Interior Formatting (Days 8-15).
3. Stage 3: Cover Design & Proofing (Days 16-22).
4. Stage 4: ISBN Allocation & Author Digital Proof Sign-off (Days 23-28).
5. Stage 5: Print File Master Generation & Channel Ingestion (Days 29-35).
6. Books in Production: For books currently in production, ISBN and official MRP remain unassigned until author proof sign-off.
""",
    "GENERAL": """
BookLeaf General Author Support Guidelines:
1. Professional, transparent, respectful, and supportive publishing guidance.
2. Response turnaround standard: Under 24 business hours for priority requests.
3. Confidentiality: Author royalty statements and contact details are private.
4. Admin Notes: Internal notes are privileged operations notes and must never be relayed to authors.
""",
}


def get_relevant_policies(category: str = None) -> str:
    if category and category in POLICIES:
        return POLICIES[category]
    return "\n\n".join(POLICIES.values())
