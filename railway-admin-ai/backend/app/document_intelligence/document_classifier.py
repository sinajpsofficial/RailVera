import re
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    document_type: str
    confidence: float

class DocumentClassifier:
    """
    Identifies what type of document was uploaded based on
    keywords found in the OCR text.
    """

    SIGNATURES = {
        "Service Book": [
            "service book", "record of service", "date of appointment",
            "date of birth", "history of pay", "increment"
        ],
        "APAR": [
            "annual performance assessment", "apar", "appraisal",
            "assessment report", "overall grade", "integrity certificate",
            "benchmark", "adverse entry"
        ],
        "Leave Record": [
            "leave account", "earned leave", "casual leave",
            "leave without pay", "half pay leave", "leave balance"
        ],
        "Medical Certificate": [
            "medical certificate", "fit for duty", "certified sick",
            "medical officer", "hospital", "diagnosis"
        ],
        "Charge Sheet": [
            "charge sheet", "article of charge", "statement of imputation",
            "charged with", "departmental inquiry"
        ],
        "Penalty Order": [
            "penalty order", "punishment order", "penalty of",
            "reduction in pay", "censure", "withholding of increment",
            "compulsory retirement", "removal", "dismissal"
        ],
        "Promotion Order": [
            "promotion order", "promoted to", "appointed to the post",
            "with effect from", "from the post of", "to the post of"
        ],
        "Transfer Order": [
            "transfer order", "transferred to", "posted to",
            "relieved from", "joining report"
        ],
        "Departmental Exam Result": [
            "departmental examination", "ldce", "gdce",
            "examination result", "passed", "failed", "merit list"
        ],
        "Retirement Record": [
            "retirement", "superannuation", "last pay certificate",
            "no dues certificate", "settlement"
        ],
    }

    def classify(self, ocr_text: str) -> ClassificationResult:
        text_lower = ocr_text.lower()
        scores = {}

        for doc_type, keywords in self.SIGNATURES.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                scores[doc_type] = matches / len(keywords)

        if not scores:
            return ClassificationResult("Unknown", 0.0)

        best = max(scores, key=scores.get)
        return ClassificationResult(best, round(scores[best], 4))
