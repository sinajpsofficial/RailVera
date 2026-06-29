"""
chat_fact_parser.py — LLM-powered free-text fact extractor for chat replies.

Replaces the old rigid regex parser with an Ollama/qwen3 call that can understand
any natural phrasing an employee might use. The regex patterns are kept as a fast
fallback when Ollama is offline.

Examples of what it can now handle:
  "I've been working in this grade for a decade."
  "My ACR has always been outstanding over the past three years."
  "I cleared the LDCE back in 2022."
  "There was a censure entry in 2021 but it's been vacated."
  "Current level: 7, department: Signal & Telecom"
"""

import re
import json
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# ── Schema for facts the chat parser is expected to extract ───────────────────
CHAT_FACT_SCHEMA = {
    "years_of_service":  "Number of years the employee has served in their current grade or total (numeric only, e.g. 7 or 7.5)",
    "apar_rating":       "APAR/ACR overall grade. Must be exactly one of: Outstanding, Very Good, Good, Average, Poor, Below Benchmark",
    "passed_exam":       "Has the employee passed the required departmental/promotional exam? (yes or no)",
    "penalty_history":   "Does the employee have any active penalty or disciplinary action? (yes or no)",
    "pay_level":         "Current pay level (numeric only, e.g. 6)",
    "appointment_date":  "Date of appointment to railway service (DD-MM-YYYY format if found)",
    "date_of_birth":     "Date of birth of the employee (DD-MM-YYYY format if found)",
    "designation":       "Current post or designation of the employee",
    "department":        "Department or division of the employee",
    "leave_reason":      "Medical diagnosis or reason for leave if mentioned",
    "from_date":         "Start date of requested leave (DD-MM-YYYY)",
    "to_date":           "End date of requested leave (DD-MM-YYYY)",
    "medical_fit":       "Is the employee medically fit for duty? (yes or no)",
    "medical_category":  "Medical fitness classification (e.g. A-1, B-1, C-1)",
}

OLLAMA_URL = "http://localhost:11434"
LLM_MODEL = "qwen3"


class ChatFactParser:
    """
    Extracts structured employee facts from a free-text chat reply.

    Primary:  Ollama/qwen3 LLM call — understands any natural phrasing.
    Fallback: Regex-based parsing — used when Ollama is offline.
    """

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Main entry point. Returns a dict of extracted facts to merge into case.extracted_facts.
        Only returns keys where a value was actually found — never returns null/None values.
        """
        # Try LLM first
        try:
            result = self._parse_with_llm(text)
            if result:
                logger.info(f"[ChatFactParser] LLM extracted {len(result)} facts from reply.")
                return result
        except Exception as e:
            logger.warning(f"[ChatFactParser] LLM unavailable ({e}). Using regex fallback.")

        # Regex fallback
        result = self._parse_with_regex(text)
        logger.info(f"[ChatFactParser] Regex extracted {len(result)} facts from reply.")
        return result

    # ── LLM path ─────────────────────────────────────────────────────────────

    def _build_prompt(self, text: str) -> str:
        fields_desc = "\n".join(
            f'  "{k}": <{v}>'
            for k, v in CHAT_FACT_SCHEMA.items()
        )
        return f"""You are a Railway HR administrative assistant parsing an employee's chat reply.

Extract structured facts from the following reply text.

RULES:
1. Only extract facts that are explicitly or clearly implied in the text.
2. If a fact is not present or cannot be determined from the text, use null.
3. For yes/no fields, use only "yes" or "no".
4. For numeric fields, output a number only (no units or surrounding text).
5. For apar_rating, map any equivalent phrasing to one of the exact allowed values.
6. Do NOT invent, guess, or assume any fact not stated in the text.
7. Respond with ONLY a valid JSON object and nothing else.

REQUIRED JSON FIELDS:
{{
{fields_desc}
}}

EMPLOYEE REPLY:
---
{text[:1500]}
---

