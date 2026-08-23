# Hybrid Financial Fraud Evaluation Engine

[![CI](https://github.com/sergiofigueras/hybrid-fraud-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/sergiofigueras/hybrid-fraud-engine/actions/workflows/ci.yml)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%E2%80%933.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A complete, clone-and-run educational project that combines **authoritative deterministic rules** with a **supervised Machine Learning model** to evaluate financial transaction risk.

The repository is part of the **AI Crash Course** hands-on series. It demonstrates how deterministic software, classical Machine Learning, feature engineering, API design, automated testing, auditability, and human review fit together in one system.

> **Important:** this project uses synthetic data and is intended for education and portfolio demonstration. It is not a production fraud product and must not be used to make real financial decisions without qualified fraud-domain, security, legal, compliance, privacy, fairness, and model-risk review.

## What the project includes

- Deterministic `BLOCK` and `REVIEW` rules.
- A regularized logistic-regression risk-ranking model.
- Shared feature engineering for training and inference.
- Chronological train/validation/test splitting.
- Validation-based manual-review threshold selection.
- A decision policy returning `approve`, `review`, or `decline`.
- A safety constraint: **the ML score alone never auto-declines**.
- Traceable responses containing reasons, rule hits, timestamps, and versions.
- A FastAPI service with generated OpenAPI documentation.
- A command-line transaction evaluator.
- Synthetic data generation and reproducible model training.
- Automated tests, GitHub Actions CI, Docker, and Docker Compose.
- Architecture documentation, a model card, a security policy, and publishing scripts.

## Decision policy

```text
1. Authoritative BLOCK rule fires
                     ↓
                  DECLINE

2. No block, but a deterministic REVIEW rule fires
                     ↓
                   REVIEW

3. No rule fires, but the model crosses its review threshold
                     ↓
                   REVIEW

4. No configured signal fires
                     ↓
                  APPROVE
```

The model is a statistical ranking component. It does not override an authoritative rule and cannot independently make an irreversible decline decision.

See [docs/DECISION_POLICY.md](docs/DECISION_POLICY.md) for the exact precedence rules and score definitions.

## Architecture

```text
                            ┌─────────────────────┐
                            │ Transaction request │
                            └──────────┬──────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │ Pydantic validation │
                            └──────────┬──────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     │                                   │
                     ▼                                   ▼
          ┌─────────────────────┐             ┌─────────────────────┐
          │ Deterministic rules │             │ Feature engineering │
          │                     │             │                     │
          │ account state       │             │ amount ratio        │
          │ stolen instrument   │             │ travel speed        │
          │ limits and velocity │             │ device novelty      │
          └──────────┬──────────┘             └──────────┬──────────┘
                     │                                   │
                     │                                   ▼
                     │                        ┌─────────────────────┐
                     │                        │ scikit-learn model  │
                     │                        │ risk-ranking score  │
                     │                        └──────────┬──────────┘
                     └─────────────────┬─────────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │ Decision policy     │
                            └──────────┬──────────┘
                                       │
                      ┌────────────────┼────────────────┐
                      ▼                ▼                ▼
                   APPROVE           REVIEW           DECLINE
                                       │
                                       ▼
                            audit-friendly evaluation
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component responsibilities, trust boundaries, and production extensions.

## Clone and run

The repository includes a trained synthetic model artifact. You can evaluate transactions immediately without generating a dataset or retraining.

### 1. Clone and create an environment

```bash
git clone https://github.com/sergiofigueras/hybrid-fraud-engine.git
cd hybrid-fraud-engine
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
git clone https://github.com/sergiofigueras/hybrid-fraud-engine.git
cd hybrid-fraud-engine
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install the project

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Verify everything

```bash
python scripts/verify_project.py
```

The verification script checks required files, loads the bundled model, evaluates example scenarios, checks API readiness, compiles Python modules, and runs the complete test suite.

### 4. Run the examples

```bash
python -m training.demo
```

Or evaluate one JSON transaction:

```bash
python -m fraud_engine.cli examples/high_risk_transaction.json
```

After installation, the console command is also available:

```bash
fraud-evaluate examples/low_risk_transaction.json
fraud-evaluate examples/high_risk_transaction.json
fraud-evaluate examples/locked_account_transaction.json
```

## Start the API

```bash
uvicorn fraud_engine.api:app --reload
```

Open:

- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Liveness: `http://127.0.0.1:8000/health/live`
- Readiness: `http://127.0.0.1:8000/health/ready`
- Model metadata: `http://127.0.0.1:8000/v1/model`

Submit the high-risk example:

```bash
curl -X POST \
  http://127.0.0.1:8000/v1/fraud/evaluate \
  -H "Content-Type: application/json" \
  --data @examples/high_risk_transaction.json
```

A response contains:

```json
{
  "transaction_id": "tx-high-risk-001",
  "trace_id": "generated-uuid",
  "evaluated_at": "2026-08-23T12:00:00Z",
  "decision": "review",
  "model_score": 0.99,
  "rule_score": 0.94,
  "hybrid_score": 0.99,
  "review_threshold": 0.82,
  "reasons": [
    "R103_NEW_DEVICE_HIGH_AMOUNT: A new device is attempting an amount far above the customer baseline.",
    "RULE_REVIEW: one or more deterministic review rules fired."
  ],
  "rule_hits": [
    {
      "rule_id": "R103_NEW_DEVICE_HIGH_AMOUNT",
      "severity": "review",
      "risk_score": 0.68,
      "reason": "A new device is attempting an amount far above the customer baseline."
    }
  ],
  "model_version": "fraud-logreg-...",
  "rule_set_version": "rules-1.0.0",
  "decision_policy_version": "decision-policy-1.0.0"
}
```

The `rule_score` is a deterministic policy heuristic. The `model_score` is used for ranking and thresholding and should not be described as a calibrated fraud probability unless calibration has been separately validated.

## Run with Docker

```bash
docker compose up --build
```

The API will be available at `http://127.0.0.1:8000`.

Without Compose:

```bash
docker build -t hybrid-fraud-engine:local .
docker run --rm -p 8000:8000 hybrid-fraud-engine:local
```

The image runs as a non-root user and exposes a readiness health check.

## Generate data and retrain

The generated CSV is not committed to Git. Create it locally with:

```bash
python -m training.generate_data --rows 50000 --seed 42
```

This writes `data/transactions.csv`. Retrain with:

```bash
python -m training.train --review-rate 0.05
```

The training pipeline performs:

```text
synthetic transactions
        ↓
chronological split
        ↓
shared feature engineering
        ↓
numeric and categorical preprocessing
        ↓
regularized logistic regression
        ↓
validation-based review threshold
        ↓
test metrics and persisted artifact
```

The generated dataset remains ignored by Git. The new model and metrics are written to `artifacts/`.

## Bundled synthetic benchmark

The committed model artifact was trained on 50,000 synthetic transactions. Its held-out synthetic test metrics are:

| Metric | Value |
|---|---:|
| Synthetic fraud prevalence | 1.72% |
| Average precision | 0.1571 |
| ROC AUC | 0.8314 |
| Precision at review threshold | 13.74% |
| Recall at review threshold | 36.43% |
| Model review rate | 4.56% |

These values demonstrate the difficulty of rare-event detection. They are **not** real-world performance claims. See [docs/MODEL_CARD.md](docs/MODEL_CARD.md) and [artifacts/metrics.json](artifacts/metrics.json).

## Automated verification

Run the tests:

```bash
pytest -q
```

Run coverage:

```bash
pytest --cov=fraud_engine --cov=training --cov-report=term-missing
```

GitHub Actions performs:

- tests on Python 3.11, 3.12, and 3.13;
- command-line and API smoke checks;
- a fresh small-model rebuild from generated synthetic data;
- a Docker build and container readiness check.

## Repository structure

```text
.
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── dependabot.yml
│   └── workflows/ci.yml
├── artifacts/
│   ├── fraud_model.joblib
│   └── metrics.json
├── data/
│   └── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISION_POLICY.md
│   └── MODEL_CARD.md
├── examples/
│   ├── high_risk_transaction.json
│   ├── locked_account_transaction.json
│   └── low_risk_transaction.json
├── fraud_engine/
│   ├── api.py
│   ├── cli.py
│   ├── engine.py
│   ├── features.py
│   ├── model.py
│   ├── rules.py
│   └── schemas.py
├── scripts/
│   ├── publish_to_github.ps1
│   ├── publish_to_github.sh
│   ├── verify_project.py
│   └── verify_project.sh
├── tests/
├── training/
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── PUBLISH_TO_GITHUB.md
├── pyproject.toml
└── README.md
```

## Security and governance boundaries

A real financial decision system needs substantially more than this tutorial, including:

- trusted online feature services and point-in-time correctness;
- authentication, authorization, rate limiting, and replay protection;
- encryption, tokenization, retention controls, and sensitive-data minimization;
- probability calibration and cost-sensitive thresholds;
- segment-level performance, fairness, and customer-impact analysis;
- immutable audits and human-review case management;
- delayed-label ingestion and controlled retraining;
- drift monitoring, champion/challenger evaluation, and rollback;
- customer appeal and correction procedures;
- formal legal, regulatory, security, and model-risk governance.

Read [SECURITY.md](SECURITY.md) before adapting the project.

## Publish to GitHub

The downloadable package is already configured for:

```text
https://github.com/sergiofigueras/hybrid-fraud-engine
```

Follow [PUBLISH_TO_GITHUB.md](PUBLISH_TO_GITHUB.md), or create an empty GitHub repository and run:

```bash
./scripts/publish_to_github.sh \
  https://github.com/sergiofigueras/hybrid-fraud-engine.git
```

Windows PowerShell:

```powershell
.\scripts\publish_to_github.ps1 `
  -RepositoryUrl "https://github.com/sergiofigueras/hybrid-fraud-engine.git"
```

The scripts initialize Git, create the first commit, configure `origin`, and push to `main`. They do not force-push.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and [CHANGELOG.md](CHANGELOG.md) for version history.

Released under the [MIT License](LICENSE).
