import pytest
from pydantic import ValidationError

from fraud_engine.schemas import Transaction
from tests.factories import transaction_payload


def test_codes_and_categories_are_normalized() -> None:
    tx = Transaction.model_validate(
        transaction_payload(
            currency="brl",
            country="br",
            home_country="br",
            merchant_category=" Grocery ",
            channel=" ECOMMERCE ",
        )
    )

    assert tx.currency == "BRL"
    assert tx.country == "BR"
    assert tx.merchant_category == "grocery"
    assert tx.channel == "ecommerce"


def test_naive_event_time_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        Transaction.model_validate(transaction_payload(event_time="2026-08-23T12:00:00"))


def test_unknown_fields_are_rejected() -> None:
    payload = transaction_payload()
    payload["unexpected"] = "value"

    with pytest.raises(ValidationError, match="Extra inputs"):
        Transaction.model_validate(payload)
