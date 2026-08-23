from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .schemas import RuleAssessment, RuleHit, RuleSeverity, Transaction

RULE_SET_VERSION = "rules-1.0.0"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: RuleSeverity
    risk_score: float
    reason: str
    predicate: Callable[[Transaction], bool]


def _amount_ratio(tx: Transaction) -> float:
    return tx.amount / max(tx.avg_amount_30d, 1.0)


def _travel_speed_kmh(tx: Transaction) -> float:
    hours = max(tx.minutes_since_last_tx, 1.0) / 60.0
    return tx.distance_from_last_tx_km / hours


RULES: tuple[Rule, ...] = (
    Rule(
        "R001_ACCOUNT_LOCKED",
        RuleSeverity.BLOCK,
        1.0,
        "The account is locked by an authoritative system.",
        lambda tx: tx.account_locked,
    ),
    Rule(
        "R002_STOLEN_CARD",
        RuleSeverity.BLOCK,
        1.0,
        "The payment instrument is reported as stolen.",
        lambda tx: tx.is_card_reported_stolen,
    ),
    Rule(
        "R003_DAILY_LIMIT",
        RuleSeverity.BLOCK,
        1.0,
        "The transaction exceeds the remaining daily limit.",
        lambda tx: tx.amount > tx.daily_limit_remaining,
    ),
    Rule(
        "R004_AUTH_FAILURES",
        RuleSeverity.BLOCK,
        0.95,
        "Five or more recent authentication failures were observed.",
        lambda tx: tx.failed_auth_attempts_10m >= 5,
    ),
    Rule(
        "R101_HIGH_VELOCITY",
        RuleSeverity.REVIEW,
        0.72,
        "Six or more transactions were observed within ten minutes.",
        lambda tx: tx.tx_count_10m >= 6,
    ),
    Rule(
        "R102_IMPOSSIBLE_TRAVEL",
        RuleSeverity.REVIEW,
        0.82,
        "Distance and elapsed time imply implausible travel speed.",
        lambda tx: (
            tx.distance_from_last_tx_km > 800
            and tx.minutes_since_last_tx < 90
            and _travel_speed_kmh(tx) > 900
        ),
    ),
    Rule(
        "R103_NEW_DEVICE_HIGH_AMOUNT",
        RuleSeverity.REVIEW,
        0.68,
        "A new device is attempting an amount far above the customer baseline.",
        lambda tx: tx.device_age_days <= 2 and _amount_ratio(tx) >= 4,
    ),
    Rule(
        "R104_EXTREME_AMOUNT_ANOMALY",
        RuleSeverity.REVIEW,
        0.62,
        "The amount is at least eight times the customer's 30-day average.",
        lambda tx: _amount_ratio(tx) >= 8,
    ),
    Rule(
        "R105_RISKY_MERCHANT_SIGNAL",
        RuleSeverity.REVIEW,
        0.55,
        "The merchant has an elevated historical chargeback rate.",
        lambda tx: tx.merchant_chargeback_rate >= 0.08 and tx.amount >= 200,
    ),
    Rule(
        "R106_LOW_TRUST_CROSS_BORDER",
        RuleSeverity.REVIEW,
        0.58,
        "A low-trust device is being used for a cross-border transaction.",
        lambda tx: tx.device_trust_score < 0.30 and tx.country != tx.home_country,
    ),
)


def _aggregate_soft_risk(hits: list[RuleHit]) -> float:
    """Aggregate deterministic signals using a bounded noisy-OR heuristic."""

    remaining_safe_probability = 1.0
    for hit in hits:
        if hit.severity == RuleSeverity.REVIEW:
            remaining_safe_probability *= 1.0 - hit.risk_score
    return round(1.0 - remaining_safe_probability, 6)


def evaluate_rules(tx: Transaction) -> RuleAssessment:
    hits = [
        RuleHit(
            rule_id=rule.rule_id,
            severity=rule.severity,
            risk_score=rule.risk_score,
            reason=rule.reason,
        )
        for rule in RULES
        if rule.predicate(tx)
    ]

    hard_block = any(hit.severity == RuleSeverity.BLOCK for hit in hits)
    soft_score = _aggregate_soft_risk(hits)
    requires_review = any(hit.severity == RuleSeverity.REVIEW for hit in hits)

    return RuleAssessment(
        rule_set_version=RULE_SET_VERSION,
        hard_block=hard_block,
        requires_review=requires_review,
        soft_score=soft_score,
        hits=hits,
    )
