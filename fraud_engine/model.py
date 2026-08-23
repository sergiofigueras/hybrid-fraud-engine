from __future__ import annotations

import math
import warnings
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import sklearn

from .features import RAW_MODEL_COLUMNS
from .schemas import ModelInfo, Transaction

EXPECTED_SCHEMA_VERSION = "fraud-model-schema-1"


class FraudModel:
    """Load and serve a trusted, locally persisted scikit-learn pipeline.

    Joblib uses pickle-compatible serialization. Never load an artifact from an
    untrusted source.
    """

    def __init__(self, artifact_path: str | Path):
        self.artifact_path = Path(artifact_path)
        if not self.artifact_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found: {self.artifact_path}. "
                "Run `python -m training.generate_data` and "
                "`python -m training.train` first."
            )

        bundle: dict[str, Any] = joblib.load(self.artifact_path)
        if not isinstance(bundle, dict) or "pipeline" not in bundle:
            raise RuntimeError("Invalid model artifact: missing pipeline bundle.")

        metadata = bundle.get("metadata")
        if not isinstance(metadata, dict):
            raise RuntimeError("Invalid model artifact: missing metadata.")

        if metadata.get("schema_version") != EXPECTED_SCHEMA_VERSION:
            raise RuntimeError(
                "Model schema mismatch: "
                f"expected {EXPECTED_SCHEMA_VERSION!r}, "
                f"received {metadata.get('schema_version')!r}"
            )

        trained_sklearn = str(metadata.get("scikit_learn_version", "unknown"))
        if trained_sklearn != sklearn.__version__:
            warnings.warn(
                "The model was trained with scikit-learn "
                f"{trained_sklearn}, but the runtime uses {sklearn.__version__}. "
                "Use the pinned project dependencies for reproducible loading.",
                RuntimeWarning,
                stacklevel=2,
            )

        self.pipeline = bundle["pipeline"]
        self.metadata = metadata
        self.version = str(metadata["model_version"])
        self.review_threshold = float(metadata["review_threshold"])

        if not 0 <= self.review_threshold <= 1:
            raise RuntimeError("Invalid review threshold in model metadata.")

    def score(self, tx: Transaction) -> float:
        payload = tx.model_dump(mode="python", include=set(RAW_MODEL_COLUMNS))
        frame = pd.DataFrame([payload], columns=RAW_MODEL_COLUMNS)
        score = float(self.pipeline.predict_proba(frame)[0, 1])

        if not math.isfinite(score):
            raise RuntimeError("The model produced a non-finite score.")
        return min(1.0, max(0.0, score))

    def info(self) -> ModelInfo:
        return ModelInfo(
            schema_version=str(self.metadata["schema_version"]),
            model_version=self.version,
            trained_at=str(self.metadata["trained_at"]),
            review_threshold=self.review_threshold,
            algorithm=str(self.metadata.get("algorithm", "LogisticRegression")),
            scikit_learn_version=str(self.metadata.get("scikit_learn_version", "unknown")),
            metrics=dict(self.metadata.get("metrics", {})),
        )
