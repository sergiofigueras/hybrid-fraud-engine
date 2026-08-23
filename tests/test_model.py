from pathlib import Path

from fraud_engine.model import EXPECTED_SCHEMA_VERSION, FraudModel
from tests.factories import transaction

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_included_model_artifact_loads_and_scores() -> None:
    model = FraudModel(PROJECT_ROOT / "artifacts" / "fraud_model.joblib")
    score = model.score(transaction())

    assert 0 <= score <= 1
    assert model.version
    assert 0 <= model.review_threshold <= 1


def test_model_info_exposes_sanitized_metadata() -> None:
    model = FraudModel(PROJECT_ROOT / "artifacts" / "fraud_model.joblib")
    info = model.info()

    assert info.schema_version == EXPECTED_SCHEMA_VERSION
    assert info.model_version == model.version
    assert info.algorithm
    assert "average_precision" in info.metrics
