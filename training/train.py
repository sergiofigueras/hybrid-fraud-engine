from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from fraud_engine.features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    RAW_MODEL_COLUMNS,
    engineer_features,
)
from fraud_engine.model import EXPECTED_SCHEMA_VERSION

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "transactions.csv"
DEFAULT_MODEL_OUTPUT = PROJECT_ROOT / "artifacts" / "fraud_model.joblib"
DEFAULT_METRICS_OUTPUT = PROJECT_ROOT / "artifacts" / "metrics.json"


def build_pipeline() -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )

    return Pipeline(
        steps=[
            (
                "feature_engineering",
                FunctionTransformer(engineer_features, validate=False),
            ),
            ("preprocessing", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2_000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def chronological_split(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if len(frame) < 100:
        raise ValueError("At least 100 rows are required for a three-way split.")

    ordered = frame.sort_values("event_time").reset_index(drop=True)
    train_end = int(len(ordered) * 0.70)
    validation_end = int(len(ordered) * 0.85)
    return (
        ordered.iloc[:train_end].copy(),
        ordered.iloc[train_end:validation_end].copy(),
        ordered.iloc[validation_end:].copy(),
    )


def threshold_for_review_capacity(scores: np.ndarray, review_rate: float) -> float:
    if not 0 < review_rate < 1:
        raise ValueError("review_rate must be between 0 and 1")
    if scores.size == 0:
        raise ValueError("scores cannot be empty")
    return float(np.quantile(scores, 1.0 - review_rate))


def evaluate(
    y_true: pd.Series,
    scores: np.ndarray,
    threshold: float,
) -> dict[str, object]:
    predictions = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()

    return {
        "base_rate": float(y_true.mean()),
        "average_precision": float(average_precision_score(y_true, scores)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "precision_at_threshold": float(
            precision_score(y_true, predictions, zero_division=0)
        ),
        "recall_at_threshold": float(
            recall_score(y_true, predictions, zero_division=0)
        ),
        "f1_at_threshold": float(f1_score(y_true, predictions, zero_division=0)),
        "review_rate": float(predictions.mean()),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_binary_labels(frame: pd.DataFrame) -> None:
    labels = set(frame["is_fraud"].dropna().astype(int).unique())
    if not labels.issubset({0, 1}) or len(labels) < 2:
        raise SystemExit("The is_fraud label must contain both 0 and 1 values.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the fraud baseline model.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL_OUTPUT)
    parser.add_argument("--metrics-output", type=Path, default=DEFAULT_METRICS_OUTPUT)
    parser.add_argument(
        "--review-rate",
        type=float,
        default=0.05,
        help="Fraction of validation transactions the model may route to review.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(
            f"Training data not found: {args.input}. "
            "Run `python -m training.generate_data` first."
        )

    frame = pd.read_csv(args.input, parse_dates=["event_time"])
    required = set(RAW_MODEL_COLUMNS) | {"event_time", "is_fraud"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise SystemExit(f"Training data is missing required columns: {missing}")

    ensure_binary_labels(frame)
    train, validation, test = chronological_split(frame)

    for split_name, split in (
        ("training", train),
        ("validation", validation),
        ("test", test),
    ):
        if split["is_fraud"].nunique() < 2:
            raise SystemExit(f"The {split_name} split must contain both classes.")

    pipeline = build_pipeline()
    pipeline.fit(train[RAW_MODEL_COLUMNS], train["is_fraud"])

    validation_scores = pipeline.predict_proba(validation[RAW_MODEL_COLUMNS])[:, 1]
    review_threshold = threshold_for_review_capacity(validation_scores, args.review_rate)

    validation_metrics = evaluate(
        validation["is_fraud"], validation_scores, review_threshold
    )
    test_scores = pipeline.predict_proba(test[RAW_MODEL_COLUMNS])[:, 1]
    test_metrics = evaluate(test["is_fraud"], test_scores, review_threshold)

    trained_at = datetime.now(timezone.utc)
    model_version = trained_at.strftime("fraud-logreg-%Y%m%dT%H%M%SZ")
    metadata = {
        "schema_version": EXPECTED_SCHEMA_VERSION,
        "model_version": model_version,
        "algorithm": "LogisticRegression(class_weight='balanced')",
        "trained_at": trained_at.isoformat(),
        "review_threshold": review_threshold,
        "threshold_strategy": "validation_score_quantile",
        "target_validation_review_rate": args.review_rate,
        "dataset_sha256": file_sha256(args.input),
        "feature_columns": RAW_MODEL_COLUMNS,
        "training_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "positive_rate_train": float(train["is_fraud"].mean()),
        "positive_rate_validation": float(validation["is_fraud"].mean()),
        "positive_rate_test": float(test["is_fraud"].mean()),
        "scikit_learn_version": sklearn.__version__,
        "validation_metrics": validation_metrics,
        "metrics": test_metrics,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "metadata": metadata}, args.output)

    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(json.dumps(metadata, indent=2))
    print(f"Saved model artifact to {args.output}")
    print(f"Saved metrics to {args.metrics_output}")


if __name__ == "__main__":
    main()
