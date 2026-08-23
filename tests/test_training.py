import numpy as np
import pandas as pd
import pytest

from training.train import chronological_split, evaluate, threshold_for_review_capacity


def test_capacity_threshold_selects_upper_scores() -> None:
    scores = np.linspace(0, 1, 100, endpoint=False)
    threshold = threshold_for_review_capacity(scores, review_rate=0.10)

    assert threshold == pytest.approx(np.quantile(scores, 0.90))
    assert (scores >= threshold).mean() == pytest.approx(0.10)


def test_invalid_review_rate_is_rejected() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        threshold_for_review_capacity(np.array([0.1, 0.2]), review_rate=1.0)


def test_chronological_split_preserves_time_order() -> None:
    frame = pd.DataFrame(
        {
            "event_time": pd.date_range("2026-01-01", periods=100, freq="h", tz="UTC")[::-1],
            "is_fraud": [0, 1] * 50,
        }
    )

    train, validation, test = chronological_split(frame)

    assert len(train) == 70
    assert len(validation) == 15
    assert len(test) == 15
    assert train["event_time"].max() <= validation["event_time"].min()
    assert validation["event_time"].max() <= test["event_time"].min()


def test_evaluate_returns_expected_confusion_matrix() -> None:
    y_true = pd.Series([0, 0, 1, 1])
    scores = np.array([0.1, 0.8, 0.7, 0.9])

    metrics = evaluate(y_true, scores, threshold=0.75)

    assert metrics["confusion_matrix"] == {
        "true_negative": 1,
        "false_positive": 1,
        "false_negative": 1,
        "true_positive": 1,
    }
