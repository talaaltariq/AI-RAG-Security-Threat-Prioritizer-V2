"""Per-request LLM configuration models for the ThreatIQ reasoning layer.

``LLMConfig`` carries the connection details for a single LLM call, letting
callers override the env-var-configured client on a per-request basis (e.g.
to test a different provider/model from the settings page) without touching
the shared ``ThreatExplainer`` instance.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class LLMConfig(BaseModel):
    """Connection details for one LLM call.

    Attributes:
        provider: LLM provider identifier. ``"gemini"`` builds a
            ChatGoogleGenerativeAI client; ``"openai"`` or ``"local"`` build
            a ChatOpenAI client (``base_url`` targets OpenAI-compatible
            endpoints such as a local inference server).
        model: Provider-specific model name (e.g. ``gemini-3.6-flash``,
            ``gpt-4o-mini``).
        api_key: API key for the provider. Local servers that ignore keys
            still require a non-empty placeholder value.
        base_url: Optional endpoint override, used by ``openai``/``local``
            providers for OpenAI-compatible APIs.
    """

    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None
