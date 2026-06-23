"""
Natural language fact extractor for follow-up chat replies.
Parses sentences like:
  "I have 10 years of service. APAR grade is Outstanding. I passed the exam."
and returns a structured dict to merge into case.extracted_facts.
"""
import re
from typing import Dict, Any


class ChatFactParser:
    """
    Lightweight regex-based parser for user follow-up replies.
    Extracts known fact keys from free-form text.
    """

    def parse(self, text: str) -> Dict[str, Any]:
        facts: Dict[str, Any] = {}
        t = text.lower()

        # ── years_of_service ─────────────────────────────────────────────
        m = re.search(
            r"(\d+)\s*(?:years?|yrs?)(?:\s+of)?\s+(?:service|experience|work)",
            t
        )
        if m:
            facts["years_of_service"] = int(m.group(1))

        # ── apar_rating ───────────────────────────────────────────────────
        apar_keywords = {
            "outstanding": "Outstanding",
            "very good": "Very Good",
            "good": "Good",
            "average": "Average",
            "poor": "Poor",
            "below benchmark": "Below Benchmark",
        }
        for kw, value in apar_keywords.items():
            if kw in t:
                # Make sure we don't accidentally match "not good"
                if f"not {kw}" not in t:
                    facts["apar_rating"] = value
                    break

        # Numeric APAR grade (e.g. "APAR grade 9" or "APAR score 8.5")
        if "apar_rating" not in facts:
            m = re.search(r"apar\s+(?:grade|score|rating)\s+(?:is\s+)?(\d+(?:\.\d+)?)", t)
            if m:
                score = float(m.group(1))
                # Map numeric to label based on typical 10-point scale
                if score >= 9:
                    facts["apar_rating"] = "Outstanding"
                elif score >= 7:
                    facts["apar_rating"] = "Very Good"
                elif score >= 5:
                    facts["apar_rating"] = "Good"
                else:
                    facts["apar_rating"] = "Average"

        # ── passed_exam ───────────────────────────────────────────────────
        passed_exam_positive = re.search(
            r"(?:i\s+have\s+)?(?:passed|cleared|qualified|completed)\s+(?:the\s+)?(?:exam|examination|departmental|promotional|ldce|gdce)",
            t
        )
        passed_exam_negative = re.search(
            r"(?:not|haven'?t|did\s+not)\s+(?:pass|clear|qualify)(?:ed)?\s+(?:the\s+)?(?:exam|examination)",
            t
        )
        if passed_exam_positive:
            facts["passed_exam"] = True
        elif passed_exam_negative:
            facts["passed_exam"] = False

        # ── penalty_history ───────────────────────────────────────────────
        penalty_negative = re.search(
            r"(?:no|none|clean|no\s+pending|no\s+active)\s+(?:penalty|disciplinary|punishments?|charges?)",
            t
        )
        penalty_positive = re.search(
            r"(?:have|has|had)\s+(?:a\s+)?(?:penalty|disciplinary|punishment)",
            t
        )
        if penalty_negative:
            facts["penalty_history"] = []
        elif penalty_positive:
            facts["penalty_history"] = ["active"]

        # ── pay_level ──────────────────────────────────────────────────────
        m = re.search(r"pay\s*level\s*(?:is\s*)?(\d+)", t)
        if m:
            facts["pay_level"] = int(m.group(1))

        return facts
