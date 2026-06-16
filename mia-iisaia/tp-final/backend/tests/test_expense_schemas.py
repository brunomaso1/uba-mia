import pytest
from pydantic import ValidationError

from app.schemas.expense import ExpenseCreate


def test_expense_create_accepts_valid_payload():
    body = ExpenseCreate(description="Supermercado", amount="125.50", date="2026-06-10")
    assert body.description == "Supermercado"
    assert str(body.amount) == "125.50"


def test_expense_create_rejects_non_positive_amount():
    with pytest.raises(ValidationError):
        ExpenseCreate(description="Bad", amount="0", date="2026-06-10")


def test_expense_create_allows_null_description():
    body = ExpenseCreate(description=None, amount="10.00", date="2026-06-10")
    assert body.description is None
