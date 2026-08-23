from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Decision(StrEnum):
    APPROVE = "approve"
    REVIEW = "review"
    DECLINE = "decline"


class RuleSeverity(StrEnum):
    INFO = "info"
    REVIEW = "review"
    BLOCK = "block"


class Transaction(BaseModel):
    """Information available when a transaction is evaluated.

    In production, behavioral and account-state features should come from
    trusted internal services. They are request fields here only to keep the
    educational project self-contained.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "transaction_id": "tx-9001",
                    "customer_id": "customer-42",
                    "event_time": "2026-08-23T12:00:00Z",
                    "amount": 2500.0,
                    "currency": "USD",
                    "merchant_category": "electronics",
                    "home_country": "BR",
                    "country": "US",
                    "channel": "ecommerce",
                    "account_age_days": 800,
                    "avg_amount_30d": 120.0,
                    "tx_count_10m": 2,
                    "tx_count_24h": 9,
                    "minutes_since_last_tx": 40.0,
                    "distance_from_home_km": 7200.0,
                    "distance_from_last_tx_km": 10.0,
                    "device_age_days": 0,
                    "device_trust_score": 0.22,
                    "merchant_chargeback_rate": 0.02,
                    "failed_auth_attempts_10m": 2,
                    "is_card_reported_stolen": False,
                    "account_locked": False,
                    "daily_limit_remaining": 5000.0,
                }
            ]
        },
    )

    transaction_id: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)
    event_time: datetime

    amount: float = Field(gt=0, le=1_000_000)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    merchant_category: str = Field(min_length=1, max_length=80)
    home_country: str = Field(pattern=r"^[A-Z]{2}$")
    country: str = Field(pattern=r"^[A-Z]{2}$")
    channel: Literal["card_present", "ecommerce", "atm", "transfer"]

    account_age_days: int = Field(ge=0, le=50_000)
    avg_amount_30d: float = Field(gt=0, le=1_000_000)
    tx_count_10m: int = Field(ge=0, le=10_000)
    tx_count_24h: int = Field(ge=0, le=1_000_000)
    minutes_since_last_tx: float = Field(ge=0, le=1_000_000)
    distance_from_home_km: float = Field(ge=0, le=50_000)
    distance_from_last_tx_km: float = Field(ge=0, le=50_000)
    device_age_days: int = Field(ge=0, le=50_000)
    device_trust_score: float = Field(ge=0, le=1)
    merchant_chargeback_rate: float = Field(ge=0, le=1)
    failed_auth_attempts_10m: int = Field(ge=0, le=10_000)

    is_card_reported_stolen: bool = False
    account_locked: bool = False
    daily_limit_remaining: float = Field(ge=0, le=10_000_000)

    @field_validator("currency", "home_country", "country", mode="before")
    @classmethod
    def normalize_codes(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("merchant_category", "channel", mode="before")
    @classmethod
    def normalize_categories(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("event_time")
    @classmethod
    def event_time_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("event_time must include a timezone")
        return value


class RuleHit(BaseModel):
    rule_id: str
    severity: RuleSeverity
    risk_score: float = Field(ge=0, le=1)
    reason: str


class RuleAssessment(BaseModel):
    rule_set_version: str
    hard_block: bool
    requires_review: bool
    soft_score: float = Field(ge=0, le=1)
    hits: list[RuleHit]


class FraudEvaluation(BaseModel):
    transaction_id: str
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    decision: Decision
    model_score: float = Field(ge=0, le=1)
    rule_score: float = Field(ge=0, le=1)
    hybrid_score: float = Field(ge=0, le=1)
    review_threshold: float = Field(ge=0, le=1)

    reasons: list[str]
    rule_hits: list[RuleHit]
    model_version: str
    rule_set_version: str
    decision_policy_version: str


class LivenessResponse(BaseModel):
    status: Literal["ok"]
    service_version: str


class ReadinessResponse(BaseModel):
    status: Literal["ready"]
    service_version: str
    model_version: str
    rule_set_version: str
    decision_policy_version: str


class ModelInfo(BaseModel):
    schema_version: str
    model_version: str
    trained_at: str
    review_threshold: float = Field(ge=0, le=1)
    algorithm: str
    scikit_learn_version: str
    metrics: dict[str, Any]
