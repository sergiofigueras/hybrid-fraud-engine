# Model Card: Synthetic Fraud-Risk Baseline

## Model details

| Field | Value |
|---|---|
| Model family | Regularized logistic regression |
| Library | scikit-learn 1.8.0 |
| Artifact | `artifacts/fraud_model.joblib` |
| Schema | `fraud-model-schema-1` |
| Primary purpose | Rank synthetic transactions for manual review |
| Automatic decline authority | None |

## Intended use

The model is intended to demonstrate:

- supervised learning on structured transaction features;
- feature engineering;
- class imbalance;
- chronological evaluation;
- validation-based threshold selection;
- model persistence and API inference;
- combination with deterministic rules.

It is suitable for education, demonstrations, interviews, and portfolio review.

## Out-of-scope use

Do not use the model for:

- real transaction authorization;
- customer account suspension;
- law-enforcement referral;
- credit eligibility or pricing;
- production fraud-loss claims;
- any decision involving real individuals.

## Training data

The dataset is completely synthetic. The generator creates transaction amount, behavioral velocity, device, merchant, location, authentication, and account-state signals. A hidden noisy statistical function produces the synthetic label.

The synthetic generator is not an accurate simulator of any real population, financial institution, geography, or fraud strategy.

## Features

The model uses structured features including:

- amount and 30-day average amount;
- account and device age;
- short- and long-window transaction counts;
- time and distance from the previous transaction;
- device trust and merchant chargeback signals;
- authentication failures;
- channel, currency, and merchant category;
- derived amount ratio, travel speed, device novelty, velocity, impossible travel, and cross-border indicators.

Authoritative fields such as `account_locked` and `is_card_reported_stolen` are handled by deterministic rules rather than model features.

## Evaluation design

Transactions are sorted by `event_time` and split chronologically:

```text
70% training
15% validation
15% test
```

The review threshold is selected from validation scores to target approximately 5% model-driven review capacity. Test data is then used for final reporting.

## Bundled synthetic metrics

| Metric | Value |
|---|---:|
| Test positive rate | 0.0172 |
| Average precision | 0.157114 |
| ROC AUC | 0.831445 |
| Precision at threshold | 0.137427 |
| Recall at threshold | 0.364341 |
| F1 at threshold | 0.199575 |
| Review rate | 0.0456 |
| True negatives | 7,076 |
| False positives | 295 |
| False negatives | 82 |
| True positives | 47 |

These are synthetic educational results, not production benchmarks.

## Limitations

- The data-generation function is much simpler than real fraud behavior.
- Labels are immediate instead of delayed.
- The dataset has no realistic customer sequence history.
- The model is not probability-calibrated.
- Threshold selection uses review capacity rather than a full business-cost function.
- No confidence intervals are reported.
- No fairness conclusions can be drawn from synthetic country or channel fields.
- The model artifact is tied to controlled Python and scikit-learn versions.
- Adversarial behavior, data poisoning, model extraction, and feature manipulation are not simulated.

## Ethical and governance considerations

A real deployment requires feature justification, prohibited-feature review, segment-level false-positive analysis, customer recourse, human oversight, auditability, privacy controls, security testing, and continuous monitoring.

## Recommended improvements

- calibrate model scores on a separate calibration set;
- tune thresholds using expected fraud loss, review cost, and customer-friction cost;
- compare gradient-boosted trees as a challenger;
- evaluate performance by channel and risk segment;
- add delayed-label and point-in-time feature pipelines;
- monitor drift and calibration after deployment;
- introduce a signed model registry and rollback process.
