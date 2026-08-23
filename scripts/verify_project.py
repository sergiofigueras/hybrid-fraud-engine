from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from fraud_engine.api import app, get_engine
from fraud_engine.engine import FraudEngine
from fraud_engine.model import FraudModel
from fraud_engine.schemas import Decision, Transaction

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "PUBLISH_TO_GITHUB.md",
    "pyproject.toml",
    "Dockerfile",
    "docker-compose.yml",
    ".github/workflows/ci.yml",
    ".github/dependabot.yml",
    "docs/ARCHITECTURE.md",
    "docs/DECISION_POLICY.md",
    "docs/MODEL_CARD.md",
    "artifacts/fraud_model.joblib",
    "artifacts/metrics.json",
    "examples/low_risk_transaction.json",
    "examples/high_risk_transaction.json",
    "examples/locked_account_transaction.json",
]


def load_transaction(name: str) -> Transaction:
    payload = json.loads((PROJECT_ROOT / "examples" / name).read_text(encoding="utf-8"))
    return Transaction.model_validate(payload)


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (PROJECT_ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing required repository files: {missing}")

    model = FraudModel(PROJECT_ROOT / "artifacts" / "fraud_model.joblib")
    engine = FraudEngine(model)

    low_risk_result = engine.evaluate(load_transaction("low_risk_transaction.json"))
    high_risk_result = engine.evaluate(load_transaction("high_risk_transaction.json"))
    locked_result = engine.evaluate(load_transaction("locked_account_transaction.json"))

    if low_risk_result.decision != Decision.APPROVE:
        raise SystemExit("The low-risk example was not approved.")
    if high_risk_result.decision != Decision.REVIEW:
        raise SystemExit("The high-risk example was not routed to review.")
    if locked_result.decision != Decision.DECLINE:
        raise SystemExit("The locked-account example did not trigger a decline.")

    get_engine.cache_clear()
    client = TestClient(app)
    for endpoint in ("/health/ready", "/v1/model"):
        response = client.get(endpoint)
        if response.status_code != 200:
            raise SystemExit(f"Endpoint check failed for {endpoint}: {response.text}")

    subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "fraud_engine", "training"],
        cwd=PROJECT_ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=PROJECT_ROOT,
        check=True,
    )

    print("Repository verification completed successfully.")
    print(f"Model version: {model.version}")
    print(f"Review threshold: {model.review_threshold:.6f}")
    print(f"Low-risk example decision: {low_risk_result.decision.value}")
    print(f"High-risk example decision: {high_risk_result.decision.value}")
    print(f"Locked-account example decision: {locked_result.decision.value}")


if __name__ == "__main__":
    main()