JSON OUTPUT:"""

    def _parse_with_llm(self, text: str) -> Optional[Dict[str, Any]]:
        """Call Ollama and parse the structured JSON response."""
        prompt = self._build_prompt(text)

        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0, "top_p": 1.0}
                }
            )
            response.raise_for_status()
            raw = response.json().get("response", "").strip()

        return self._parse_json_response(raw)

    def _parse_json_response(self, raw: str) -> Optional[Dict[str, Any]]:
        """Extract and clean the JSON object from LLM output."""
        # Strip markdown code fences
        fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
        json_str = fence_match.group(1) if fence_match else raw

        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            obj_match = re.search(r'\{[^{}]+\}', raw, re.DOTALL)
            if not obj_match:
                return None
            try:
                data = json.loads(obj_match.group(0))
            except (json.JSONDecodeError, ValueError):
                return None

        # Clean up: keep only known keys with non-null, non-empty values
        cleaned: Dict[str, Any] = {}
        for key in CHAT_FACT_SCHEMA:
            val = data.get(key)
            if val is None or val == "" or str(val).lower() == "null":
                continue
            # Normalise yes/no booleans consistently
            if key in ("passed_exam", "penalty_history", "medical_fit"):
                val = str(val).lower().strip()
                if val in ("yes", "true", "1"):
                    val = "yes"
                elif val in ("no", "false", "0"):
                    val = "no"
                else:
                    continue  # skip ambiguous values
            # Normalise APAR rating casing
            if key == "apar_rating":
                val = str(val).strip().title()
                allowed = {"Outstanding", "Very Good", "Good", "Average", "Poor", "Below Benchmark"}
                if val not in allowed:
                    continue
            cleaned[key] = val

        return cleaned if cleaned else None

    # ── Regex fallback ────────────────────────────────────────────────────────

    def _parse_with_regex(self, text: str) -> Dict[str, Any]:
        """
        Regex-based fallback. Handles common patterns even if phrased differently.
        Kept as an unambiguous, reliable safety net for Ollama-offline scenarios.
        """
        facts: Dict[str, Any] = {}
        t = text.lower()

        # years_of_service — handles: "10 years", "a decade", "10 yrs of service"
        m = re.search(
            r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?|yr)(?:\s+of)?(?:\s+service|\s+experience|\s+in\s+grade)?',
            t
        )
        if m:
            facts["years_of_service"] = float(m.group(1)) if '.' in m.group(1) else int(m.group(1))
        # Handle "a decade" etc.
        elif re.search(r'\ba decade\b', t):
            facts["years_of_service"] = 10
        elif re.search(r'\bhalf a decade\b', t):
            facts["years_of_service"] = 5

        # apar_rating
        apar_map = [
            ("outstanding", "Outstanding"),
            ("very good", "Very Good"),
            ("good", "Good"),
            ("average", "Average"),
            ("poor", "Poor"),
            ("below benchmark", "Below Benchmark"),
        ]
        for kw, label in apar_map:
            if kw in t and f"not {kw}" not in t:
                facts["apar_rating"] = label
                break

        # Numeric APAR score (e.g. "APAR score 9")
        if "apar_rating" not in facts:
            m = re.search(r'apar\s+(?:grade|score|rating)\s+(?:is\s+)?(\d+(?:\.\d+)?)', t)
            if m:
                score = float(m.group(1))
                if score >= 9:
                    facts["apar_rating"] = "Outstanding"
                elif score >= 7:
                    facts["apar_rating"] = "Very Good"
                elif score >= 5:
                    facts["apar_rating"] = "Good"
                else:
                    facts["apar_rating"] = "Average"

        # passed_exam
        if re.search(
            r'(?:passed|cleared|qualified|completed)\s+(?:the\s+)?(?:exam|examination|departmental|promotional|ldce|gdce)',
            t
        ):
            facts["passed_exam"] = "yes"
        elif re.search(
            r"(?:not|haven'?t|did\s+not)\s+(?:pass|clear|qualify)(?:ed)?\s+(?:the\s+)?(?:exam|examination)",
            t
        ):
            facts["passed_exam"] = "no"

        # penalty_history
        if re.search(
            r'(?:no|none|clean|no\s+pending|no\s+active)\s+(?:penalty|disciplinary|punishments?|charges?|adverse)',
            t
        ):
            facts["penalty_history"] = "no"
        elif re.search(
            r'(?:have|has|had|there\s+(?:was|is|were))\s+(?:a\s+)?(?:penalty|disciplinary|punishment|censure|charge)',
            t
        ):
            facts["penalty_history"] = "yes"

        # pay_level
        m = re.search(r'(?:pay\s*level|level)\s*(?:is\s*)?(\d+)', t)
        if m:
            facts["pay_level"] = int(m.group(1))

        # medical fitness
        if re.search(r'(?:medically\s+fit|fit\s+for\s+duty|certified\s+fit)', t):
            facts["medical_fit"] = "yes"
        elif re.search(r'(?:medically\s+unfit|not\s+fit|unfit\s+for\s+duty)', t):
            facts["medical_fit"] = "no"

        # medical category
        m = re.search(r'(?:medical\s+(?:category|class(?:ification)?)|category)\s*[:\-]?\s*([A-Ca-c][\-\d]+)', text)
        if m:
            facts["medical_category"] = m.group(1).upper()

        # designation
        m = re.search(r'(?:designation|post|working\s+as)\s*[:\-]?\s*([A-Z][a-zA-Z\s]+?)(?:[,\.\n]|$)', text)
        if m:
            desig = m.group(1).strip()
            if 3 < len(desig) < 80:
                facts["designation"] = desig

        # department
        m = re.search(r'department\s*[:\-]?\s*([A-Za-z\s&\/]+?)(?:[,\.\n]|$)', text, re.IGNORECASE)
        if m:
            dept = m.group(1).strip()
            if 2 < len(dept) < 60:
                facts["department"] = dept

        return facts
