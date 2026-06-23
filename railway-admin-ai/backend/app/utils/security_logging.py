import re

# PII pattern regular expressions and their replacement placeholders
PII_PATTERNS = [
    # Indian Mobile Numbers / standard phone numbers (10 digits, optional country code)
    (r"(?<!\d)(?:\+91|0)?[6-9]\d{9}(?!\d)", "[PHONE]"),
    # Aadhaar Number (12 digits, optional spaces or dashes)
    (r"(?<!\+)\b\d{4}[ -]?\d{4}[ -]?\d{4}\b", "[AADHAAR]"),
    # PAN Card (5 letters, 4 digits, 1 letter)
    (r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN]"),
    # Email addresses
    (r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "[EMAIL]"),
    # Employee ID formats (case-insensitive EMP followed by identifiers, or 8 digits)
    (r"\bEMP\w+\b", "[EMPLOYEE_ID]"),
    (r"\bemp\w+\b", "[EMPLOYEE_ID]"),
]

def mask_pii(text: str) -> str:
    """
    Scans a block of text (such as logs or prompts) and replaces any sensitive
    Personally Identifiable Information (PII) with generic tags.
    """
    if not text:
        return ""
    
    masked_text = text
    for pattern, replacement in PII_PATTERNS:
        masked_text = re.sub(pattern, replacement, masked_text)
    return masked_text
