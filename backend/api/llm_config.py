"""LLM configuration API routes for ThreatIQ.

Exposes a live connection-test endpoint so the settings page can verify a
candidate provider/model/API key combination before it is saved. The
endpoint builds a one-off client from the submitted ``LLMConfig``, sends a
minimal probe prompt with a short timeout, and always answers with a
structured JSON payload — failures are classified into actionable error
types instead of surfacing as raw 500s.

The submitted API key is used only for the in-flight test request and is
never persisted.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, Optional

from fastapi import APIRouter

from backend.llm.config_models import LLMConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])

TEST_PROMPT = "Reply with the single word OK."
TEST_TIMEOUT_SECONDS = 8

# Last LLM config submitted to test-connection this session (never persisted
# to disk). Used by /api/settings/probe-health to re-probe the active config.
_session_config: Optional[LLMConfig] = None


def get_session_llm_config() -> Optional[LLMConfig]:
    """Return the LLM config last tested this session, or None."""
    return _session_config

# Human-readable explanations matched to each classified error type.
_ERROR_MESSAGES = {
    "auth": "This API key was rejected. Double-check it's correct and hasn't expired.",
    "timeout": "The model didn't respond in time. Check your internet connection or try a different model.",
    "not_found": "Model wasn't found for this provider. Check the model name is spelled correctly.",
    "rate_limit": "You've hit the rate limit for this API key. Wait a moment and try again.",
    "connection": "Couldn't reach the model at that address. Make sure it's running and the URL is correct.",
    "unknown": "Something went wrong connecting to this model.",
}


@router.get("/config")
def get_active_llm_config() -> Dict[str, Any]:
    """Return the LLM provider/model configured via /setup this session.

    Read-only: the API key is never returned. ``configured`` is False when
    no connection test has run yet this session.
    """
    config = get_session_llm_config()
    if config is None:
        return {"configured": False, "provider": None, "model": None}
    return {"configured": True, "provider": config.provider, "model": config.model}


@router.post("/test-connection")
def test_llm_connection(config: LLMConfig) -> Dict[str, Any]:
    """Probe the configured LLM provider with a minimal test prompt.

    Sends ``TEST_PROMPT`` through a one-off client built from ``config``
    with an 8-second timeout. Returns ``{"status": "ok", "latency_ms": N}``
    on success; on any failure, classifies the exception and returns a
    structured error payload (``error_type`` + human-readable ``message``
    + ``raw_detail``) instead of raising.

    The API key is used only for this request and is never stored.
    """
    global _session_config
    _session_config = config

    try:
        llm = _build_test_client(config)
    except Exception as exc:  # noqa: BLE001 - structured response, never raise
        logger.warning("LLM test-connection client build failed: %s", exc)
        return _error_response("unknown", exc)

    start = time.perf_counter()
    try:
        _invoke_with_timeout(llm)
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "LLM test-connection ok: provider=%s model=%s latency=%dms",
            config.provider,
            config.model,
            latency_ms,
        )
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as exc:  # noqa: BLE001 - structured response, never raise
        error_type = _classify_error(exc)
        logger.warning(
            "LLM test-connection failed: provider=%s model=%s type=%s detail=%s",
            config.provider,
            config.model,
            error_type,
            exc,
        )
        return _error_response(error_type, exc)


# --------------------------------------------------------------------- #
# Client construction
# --------------------------------------------------------------------- #


def _invoke_with_timeout(llm: Any) -> None:
    """Invoke the probe prompt, enforcing TEST_TIMEOUT_SECONDS ourselves.

    Some provider SDKs reject short client-side deadlines (Gemini requires
    >=10s), so the timeout is enforced around the call instead of only
    through client options.
    """
    from langchain_core.messages import HumanMessage

    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(llm.invoke, [HumanMessage(content=TEST_PROMPT)])
    try:
        future.result(timeout=TEST_TIMEOUT_SECONDS)
    except FuturesTimeoutError:
        future.cancel()
        raise TimeoutError(
            f"LLM probe exceeded {TEST_TIMEOUT_SECONDS}s deadline"
        ) from None
    finally:
        pool.shutdown(wait=False)


def _build_test_client(config: LLMConfig) -> Any:
    """Build a one-off chat model for the probe, mirroring the explainer."""
    provider = (config.provider or "").strip().lower()

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        # No client-side timeout here: Gemini rejects deadlines under 10s,
        # and _invoke_with_timeout enforces the 8s limit around the call.
        return ChatGoogleGenerativeAI(
            model=config.model,
            api_key=config.api_key,
        )
    if provider in ("openai", "local"):
        from langchain_openai import ChatOpenAI

        kwargs: Dict[str, Any] = {
            "model": config.model,
            "api_key": config.api_key,
            # Fail fast so an unreachable base_url surfaces as a connection
            # error well inside the 8s envelope (SDK retries would exceed it).
            "request_timeout": TEST_TIMEOUT_SECONDS,
            "max_retries": 0,
        }
        if config.base_url:
            kwargs["base_url"] = config.base_url
        return ChatOpenAI(**kwargs)
    raise ValueError(
        f"Unsupported LLM provider: {config.provider!r} "
        "(expected 'gemini', 'openai', or 'local')"
    )


# --------------------------------------------------------------------- #
# Error classification and responses
# --------------------------------------------------------------------- #


def _classify_error(exc: Exception) -> str:
    """Map an arbitrary provider exception to a known error_type."""
    text = f"{type(exc).__name__} {exc}".lower()

    if "timeout" in text or "timed out" in text or "deadline exceeded" in text:
        return "timeout"
    if (
        "401" in text
        or "403" in text
        or "unauthorized" in text
        or "unauthenticated" in text
        or "invalid api key" in text
        or "api key not valid" in text
        or "api_key_invalid" in text
        or "permission_denied" in text
    ):
        return "auth"
    if "429" in text or "rate limit" in text or "resource_exhausted" in text or "quota" in text:
        return "rate_limit"
    if "404" in text or "not_found" in text or "not found" in text:
        return "not_found"
    if (
        "connection" in text
        or "connecterror" in text
        or "refused" in text
        or "failed to establish" in text
        or "name or service" in text
        or "getaddrinfo" in text
        or "unreachable" in text
    ):
        return "connection"
    return "unknown"


def _error_response(error_type: str, exc: Optional[Exception]) -> Dict[str, Any]:
    """Build the structured failure payload for a classified error."""
    return {
        "status": "error",
        "error_type": error_type,
        "message": _ERROR_MESSAGES[error_type],
        "raw_detail": str(exc) if exc else "unknown error",
    }
