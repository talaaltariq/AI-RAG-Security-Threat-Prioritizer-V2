import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend and root are in sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
for p in [str(backend_dir), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

load_dotenv(backend_dir / ".env")
load_dotenv(project_root / ".env")

try:
    from backend.llm.explainer import ThreatExplainer
except ImportError:
    from llm.explainer import ThreatExplainer

explainer = ThreatExplainer()
print(f"[*] Initialized ThreatExplainer with model: {explainer.model}", flush=True)

incident = {
    "incident_id": "INC-001",
    "asset": "prod-db-01",
    "asset_criticality": "CRITICAL",
    "latest_event_time": "2024-01-15T03:50:00Z",
    "mitre_technique": "T1110.001",
    "events": [
        {"event_type": "port_scan", "source_ip": "192.168.1.201"},
        {"event_type": "authentication_failure", "source_ip": "192.168.1.201"},
        {"event_type": "authentication_failure", "source_ip": "192.168.1.201"},
    ],
}

score_factors = {
    "total_score": 93,
    "factors": [
        {"factor": "Base Severity", "points": 15, "max_points": 20, "reason": "multiple authentication failures"},
        {"factor": "Anomaly Score", "points": 18, "max_points": 20, "reason": "high anomaly burst detected"},
        {"factor": "Asset Criticality", "points": 20, "max_points": 20, "reason": "prod-db-01 is critical infrastructure"},
        {"factor": "Threat Intel Match", "points": 20, "max_points": 20, "reason": "matched MITRE T1110.001"},
        {"factor": "Lateral Movement Risk", "points": 20, "max_points": 20, "reason": "database server target"}
    ]
}

rag_results = [
    {
        "content": "T1110.001 Brute Force: Password Guessing. Adversaries may systematically guess passwords to gain access to accounts.",
        "source": "MITRE ATT&CK v14",
        "technique_id": "T1110.001",
    }
]

print("[*] Generating LLM explanation...", flush=True)
result = explainer.explain(incident, score_factors, rag_results)

print("\n=== Explanation Result ===", flush=True)
print("Observed Evidence:", result.observed_evidence, flush=True)
print("\nRetrieved Context:", result.retrieved_context, flush=True)
print("\nAI Interpretation:", result.ai_interpretation, flush=True)
print("\nRecommended Action:", result.recommended_action, flush=True)
print("\nConfidence:", result.confidence, flush=True)
print("Confidence Reason:", result.confidence_reason, flush=True)
if result.error:
    print("\nError:", result.error, flush=True)
else:
    print("\n[+] LLM reasoning layer is working successfully!", flush=True)