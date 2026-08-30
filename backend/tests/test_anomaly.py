import sys
from pathlib import Path

# Allow running from the repo root: modules import via `backend.*`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.detection.anomaly_detector import AnomalyDetector

def test_anomaly_layer():
    detector = AnomalyDetector()

    # 1. Normal Event
    normal_event = {
        "event_id": "test-norm-01",
        "timestamp": "2026-08-29T10:15:00Z",
        "source_ip": "10.0.0.15",
        "destination_ip": "10.0.0.1",
        "destination_asset": "dev-server-01",
        "asset_criticality": "low",
        "event_type": "authentication",
        "protocol": "SSH",
        "port": 22,
        "failed_attempts": 0,
        "bytes_transferred": 1200,
        "events_from_ip_last_hour": 5,
        "raw_severity": "low",
        "details": "Routine login"
    }

    # 2. Attack Event (47 failed attempts, 3 AM off-hours)
    attack_event = {
        "event_id": "test-atk-01",
        "timestamp": "2026-08-29T03:00:00Z",
        "source_ip": "192.168.1.201",
        "destination_ip": "10.0.0.5",
        "destination_asset": "prod-db-01",
        "asset_criticality": "critical",
        "event_type": "authentication",
        "protocol": "SSH",
        "port": 22,
        "failed_attempts": 47,
        "bytes_transferred": 8500,
        "events_from_ip_last_hour": 50,
        "raw_severity": "high",
        "details": "Brute force attack"
    }

    print("--- Testing Prompt 4: Anomaly Detector ---")
    res_normal = detector.detect(normal_event)
    res_attack = detector.detect(attack_event)

    print(f"Normal Event: score={res_normal.get('anomaly_score')}, is_anomaly={res_normal.get('is_anomaly')}")
    print(f"Attack Event: score={res_attack.get('anomaly_score')}, is_anomaly={res_attack.get('is_anomaly')}")

    # Acceptance benchmarks
    assert res_normal["anomaly_score"] < 0.4, f"Normal score too high: {res_normal['anomaly_score']}"
    assert res_normal["is_anomaly"] is False, "Normal event flagged as anomaly"

    assert res_attack["anomaly_score"] > 0.7, f"Attack score too low: {res_attack['anomaly_score']}"
    assert res_attack["is_anomaly"] is True, "Attack event NOT flagged as anomaly"

    print("[OK] Prompt 4 Anomaly Detection PASSED!\n")

if __name__ == "__main__":
    test_anomaly_layer()