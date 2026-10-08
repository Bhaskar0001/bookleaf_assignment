import re
from typing import Set, Tuple, Optional
from datetime import datetime, timezone

STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above",
    "below", "from", "up", "down", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "i", "my", "me", "we", "our", "you",
    "your", "he", "she", "it", "they", "this", "that", "these", "those", "can", "will",
    "just", "should", "not", "no", "of", "off", "over", "under", "again", "further",
}


def normalize_text(text: str) -> str:
    """Normalize text by lowering case, removing punctuation, and stripping whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOP_WORDS]
    return " ".join(tokens)


def get_ngrams(text: str, n: int = 3) -> Set[str]:
    """Generate character n-grams from normalized text."""
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) < n:
        return {clean} if clean else set()
    return {clean[i : i + n] for i in range(len(clean) - n + 1)}


def get_token_set(text: str) -> Set[str]:
    """Generate set of distinct meaningful tokens."""
    return set(normalize_text(text).split())


def calculate_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    if union == 0:
        return 0.0
    return round(intersection / union, 4)


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Combines token-level Jaccard similarity and character trigram similarity."""
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    if norm1 == norm2 and norm1:
        return 1.0

    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())
    token_sim = calculate_jaccard_similarity(tokens1, tokens2)

    trigrams1 = get_ngrams(norm1, 3)
    trigrams2 = get_ngrams(norm2, 3)
    trigram_sim = calculate_jaccard_similarity(trigrams1, trigrams2)

    # Blend token and trigram similarity
    blended = 0.6 * token_sim + 0.4 * trigram_sim
    return round(blended, 4)


def score_candidate(
    new_subject: str,
    new_description: str,
    new_book_id: Optional[str],
    cand_subject: str,
    cand_description: str,
    cand_book_id: Optional[str],
    cand_status: str,
    cand_created_at: datetime,
) -> Tuple[float, str, dict]:
    """
    Deterministic scoring pipeline returning:
    (overall_score, explanation_reason, signals_dict)
    """
    subject_sim = calculate_text_similarity(new_subject, cand_subject)
    desc_sim = calculate_text_similarity(new_description, cand_description)

    same_book = bool(new_book_id and cand_book_id and str(new_book_id) == str(cand_book_id))

    # Recency decay in days
    now = datetime.now(timezone.utc)
    delta_days = max(0, (now - cand_created_at).days)

    # Base text score
    text_score = (subject_sim * 0.60) + (desc_sim * 0.40)

    # Heuristic adjustments
    score = text_score
    if same_book:
        # High confidence signal
        score = min(1.0, score + 0.20)
    
    if cand_status in ("OPEN", "IN_PROGRESS"):
        score = min(1.0, score + 0.05)
    elif cand_status == "RESOLVED" and delta_days <= 14:
        score = min(1.0, score + 0.02)
    elif cand_status == "CLOSED":
        score = max(0.0, score - 0.15)

    score = round(score, 2)

    reason_parts = ["Same author"]
    if same_book:
        reason_parts.append("same book")
    if subject_sim > 0.50:
        reason_parts.append("similar subject")
    elif desc_sim > 0.40:
        reason_parts.append("similar description")

    reason = ", ".join(reason_parts) + f" (status: {cand_status})"

    signals = {
        "same_author": True,
        "same_book": same_book,
        "subject_similarity": subject_sim,
        "description_similarity": desc_sim,
        "existing_status": cand_status,
        "recency_days": delta_days,
    }

    return score, reason, signals
