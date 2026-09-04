"""IsolationForest-based anomaly detection for ThreatIQ security events.

On first use the detector trains an IsolationForest on 500 synthetic
"normal" events and persists it to ``backend/models/isolation_forest.pkl``.
Subsequent runs load the persisted model directly.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from backend.detection.feature_extractor import (
    COMMON_PORTS,
    FEATURE_NAMES,
    FeatureExtractor,
)
from backend.models_config.pipeline_settings import load_settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[1] / "models" / "isolation_forest.pkl"
)


class AnomalyDetector:
    """Unsupervised anomaly detector backed by scikit-learn IsolationForest."""

    CONTAMINATION = 0.1
    N_ESTIMATORS = 100
    RANDOM_STATE = 42
    ANOMALY_THRESHOLD = 0.5
    SYNTHETIC_SAMPLE_SIZE = 500

    def __init__(self, model_path: Optional[Union[str, Path]] = None) -> None:
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.feature_extractor = FeatureExtractor()
        self.model: Optional[IsolationForest] = None
        # Range of decision_function values observed on the training data;
        # used to normalize raw scores into the 0.0-1.0 range.
        self._df_min = 0.0
        self._df_max = 1.0

        if self.model_path.exists():
            self._load_model()
        else:
            self._train_and_save()

    # ------------------------------------------------------------------ #
    # Training / persistence
    # ------------------------------------------------------------------ #

    def _generate_synthetic_normal_events(self) -> np.ndarray:
        """Generate synthetic baseline traffic shaped like normal business hours.

        hour 8-18, failed_attempts 0-2, bytes 100-5000, common service ports,
        known IPs, and low (1-2) asset criticality.
        """
        n = self.SYNTHETIC_SAMPLE_SIZE
        rng = np.random.default_rng(self.RANDOM_STATE)
        return np.column_stack(
            [
                rng.integers(8, 19, size=n),  # hour_of_day (8-18)
                rng.integers(0, 3, size=n),  # failed_attempts (0-2)
                rng.integers(100, 5001, size=n),  # bytes_transferred
                rng.choice(COMMON_PORTS, size=n),  # port_number
                rng.integers(1, 11, size=n),  # events_from_ip_last_hour
                np.ones(n),  # is_known_ip
                rng.integers(1, 3, size=n),  # asset_criticality_score (1-2)
            ]
        ).astype(float)

    def _train_and_save(self) -> None:
        """Train on synthetic normal events and persist the model to disk."""
        logger.info("No model found at %s; training a new IsolationForest.", self.model_path)
        training_data = self._generate_synthetic_normal_events()
        model = IsolationForest(
            contamination=self.CONTAMINATION,
            n_estimators=self.N_ESTIMATORS,
            random_state=self.RANDOM_STATE,
        )
        model.fit(training_data)
        decision_scores = model.decision_function(training_data)
        self._df_min = float(decision_scores.min())
        self._df_max = float(decision_scores.max())
        self.model = model

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"model": model, "df_min": self._df_min, "df_max": self._df_max},
            self.model_path,
        )
        logger.info("Trained IsolationForest saved to %s.", self.model_path)

    def _load_model(self) -> None:
        """Load a previously trained model from disk."""
        payload = joblib.load(self.model_path)
        if isinstance(payload, dict) and "model" in payload:
            self.model = payload["model"]
            self._df_min = float(payload.get("df_min", 0.0))
            self._df_max = float(payload.get("df_max", 1.0))
        else:  # backward compatibility: plain model object
            self.model = payload
        logger.info("Loaded IsolationForest from %s.", self.model_path)

    # ------------------------------------------------------------------ #
    # Inference
    # ------------------------------------------------------------------ #

    def _normalize_score(self, raw_score: float) -> float:
        """Invert and scale decision_function output into the 0.0-1.0 range.

        sklearn's decision_function returns higher values for normal points
        and lower (negative) values for anomalies, so the raw score is
        inverted against the training-data range and clipped to [0, 1].
        """
        span = self._df_max - self._df_min
        if span <= 0:
            span = 1.0
        normalized = (self._df_max - raw_score) / span
        return float(np.clip(normalized, 0.0, 1.0))

    def _resolve_threshold(self, threshold: Optional[float]) -> float:
        """Return the explicit threshold, else the configured DB value.

        When no threshold is passed, the current value is read from the
        persisted PipelineSettings row; any lookup failure falls back to
        the class default so detection never breaks on a settings read.
        """
        if threshold is not None:
            return float(threshold)
        try:
            return float(load_settings().anomaly_threshold)
        except Exception:  # noqa: BLE001 - detection must never fail here
            logger.exception("Settings lookup failed; using default threshold.")
            return self.ANOMALY_THRESHOLD

    def detect(
        self, event_dict: Dict[str, Any], threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Score a normalized event dict for anomalous behavior.

        Args:
            event_dict: normalized event fields (see backend/models/event.py).
            threshold: anomaly cutoff in 0.0-1.0; when omitted, the current
                value from PipelineSettings is used (default 0.5).

        Returns:
            {
                "anomaly_score": float in 0.0-1.0 (higher = more anomalous),
                "is_anomaly": True when anomaly_score > threshold,
                "features_used": list of feature names, in model order,
            }
        """
        if self.model is None:
            raise RuntimeError("Anomaly detection model is not initialized.")

        threshold = self._resolve_threshold(threshold)
        features = self.feature_extractor.extract(event_dict)
        raw_score = float(self.model.decision_function(features)[0])
        anomaly_score = round(self._normalize_score(raw_score), 4)

        return {
            "anomaly_score": anomaly_score,
            "is_anomaly": bool(anomaly_score > threshold),
            "features_used": list(FEATURE_NAMES),
        }
