from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float


class DocumentClassifier:
    """
    Identifies what type of document was uploaded based on keywords in the OCR text.

    Improvements over v1:
    - Weighted scoring: high-signal keywords score higher than generic ones.
    - Minimum keyword hit threshold: requires at least 2 keyword matches to classify.
    - Normalizes confidence as a fraction of total weighted score possible.
    """

    # Each entry: (keyword, weight)
    # Higher weight = stronger signal for that document type
    SIGNATURES: Dict[str, List[Tuple[str, float]]] = {
        "Service Book": [
            ("service book", 3.0),
            ("record of service", 3.0),
            ("history of pay", 2.0),
            ("date of appointment", 2.0),
            ("date of birth", 1.0),
            ("increment", 1.0),
            ("active service years", 2.0),
            ("passed departmental exam", 2.0),
        ],
        "APAR": [
            ("annual performance assessment", 3.0),
            ("apar", 3.0),
            ("assessment report", 2.0),
            ("overall grade", 2.0),
            ("integrity certificate", 2.0),
            ("benchmark", 1.5),
            ("adverse entry", 2.0),
            ("appraisal", 1.5),
        ],
        "Leave Record": [
            ("leave account", 3.0),
            ("leave account ledger", 3.0),
            ("earned leave", 2.0),
            ("casual leave", 1.5),
            ("leave without pay", 2.0),
            ("half pay leave", 2.0),
            ("leave balance", 2.0),
        ],
        "Medical Certificate": [
            ("medical certificate", 3.0),
            ("fit for duty", 3.0),
            ("certified sick", 2.5),
            ("medical officer", 2.0),
            ("diagnosis", 1.5),
            ("hospital", 1.0),
            ("certificate of fitness", 3.0),
            ("medical classification", 2.0),
        ],
        "Charge Sheet": [
            ("charge sheet", 3.0),
            ("article of charge", 3.0),
            ("statement of imputation", 3.0),
            ("charged with", 2.0),
            ("departmental inquiry", 2.0),
            ("misconduct", 1.5),
        ],
        "Penalty Order": [
            ("penalty order", 3.0),
            ("punishment order", 3.0),
            ("penalty of", 2.5),
            ("reduction in pay", 2.0),
            ("censure", 2.0),
            ("withholding of increment", 2.0),
            ("compulsory retirement", 2.0),
            ("removal from service", 2.5),
            ("dismissal", 2.0),
        ],
        "Promotion Order": [
            ("promotion order", 3.0),
            ("promoted to", 2.5),
            ("appointed to the post", 2.0),
            ("with effect from", 1.0),
            ("from the post of", 2.0),
            ("to the post of", 2.0),
            ("office order", 1.0),
        ],
        "Transfer Order": [
            ("transfer order", 3.0),
            ("transferred to", 2.5),
            ("posted to", 2.0),
            ("relieved from", 2.0),
            ("joining report", 2.0),
        ],
        "Departmental Exam Result": [
            ("departmental examination", 3.0),
            ("ldce", 3.0),
            ("gdce", 3.0),
            ("examination result", 2.5),
            ("merit list", 2.0),
            ("passed the examination", 2.5),
            ("failed the examination", 2.5),
        ],
        "Retirement Record": [
            ("retirement", 2.0),
            ("superannuation", 3.0),
            ("last pay certificate", 3.0),
            ("no dues certificate", 3.0),
            ("settlement", 1.5),
            ("voluntary retirement", 2.5),
        ],
    }

    def classify(self, ocr_text: str) -> ClassificationResult:
        text_lower = ocr_text.lower()
        scores: Dict[str, float] = {}
        hit_counts: Dict[str, int] = {}
        max_scores: Dict[str, float] = {}

        for doc_type, keywords in self.SIGNATURES.items():
            total_weight = sum(w for _, w in keywords)
            matched_weight = sum(w for kw, w in keywords if kw in text_lower)
            matched_count = sum(1 for kw, _ in keywords if kw in text_lower)

            scores[doc_type] = matched_weight
            hit_counts[doc_type] = matched_count
            max_scores[doc_type] = total_weight

        # Require at least 2 keyword hits to classify
        eligible = {
            doc_type: score
            for doc_type, score in scores.items()
            if hit_counts[doc_type] >= 2 and score > 0
        }

        if not eligible:
            # Fallback: if only 1 hit, still classify if score is very high
            eligible = {
                doc_type: score
                for doc_type, score in scores.items()
                if hit_counts[doc_type] >= 1 and score >= 3.0
            }

        if not eligible:
            return ClassificationResult("Unknown", 0.0)

        best = max(eligible, key=eligible.get)
        confidence = round(eligible[best] / max_scores[best], 4)

        return ClassificationResult(best, confidence)
