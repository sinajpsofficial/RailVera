from dataclasses import dataclass, field
from typing import List, Dict, Optional
from app.core.document_demand_engine import DocumentDemandEngine
from app.core.rag_pipeline import RAGPipeline
from app.core.llm_client import LLMClient
from app.core.prompt_builder import PromptBuilder

@dataclass
class EligibilityResult:
    decision: str                            # Eligible / Not Eligible / Cannot Determine
    eligibility_status: str
    supporting_rules: List[Dict] = field(default_factory=list)
    supporting_facts: List[Dict] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    risk_indicators: List[str] = field(default_factory=list)
    administrative_notes: str = ""
    confidence_level: str = "Low"            # High / Medium / Low
    follow_up_questions: List[str] = field(default_factory=list)
    document_demand_notice: str = ""         # Set if documents are missing

class EligibilityEngine:
    """
    The main decision engine.

    Evaluation sequence (NEVER skip steps):
    1. Document completeness check — demand if missing
    2. Fact extraction availability check — check key facts, prompt questions if missing
    3. Rule retrieval from RAG pipeline
    4. Rule evaluation against facts (using LLM or fallback)
    5. Decision generation with full reasoning
    """

    def __init__(self, rag_instance: Optional[RAGPipeline] = None):
        self.demand_engine   = DocumentDemandEngine()
        self.rag             = rag_instance or RAGPipeline()
        self.llm             = LLMClient()
        self.prompt_builder  = PromptBuilder()

    async def evaluate(
        self,
        query: str,
        domain: str,
        submitted_docs: List[str],
        extracted_facts: Dict,
        conversation_history: List[Dict],
        db
    ) -> EligibilityResult:

        # ── Step 1: Document completeness gate ─────────────────────────
        demand = self.demand_engine.check(domain, submitted_docs, extracted_facts)
        if not demand.all_present:
            return EligibilityResult(
                decision="Cannot Determine",
                eligibility_status="Blocked — required documents missing",
                document_demand_notice=demand.demand_notice,
                administrative_notes="Case blocked pending document submission.",
                confidence_level="N/A"
            )

        # ── Step 2: Identify missing facts ─────────────────────────────
        missing_facts = self._identify_missing_facts(domain, extracted_facts)
        # Note: We no longer exit early here to support flagged guessing.
        # If facts are missing, they will be passed to the prompt builder as missing,
        # and the LLM will recommend follow-ups or guess accordingly.

        # ── Step 3: Retrieve relevant rules ────────────────────────────
        retrieved_rules = await self.rag.retrieve(query, db) or []

        # ── Step 4: Build prompt and call LLM ──────────────────────────
        prompt = self.prompt_builder.build(
            question=query,
            retrieved_rules=retrieved_rules,
            extracted_facts=extracted_facts,
            missing_documents=[],
            conversation_history=conversation_history
        )
        llm_response = await self.llm.generate(
            prompt=prompt,
            retrieved_rules=retrieved_rules,
            extracted_facts=extracted_facts,
            missing_documents=[]
        )

        # ── Step 5: Parse decision and metadata from response ──────────
        # ── Step 5: Parse structured JSON decision from LLM response ──────
        parsed = self._parse_structured_response(llm_response)
        decision = parsed.get("decision", "Cannot Determine")
        confidence = parsed.get("confidence") or self._assess_confidence(retrieved_rules, extracted_facts)
        risks = parsed.get("risk_indicators") or self._identify_risks(extracted_facts)
        reasoning = parsed.get("reasoning") or parsed.get("summary") or llm_response

        return EligibilityResult(
            decision=decision,
            eligibility_status=parsed.get("summary", decision),
            supporting_rules=retrieved_rules,
            supporting_facts=self._format_facts(extracted_facts),
            missing_information=missing_facts,
            risk_indicators=risks,
            administrative_notes=reasoning,
            confidence_level=confidence,
            follow_up_questions=self._generate_questions(parsed.get("missing_information", [])),
            document_demand_notice=parsed.get("document_demand_notice", "")
        )

    def _identify_missing_facts(self, domain: str, facts: Dict) -> List[str]:
        """
        Returns a list of fact keys that are required for this domain
        but are not yet present in the case's extracted_facts.
        """
        required_facts: Dict[str, List[str]] = {
            "Promotion": [
                "years_of_service", "apar_rating", "passed_exam", "penalty_history"
            ],
            "Leave": [
                "leave_reason", "from_date", "to_date"
            ],
            "Leave.Earned": [
                "leave_reason", "from_date", "to_date"
            ],
            "Leave.Medical": [
                "leave_reason", "from_date", "to_date", "medical_fit"
            ],
            "Increment": [
                "appointment_date", "pay_level"
            ],
            "Discipline": [
                "penalty_history", "years_of_service"
            ],
            "Transfer": [
                "designation", "department"
            ],
            "Retirement": [
                "appointment_date", "date_of_birth"
            ],
            "Pension": [
                "appointment_date", "years_of_service"
            ],
            "Service": [
                "appointment_date", "designation"
            ],
            "DeptExam": [
                "passed_exam"
            ],
            "Benefits": [
                "designation", "pay_level"
            ],
        }
        needed = required_facts.get(domain, [])
        return [f for f in needed if facts.get(f) is None]

    def _generate_questions(self, missing_facts: List[str]) -> List[str]:
        questions_map = {
            "years_of_service":  "How many years of service have you completed in your current grade/post?",
            "apar_rating":       "What is your APAR grading score/benchmark rating for the last three years? (e.g. Outstanding, Very Good, Good)",
            "passed_exam":       "Have you passed the required departmental promotional examination? (Yes / No)",
            "penalty_history":   "Do you have any active penalty or disciplinary cases on your record? (Yes / No)",
            "appointment_date":  "What is your date of appointment to the current post? (DD-MM-YYYY)",
            "date_of_birth":     "What is your date of birth? (DD-MM-YYYY)",
            "pay_level":         "What is your current pay level under 7th CPC? (e.g. Level 6)",
            "leave_reason":      "What is the medical reason or diagnosis for the leave requested?",
            "from_date":         "What is the start date of the requested leave? (DD-MM-YYYY)",
            "to_date":           "What is the end date of the requested leave? (DD-MM-YYYY)",
            "medical_fit":       "Has a Railway Medical Officer certified you as fit/unfit for duty? (Yes = Fit / No = Unfit)",
            "medical_category":  "What is your current medical fitness classification? (e.g. A-1, B-1, C-1)",
            "designation":       "What is your current post/designation?",
            "department":        "Which department or division are you currently posted in?",
        }
        return [
            questions_map.get(f, f"Please provide details for: {f}")
            for f in missing_facts
        ]

    def _parse_structured_response(self, response: str) -> dict:
        """
        Parse the structured JSON block from the LLM response.
        Handles both clean JSON and JSON embedded inside ```json ... ``` fences.
        Falls back to naive substring parsing if JSON is malformed.
        """
        import json, re
        # Strip markdown code fences
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response, re.DOTALL)
        json_str = json_match.group(1) if json_match else response.strip()
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        # Try extracting just the JSON object from the response
        obj_match = re.search(r'\{.*\}', response, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group(0))
            except (json.JSONDecodeError, ValueError):
                pass
        # Final fallback: naive substring matching
        r = response.lower()
        if "not eligible" in r or "ineligible" in r:
            return {"decision": "Not Eligible", "confidence": "Low", "reasoning": response}
        if "eligible" in r:
            return {"decision": "Eligible", "confidence": "Low", "reasoning": response}
        return {"decision": "Cannot Determine", "confidence": "Low", "reasoning": response}

    def _parse_decision(self, response: str) -> str:
        """Legacy helper kept for compatibility."""
        parsed = self._parse_structured_response(response)
        return parsed.get("decision", "Cannot Determine")

    def _assess_confidence(self, rules: List, facts: Dict) -> str:
        if len(rules) >= 3 and len(facts) >= 3:
            return "High"
        if len(rules) >= 1 and len(facts) >= 1:
            return "Medium"
        return "Low"

    def _identify_risks(self, facts: Dict) -> List[str]:
        risks = []

        # Disciplinary risk
        penalty = facts.get("penalty_history")
        if penalty and str(penalty).lower() not in ["no", "none", "false", "0", ""]:
            risks.append("Active or recent disciplinary/penalty record detected. This may affect eligibility.")

        # APAR benchmark risk
        apar = facts.get("apar_rating")
        if apar and str(apar).lower() in ["average", "poor", "below benchmark"]:
            risks.append(f"APAR rating '{apar}' may not meet the required benchmark for this case.")

        # Medical fitness risk
        med_fit = facts.get("medical_fit")
        if med_fit and str(med_fit).lower() in ["no", "false", "0"]:
            risks.append("Employee has been medically decategorised. Alternative employment eligibility should be checked.")

        # Service years risk (less than 2 years is typically flagged)
        svc = facts.get("years_of_service")
        if svc is not None:
            try:
                if float(svc) < 2:
                    risks.append(f"Employee has only {svc} year(s) of service — may not meet minimum service requirements.")
            except (ValueError, TypeError):
                pass

        return risks

    def _format_facts(self, facts: Dict) -> List[Dict]:
        return [{"fact": k, "value": str(v)} for k, v in facts.items() if v is not None]
