# Architecture

## Objective

The engine evaluates one transaction and returns an operational recommendation:

```text
approve | review | decline
```

The design intentionally separates **policy authority** from **statistical risk ranking**.

## Components

### 1. Transaction contract

`fraud_engine/schemas.py` defines the Pydantic request and response models. Unknown request fields are rejected, numeric ranges are constrained, and event timestamps must include a timezone.

### 2. Deterministic rule engine

`fraud_engine/rules.py` contains explicit policy rules with:

```text
rule ID
severity
policy score
human-readable reason
predicate
```

`BLOCK` rules represent authoritative conditions. `REVIEW` rules represent known suspicious patterns that require investigation.

### 3. Feature engineering

`fraud_engine/features.py` derives reusable features such as:

```text
amount_to_avg_ratio
travel_speed_kmh
is_new_device
high_velocity_10m
is_impossible_travel
low_device_trust
high_merchant_chargeback
many_failed_auth
is_cross_border
```

The function is embedded in the scikit-learn pipeline so training and inference use the same implementation.

### 4. Machine Learning model

The baseline model is regularized logistic regression. A `ColumnTransformer` applies:

```text
numeric features    → median imputation → standard scaling
categorical features → mode imputation  → one-hot encoding
```

The model outputs a ranking score used for review routing.

### 5. Decision orchestrator

`fraud_engine/engine.py` applies this hierarchy:

```text
hard block rule     → decline
review rule         → review
model over threshold → review
otherwise           → approve
```

The model cannot independently decline a transaction.

### 6. Model adapter

`fraud_engine/model.py` validates artifact existence and schema version, exposes metadata, warns about incompatible scikit-learn major/minor versions, and provides a stable `score(transaction)` interface.

### 7. Delivery interfaces

- `fraud_engine/api.py`: FastAPI HTTP interface.
- `fraud_engine/cli.py`: JSON-file command-line evaluation.
- `training/`: synthetic data generation, training, evaluation, and demo.

## Training architecture

```text
synthetic raw data
       ↓
chronological ordering
       ↓
70% training | 15% validation | 15% test
       ↓
fit preprocessing and model on training only
       ↓
select review threshold from validation scores
       ↓
evaluate once on held-out test data
       ↓
persist pipeline + metadata
```

## Trust boundaries

The tutorial accepts all fields in the request so it can run independently. In production, the boundary should look like:

```text
external transaction request
        │
        ├── account service
        ├── payment-instrument service
        ├── online velocity feature service
        ├── device-intelligence service
        └── merchant-risk service
                ↓
        trusted feature snapshot
                ↓
        fraud evaluation engine
```

## Production evolution

A production implementation should add:

- a streaming feature pipeline and online feature store;
- point-in-time-correct offline training data;
- authentication, authorization, and rate limiting;
- idempotency and replay protection;
- a model registry and signed artifacts;
- probability calibration and cost-sensitive thresholds;
- case-management and analyst feedback;
- delayed-label handling;
- segment, fairness, drift, and calibration monitoring;
- champion/challenger and shadow deployment;
- rollback and rules-only degraded operation.
