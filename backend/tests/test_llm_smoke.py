import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow running from the repo root: modules import via `backend.*`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv("backend/.env")

from backend.llm.explainer import ThreatExplainer

incident = {
    "id": "INC-0042",
    "latest_event_time": "2026-08-29T03:14:00",
    "asset": "web-server-01",
    "asset_criticality": "high",
    "mitre_technique": "T1110.001",
    "events": [
        {"event_type": "failed_login", "source_ip": "203.0.113.7"},
        {"event_type": "failed_login", "source_ip": "203.0.113.7"},
        {"event_type": "failed_login", "source_ip": "203.0.113.7"},
        {"event_type": "successful_login", "source_ip": "203.0.113.7"},
    ],
}
score = {
    "total_score": 87,
    "factors": [
        {"factor": "Base Severity", "points": 16, "max_points": 20, "reason": "high severity events"},
        {"factor": "Anomaly Score", "points": 18, "max_points": 20, "reason": "off-hours login burst"},
        {"factor": "Asset Criticality", "points": 20, "max_points": 20, "reason": "asset is high criticality"},
    ],
}
rag = [
    {
        "content": "Password Guessing (T1110.001): adversaries may guess passwords to gain access to accounts, often via repeated failed authentication attempts followed by a success.",
        "source": "mitre_attack",
        "technique_id": "T1110.001",
        "cve_id": None,
        "relevance_score": 0.91,
    },
]

explainer = ThreatExplainer()
print("model:", explainer.model)
result = explainer.explain(incident, score, rag)
print(json.dumps(result.model_dump(), indent=2))
