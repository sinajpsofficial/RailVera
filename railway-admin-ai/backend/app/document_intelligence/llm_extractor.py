"""
llm_extractor.py — Generic LLM-based document fact extractor.

Uses the local Ollama (qwen3) to extract structured facts from any document
via a JSON-constrained prompt. Falls back to regex extraction if Ollama is offline.
This replaces fragile, hard-coded regex patterns with robust LLM understanding.
"""

import re
import json
import logging
import httpx
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# ── Field schemas for each document type ──────────────────────────────────────
# Defines what facts to extract and their types/descriptions.
EXTRACTION_SCHEMAS: Dict[str, Dict[str, str]] = {
    "Service Book": {
        "employee_name":     "Full name of the employee",
        "employee_id":       "Employee ID, staff number, or PF number",
        "designation":       "Current post or designation",
        "department":        "Department or division",
        "pay_level":         "Pay level (numeric, e.g. 6)",
        "appointment_date":  "Date of appointment to railway service (DD-MM-YYYY)",
        "date_of_birth":     "Date of birth (DD-MM-YYYY)",
        "retirement_date":   "Date of retirement / superannuation (DD-MM-YYYY)",
        "years_of_service":  "Number of years in current grade or total service (numeric)",
        "passed_exam":       "Whether the employee has passed required departmental exams (yes/no)",
        "penalty_history":   "Any active penalties or disciplinary proceedings on record (yes/no)",
        "apar_rating":       "APAR/ACR overall grade or benchmark rating for last 3 years",
    },
    "APAR": {
        "employee_name":     "Full name of the employee being appraised",
        "reporting_period":  "The year or period this APAR covers (e.g. 2023-2024)",
        "apar_rating":       "Overall grade/benchmark: Outstanding, Very Good, Good, Average, Poor",
        "integrity_verified":"Whether the integrity certificate is verified (yes/no)",
        "adverse_entry":     "Whether there is any adverse entry (yes/no)",
        "designation":       "Designation/post of the employee",
    },
    "Medical Certificate": {
        "employee_name":     "Full name of the employee",
        "diagnosis":         "Medical diagnosis or condition mentioned",
        "fit_for_duty":      "Whether the employee is certified fit for duty (yes/no)",
        "medical_category":  "Medical classification category (e.g. A-1, B-1, C-1)",
        "medical_officer":   "Name or designation of issuing medical officer",
        "certificate_date":  "Date the certificate was issued (DD-MM-YYYY)",
    },
    "Leave Record": {
        "employee_name":     "Full name of the employee",
        "earned_leave_balance":  "Earned leave (LAP) balance in days (numeric)",
        "casual_leave_balance":  "Casual leave (CL) balance in days (numeric)",
        "half_pay_leave_balance":"Half pay leave (LHAP) balance in days (numeric)",
        "leave_without_pay": "Leave without pay taken, if any (numeric days or 'Nil')",
    },
    "Charge Sheet": {
        "employee_name":     "Full name of the charged employee",
        "charge_description":"Summary of the article of charge or misconduct",
        "inquiry_type":      "Type of inquiry: major penalty or minor penalty",
        "charge_date":       "Date of issue of the charge sheet (DD-MM-YYYY)",
        "inquiry_officer":   "Name or designation of the inquiry officer if mentioned",
    },
    "Penalty Order": {
        "employee_name":     "Full name of the employee penalised",
        "penalty_type":      "Type of penalty imposed (e.g. censure, withholding of increment, reduction in pay, dismissal)",
        "penalty_date":      "Date of the penalty order (DD-MM-YYYY)",
        "authority":         "Issuing authority of the penalty order",
        "cumulative_effect": "Whether the penalty has cumulative effect (yes/no)",
    },
    "Promotion Order": {
        "employee_name":     "Full name of the promoted employee",
        "promoted_from":     "The post/grade promoted from",
        "promoted_to":       "The post/grade promoted to",
        "effective_date":    "Date from which promotion takes effect (DD-MM-YYYY)",
        "authority":         "Issuing authority of the order",
    },
    "Transfer Order": {
        "employee_name":     "Full name of the transferred employee",
        "transferred_from":  "The station/division/unit transferred from",
        "transferred_to":    "The station/division/unit transferred to",
        "effective_date":    "Date from which transfer takes effect (DD-MM-YYYY)",
        "joining_date":      "Joining report date at new station (DD-MM-YYYY)",
    },
    "Departmental Exam Result": {
        "employee_name":     "Full name of the candidate",
        "exam_name":         "Name of the examination (e.g. LDCE, GDCE, Safety exam)",
        "result":            "Result: Passed or Failed",
        "merit_rank":        "Merit list rank if mentioned (numeric)",
        "exam_date":         "Date of examination (DD-MM-YYYY)",
        "passed_exam":       "Whether the employee passed the examination (yes/no)",
    },
    "Retirement Record": {
        "employee_name":     "Full name of the retiring employee",
        "retirement_date":   "Date of retirement / superannuation (DD-MM-YYYY)",
        "last_pay_certificate": "Reference number or status of last pay certificate",
        "no_dues_status":    "Whether no-dues certificate has been cleared (yes/no)",
        "settlement_status": "Status of settlement payment (e.g. paid, pending)",
    },
}


