"""ThreatIQ mitigation layer (Phase 13): recommendations, analyst actions,
human-in-the-loop status transitions, and fix simulation."""

from backend.mitigation.analyst_actions import (
    ACTION_TO_STATUS,
    VALID_ACTIONS,
    apply_action,
    build_action_record,
)
from backend.mitigation.recommender import (
    Recommendation,
    RecommendationEngine,
    RecommendationUrgency,
)
from backend.mitigation.simulator import SimulationResult, severity_for_score, simulate_fix
from backend.mitigation.store import MitigationStore

__all__ = [
    "ACTION_TO_STATUS",
    "VALID_ACTIONS",
    "apply_action",
    "build_action_record",
    "Recommendation",
    "RecommendationEngine",
    "RecommendationUrgency",
    "SimulationResult",
    "severity_for_score",
    "simulate_fix",
    "MitigationStore",
]
