"""Simulation mode for the ThreatIQ mitigation layer.

Implements the "Simulate Fix" demo moment: applying the recommended
mitigation is projected by recalculating the composite risk score with the
exploit removed (``exploitability_pts = 0``) and the anomaly resolved
(``is_anomaly = False`` → ``anomaly_score_pts = 0``). All other factors are
kept exactly as scored, so the score drop is attributable solely to the
simulated fix — e.g. a CRITICAL incident can fall to LOW after mitigation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from backend.scoring.score_factors import ScoreFactors

# Composite-score → severity label thresholds (matches reporting bands).
_SEVERITY_BANDS: List[Tuple[int, str]] = [
    (80, "CRITICAL"),
    (60, "HIGH"),
    (40, "MEDIUM"),
]


def severity_for_score(total_score: int) -> str:
    """Map a composite score (0-100) to a severity label."""
    for threshold, label in _SEVERITY_BANDS:
        if total_score >= threshold:
            return label
    return "LOW"


class SimulationResult(BaseModel):
    """Before/after projection of applying a recommended fix."""

    incident_id: Optional[str] = None
    score_before: ScoreFactors
    score_after: ScoreFactors
    severity_before: str
    severity_after: str
    points_removed: int


def simulate_fix(
    score_factors: Union[ScoreFactors, Dict[str, Any]],
    incident_id: Optional[str] = None,
) -> SimulationResult:
    """Project the risk score after applying the recommended mitigation.

    The projected score zeroes ``exploitability_pts`` (the exploit path is
    removed) and ``anomaly_score_pts`` (the anomalous behavior is resolved,
    i.e. ``is_anomaly = False``); every other factor is unchanged.

    Args:
        score_factors: current ScoreFactors (or a flat dict coercible to it).
        incident_id: optional incident identifier for the result payload.

    Returns:
        SimulationResult with before/after ScoreFactors and severity labels.
    """
    before = (
        score_factors
        if isinstance(score_factors, ScoreFactors)
        else ScoreFactors.model_validate(score_factors)
    )

    reasons = dict(before.reasons)
    reasons["exploitability_pts"] = (
        "Simulated mitigation applied: exploit path removed "
        f"(was {before.exploitability_pts} pts)"
    )
    reasons["anomaly_score_pts"] = (
        "Simulated mitigation applied: anomalous behavior resolved, "
        f"is_anomaly=False (was {before.anomaly_score_pts} pts)"
    )

    after = before.model_copy(
        update={
            "exploitability_pts": 0,
            "anomaly_score_pts": 0,
            "total_score": before.total_score
            - before.exploitability_pts
            - before.anomaly_score_pts,
            "reasons": reasons,
        }
    )

    return SimulationResult(
        incident_id=incident_id,
        score_before=before,
        score_after=after,
        severity_before=severity_for_score(before.total_score),
        severity_after=severity_for_score(after.total_score),
        points_removed=before.total_score - after.total_score,
    )
