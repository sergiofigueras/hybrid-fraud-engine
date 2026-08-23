from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fraud_engine.engine import FraudEngine
from fraud_engine.model import FraudModel
from fraud_engine.schemas import Transaction

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = PROJECT_ROOT / "artifacts" / "fraud_model.joblib"

BASE_TRANSACTION: dict[str, Any] = {
    "transaction_id": "demo-low-risk-001",
    "customer_id": "customer-demo-001",
    "event_time": "2026-08-23T12:00:00Z",
    "amount": 85.0,
    "currency": "BRL",
    "merchant_category": "grocery",
    "home_country": "BR",
    "country": "BR",
    "channel": "card_present",
    "account_age_days": 900,
    "avg_amount_30d": 100.0,
    "tx_count_10m": 1,
    "tx_count_24h": 4,
    "minutes_since_last_tx": 600.0,
    "distance_from_home_km": 3.0,
    "distance_from_last_tx_km": 2.0,
    "device_age_days": 200,
    "device_trust_score": 0.95,
    "merchant_chargeback_rate": 0.005,
    "failed_auth_attempts_10m": 0,
    "is_card_reported_stolen": False,
    "account_locked": False,
    "daily_limit_remaining": 5000.0,
}


def example_transactions() -> list[tuple[str, dict[str, Any]]]:
    review = {
        **BASE_TRANSACTION,
        "transaction_id": "demo-review-001",
        "amount": 2500.0,
        "currency": "USD",
        "merchant_category": "electronics",
        "country": "US",
        "channel": "ecommerce",
        "avg_amount_30d": 120.0,
        "device_age_days": 0,
        "device_trust_score": 0.22,
        "distance_from_home_km": 7200.0,
        "failed_auth_attempts_10m": 2,
    }
    decline = {
        **BASE_TRANSACTION,
        "transaction_id": "demo-decline-001",
        "account_locked": True,
    }
    return [
        ("low-risk", BASE_TRANSACTION),
        ("manual-review", review),
        ("authoritative-decline", decline),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run three local fraud scenarios.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()

    engine = FraudEngine(FraudModel(args.model))

    for name, payload in example_transactions():
        transaction = Transaction.model_validate(payload)
        result = engine.evaluate(transaction)
        print(f"\n=== {name} ===")
        print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
