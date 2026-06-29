import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class DemandResult:
    all_present: bool
    submitted: List[str]
    missing: List[str]
    demand_notice: str
    rule_citations: List[str]

class DocumentDemandEngine:
    """
    THE GATEKEEPER.

    Before ANY eligibility evaluation happens, this engine checks
    whether all required documents for the case domain have been
    submitted. If even one is missing, it blocks the case and
    returns a formal Document Demand Notice.

    The system will NOT call the LLM or run any rule evaluation
    until this check passes.
    """

    def __init__(self):
        req_path = Path(__file__).parent.parent / "knowledge" / "document_requirements.json"
        self.requirements = json.loads(req_path.read_text())

    def check(
        self,
        domain: str,
        submitted_doc_types: List[str],
        employee_facts: Dict = None
    ) -> DemandResult:

        domain_req = self.requirements.get(domain, {})
        if not domain_req:
            # If domain is not defined, default to requiring nothing (pass-through)
            return DemandResult(
                all_present=True,
                submitted=submitted_doc_types,
                missing=[],
                demand_notice="",
                rule_citations=[]
            )

        mandatory = domain_req.get("mandatory", [])
        conditional = domain_req.get("conditional", {})
        rule_citations = domain_req.get("rule_citations", [])

        # Determine which conditional docs are needed
        required = list(mandatory)
        if employee_facts:
            for condition, docs in conditional.items():
                if self._condition_met(condition, employee_facts):
                    required.extend(docs)

        # Compare
        submitted_lower = [s.lower() for s in submitted_doc_types]
        missing = [
            doc for doc in required
            if not any(doc.lower() in s for s in submitted_lower)
        ]

        all_present = len(missing) == 0

        notice = "" if all_present else self._build_notice(
            domain, mandatory, missing, submitted_doc_types,
            rule_citations, domain_req.get("reasons", {})
        )

        return DemandResult(
            all_present=all_present,
            submitted=submitted_doc_types,
            missing=missing,
            demand_notice=notice,
            rule_citations=rule_citations
        )

    def _condition_met(self, condition: str, facts: Dict) -> bool:
        conditions = {
            "if_penalty_exists":   lambda f: f.get("penalty_history") not in [None, False, "no", "none", "false", "0", "", []],
            "if_medical_grounds":  lambda f: f.get("leave_reason") == "medical",
            "if_hospitalized":     lambda f: f.get("hospitalized") is True,
            "if_appealing":        lambda f: f.get("appeal_filed") is True,
            "if_spouse_transfer":  lambda f: bool(f.get("spouse_transfer_order")),
        }
        evaluator = conditions.get(condition)
        return evaluator(facts) if evaluator else False

    def _build_notice(
        self,
        domain: str,
        mandatory: List[str],
        missing: List[str],
        submitted: List[str],
        citations: List[str],
        reasons: Dict
    ) -> str:

        submitted_lines = "\n".join([f"  - {d}" for d in submitted]) or "  (none submitted yet)"
        missing_lines = "\n".join([f"  - {d}  * REQUIRED" for d in missing])

        reason_lines = ""
        for doc in missing:
            reason = reasons.get(doc, f"Required to verify facts relevant to {domain} eligibility.")
            rule = ", ".join(citations) if citations else "applicable rule"
            reason_lines += f"\n  - {doc}: {reason} [{rule}]"

        return f"""
================================================================
              DOCUMENT REQUIREMENT NOTICE                     
              Case Type: {domain:<36}
================================================================

To evaluate your {domain} request, the following documents
are required:

SUBMITTED :
{submitted_lines}

MISSING : ! CASE CANNOT PROCEED
{missing_lines}

WHY THESE DOCUMENTS ARE NEEDED:
{reason_lines}

*  This case cannot be evaluated until all required documents
   are uploaded. Please submit the missing documents to continue.
""".strip()
