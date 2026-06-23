import httpx
import logging
from typing import List, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Sends prompts to Qwen3 running locally via Ollama.
    If Ollama is offline or unavailable, falls back gracefully to a
    deterministic, rule-grounded Python evaluation.
    """

    async def generate(
        self,
        prompt: str,
        retrieved_rules: Optional[List[Dict]] = None,
        extracted_facts: Optional[Dict] = None,
        missing_documents: Optional[List[str]] = None
    ) -> str:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": settings.LLM_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,   # Low = more factual, less creative
                            "top_p": 0.9,
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except (httpx.ConnectError, httpx.HTTPStatusError, httpx.TimeoutException) as e:
            logger.warning(f"Ollama integration offline or failed: {str(e)}. Activating programmatic fallback.")
            return self._fallback_evaluate(retrieved_rules, extracted_facts, missing_documents)

    def _fallback_evaluate(
        self,
        retrieved_rules: Optional[List[Dict]] = None,
        extracted_facts: Optional[Dict] = None,
        missing_documents: Optional[List[str]] = None
    ) -> str:
        """
        Deterministic programmatic evaluator to serve as a reliable fallback
        when the local Ollama daemon is offline/busy.
        """
        # Rule 5: If required documents are listed in MISSING DOCUMENTS,
        # respond ONLY with a document demand notice.
        if missing_documents:
            doc_list = "\n".join(f"- {doc}" for doc in missing_documents)
            return (
                "[DOCUMENT DEMAND NOTICE]\n"
                "The case cannot proceed because the following required documents are missing:\n"
                f"{doc_list}\n\n"
                "Please submit these documents to continue the administrative evaluation."
            )

        if not retrieved_rules:
            return "The rule repository does not contain sufficient information to determine this."

        facts = extracted_facts or {}
        
        # Try to match rules with facts programmatically
        for rule in retrieved_rules:
            rule_id = rule.get("rule_id", "")
            rule_name = rule.get("rule_name", "").lower()
            desc = rule.get("description", "").lower()
            
            # 1. Check promotion rules (e.g. minimum service years)
            if "service" in desc or "years" in desc or "promotion" in rule_name:
                years_req = 5  # default assumption if not parsed
                if "5 years" in desc:
                    years_req = 5
                elif "3 years" in desc:
                    years_req = 3
                elif "2 years" in desc:
                    years_req = 2
                
                emp_years = facts.get("years_of_service") or facts.get("service_years")
                if emp_years is not None:
                    try:
                        emp_years = float(emp_years)
                        if emp_years >= years_req:
                            return (
                                f"Based on rule [{rule_id}] ({rule.get('rule_name')}), the employee is eligible for promotion. "
                                f"The rule requires a minimum of {years_req} years of service, and the employee has completed {emp_years} years."
                            )
                        else:
                            return (
                                f"Based on rule [{rule_id}] ({rule.get('rule_name')}), the employee is not eligible for promotion. "
                                f"The rule requires a minimum of {years_req} years of service, but the employee has completed only {emp_years} years."
                            )
                    except ValueError:
                        pass

            # 2. Check exam/test rules
            if "exam" in desc or "examination" in desc or "test" in desc:
                # If rule requires passing an exam, check if employee passed it
                passed = facts.get("passed_exam") or facts.get("exam_passed")
                if passed is not None:
                    is_passed = str(passed).lower() in ["true", "yes", "1"]
                    if is_passed:
                        return (
                            f"Based on rule [{rule_id}] ({rule.get('rule_name')}), the employee is eligible. "
                            "The departmental examination requirement has been successfully cleared."
                        )
                    else:
                        return (
                            f"Based on rule [{rule_id}] ({rule.get('rule_name')}), the employee is ineligible. "
                            "The employee has not cleared the mandatory departmental examination."
                        )

            # 3. Check medical category/incapacitation rules
            if "medical" in desc or "incapacitated" in desc or "fitness" in desc:
                med_fit = facts.get("medical_fit") or facts.get("medically_fit")
                if med_fit is not None:
                    is_fit = str(med_fit).lower() in ["true", "yes", "1"]
                    if not is_fit:
                        return (
                            f"Based on rule [{rule_id}] ({rule.get('rule_name')}), the employee is medically incapacitated. "
                            "Alternative employment matching their medical decategorization class should be evaluated."
                        )

        # Default fallback when no rules match the employee facts deterministically
        return "The rule repository does not contain sufficient information to determine this."
