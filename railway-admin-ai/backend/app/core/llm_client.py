import httpx
import json
import logging
from typing import List, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)


# ── Base interface ─────────────────────────────────────────────────────────────

class BaseLLMClient:
    async def generate(
        self,
        prompt: str,
        retrieved_rules: Optional[List[Dict]] = None,
        extracted_facts: Optional[Dict] = None,
        missing_documents: Optional[List[str]] = None
    ) -> str:
        raise NotImplementedError


# ── Ollama client (local) ──────────────────────────────────────────────────────

class OllamaLLMClient(BaseLLMClient):
    """Sends prompts to a locally-running Ollama daemon."""

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
                            "temperature": 0.1,
                            "top_p": 0.9,
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except (httpx.ConnectError, httpx.HTTPStatusError, httpx.TimeoutException) as e:
            logger.warning(f"Ollama offline or failed: {str(e)}.")
            raise  # Let the factory handle the fallback


# ── Gemini client (Google AI cloud) ───────────────────────────────────────────

class GeminiLLMClient(BaseLLMClient):
    """
    Calls Google Gemini via the REST API (no SDK required).
    Uses gemini-2.0-flash by default for fast, low-latency responses.
    """

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def generate(
        self,
        prompt: str,
        retrieved_rules: Optional[List[Dict]] = None,
        extracted_facts: Optional[Dict] = None,
        missing_documents: Optional[List[str]] = None
    ) -> str:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in .env")

        url = self.GEMINI_API_URL.format(model=settings.GEMINI_MODEL)
        headers = {"Content-Type": "application/json"}
        params = {"key": settings.GEMINI_API_KEY}

        # Gemini expects a system instruction + user content structure
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.9,
                "maxOutputTokens": 2048,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, params=params, json=body)
                response.raise_for_status()
                data = response.json()

                # Extract text from Gemini response structure
                candidates = data.get("candidates", [])
                if not candidates:
                    raise ValueError("Gemini returned no candidates in response.")

                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()

                # Strip any surrounding markdown fences Gemini might add
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]

                return text.strip()

        except httpx.HTTPStatusError as e:
            # Log the full Gemini error body — critical for diagnosing bad API keys
            try:
                err_body = e.response.json()
            except Exception:
                err_body = e.response.text
            logger.error(f"Gemini API HTTP error {e.response.status_code}: {err_body}")
            raise
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning(f"Gemini API connection failed: {str(e)}.")
            raise


# ── Programmatic deterministic fallback ────────────────────────────────────────

def _programmatic_fallback(
    retrieved_rules: Optional[List[Dict]],
    extracted_facts: Optional[Dict],
    missing_documents: Optional[List[str]]
) -> str:
    """
    Rule-grounded deterministic evaluator.
    Activates when both Ollama and Gemini are unavailable.
    Returns a structured JSON string matching the LLM output schema.
    """
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


# ── Factory / unified client (used everywhere in the codebase) ─────────────────

class LLMClient:
    """
    Unified LLM client. Selects backend automatically from settings:
      - LLM_PROVIDER=gemini  → GeminiLLMClient (cloud, recommended)
      - LLM_PROVIDER=ollama  → OllamaLLMClient (local)
    Falls back to the programmatic deterministic evaluator if the
    selected provider is unreachable.
    """

    async def generate(
        self,
        prompt: str,
        retrieved_rules: Optional[List[Dict]] = None,
        extracted_facts: Optional[Dict] = None,
        missing_documents: Optional[List[str]] = None
    ) -> str:
        provider = (settings.LLM_PROVIDER or "ollama").lower()

        # Determine primary and optional secondary client
        if provider == "gemini" and settings.GEMINI_API_KEY:
            primary = GeminiLLMClient()
            secondary = OllamaLLMClient()
        else:
            primary = OllamaLLMClient()
            secondary = GeminiLLMClient() if settings.GEMINI_API_KEY else None

        # Try primary
        try:
            result = await primary.generate(prompt, retrieved_rules, extracted_facts, missing_documents)
            logger.info(f"[LLMClient] Response from {type(primary).__name__}.")
            return result
        except Exception as primary_err:
            logger.warning(f"[LLMClient] Primary ({type(primary).__name__}) failed: {primary_err}. Trying secondary.")

        # Try secondary if available
        if secondary:
            try:
                result = await secondary.generate(prompt, retrieved_rules, extracted_facts, missing_documents)
                logger.info(f"[LLMClient] Response from {type(secondary).__name__} (secondary fallback).")
                return result
            except Exception as secondary_err:
                logger.warning(f"[LLMClient] Secondary ({type(secondary).__name__}) also failed: {secondary_err}. Activating programmatic fallback.")

        # Final programmatic fallback — always available, no network required
        logger.warning("[LLMClient] All LLM providers offline. Using programmatic fallback.")
        return _programmatic_fallback(retrieved_rules, extracted_facts, missing_documents)
