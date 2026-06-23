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
        if missing_facts:
            questions = self._generate_questions(missing_facts)
            return EligibilityResult(
                decision="Cannot Determine",
                eligibility_status="Additional information required",
                missing_information=missing_facts,
                follow_up_questions=questions,
                confidence_level="N/A"
            )

        # ── Step 3: Retrieve relevant rules ────────────────────────────
        retrieved_rules = await self.rag.retrieve(query, db)
        if not retrieved_rules:
            return EligibilityResult(
                decision="Cannot Determine",
                eligibility_status="No applicable rules found",
                administrative_notes=(
                    "The rule repository does not contain sufficient "
                    "information to determine this."
                ),
                confidence_level="N/A"
            )

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
        decision = self._parse_decision(llm_response)
        confidence = self._assess_confidence(retrieved_rules, extracted_facts)
        risks = self._identify_risks(extracted_facts)

        return EligibilityResult(
            decision=decision,
            eligibility_status=decision,
            supporting_rules=retrieved_rules,
            supporting_facts=self._format_facts(extracted_facts),
            risk_indicators=risks,
            administrative_notes=llm_response,
            confidence_level=confidence
        )

    def _identify_missing_facts(self, domain: str, facts: Dict) -> List[str]:
        required_facts = {
            "Promotion": [
                "years_of_service", "apar_rating", "passed_exam", "penalty_history"
            ],
            "Leave.Medical": [
                "leave_reason", "from_date", "to_date"
            ],
            "Increment": [
                "appointment_date", "pay_level"
            ],
        }
        needed = required_facts.get(domain, [])
        return [f for f in needed if facts.get(f) is None]

    def _generate_questions(self, missing_facts: List[str]) -> List[str]:
        questions_map = {
            "years_of_service":     "How many years of service have you completed in your current grade/post?",
            "apar_rating":          "What is your APAR grading score/benchmark rating for the last three years?",
            "passed_exam":          "Have you passed the required departmental promotional examination?",
            "penalty_history":      "Do you have any active penalty or disciplinary cases on your record?",
            "appointment_date":     "What is your date of appointment to the current post?",
            "pay_level":            "What is your current pay level?",
            "leave_reason":         "What is the medical reason or diagnosis for the leave requested?",
            "from_date":            "What is the start date of the requested medical leave?",
            "to_date":              "What is the end date of the requested medical leave?",
        }
        return [
            questions_map.get(f, f"Please provide details for: {f}")
            for f in missing_facts
        ]

    def _parse_decision(self, response: str) -> str:
        r = response.lower()
        if "not eligible" in r or "ineligible" in r:
            return "Not Eligible"
        if "eligible" in r:
            return "Eligible"
        return "Cannot Determine"

    def _assess_confidence(self, rules: List, facts: Dict) -> str:
        if len(rules) >= 3 and len(facts) >= 3:
            return "High"
        if len(rules) >= 1 and len(facts) >= 1:
            return "Medium"
        return "Low"

    def _identify_risks(self, facts: Dict) -> List[str]:
        risks = []
        if facts.get("penalty_history"):
            risks.append("Active or recent disciplinary record detected.")
        
        apar = facts.get("apar_rating")
        if apar and str(apar).lower() in ["average", "poor", "below benchmark"]:
            risks.append("APAR rating may not meet the required benchmark.")
        return risks

    def _format_facts(self, facts: Dict) -> List[Dict]:
        return [{"fact": k, "value": str(v)} for k, v in facts.items() if v is not None]
