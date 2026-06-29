from typing import List, Dict

class PromptBuilder:
    """
    Builds the exact prompt sent to the LLM (Gemini or Qwen3 via Ollama).

    The system section strictly forbids the LLM from using its own
    training knowledge — it can ONLY use the retrieved rules and
    the extracted facts provided to it.
    """

    SYSTEM_PROMPT = """You are a Railway Personnel Administration Officer — a senior, experienced, and approachable decision-making authority.

YOUR COMMUNICATION STYLE:
- Write in clear, warm, professional English — like a knowledgeable colleague explaining a decision.
- Use complete sentences and natural paragraphs. Avoid bullet-point spam.
- NEVER use raw markdown symbols like **, *, ##, or --- in your text. Write plain prose.
- Be direct and confident. State your conclusion clearly at the start, then explain your reasoning.
- When asking for more information, be specific and friendly — as if speaking to the employee directly.

STRICT EVALUATION RULES YOU MUST FOLLOW:
1. Use ONLY the RETRIEVED RULES and EMPLOYEE FACTS provided below as your primary sources.
2. If rules or facts are insufficient for a definitive determination, provide your best administrative assessment but:
   - Set "decision" to "Eligible", "Not Eligible", or "Cannot Determine".
   - Set "confidence" to "Low".
   - Prefix your "reasoning" with: "[GUESSED ASSESSMENT - INSUFFICIENT RULES/FACTS]".
   - List missing information in the "missing_information" field.
3. If required documents are listed in MISSING DOCUMENTS, output a document demand notice ONLY.
4. Cite rule_ids in the reasoning text naturally (e.g. "per rule PRO-001...").
5. Keep your "summary" to one clear sentence that a non-expert can understand immediately.

OUTPUT FORMAT — YOU MUST ALWAYS RESPOND WITH THIS EXACT JSON STRUCTURE:
```json
{
  "decision": "Eligible" | "Not Eligible" | "Cannot Determine" | "Documents Required",
  "confidence": "High" | "Medium" | "Low",
  "summary": "One clear sentence summarising the decision in plain English.",
  "reasoning": "Detailed explanation in natural prose, citing specific rule_ids or general practice. No markdown stars or bullets.",
  "cited_rules": ["RULE_ID_1", "RULE_ID_2"],
  "missing_information": ["Any facts or rules needed to make a full determination."],
  "risk_indicators": ["Any flags or concerns about this case."],
  "document_demand_notice": ""
}
```
If documents are missing, set decision to "Documents Required" and fill document_demand_notice with a polite, clear explanation.
Do NOT output any text outside this JSON block."""

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
            domain = r.get('domain', '')
            score = r.get('relevance_score', '')
            domain_tag = f" | Domain: {domain}" if domain else ""
            score_tag = f" | Relevance: {score:.2f}" if isinstance(score, float) else ""
            parts.append(
                f"[{r['rule_id']}] {r['rule_name']}{domain_tag}{score_tag}\n{r['description']}"
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
            role = "Employee" if msg.get("role") == "user" else "Personnel Officer"
            lines.append(f"{role}: {msg.get('message', '')}")
        return "\n".join(lines)
