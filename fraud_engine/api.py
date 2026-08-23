from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI

from . import __version__
from .engine import DECISION_POLICY_VERSION, FraudEngine
from .model import FraudModel
from .rules import RULE_SET_VERSION
from .schemas import (
    FraudEvaluation,
    LivenessResponse,
    ModelInfo,
    ReadinessResponse,
    Transaction,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "artifacts" / "fraud_model.joblib"

app = FastAPI(
    title="Hybrid Financial Fraud Evaluation Engine",
    version=__version__,
    description=(
        "Educational API combining authoritative deterministic rules with a "
        "supervised machine-learning risk score. The model can request manual "
        "review but cannot auto-decline a transaction by itself."
    ),
    contact={
        "name": "Sergio Luiz Wermuth",
        "url": "https://github.com/sergiofigueras/hybrid-fraud-engine",
    },
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "service", "description": "Service and readiness information."},
        {"name": "fraud", "description": "Hybrid transaction evaluation."},
    ],
)


@lru_cache(maxsize=1)
def get_engine() -> FraudEngine:
    model_path = Path(os.getenv("FRAUD_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
    return FraudEngine(FraudModel(model_path))


@app.get("/", tags=["service"])
def service_info() -> dict[str, str]:
    return {
        "name": app.title,
        "version": __version__,
        "documentation": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", response_model=LivenessResponse, tags=["service"])
@app.get("/health/live", response_model=LivenessResponse, tags=["service"])
def liveness() -> LivenessResponse:
    return LivenessResponse(status="ok", service_version=__version__)


@app.get("/health/ready", response_model=ReadinessResponse, tags=["service"])
def readiness(engine: FraudEngine = Depends(get_engine)) -> ReadinessResponse:
    return ReadinessResponse(
        status="ready",
        service_version=__version__,
        model_version=engine.model_version,
        rule_set_version=RULE_SET_VERSION,
        decision_policy_version=DECISION_POLICY_VERSION,
    )


@app.get("/v1/model", response_model=ModelInfo, tags=["service"])
def model_info(engine: FraudEngine = Depends(get_engine)) -> ModelInfo:
    model = engine.model
    if not isinstance(model, FraudModel):
        raise RuntimeError("Model metadata is unavailable for this scorer.")
    return model.info()


@app.get("/v1/model/metadata", response_model=ModelInfo, include_in_schema=False)
def model_info_compatibility(engine: FraudEngine = Depends(get_engine)) -> ModelInfo:
    return model_info(engine)


@app.post(
    "/v1/fraud/evaluate",
    response_model=FraudEvaluation,
    tags=["fraud"],
    summary="Evaluate a financial transaction",
)
def evaluate_transaction(
    transaction: Transaction,
    engine: FraudEngine = Depends(get_engine),
) -> FraudEvaluation:
    return engine.evaluate(transaction)