class LLMExtractor:
    """
    Extracts structured facts from OCR text using Ollama (qwen3).

    For each document type, it builds a precise extraction prompt,
    calls the local LLM, and parses the returned JSON.
    Falls back to regex heuristics if Ollama is unavailable.
    """

    OLLAMA_URL = "http://localhost:11434"
    LLM_MODEL = "qwen3"
    TIMEOUT = 60.0

    def extract(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Main entry point. Attempts LLM extraction, then falls back to regex.
        Returns a flat dict of fact_name -> value.
        """
        schema = EXTRACTION_SCHEMAS.get(document_type)
        if not schema:
            logger.warning(f"[LLMExtractor] No schema for document type: '{document_type}'. Returning empty facts.")
            return {}

        # Try LLM extraction first
        try:
            result = self._extract_with_llm(text, document_type, schema)
            if result:
                logger.info(f"[LLMExtractor] LLM extraction succeeded for '{document_type}'.")
                return result
        except Exception as e:
            logger.warning(f"[LLMExtractor] LLM extraction failed: {e}. Falling back to regex.")

        # Fallback to regex
        logger.info(f"[LLMExtractor] Using regex fallback for '{document_type}'.")
        return self._extract_with_regex(text, document_type)

    def _build_prompt(self, text: str, document_type: str, schema: Dict[str, str]) -> str:
        """Build the LLM extraction prompt with the schema as instructions."""
        fields_desc = "\n".join(
            f'  "{k}": <{v}>'
            for k, v in schema.items()
        )
        # Truncate text to stay within token limits (approx 3000 chars)
        truncated_text = text[:3000]
        return f"""You are a document data extraction assistant for Indian Railways HR administration.

Extract structured facts from the following {document_type} document text.

EXTRACTION RULES:
1. Extract ONLY facts that are explicitly present in the document text.
2. If a field is not mentioned or cannot be determined, use null.
3. For yes/no fields, use only "yes" or "no" as values.
4. For date fields, use DD-MM-YYYY format.
5. For numeric fields, use a number only (no units or text).
6. Do NOT infer, assume, or generate any facts not in the text.
7. Respond ONLY with a valid JSON object and nothing else.

REQUIRED JSON FIELDS:
{{
{fields_desc}
}}

DOCUMENT TEXT:
---
{truncated_text}
---

JSON OUTPUT:"""

    def _extract_with_llm(self, text: str, document_type: str, schema: Dict[str, str]) -> Optional[Dict]:
        """Send extraction prompt to Ollama and parse the JSON response."""
        prompt = self._build_prompt(text, document_type, schema)

        with httpx.Client(timeout=self.TIMEOUT) as client:
            response = client.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,   # Fully deterministic for extraction
                        "top_p": 1.0,
                    }
                }
            )
            response.raise_for_status()
            raw = response.json().get("response", "").strip()

        # Parse JSON from the response
        return self._parse_json_response(raw, schema)

    def _parse_json_response(self, raw: str, schema: Dict[str, str]) -> Optional[Dict]:
        """Parse the JSON block from the LLM response, handling fences."""
        # Strip markdown code fences
        fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
        json_str = fence_match.group(1) if fence_match else raw

        # Try direct JSON parse
        try:
            data = json.loads(json_str)
            # Clean up: remove null values and empty strings for cleaner facts
            return {k: v for k, v in data.items() if v is not None and v != "" and k in schema}
        except (json.JSONDecodeError, ValueError):
            pass

        # Try finding a JSON object embedded in the response
        obj_match = re.search(r'\{[^{}]+\}', raw, re.DOTALL)
        if obj_match:
            try:
                data = json.loads(obj_match.group(0))
                return {k: v for k, v in data.items() if v is not None and v != "" and k in schema}
            except (json.JSONDecodeError, ValueError):
                pass

        logger.warning(f"[LLMExtractor] Could not parse JSON from LLM response: {raw[:200]}")
        return None

    # ── Regex fallback ────────────────────────────────────────────────────────

    def _extract_with_regex(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Regex-based fallback extractor. Used when Ollama is offline.
        Covers the most critical fields for each document type.
        """
        t = text  # original case
        tl = text.lower()

        facts = {}

        # ── Common fields (apply to all types) ──
        name_match = re.search(
            r'(?:employee\s*name|name)[:\s]+([A-Z][a-zA-Z]+(?:[ \t][A-Z][a-zA-Z]+)*)',
            t, re.IGNORECASE
        )
        if name_match:
            facts["employee_name"] = name_match.group(1).strip()

        date_match = re.search(
            r'(?:date of appointment|appointed on)[:\s]+'
            r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            t, re.IGNORECASE
        )
        if date_match:
            facts["appointment_date"] = date_match.group(1).strip()

        dob_match = re.search(
            r'date of birth[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            t, re.IGNORECASE
        )
        if dob_match:
            facts["date_of_birth"] = dob_match.group(1).strip()

        # ── Service Book specific ──
        if document_type == "Service Book":
            emp_id = re.search(r'(?:employee\s*id|staff\s*no|pf\s*no)[:\s#]+(\w+)', t, re.IGNORECASE)
            if emp_id:
                facts["employee_id"] = emp_id.group(1).strip()

            desig = re.search(r'(?:designation|post|current\s*post)[:\s]+(.+?)[\n,]', t, re.IGNORECASE)
            if desig:
                facts["designation"] = desig.group(1).strip()

            dept = re.search(r'department[:\s]+(.+?)[\n,]', t, re.IGNORECASE)
            if dept:
                facts["department"] = dept.group(1).strip()

            pay = re.search(r'(?:pay\s*level|level)[:\s]+(\d+)', t, re.IGNORECASE)
            if pay:
                facts["pay_level"] = pay.group(1).strip()

            svc_years = re.search(r'(?:active service years|years of service|service years)[:\s]+([\d\.]+)', t, re.IGNORECASE)
            if svc_years:
                facts["years_of_service"] = svc_years.group(1).strip()

            passed_exam = re.search(r'(?:passed departmental exam|passed exam)[:\s]+(yes|no)', t, re.IGNORECASE)
            if passed_exam:
                facts["passed_exam"] = passed_exam.group(1).lower().strip()

            ret_date = re.search(r'(?:date of retirement|due to retire)[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', t, re.IGNORECASE)
            if ret_date:
                facts["retirement_date"] = ret_date.group(1).strip()

            penalty = re.search(r'(?:penalty|punishment|censure|disciplinary)', tl)
            facts["penalty_history"] = "yes" if penalty else "no"

        # ── APAR specific ──
        elif document_type == "APAR":
            grade = re.search(
                r'(?:overall\s*grade|benchmark|overall\s*assessment)[:\s]+(outstanding|very\s*good|good|average|poor)',
                t, re.IGNORECASE
            )
            if grade:
                facts["apar_rating"] = grade.group(1).strip().title()

            period = re.search(r'(?:reporting\s*period|period)[:\s]+([\d]{4}[\-\/][\d]{4})', t, re.IGNORECASE)
            if period:
                facts["reporting_period"] = period.group(1).strip()

            facts["integrity_verified"] = "yes" if "integrity certificate" in tl else "no"
            facts["adverse_entry"] = "yes" if re.search(r'adverse entry(?!\s*:\s*none)', tl) else "no"

        # ── Medical Certificate specific ──
        elif document_type == "Medical Certificate":
            facts["fit_for_duty"] = "yes" if re.search(r'fit for duty|certified fit', tl) else "no"
            diag = re.search(r'diagnosis[:\s]+(.+?)[\n,\.]', t, re.IGNORECASE)
            if diag:
                facts["diagnosis"] = diag.group(1).strip()
            cat = re.search(r'(?:medical\s*classification|category)[:\s]+([A-C][\-\d]+)', t, re.IGNORECASE)
            if cat:
                facts["medical_category"] = cat.group(1).strip()

        # ── Charge Sheet ──
        elif document_type == "Charge Sheet":
            charge = re.search(r'(?:article of charge|charged with)[:\s]+(.+?)[\n\.]', t, re.IGNORECASE)
            if charge:
                facts["charge_description"] = charge.group(1).strip()
            facts["inquiry_type"] = (
                "major penalty" if "major penalty" in tl
                else "minor penalty" if "minor penalty" in tl
                else None
            )

        # ── Penalty Order ──
        elif document_type == "Penalty Order":
            penalty = re.search(r'penalty of[:\s]+(.+?)[\n\.]', t, re.IGNORECASE)
            if penalty:
                facts["penalty_type"] = penalty.group(1).strip()
            facts["cumulative_effect"] = "no" if "without cumulative effect" in tl else "yes"

        # ── Promotion Order ──
        elif document_type == "Promotion Order":
            from_post = re.search(r'from the post of[:\s]+(.+?)[\n\.,]', t, re.IGNORECASE)
            if from_post:
                facts["promoted_from"] = from_post.group(1).strip()
            to_post = re.search(r'to the post of[:\s]+(.+?)[\n\.,]', t, re.IGNORECASE)
            if to_post:
                facts["promoted_to"] = to_post.group(1).strip()
            eff_date = re.search(
                r'with effect from[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                t, re.IGNORECASE
            )
            if eff_date:
                facts["effective_date"] = eff_date.group(1).strip()

        # ── Transfer Order ──
        elif document_type == "Transfer Order":
            to_station = re.search(r'(?:transferred to|posted to)[:\s]+(.+?)[\n\.,]', t, re.IGNORECASE)
            if to_station:
                facts["transferred_to"] = to_station.group(1).strip()
            from_station = re.search(r'(?:relieved from|transferred from)[:\s]+(.+?)[\n\.,]', t, re.IGNORECASE)
            if from_station:
                facts["transferred_from"] = from_station.group(1).strip()
            joining = re.search(
                r'joining report date[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                t, re.IGNORECASE
            )
            if joining:
                facts["joining_date"] = joining.group(1).strip()

        # ── Departmental Exam ──
        elif document_type == "Departmental Exam Result":
            result = re.search(r'result[:\s]+(passed|failed)', t, re.IGNORECASE)
            if result:
                facts["result"] = result.group(1).strip().title()
                facts["passed_exam"] = "yes" if result.group(1).lower() == "passed" else "no"
            rank = re.search(r'merit list rank[:\s]+(\d+)', t, re.IGNORECASE)
            if rank:
                facts["merit_rank"] = int(rank.group(1))

        # ── Leave Record ──
        elif document_type == "Leave Record":
            el = re.search(r'earned leave.*?balance[:\s]+([\d]+)\s*days?', t, re.IGNORECASE)
            if el:
                facts["earned_leave_balance"] = int(el.group(1))
            cl = re.search(r'casual leave.*?balance[:\s]+([\d]+)\s*days?', t, re.IGNORECASE)
            if cl:
                facts["casual_leave_balance"] = int(cl.group(1))
            lwp = re.search(r'leave without pay[:\s]+(.+?)[\n\.,]', t, re.IGNORECASE)
            if lwp:
                facts["leave_without_pay"] = lwp.group(1).strip()

        # ── Retirement Record ──
        elif document_type == "Retirement Record":
            ret_date = re.search(
                r'(?:date of retirement|retirement date)[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                t, re.IGNORECASE
            )
            if ret_date:
                facts["retirement_date"] = ret_date.group(1).strip()
            lpc = re.search(r'last pay certificate[:\s]+(.+?)[\n\.,]', t, re.IGNORECASE)
            if lpc:
                facts["last_pay_certificate"] = lpc.group(1).strip()
            facts["no_dues_status"] = "yes" if "no dues" in tl and "cleared" in tl else "pending"

        return {k: v for k, v in facts.items() if v is not None}
