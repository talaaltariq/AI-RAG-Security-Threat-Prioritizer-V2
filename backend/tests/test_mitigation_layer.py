import sys
from pathlib import Path

# Ensure backend and project root are in sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
for p in [str(backend_dir), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.mitigation import (
    MitigationStore,
    RecommendationEngine,
    RecommendationUrgency,
    apply_action,
    simulate_fix,
)
from backend.scoring.score_factors import ScoreFactors

failures = []


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}", flush=True)
    if not condition:
        failures.append(label)


INCIDENT = {
    "incident_id": "INC-001",
    "asset": "prod-db-01",
    "asset_criticality": "CRITICAL",
    "severity_label": "CRITICAL",
    "mitre_technique": "T1110.001",
    "events": [
        {"event_type": "authentication_failure", "source_ip": "192.168.1.201"},
        {"event_type": "authentication_failure", "source_ip": "192.168.1.201"},
        {"event_type": "port_scan", "source_ip": "192.168.1.201"},
    ],
}

engine = RecommendationEngine()

print("\n=== 1. Recommendation layer ===", flush=True)

# 1a. No LLM explanation -> deterministic fallback, always populated
rec = engine.recommend(INCIDENT, {"total_score": 93})
check("fallback recommendation is populated", bool(rec.action))
check("fallback names the asset", "prod-db-01" in rec.action)
check("CRITICAL incident ranked IMMEDIATE", rec.urgency is RecommendationUrgency.IMMEDIATE)
check("fallback action is urgency-framed", rec.action.startswith("Immediately"))
check("fallback source is 'fallback'", rec.source == "fallback")
check("fallback is conservative", rec.conservative)

# 1b. Specific + conservative LLM action passes through
good_llm = {
    "recommended_action": (
        "Isolate prod-db-01 from the network segment and review "
        "authentication logs for successful logins from 192.168.1.201; "
        "expected outcome: brute-force access is contained."
    )
}
rec = engine.recommend(INCIDENT, {"total_score": 93}, good_llm)
check("valid LLM action is used", rec.source == "llm")
check("valid LLM action kept verbatim content", "Isolate prod-db-01" in rec.action)

# 1c. Vague LLM action -> fallback
vague_llm = {"recommended_action": "Investigate this further."}
rec = engine.recommend(INCIDENT, {"total_score": 93}, vague_llm)
check("vague LLM action rejected to fallback", rec.source == "fallback")
check("fallback still names the asset", "prod-db-01" in rec.action)

# 1d. Non-conservative LLM action -> fallback
destructive_llm = {
    "recommended_action": (
        "Block the IP 192.168.1.201 at the perimeter firewall and shut down "
        "prod-db-01 to stop the attack immediately."
    )
}
rec = engine.recommend(INCIDENT, {"total_score": 93}, destructive_llm)
check("destructive LLM action rejected to fallback", rec.source == "fallback")
check("fallback avoids blocking", "block" not in rec.action.lower())

# 1e. LOW severity -> monitoring recommendation
low_incident = dict(INCIDENT, severity_label="LOW")
rec = engine.recommend(low_incident, {"total_score": 15})
check("LOW incident ranked MONITOR", rec.urgency is RecommendationUrgency.MONITOR)
check("LOW incident gets monitoring action", "monitoring" in rec.action.lower())

print("\n=== 2. Analyst action state machine ===", flush=True)
check("acknowledge -> acknowledged", apply_action("active", "acknowledge").value == "acknowledged")
check("escalate -> escalated", apply_action("acknowledged", "escalate").value == "escalated")
check("resolve -> resolved", apply_action("escalated", "resolve").value == "resolved")
try:
    apply_action("resolved", "acknowledge")
    check("resolved is terminal", False)
except ValueError:
    check("resolved is terminal", True)
try:
    apply_action("active", "delete")
    check("unknown action rejected", False)
except ValueError:
    check("unknown action rejected", True)

print("\n=== 3. Simulation mode ===", flush=True)
before = ScoreFactors(
    base_severity=15,
    anomaly_score_pts=18,
    asset_criticality_pts=20,
    exploitability_pts=15,
    evidence_count_pts=10,
    recency_pts=10,
    ti_relevance_pts=5,
    total_score=93,
    reasons={"exploitability_pts": "active exploit", "anomaly_score_pts": "0.91"},
)
sim = simulate_fix(before, incident_id="INC-001")
print(f"    score: {sim.score_before.total_score} -> {sim.score_after.total_score}", flush=True)
print(f"    severity: {sim.severity_before} -> {sim.severity_after}", flush=True)
check("simulated exploitability is 0", sim.score_after.exploitability_pts == 0)
check("simulated anomaly pts are 0 (is_anomaly=False)", sim.score_after.anomaly_score_pts == 0)
check("score dropped from 93", sim.score_after.total_score == 93 - 15 - 18)
check("severity dropped CRITICAL -> HIGH", (sim.severity_before, sim.severity_after) == ("CRITICAL", "HIGH"))
check("other factors untouched", sim.score_after.asset_criticality_pts == 20)
check("dict input also works", simulate_fix(before.model_dump()).score_after.total_score == 60)

print("\n=== 4. Analyst action persistence ===", flush=True)
store = MitigationStore(":memory:")
check("unseen incident defaults to active", store.get_status("INC-001") == "active")
result = store.record_action("INC-001", "acknowledge", analyst_note="Investigating now")
check("action saved to database", store.get_status("INC-001") == "acknowledged")
check("action record returned", result["action"]["action"] == "acknowledge")
store.record_action("INC-001", "escalate")
check("status updated to escalated", store.get_status("INC-001") == "escalated")
actions = store.list_actions("INC-001")
check("both actions persisted in order", [a["action"] for a in actions] == ["acknowledge", "escalate"])
store.mark_mitigated("INC-001")
check("simulate-fix marks incident resolved", store.get_status("INC-001") == "resolved")
try:
    store.record_action("INC-001", "acknowledge")
    check("no actions after resolution", False)
except ValueError:
    check("no actions after resolution", True)
check("invalid action writes nothing", len(store.list_actions("INC-001")) == 3)

print("\n=== Summary ===", flush=True)
if failures:
    print(f"[-] {len(failures)} check(s) failed: {failures}", flush=True)
    sys.exit(1)
print("[+] Phase 13 mitigation layer is working successfully!", flush=True)
