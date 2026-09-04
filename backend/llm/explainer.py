"""LLM reasoning layer for ThreatIQ incident explanation.

Calls Google Gemini (via langchain-google-genai) with the grounded incident
prompt by default, or a per-request LLM client (Gemini, OpenAI, or an
OpenAI-compatible local endpoint) when ``explain()`` receives an
``llm_config`` override. Responses are parsed into an ExplanationResult;
all failures degrade to a low-confidence ExplanationResult carrying the
error message.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

from pydantic import BaseModel

from backend.llm.prompt_builder import build_incident_prompt

if TYPE_CHECKING:
    from backend.rag.rag_retriever import RAGResult

DEFAULT_MODEL = "gemini-3.6-flash"
DEFAULT_TEMPERATURE = 0.2
MAX_RETRIES = 1


class ExplanationResult(BaseModel):
    """Structured analyst explanation produced by the LLM."""

    observed_evidence: str
    retrieved_context: str
    ai_interpretation: str
    recommended_action: str
    confidence: Literal["high", "medium", "low"]
    confidence_reason: str
    error: Optional[str] = None


class ThreatExplainer:
    """Generates grounded incident explanations via Google Gemini."""

    def __init__(self) -> None:
        """Create the Gemini chat model and a structured-output runnable.

        Credentials come from GEMINI_API_KEY, falling back to
        GOOGLE_API_KEY. The model comes from the LLM_MODEL env var,
        defaulting to ``gemini-3.6-flash``.
        """
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No LLM API key configured: set GEMINI_API_KEY or GOOGLE_API_KEY."
            )
        self.model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
        llm = ChatGoogleGenerativeAI(
            model=self.model,
            api_key=api_key,
            temperature=DEFAULT_TEMPERATURE,
        )
        self.chain = llm.with_structured_output(ExplanationResult)

    def explain(
        self,
        incident_dict: Dict[str, Any],
        score_factors_dict: Dict[str, Any],
        rag_results_list: List[RAGResult],
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> ExplanationResult:
        """Explain an incident; retry once on timeout, degrade on failure.

        Args:
            incident_dict: incident payload (asset, events, mitre_technique).
            score_factors_dict: composite score breakdown dict.
            rag_results_list: retrieved threat-intelligence entries.
            llm_config: optional per-request LLM override dict with keys
                ``provider``/``model``/``api_key``/``base_url`` (see
                ``backend.llm.config_models.LLMConfig``). When omitted, the
                env-var-configured client built at construction is used.

        Returns:
            ExplanationResult parsed from the LLM structured response, or an
            error-populated result with confidence="low" on any failure.
        """
        system_prompt, user_prompt = build_incident_prompt(
            incident_dict, score_factors_dict, rag_results_list
        )

        try:
            chain = self._resolve_chain(llm_config)
        except Exception as exc:  # noqa: BLE001 - degrade, never raise
            return self._error_result(exc)

        last_error: Optional[Exception] = None
        for attempt in range(1 + MAX_RETRIES):
            try:
                return self._call_and_parse(chain, system_prompt, user_prompt)
            except Exception as exc:  # noqa: BLE001 - degrade, never raise
                last_error = exc
                if not self._is_timeout(exc) or attempt >= MAX_RETRIES:
                    break
        return self._error_result(last_error)

    # ------------------------------------------------------------------ #
    # Client resolution
    # ------------------------------------------------------------------ #

    def _resolve_chain(self, llm_config: Optional[Dict[str, Any]]) -> Any:
        """Return the structured-output chain for this request.

        Falls back to the env-var-configured chain built in ``__init__``
        when no per-request config is supplied.
        """
        if llm_config is None:
            return self.chain
        return self._build_config_chain(llm_config)

    def _build_config_chain(self, llm_config: Dict[str, Any]) -> Any:
        """Build a one-off LLM client from a per-request config dict."""
        from backend.llm.config_models import LLMConfig

        config = LLMConfig.model_validate(llm_config)
        provider = (config.provider or "").strip().lower()

        if provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=config.model,
                api_key=config.api_key,
                temperature=DEFAULT_TEMPERATURE,
            )
        elif provider in ("openai", "local"):
            from langchain_openai import ChatOpenAI

            kwargs: Dict[str, Any] = {
                "model": config.model,
                "api_key": config.api_key,
                "temperature": DEFAULT_TEMPERATURE,
            }
            if config.base_url:
                kwargs["base_url"] = config.base_url
            llm = ChatOpenAI(**kwargs)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {config.provider!r} "
                "(expected 'gemini', 'openai', or 'local')"
            )
        return llm.with_structured_output(ExplanationResult)

    # ------------------------------------------------------------------ #
    # API call and response handling
    # ------------------------------------------------------------------ #

    def _call_and_parse(
        self, chain: Any, system_prompt: str, user_prompt: str
    ) -> ExplanationResult:
        """Invoke the chain once and coerce the response to ExplanationResult."""
        from langchain_core.messages import HumanMessage, SystemMessage

        result = chain.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        if isinstance(result, ExplanationResult):
            return result
        return ExplanationResult.model_validate(result)

    def _error_result(self, exc: Optional[Exception]) -> ExplanationResult:
        """Build a low-confidence fallback result carrying the error."""
        message = f"LLM explanation unavailable: {exc}"
        return ExplanationResult(
            observed_evidence=message,
            retrieved_context=message,
            ai_interpretation=message,
            recommended_action=message,
            confidence="low",
            confidence_reason=message,
            error=str(exc) if exc else "unknown error",
        )

    def _is_timeout(self, exc: Exception) -> bool:
        """Return True when the exception looks like a request timeout."""
        return "timeout" in type(exc).__name__.lower() or "timed out" in str(exc).lower()
