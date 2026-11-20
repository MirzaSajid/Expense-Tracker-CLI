"""Domain model and input validation.

Money is handled with :class:`decimal.Decimal` rather than ``float`` so that
sums are exact (0.1 + 0.2 == 0.3) and never accumulate rounding error.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

CATEGORIES = (
    "food", "transport", "bills", "shopping",
    "health", "education", "entertainment", "other",
)
_TWO_PLACES = Decimal("0.01")


class ValidationError(ValueError):
    """Raised when user-supplied data is invalid."""


def parse_amount(value: object) -> Decimal:
    """Convert input to a positive Decimal rounded to 2 places."""
    try:
        amount = Decimal(str(value).replace(",", "").strip())
        if not amount.is_finite():          # rejects NaN and Infinity
            raise InvalidOperation
        amount = amount.quantize(_TWO_PLACES)
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid amount: {value!r}") from None
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    return amount


def parse_date(value: object = None) -> date:
    """Parse an ISO date (YYYY-MM-DD). ``None`` means today. Future dates are rejected."""
    if value is None:
        return date.today()
    if isinstance(value, date):
        parsed = value
    else:
        try:
            parsed = date.fromisoformat(str(value).strip())
        except ValueError:
            raise ValidationError(
                f"Invalid date: {value!r} (expected YYYY-MM-DD)") from None
    if parsed > date.today():
        raise ValidationError("Date cannot be in the future.")
    return parsed


def parse_category(value: str) -> str:
    category = str(value).strip().lower()
    if category not in CATEGORIES:
        raise ValidationError(
            f"Unknown category {value!r}. Choose from: {', '.join(CATEGORIES)}")
    return category


def parse_month(value: str) -> tuple[int, int]:
    """Parse 'YYYY-MM' into (year, month)."""
    try:
        year_s, month_s = str(value).split("-")
        year, month = int(year_s), int(month_s)
        date(year, month, 1)
    except ValueError:
        raise ValidationError(f"Invalid month: {value!r} (expected YYYY-MM)") from None
    return year, month


@dataclass(frozen=True)
class Expense:
    """A single immutable expense record."""

    id: int
    date: date
    amount: Decimal
    category: str
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount": str(self.amount),
            "category": self.category,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        return cls(
            id=int(data["id"]),
            date=date.fromisoformat(data["date"]),
            amount=Decimal(data["amount"]),
            category=data["category"],
            description=data.get("description", ""),
        )
