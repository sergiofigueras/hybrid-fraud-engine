import json
from pathlib import Path

from fastapi.testclient import TestClient

from fraud_engine.api import app, get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def load_example(name: str) -> dict[str, object]:
    return json.loads((PROJECT_ROOT / "examples" / name).read_text(encoding="utf-8"))


def setup_function() -> None:
    get_engine.cache_clear()


def test_service_and_health_endpoints() -> None:
    assert client.get("/").status_code == 200
    assert client.get("/health/live").json()["status"] == "ok"

    readiness = client.get("/health/ready")
    assert readiness.status_code == 200
    assert readiness.json()["status"] == "ready"
    assert readiness.json()["model_version"]


def test_model_metadata_endpoint() -> None:
    response = client.get("/v1/model")

    assert response.status_code == 200
    assert response.json()["algorithm"]
    assert 0 <= response.json()["review_threshold"] <= 1


def test_evaluate_endpoint_returns_traceable_decision() -> None:
    response = client.post(
        "/v1/fraud/evaluate",
        json=load_example("high_risk_transaction.json"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "review"
    assert body["trace_id"]
    assert body["model_version"]
    assert body["rule_set_version"]
    assert body["decision_policy_version"]
    assert body["reasons"]


def test_invalid_request_returns_validation_error() -> None:
    payload = load_example("low_risk_transaction.json")
    payload["device_trust_score"] = 2

    response = client.post("/v1/fraud/evaluate", json=payload)

    assert response.status_code == 422
