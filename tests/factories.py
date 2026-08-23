from __future__ import annotations

from typing import Any

from fraud_engine.schemas import Transaction


def transaction_payload(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "transaction_id": "tx-test-001",
        "customer_id": "customer-test-001",
        "event_time": "2026-08-23T12:00:00Z",
        "amount": 100.0,
        "currency": "BRL",
        "merchant_category": "grocery",
        "home_country": "BR",
        "country": "BR",
        "channel": "card_present",
        "account_age_days": 500,
        "avg_amount_30d": 90.0,
        "tx_count_10m": 1,
        "tx_count_24h": 5,
        "minutes_since_last_tx": 600.0,
        "distance_from_home_km": 5.0,
        "distance_from_last_tx_km": 3.0,
        "device_age_days": 100,
        "device_trust_score": 0.9,
        "merchant_chargeback_rate": 0.01,
        "failed_auth_attempts_10m": 0,
        "is_card_reported_stolen": False,
        "account_locked": False,
        "daily_limit_remaining": 5_000.0,
    }
    values.update(overrides)
    return values


def transaction(**overrides: Any) -> Transaction:
    return Transaction.model_validate(transaction_payload(**overrides))
