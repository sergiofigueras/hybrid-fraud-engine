from __future__ import annotations

import numpy as np
import pandas as pd


RAW_MODEL_COLUMNS = [
    "amount",
    "currency",
    "merchant_category",
    "home_country",
    "country",
    "channel",
    "account_age_days",
    "avg_amount_30d",
    "tx_count_10m",
    "tx_count_24h",
    "minutes_since_last_tx",
    "distance_from_home_km",
    "distance_from_last_tx_km",
    "device_age_days",
    "device_trust_score",
    "merchant_chargeback_rate",
    "failed_auth_attempts_10m",
]

NUMERIC_FEATURES = [
    "amount",
    "account_age_days",
    "avg_amount_30d",
    "tx_count_10m",
    "tx_count_24h",
    "minutes_since_last_tx",
    "distance_from_home_km",
    "distance_from_last_tx_km",
    "device_age_days",
    "device_trust_score",
    "merchant_chargeback_rate",
    "failed_auth_attempts_10m",
    "amount_to_avg_ratio",
    "travel_speed_kmh",
    "is_new_device",
    "high_velocity_10m",
    "is_impossible_travel",
    "low_device_trust",
    "high_merchant_chargeback",
    "many_failed_auth",
    "is_cross_border",
]

CATEGORICAL_FEATURES = [
    "currency",
    "merchant_category",
    "channel",
]


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create model features with one shared training/inference function.

    This function must remain importable because the persisted scikit-learn
    pipeline references it through FunctionTransformer.
    """

    missing = sorted(set(RAW_MODEL_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing model input columns: {missing}")

    output = frame.copy()

    safe_average = output["avg_amount_30d"].clip(lower=1.0)
    safe_minutes = output["minutes_since_last_tx"].clip(lower=1.0)

    output["amount_to_avg_ratio"] = output["amount"] / safe_average
    output["travel_speed_kmh"] = (
        output["distance_from_last_tx_km"] / (safe_minutes / 60.0)
    ).clip(upper=20_000)

    output["is_new_device"] = (output["device_age_days"] <= 2).astype(int)
    output["high_velocity_10m"] = (output["tx_count_10m"] >= 5).astype(int)
    output["is_impossible_travel"] = (
        (output["distance_from_last_tx_km"] > 800)
        & (output["minutes_since_last_tx"] < 90)
    ).astype(int)
    output["low_device_trust"] = (output["device_trust_score"] < 0.35).astype(int)
    output["high_merchant_chargeback"] = (
        output["merchant_chargeback_rate"] >= 0.05
    ).astype(int)
    output["many_failed_auth"] = (
        output["failed_auth_attempts_10m"] >= 3
    ).astype(int)
    output["is_cross_border"] = (
        output["country"].astype(str) != output["home_country"].astype(str)
    ).astype(int)

    # Replace unexpected infinities before preprocessing.
    return output.replace([np.inf, -np.inf], np.nan)
