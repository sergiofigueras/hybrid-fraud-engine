# Decision Policy

Version: `decision-policy-1.0.0`

## Outcomes

| Outcome | Meaning |
|---|---|
| `approve` | No configured deterministic or model review signal fired |
| `review` | A deterministic review rule fired or the model crossed its review threshold |
| `decline` | An authoritative block rule fired |

## Precedence

1. Authoritative block rules have the highest precedence.
2. Deterministic review rules have precedence over a low model score.
3. A high model score requests manual review but does not decline.
4. A low model score cannot override an authoritative rule.

## Scores

- `model_score` is the classifier output used for ranking and thresholding.
- `rule_score` is a bounded aggregation of deterministic review signals.
- `hybrid_score` is the maximum of those two values for display and ranking.
- None of these values should be described as a verified financial-loss probability without calibration and validation.

## Human oversight

Manual review is required for ambiguous statistical signals in this tutorial. A production review workflow should provide the analyst with the transaction snapshot, rule hits, model version, score, threshold, trace ID, and relevant historical evidence.
