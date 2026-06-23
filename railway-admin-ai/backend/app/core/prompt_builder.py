from typing import List, Dict

class PromptBuilder:
    """
    Builds the exact prompt sent to Qwen3.

    The system section strictly forbids the LLM from using its own
    training knowledge — it can ONLY use the retrieved rules and
    the extracted facts provided to it.
    """

    SYSTEM_PROMPT = """You are a Railway Personnel Administration Officer.

STRICT RULES YOU MUST FOLLOW:
1. You answer ONLY using the rules provided in RETRIEVED RULES below.
2. You use ONLY the facts provided in EMPLOYEE FACTS below.
3. Never use your own training knowledge for any administrative rule.
4. If the answer is not in the retrieved rules, respond EXACTLY:
   "The rule repository does not contain sufficient information to determine this."
5. If required documents are listed in MISSING DOCUMENTS, respond ONLY with
   a document demand notice. Do not attempt any eligibility evaluation.
6. Every claim you make must cite its rule_id (e.g. [PROM_001]) or
   its source document (e.g. [Service Book, p.3]).
7. Use formal, professional language at all times.
8. Never guess. Never assume. Never extrapolate."""

    def build(
        self,
        question: str,
        retrieved_rules: List[Dict],
        extracted_facts: Dict,
        missing_documents: List[str],
        conversation_history: List[Dict]
    ) -> str:

        rules_text = self._format_rules(retrieved_rules)
        facts_text = self._format_facts(extracted_facts)
        missing_text = self._format_missing(missing_documents)
        history_text = self._format_history(conversation_history)

        return f"""{self.SYSTEM_PROMPT}

=======================================
RETRIEVED RULES (from rules.md only):
=======================================
{rules_text}

=======================================
EMPLOYEE FACTS (from uploaded documents):
=======================================
{facts_text}

=======================================
MISSING DOCUMENTS (case cannot proceed without these):
=======================================
{missing_text}

=======================================
CONVERSATION HISTORY:
=======================================
{history_text}

=======================================
USER QUESTION:
=======================================
{question}

YOUR RESPONSE:"""

    def _format_rules(self, rules: List[Dict]) -> str:
        if not rules:
            return "No relevant rules retrieved for this query."
        parts = []
        for r in rules:
            parts.append(
                f"[{r['rule_id']}] {r['rule_name']}\n{r['description']}"
            )
        return "\n\n".join(parts)

    def _format_facts(self, facts: Dict) -> str:
        if not facts:
            return "No employee facts available. Documents not yet uploaded."
        lines = []
        for key, val in facts.items():
            lines.append(f"- {key}: {val}")
        return "\n".join(lines)

    def _format_missing(self, missing: List[str]) -> str:
        if not missing:
            return "None — all required documents have been submitted."
        return "\n".join([f"- {doc}" for doc in missing])

    def _format_history(self, history: List[Dict]) -> str:
        if not history:
            return "No previous conversation."
        lines = []
        for msg in history[-6:]:  # last 6 messages only
            role = "User" if msg.get("role") == "user" else "Assistant"
            lines.append(f"{role}: {msg.get('message', '')}")
        return "\n".join(lines)
