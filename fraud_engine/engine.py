from __future__ import annotations

import math
from typing import Protocol

from .rules import RULE_SET_VERSION, evaluate_rules
from .schemas import Decision, FraudEvaluation, Transaction

DECISION_POLICY_VERSION = "decision-policy-1.0.0"


class ScoringModel(Protocol):
    version: str
    review_threshold: float

    def score(self, tx: Transaction) -> float: ...


class FraudEngine:
    """Combine deterministic policy with a probabilistic model score.

    Tutorial policy:
      1. Authoritative BLOCK rules override every other signal.
      2. A deterministic REVIEW rule routes the transaction to manual review.
      3. A model score above its validated threshold also routes to review.
      4. The model never auto-declines a transaction by itself.
    """

    def __init__(self, model: ScoringModel):
        self.model = model

    @property
    def model_version(self) -> str:
        return self.model.version

    @property
    def review_threshold(self) -> float:
        return self.model.review_threshold

    def evaluate(self, tx: Transaction) -> FraudEvaluation:
        rule_assessment = evaluate_rules(tx)
        model_score = float(self.model.score(tx))

        if not math.isfinite(model_score) or not 0 <= model_score <= 1:
            raise ValueError("Model score must be a finite value between 0 and 1.")

        hybrid_score = max(model_score, rule_assessment.soft_score)
        reasons = [f"{hit.rule_id}: {hit.reason}" for hit in rule_assessment.hits]

        if rule_assessment.hard_block:
            decision = Decision.DECLINE
            reasons.append("POLICY_OVERRIDE: an authoritative blocking rule fired.")
        elif rule_assessment.requires_review:
            decision = Decision.REVIEW
            reasons.append("RULE_REVIEW: one or more deterministic review rules fired.")
        elif model_score >= self.model.review_threshold:
            decision = Decision.REVIEW
            reasons.append(
                "MODEL_REVIEW: the model score exceeded the validated review threshold."
            )
        else:
            decision = Decision.APPROVE
            reasons.append("NO_REVIEW_SIGNAL: no configured rule or model threshold fired.")

        return FraudEvaluation(
            transaction_id=tx.transaction_id,
            decision=decision,
            model_score=round(model_score, 6),
            rule_score=rule_assessment.soft_score,
            hybrid_score=round(hybrid_score, 6),
            review_threshold=round(self.model.review_threshold, 6),
            reasons=reasons,
            rule_hits=rule_assessment.hits,
            model_version=self.model.version,
            rule_set_version=rule_assessment.rule_set_version,
            decision_policy_version=DECISION_POLICY_VERSION,
        )


__all__ = ["DECISION_POLICY_VERSION", "FraudEngine", "RULE_SET_VERSION"]
