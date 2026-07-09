import re
import unicodedata


def clean_text(text: str) -> str:
    """Remove OCR artifacts and normalize whitespace."""
    if not text:
        return ""
    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)
    # Remove null bytes and control chars (except newlines/tabs)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces (but not newlines) to single space
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def truncate_for_llm(text: str, max_chars: int = 100_000) -> str:
    """
    Truncate text to fit within LLM context.
    Gemini 1.5 Flash: 1M token context — very generous.
    100K chars ≈ 25K tokens, well within limits.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[Document truncated — showing first portion]"


def extract_dates(text: str) -> list[str]:
    """Extract date strings from text using multiple patterns."""
    patterns = [
        r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b",           # 12/31/2024
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4}\b",  # 12 Jan 2024
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b",  # January 12, 2024
        r"\b\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\b",                  # 2024-12-31
    ]
    dates = []
    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(found)
    return list(dict.fromkeys(dates))  # deduplicate, preserve order


def extract_amounts(text: str) -> list[str]:
    """Extract monetary amounts from text."""
    patterns = [
        r"[$£€₹¥₩]\s*[\d,]+(?:\.\d{1,2})?",      # $1,234.56
        r"[\d,]+(?:\.\d{1,2})?\s*(?:USD|EUR|GBP|INR|AED)",  # 1234.56 USD
        r"(?:Rs\.?|INR)\s*[\d,]+(?:\.\d{1,2})?",   # Rs. 1234
    ]
    amounts = []
    for pattern in patterns:
        found = re.findall(pattern, text)
        amounts.extend(found)
    return list(dict.fromkeys(amounts))


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from text."""
    pattern = r"https?://[^\s\)\]\>\"\']+|www\.[^\s\)\]\>\"\']{3,}"
    return re.findall(pattern, text)


def extract_phone_numbers(text: str) -> list[str]:
    """Extract phone numbers."""
    pattern = r"(?:\+?\d{1,3}[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}"
    return re.findall(pattern, text)


def extract_all_entities(text: str) -> dict:
    """Extract all entity types from text in one call."""
    return {
        "dates": extract_dates(text),
        "amounts": extract_amounts(text),
        "urls": extract_urls(text),
        "phones": extract_phone_numbers(text),
    }


def estimate_token_count(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 chars (works for most LLMs)."""
    return len(text) // 4
