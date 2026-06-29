import json
from typing import List, Dict, Optional

class FallbackEvaluator:
    """
    Rule-grounded deterministic evaluator.
    Activates when both Ollama and Gemini are unavailable.
    Returns a structured JSON string matching the LLM output schema.
    """
    
    @staticmethod
    def evaluate(
        retrieved_rules: Optional[List[Dict]],
        extracted_facts: Optional[Dict],
        missing_documents: Optional[List[str]]
    ) -> str:
        if missing_documents:
            doc_list = "\n".join(f"- {doc}" for doc in missing_documents)
            return json.dumps({
                "decision": "Documents Required",
                "confidence": "N/A",
                "summary": "Case blocked. Required documents have not been submitted.",
                "reasoning": "The following documents are mandatory to proceed with the evaluation.",
                "cited_rules": [],
                "missing_information": [],
                "risk_indicators": [],
                "document_demand_notice": (
                    "DOCUMENT DEMAND NOTICE\n"
                    "The case cannot proceed because the following required documents are missing:\n"
                    f"{doc_list}\n\n"
                    "Please submit these documents to continue the administrative evaluation."
                )
            })

        if not retrieved_rules:
            return json.dumps({
                "decision": "Cannot Determine",
                "confidence": "Low",
                "summary": "No applicable rules were retrieved for this query.",
                "reasoning": "The rule repository does not contain sufficient information to determine this.",
                "cited_rules": [],
                "missing_information": [],
                "risk_indicators": [],
                "document_demand_notice": ""
            })

        facts = extracted_facts or {}
        cited = []
        decision = "Cannot Determine"
        reasoning_parts = []

        for rule in retrieved_rules:
            rule_id = rule.get("rule_id", "")
            rule_name = rule.get("rule_name", "").lower()
            desc = rule.get("description", "").lower()

            if "service" in desc or "years" in desc or "promotion" in rule_name:
                years_req = 5
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
                        cited.append(rule_id)
                        if emp_years >= years_req:
                            decision = "Eligible"
                            reasoning_parts.append(
                                f"[{rule_id}] {rule.get('rule_name')}: Employee has completed "
                                f"{emp_years} years, meeting the minimum {years_req}-year service requirement."
                            )
                        else:
                            decision = "Not Eligible"
                            reasoning_parts.append(
                                f"[{rule_id}] {rule.get('rule_name')}: Employee has only "
                                f"{emp_years} years of service; {years_req} years required."
                            )
                        break
                    except ValueError:
                        pass

            if "exam" in desc or "examination" in desc or "test" in desc:
                passed = facts.get("passed_exam") or facts.get("exam_passed")
                if passed is not None:
                    is_passed = str(passed).lower() in ["true", "yes", "1"]
                    cited.append(rule_id)
                    if is_passed:
                        decision = "Eligible"
                        reasoning_parts.append(
                            f"[{rule_id}] {rule.get('rule_name')}: "
                            "Departmental examination requirement has been successfully cleared."
                        )
                    else:
                        decision = "Not Eligible"
                        reasoning_parts.append(
                            f"[{rule_id}] {rule.get('rule_name')}: "
                            "Employee has not cleared the mandatory departmental examination."
                        )
                    break

        risks = []
        if facts.get("penalty_history"):
            risks.append("Active or recent disciplinary record detected.")

        apar = facts.get("apar_rating")
        if apar and str(apar).lower() in ["average", "poor", "below benchmark"]:
            risks.append("APAR rating may not meet the required benchmark.")

        summary = f"Based on available rules and submitted facts, the assessment is: {decision}."
        reasoning = (
            " ".join(reasoning_parts)
            if reasoning_parts
            else "No definitive rule-fact match could be established. A manual review by the Personnel Officer is recommended."
        )

        return json.dumps({
            "decision": decision,
            "confidence": "Medium" if decision != "Cannot Determine" else "Low",
            "summary": summary,
            "reasoning": reasoning,
            "cited_rules": cited,
            "missing_information": [],
            "risk_indicators": risks,
            "document_demand_notice": ""
        })
