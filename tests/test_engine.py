from dataclasses import dataclass

import pytest

from fraud_engine.engine import DECISION_POLICY_VERSION, FraudEngine
from fraud_engine.schemas import Decision, Transaction
from tests.factories import transaction


@dataclass
class StubModel:
    value: float
    version: str = "stub-model-1"
    review_threshold: float = 0.8

    def score(self, tx: Transaction) -> float:
        return self.value


def test_authoritative_rule_overrides_low_model_score() -> None:
    engine = FraudEngine(StubModel(0.01))
    result = engine.evaluate(transaction(account_locked=True))

    assert result.decision == Decision.DECLINE
    assert result.decision_policy_version == DECISION_POLICY_VERSION
    assert any(reason.startswith("POLICY_OVERRIDE") for reason in result.reasons)


def test_high_model_score_routes_to_review_not_auto_decline() -> None:
    engine = FraudEngine(StubModel(0.95))
    result = engine.evaluate(transaction())

    assert result.decision == Decision.REVIEW
    assert any(reason.startswith("MODEL_REVIEW") for reason in result.reasons)


def test_low_risk_transaction_is_approved() -> None:
    engine = FraudEngine(StubModel(0.10))
    result = engine.evaluate(transaction())

    assert result.decision == Decision.APPROVE
    assert result.rule_score == 0


def test_soft_rule_routes_to_review() -> None:
    engine = FraudEngine(StubModel(0.10))
    result = engine.evaluate(
        transaction(
            amount=2_000.0,
            avg_amount_30d=100.0,
            device_age_days=0,
            daily_limit_remaining=5_000.0,
        )
    )

    assert result.decision == Decision.REVIEW
    assert result.rule_score > 0
    assert any(hit.rule_id == "R103_NEW_DEVICE_HIGH_AMOUNT" for hit in result.rule_hits)


@pytest.mark.parametrize("score", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_model_scores_are_rejected(score: float) -> None:
    engine = FraudEngine(StubModel(score))

    with pytest.raises(ValueError, match="Model score"):
        engine.evaluate(transaction())
