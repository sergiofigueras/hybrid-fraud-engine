import pandas as pd
import pytest

from fraud_engine.features import RAW_MODEL_COLUMNS, engineer_features
from tests.factories import transaction_payload


def test_engineer_features_creates_behavioral_signals() -> None:
    payload = transaction_payload(
        amount=1_000.0,
        avg_amount_30d=100.0,
        device_age_days=0,
        tx_count_10m=7,
        distance_from_last_tx_km=2_000.0,
        minutes_since_last_tx=30.0,
        device_trust_score=0.2,
        merchant_chargeback_rate=0.10,
        failed_auth_attempts_10m=4,
        country="US",
        home_country="BR",
    )
    frame = pd.DataFrame([{key: payload[key] for key in RAW_MODEL_COLUMNS}])

    engineered = engineer_features(frame)
    row = engineered.iloc[0]

    assert row["amount_to_avg_ratio"] == 10
    assert row["travel_speed_kmh"] == 4_000
    assert row["is_new_device"] == 1
    assert row["high_velocity_10m"] == 1
    assert row["is_impossible_travel"] == 1
    assert row["low_device_trust"] == 1
    assert row["high_merchant_chargeback"] == 1
    assert row["many_failed_auth"] == 1
    assert row["is_cross_border"] == 1


def test_engineer_features_rejects_missing_inputs() -> None:
    frame = pd.DataFrame([{"amount": 100.0}])

    with pytest.raises(ValueError, match="Missing model input columns"):
        engineer_features(frame)
