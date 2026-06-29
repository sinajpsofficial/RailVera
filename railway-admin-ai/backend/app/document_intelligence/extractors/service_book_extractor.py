import re
from app.document_intelligence.llm_extractor import LLMExtractor


class ServiceBookExtractor:
    """
    Extracts structured employee facts from a Service Book's OCR text.
    Delegates to LLMExtractor which uses Ollama (qwen3) for intelligent
    extraction, with automatic regex fallback if Ollama is offline.
    """

    def extract(self, text: str) -> dict:
        extractor = LLMExtractor()
        facts = extractor.extract(text, "Service Book")
        
        # Merge promotion_history and penalty_history as lists for backward compatibility/testing
        facts["promotion_history"] = self._extract_promotions(text)
        facts["penalty_history"] = self._extract_penalties(text)
        
        return facts

    def _extract_promotions(self, text: str) -> list:
        # Look for promotion date patterns
        pattern = r"promoted.*?(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [{"date": m} for m in matches]

    def _extract_penalties(self, text: str) -> list:
        pattern = r"(?:penalty|punishment|censure).*?(\d{4})"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [{"year": m} for m in matches]
