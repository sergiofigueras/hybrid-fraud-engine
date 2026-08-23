from fraud_engine.rules import RULE_SET_VERSION, evaluate_rules
from fraud_engine.schemas import RuleSeverity
from tests.factories import transaction


def test_stolen_card_is_a_hard_block() -> None:
    assessment = evaluate_rules(transaction(is_card_reported_stolen=True))

    assert assessment.hard_block is True
    assert assessment.rule_set_version == RULE_SET_VERSION
    assert any(hit.rule_id == "R002_STOLEN_CARD" for hit in assessment.hits)


def test_impossible_travel_requires_review() -> None:
    assessment = evaluate_rules(
        transaction(
            distance_from_last_tx_km=2_000.0,
            minutes_since_last_tx=30.0,
        )
    )

    assert assessment.requires_review is True
    assert any(
        hit.rule_id == "R102_IMPOSSIBLE_TRAVEL"
        and hit.severity == RuleSeverity.REVIEW
        for hit in assessment.hits
    )


def test_multiple_review_rules_produce_bounded_aggregate_score() -> None:
    assessment = evaluate_rules(
        transaction(
            amount=2_000.0,
            avg_amount_30d=100.0,
            device_age_days=0,
            country="US",
            device_trust_score=0.10,
            merchant_chargeback_rate=0.12,
        )
    )

    assert assessment.requires_review is True
    assert 0 < assessment.soft_score <= 1
    assert len(assessment.hits) >= 3


def test_normal_transaction_has_no_rule_hits() -> None:
    assessment = evaluate_rules(transaction())

    assert assessment.hard_block is False
    assert assessment.requires_review is False
    assert assessment.soft_score == 0.0
    assert assessment.hits == []
