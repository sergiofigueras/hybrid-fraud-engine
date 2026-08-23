from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from pydantic import ValidationError

from .engine import FraudEngine
from .model import FraudModel
from .schemas import Transaction

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "artifacts" / "fraud_model.joblib"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate one transaction JSON file with the hybrid fraud engine."
    )
    parser.add_argument("transaction", type=Path, help="Path to a transaction JSON file.")
    parser.add_argument(
        "--model",
        type=Path,
        default=Path(os.getenv("FRAUD_MODEL_PATH", str(DEFAULT_MODEL_PATH))),
        help="Path to the joblib model artifact.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON instead of indented JSON.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    try:
        payload = json.loads(args.transaction.read_text(encoding="utf-8"))
        transaction = Transaction.model_validate(payload)
        result = FraudEngine(FraudModel(args.model)).evaluate(transaction)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {args.transaction}: {exc}") from exc
    except ValidationError as exc:
        raise SystemExit(f"Invalid transaction payload:\n{exc}") from exc

    indent = None if args.compact else 2
    print(json.dumps(result.model_dump(mode="json"), indent=indent, sort_keys=True))


if __name__ == "__main__":
    main()
