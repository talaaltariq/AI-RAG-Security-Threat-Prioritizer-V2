import sys
from pathlib import Path

# Allow running from the repo root: modules import via `backend.*`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.scoring.risk_scorer import RiskScorer
scorer = RiskScorer()

incident = {
    "severity": "HIGH",
    "asset_criticality": "CRITICAL",
    "has_known_exploit": True,
    "has_active_exploit": True,
    "events": ["e1", "e2", "e3", "e4"],
    "latest_event_time": "2024-01-15T03:50:00Z",
    "mitre_technique_matched": True,
    "high_relevance_ti": True
}

result = scorer.calculate(incident, anomaly_score_float=0.91)
print(result.total_score)  # Should be ~93
print(result.to_breakdown_dict())  # Should show all 7 factors