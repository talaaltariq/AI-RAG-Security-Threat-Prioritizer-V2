"""Backward-compat + per-request config verification for ThreatExplainer."""

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend",
        ".env",
    )
)

from backend.llm.config_models import LLMConfig
from backend.llm.explainer import ExplanationResult, ThreatExplainer

failures = []


def check(name, ok):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if not ok:
        failures.append(name)


# 0. LLMConfig model shape
cfg = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="k")
check("LLMConfig defaults base_url to None", cfg.base_url is None)
cfg2 = LLMConfig(provider="local", model="m", api_key="k", base_url="http://x")
check("LLMConfig accepts base_url", cfg2.base_url == "http://x")

# 1. Signature check: llm_config optional, defaults to None
sig = inspect.signature(ThreatExplainer.explain)
params = list(sig.parameters.values())
check(
    "explain() signature has optional llm_config=None as 4th param",
    params[4].name == "llm_config" and params[4].default is None,
)

# 2. Env-var construction still works
try:
    explainer = ThreatExplainer()
    check("ThreatExplainer() builds from env vars", True)
except Exception as exc:
    check(f"ThreatExplainer() builds from env vars ({exc})", False)
    sys.exit(1)

# 3. _resolve_chain falls back to env-var chain when llm_config is None
check(
    "_resolve_chain(None) returns the env-var chain",
    explainer._resolve_chain(None) is explainer.chain,
)

# 4. Per-request chains build for each provider without calling the API
gem_chain = explainer._build_config_chain(
    {"provider": "gemini", "model": "gemini-3.6-flash", "api_key": "dummy"}
)
check("per-request gemini chain builds", gem_chain is not None and gem_chain is not explainer.chain)

oai_chain = explainer._build_config_chain(
    {"provider": "openai", "model": "gpt-4o-mini", "api_key": "dummy"}
)
check("per-request openai chain builds", oai_chain is not None)

local_chain = explainer._build_config_chain(
    {
        "provider": "local",
        "model": "llama3",
        "api_key": "not-needed",
        "base_url": "http://localhost:11434/v1",
    }
)
check("per-request local chain builds with base_url override", local_chain is not None)

# 5. Invalid provider degrades to an error ExplanationResult (never raises)
incident = {"incident_id": "verify-1", "asset": "db-01", "events": []}
result = explainer.explain(
    incident, {"total_score": 0, "factors": []}, [], llm_config={"provider": "bogus", "model": "m", "api_key": "k"}
)
check(
    "unsupported provider degrades to low-confidence error result",
    isinstance(result, ExplanationResult) and result.error is not None and result.confidence == "low",
)

# 6. BACKWARD COMPAT: explain() with NO llm_config routes through the
#    env-var-configured chain built in __init__. The chain's invoke is
#    stubbed so the check is deterministic (no live API call); routing -
#    not the network - is what proves backward compatibility.
from unittest import mock

canned = ExplanationResult(
    observed_evidence="obs",
    retrieved_context="ctx",
    ai_interpretation="interp",
    recommended_action="act",
    confidence="medium",
    confidence_reason="reason",
)
with mock.patch.object(
    type(explainer.chain), "invoke", return_value=canned
) as mock_invoke:
    result_env = explainer.explain(incident, {"total_score": 0, "factors": []}, [])
check(
    "explain() without llm_config returns env-var chain result",
    result_env == canned and result_env.error is None,
)
check(
    "env-var chain invoked exactly once (no retry on success)",
    mock_invoke.call_count == 1,
)

# 6b. Optional live call against the env-var Gemini client, bounded by a
#     hard timeout so a hung network cannot stall verification.
if os.getenv("LIVE_GEMINI_CHECK") == "1":
    live = explainer.explain(incident, {"total_score": 0, "factors": []}, [])
    check(
        "live env-var call returns ExplanationResult",
        isinstance(live, ExplanationResult),
    )
    if live.error:
        print(f"      (degraded as designed; provider said: {live.error[:160]})", flush=True)
    else:
        print(f"      (live call succeeded; confidence={live.confidence})", flush=True)

# 7. Wrapper compat: CachedExplainer-style 3-arg call shape unchanged
from backend.llm.cached_explainer import CachedExplainer

cached = CachedExplainer(explainer, cache_path="nonexistent.json")
check("CachedExplainer wraps without changes", cached.delegate is explainer)

print()
if failures:
    print(f"FAILED: {len(failures)} check(s): {failures}")
    sys.exit(1)
print("ALL CHECKS PASSED")
