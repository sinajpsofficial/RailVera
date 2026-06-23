import re
from typing import Dict, Optional

class ServiceBookExtractor:
    """
    Pulls structured facts from a Service Book's OCR text.
    Uses regex patterns to find names, dates, designations, etc.
    """

    def extract(self, text: str) -> Dict:
        return {
            "employee_name":      self._find(text, r"name[: \t]+([A-Z][a-zA-Z]+(?:[ \t][A-Z][a-zA-Z]+)*)", re.IGNORECASE),
            "employee_id":        self._find(text, r"(?:employee\s*id|staff\s*no|emp\s*no)[:\s#]+(\w+)", re.IGNORECASE),
            "designation":        self._find(text, r"(?:designation|post|current\s*post)[:\s]+(.+?)[\n,]", re.IGNORECASE),
            "department":         self._find(text, r"department[:\s]+(.+?)[\n,]", re.IGNORECASE),
            "pay_level":          self._find(text, r"(?:pay\s*level|level)[:\s]+(\d+)", re.IGNORECASE),
            "appointment_date":   self._find_date(text, r"(?:date of appointment|appointed on)[:\s]+"),
            "date_of_birth":      self._find_date(text, r"date of birth[:\s]+"),
            "retirement_date":    self._find_date(text, r"(?:date of retirement|due to retire)[:\s]+"),
            "promotion_history":  self._extract_promotions(text),
            "penalty_history":    self._extract_penalties(text),
        }

    def _find(self, text: str, pattern: str, flags=0) -> Optional[str]:
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else None

    def _find_date(self, text: str, prefix_pattern: str) -> Optional[str]:
        date_pattern = prefix_pattern + r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
        return self._find(text, date_pattern, re.IGNORECASE)

    def _extract_promotions(self, text: str) -> list:
        # Look for promotion date patterns
        pattern = r"promoted.*?(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [{"date": m} for m in matches]

    def _extract_penalties(self, text: str) -> list:
        pattern = r"(?:penalty|punishment|censure).*?(\d{4})"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [{"year": m} for m in matches]
