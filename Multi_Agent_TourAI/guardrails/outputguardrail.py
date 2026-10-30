import re
import json
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from Multi_Agent_TourAI.graph.state import TravelState
from Multi_Agent_TourAI.llms.llm import fast_llm
from Multi_Agent_TourAI.config.prompts import (OUTPUT_GUARDRAIL_SYSTEM_PROMPT, OUTPUT_GUARDRAIL_PROMPT_TEMPLATE, )
from Multi_Agent_TourAI.utils.logger import get_logger, log_execution

logger = get_logger(__name__)

# Patterns for sensitive credentials & tokens to redact
SECRET_PATTERNS = [
    re.compile(r"gsk_[a-zA-Z0-9_-]{20,}", re.IGNORECASE),                         # Groq API keys
    re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE),                          # Google Gemini API keys
    re.compile(r"tvly-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),                        # Tavily API keys
    re.compile(r"postgres(?:ql)?://[^\s\"']+", re.IGNORECASE),                    # PostgreSQL URLs
    re.compile(r"(?:api[_-]?key|secret|token)\s*[:=]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?", re.IGNORECASE),
]

# Unwanted internal system prompt leakage patterns
LEAKAGE_PATTERNS = [
    re.compile(r"Human Review Instruction:\s*.*?\n", re.IGNORECASE),
    re.compile(r"=== (?:EXISTING ITINERARY|FLIGHT DETAILS|HOTEL DETAILS|WEATHER DETAILS) ===\s*", re.IGNORECASE),
]

# Safe fallback message when a critical safety violation is detected
SAFE_FALLBACK_RESPONSE = (
    "I have processed your travel request. However, some specific recommendations "
    "could not be verified against live safety and accuracy sources. "
    "Please ask our assistant to check your specific flights, hotels, or destinations individually."
)


def _extract_json(text: str) -> dict[str, Any]:
    """Extracts the first valid JSON object from model response."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model did not return a valid JSON object.")
    return json.loads(text[start : end + 1])


def sanitize_text(text: str) -> tuple[str, bool]:
    """
    Deterministic Layer 1 Sanitization (Zero LLM Tokens):
    - Redacts any API keys or database URLs.
    - Strips internal system prompt leaks.
    - Fixes common broken markdown table issues.
    """
    modified = False
    cleaned = text

    # 1. Redact Secrets
    for pattern in SECRET_PATTERNS:
        if pattern.search(cleaned):
            cleaned = pattern.sub("[REDACTED_SECRET]", cleaned)
            modified = True

    # 2. Strip internal system prompt echoes
    for pattern in LEAKAGE_PATTERNS:
        if pattern.search(cleaned):
            cleaned = pattern.sub("", cleaned)
            modified = True

    # 3. Fix compressed Markdown Table Rows (ensure linebreaks between rows)
    if "|" in cleaned:
        table_fix = re.sub(r"(\|\s*)\n?(\|\s*[-:]+[-| :]*\|)\n?(\|)", r"\1\n\2\n\3", cleaned)
        if table_fix != cleaned:
            cleaned = table_fix
            modified = True

    return cleaned, modified


@log_execution
def output_guardrail(state: TravelState):
    """
    Output Guardrail Node for LangGraph:
    1. Layer 1: Deterministic regex scan & sanitization for secrets & broken formatting (0 tokens).
    2. Layer 2: Fast-LLM semantic audit for severe hallucinations & harmful instructions.
    3. Layer 3: Decision & dispatch:
       - 'allow': Pass final response through.
       - 'sanitize': Apply cleaned text without altering safe travel advice.
       - 'block': Replace with safe fallback response on critical safety violations.
    """
    raw_response = state.get("final_response", "")
    if not raw_response:
        messages = state.get("messages", [])
        if messages:
            raw_response = messages[-1].content if isinstance(messages[-1].content, str) else str(messages[-1].content)

    user_query = state.get("user_query", "")
    logger.info("Output Guardrail: Initiating multi-layer audit...")

    # Layer 1: Deterministic Sanitize (0 tokens, <1ms)
    sanitized_text, regex_modified = sanitize_text(raw_response)
    if regex_modified:
        logger.info("Output Guardrail: Layer 1 sanitized secrets or format traces.")

    # Layer 2: Lightweight Semantic Audit (Fast LLM gpt-oss-20b)
    # Token-budget optimization: pass concise summaries rather than massive raw JSONs
    def _truncate(text: str, max_chars: int = 400) -> str:
        s = str(text or "").strip()
        return s[:max_chars] + "..." if len(s) > max_chars else s

    audit_prompt = OUTPUT_GUARDRAIL_PROMPT_TEMPLATE.format(
        user_query=user_query,
        flight_results=_truncate(state.get("flight_results", "None")),
        hotel_results=_truncate(state.get("hotel_results", "None")),
        weather_results=_truncate(state.get("weather_results", "None")),
        maps_results=_truncate(state.get("maps_results", "None")),
        itinerary=_truncate(state.get("itinerary", "None")),
        final_response=_truncate(sanitized_text, max_chars=2500),
    )

    action = "allow"
    reason = "Passed audit"

    try:
        response = fast_llm.invoke([
            SystemMessage(content=OUTPUT_GUARDRAIL_SYSTEM_PROMPT),
            HumanMessage(content=audit_prompt)
        ])
        audit_res = _extract_json(response.content)
        is_safe = bool(audit_res.get("is_safe", True))
        action = str(audit_res.get("action", "allow")).lower().strip()
        reason = str(audit_res.get("reason", "")).strip()

        if not is_safe and action == "allow":
            action = "block"

    except Exception as e:
        # Fail-open strategy: LLM audit failure should not break valid user responses
        logger.warning(f"Output Guardrail LLM audit fallback (fail-open): {e}")
        action = "allow" if not regex_modified else "sanitize"
        reason = "Audit fallback allowed response"

    # Layer 3: Decision & State Dispatch
    if action == "block":
        logger.warning(f"Output Guardrail BLOCKED final response: {reason}")
        final_content = SAFE_FALLBACK_RESPONSE
        passed = False
    elif action == "sanitize" or regex_modified:
        logger.info(f"Output Guardrail SANITIZED final response: {reason}")
        final_content = sanitized_text
        passed = True
    else:
        logger.info("Output Guardrail PASSED: Output verified as safe.")
        final_content = sanitized_text
        passed = True

    # Append the single verified, sanitized AIMessage to conversation history
    return {
        "final_response": final_content,
        "messages": [AIMessage(content=final_content)],
        "output_guardrail_passed": passed,
        "output_guardrail_reason": reason,
        "llm_calls": 1,
    }


__all__ = ["output_guardrail", "sanitize_text"]
