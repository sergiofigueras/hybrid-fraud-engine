from __future__ import annotations

import argparse
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "transactions.csv"


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


def generate_transactions(rows: int, seed: int) -> pd.DataFrame:
    """Generate a synthetic and intentionally imperfect fraud dataset.

    The hidden label function exists only to create tutorial data. Real fraud
    labels often arrive later through chargebacks, investigations, or customer
    reports, and they contain delay, ambiguity, and noise.
    """

    rng = np.random.default_rng(seed)

    start = pd.Timestamp("2025-01-01", tz="UTC")
    event_seconds = np.sort(rng.integers(0, 180 * 24 * 60 * 60, rows))
    event_time = start + pd.to_timedelta(event_seconds, unit="s")

    amount = np.round(np.exp(rng.normal(4.2, 1.0, rows)), 2)
    avg_amount_30d = np.round(np.exp(rng.normal(3.9, 0.65, rows)), 2)

    burst = rng.random(rows) < 0.025
    tx_count_10m = rng.poisson(0.45, rows) + np.where(
        burst, rng.integers(5, 13, rows), 0
    )
    tx_count_24h = rng.poisson(5, rows) + tx_count_10m

    fast_travel = rng.random(rows) < 0.008
    normal_long_trip = rng.random(rows) < 0.012
    distance_from_last_tx_km = np.where(
        fast_travel | normal_long_trip,
        rng.uniform(600, 9_000, rows),
        rng.exponential(35, rows),
    )
    minutes_since_last_tx = np.where(
        fast_travel,
        rng.uniform(5, 90, rows),
        np.where(
            normal_long_trip,
            rng.uniform(180, 10_080, rows),
            rng.exponential(420, rows),
        ),
    )
    distance_from_home_km = np.where(
        rng.random(rows) < 0.05,
        rng.uniform(300, 9_000, rows),
        rng.exponential(45, rows),
    )

    is_new_device = rng.random(rows) < 0.07
    device_age_days = np.where(
        is_new_device,
        rng.integers(0, 3, rows),
        rng.gamma(2.2, 100, rows),
    ).astype(int)

    low_trust = rng.random(rows) < 0.04
    device_trust_score = np.where(
        low_trust,
        rng.uniform(0.05, 0.34, rows),
        rng.beta(8, 2, rows),
    )

    elevated_chargebacks = rng.random(rows) < 0.035
    merchant_chargeback_rate = np.where(
        elevated_chargebacks,
        rng.uniform(0.05, 0.25, rows),
        rng.beta(1.2, 80, rows),
    )

    many_failed_auth = rng.random(rows) < 0.018
    failed_auth_attempts_10m = np.where(
        many_failed_auth,
        rng.integers(3, 9, rows),
        rng.poisson(0.08, rows),
    ).astype(int)

    account_age_days = np.maximum(1, rng.gamma(2.8, 420, rows)).astype(int)

    channel = rng.choice(
        ["card_present", "ecommerce", "atm", "transfer"],
        rows,
        p=[0.42, 0.38, 0.10, 0.10],
    )
    merchant_category = rng.choice(
        ["grocery", "fuel", "electronics", "travel", "gaming", "cash_equivalent"],
        rows,
        p=[0.28, 0.17, 0.16, 0.12, 0.17, 0.10],
    )

    countries = np.array(["BR", "US", "GB", "DE", "MX", "CA"])
    home_country = rng.choice(
        countries,
        rows,
        p=[0.58, 0.16, 0.08, 0.06, 0.07, 0.05],
    )
    cross_border = rng.random(rows) < 0.10
    alternate_country = rng.choice(countries, rows)
    country = np.where(cross_border, alternate_country, home_country)

    currency_map = {
        "BR": "BRL",
        "US": "USD",
        "GB": "GBP",
        "DE": "EUR",
        "MX": "MXN",
        "CA": "CAD",
    }
    currency = np.array([currency_map[value] for value in country])

    is_card_reported_stolen = rng.random(rows) < 0.0015
    account_locked = rng.random(rows) < 0.002
    daily_limit_remaining = np.round(np.exp(rng.normal(6.3, 0.7, rows)), 2)

    amount_ratio = amount / np.maximum(avg_amount_30d, 1.0)
    impossible_travel = (
        (distance_from_last_tx_km > 800) & (minutes_since_last_tx < 90)
    )
    limit_exceeded = amount > daily_limit_remaining
    cross_border_signal = country != home_country
    risky_merchant_category = np.isin(
        merchant_category, ["gaming", "cash_equivalent"]
    )

    # Hidden synthetic process. Randomness prevents a perfectly separable and
    # unrealistic dataset.
    log_odds = (
        -6.4
        + 1.4 * is_new_device
        + 1.6 * (amount_ratio > 4)
        + 2.0 * (tx_count_10m >= 5)
        + 2.6 * impossible_travel
        + 1.0 * cross_border_signal
        + 0.8 * risky_merchant_category
        + 1.9 * (failed_auth_attempts_10m >= 3)
        + 1.7 * (device_trust_score < 0.35)
        + 1.4 * (merchant_chargeback_rate >= 0.05)
        + 0.8 * (channel == "ecommerce")
        + 3.5 * is_card_reported_stolen
        + 2.5 * account_locked
        + 1.5 * limit_exceeded
        + rng.normal(0, 0.45, rows)
    )
    fraud_probability = sigmoid(log_odds)
    is_fraud = rng.binomial(1, fraud_probability)

    transaction_ids = [
        str(uuid5(NAMESPACE_URL, f"fraud-course-transaction-{seed}-{index}"))
        for index in range(rows)
    ]
    customer_ids = [f"customer-{value:06d}" for value in rng.integers(1, 20_000, rows)]

    return pd.DataFrame(
        {
            "transaction_id": transaction_ids,
            "customer_id": customer_ids,
            "event_time": event_time,
            "amount": amount,
            "currency": currency,
            "merchant_category": merchant_category,
            "home_country": home_country,
            "country": country,
            "channel": channel,
            "account_age_days": account_age_days,
            "avg_amount_30d": avg_amount_30d,
            "tx_count_10m": tx_count_10m,
            "tx_count_24h": tx_count_24h,
            "minutes_since_last_tx": np.round(minutes_since_last_tx, 2),
            "distance_from_home_km": np.round(distance_from_home_km, 2),
            "distance_from_last_tx_km": np.round(distance_from_last_tx_km, 2),
            "device_age_days": device_age_days,
            "device_trust_score": np.round(device_trust_score, 6),
            "merchant_chargeback_rate": np.round(merchant_chargeback_rate, 6),
            "failed_auth_attempts_10m": failed_auth_attempts_10m,
            "is_card_reported_stolen": is_card_reported_stolen,
            "account_locked": account_locked,
            "daily_limit_remaining": daily_limit_remaining,
            "is_fraud": is_fraud,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic fraud data.")
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.rows < 1_000:
        raise SystemExit("Use at least 1,000 rows for a meaningful tutorial dataset.")

    frame = generate_transactions(args.rows, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)

    print(f"Saved {len(frame):,} rows to {args.output}")
    print(f"Synthetic fraud rate: {frame['is_fraud'].mean():.4%}")


if __name__ == "__main__":
    main()
