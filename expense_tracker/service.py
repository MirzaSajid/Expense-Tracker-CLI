"""Business logic: everything the CLI needs, independent of any UI."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import (Expense, ValidationError, parse_amount, parse_category,
                     parse_date, parse_month)
from .storage import JsonStore


class NotFoundError(LookupError):
    """Raised when an expense id does not exist."""


@dataclass(frozen=True)
class BudgetStatus:
    category: str
    budget: Decimal
    spent: Decimal

    @property
    def remaining(self) -> Decimal:
        return self.budget - self.spent

    @property
    def percent_used(self) -> Decimal:
        return (self.spent / self.budget * 100).quantize(Decimal("0.1"))

    @property
    def exceeded(self) -> bool:
        return self.spent > self.budget


class ExpenseTracker:
    def __init__(self, store: JsonStore | None = None):
        self.store = store or JsonStore()

    # ---- commands -------------------------------------------------------
    def add(self, amount, category: str, description: str = "", on=None) -> Expense:
        state = self.store.load()
        expense = Expense(
            id=state["next_id"],
            date=parse_date(on),
            amount=parse_amount(amount),
            category=parse_category(category),
            description=description.strip(),
        )
        state["expenses"].append(expense.to_dict())
        state["next_id"] += 1
        self.store.save(state)
        return expense

    def delete(self, expense_id: int) -> Expense:
        state = self.store.load()
        for i, raw in enumerate(state["expenses"]):
            if raw["id"] == expense_id:
                removed = Expense.from_dict(state["expenses"].pop(i))
                self.store.save(state)
                return removed
        raise NotFoundError(f"No expense with id {expense_id}")

    # ---- queries --------------------------------------------------------
    def list(self, category: str | None = None, month: str | None = None,
             start: str | None = None, end: str | None = None) -> list[Expense]:
        """Return expenses filtered by category / month / date range, newest first."""
        expenses = [Expense.from_dict(r) for r in self.store.load()["expenses"]]
        if category:
            cat = parse_category(category)
            expenses = [e for e in expenses if e.category == cat]
        if month:
            year, mon = parse_month(month)
            expenses = [e for e in expenses if (e.date.year, e.date.month) == (year, mon)]
        if start:
            s = parse_date(start)
            expenses = [e for e in expenses if e.date >= s]
        if end:
            t = parse_date(end)
            expenses = [e for e in expenses if e.date <= t]
        return sorted(expenses, key=lambda e: (e.date, e.id), reverse=True)

    @staticmethod
    def total(expenses: list[Expense]) -> Decimal:
        return sum((e.amount for e in expenses), Decimal("0.00"))

    @staticmethod
    def by_category(expenses: list[Expense]) -> list[tuple[str, Decimal]]:
        """Totals per category, largest first."""
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for e in expenses:
            totals[e.category] += e.amount
        return sorted(totals.items(), key=lambda kv: kv[1], reverse=True)

    @staticmethod
    def monthly_totals(expenses: list[Expense]) -> list[tuple[str, Decimal]]:
        """Totals per 'YYYY-MM', chronological."""
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for e in expenses:
            totals[f"{e.date.year}-{e.date.month:02d}"] += e.amount
        return sorted(totals.items())

    # ---- budgets --------------------------------------------------------
    def set_budget(self, category: str, amount) -> None:
        state = self.store.load()
        state["budgets"][parse_category(category)] = str(parse_amount(amount))
        self.store.save(state)

    def budget_status(self, month: str | None = None) -> list[BudgetStatus]:
        """Compare each category's monthly budget with actual spending."""
        if month is None:
            today = date.today()
            month = f"{today.year}-{today.month:02d}"
        budgets = self.store.load()["budgets"]
        spent = dict(self.by_category(self.list(month=month)))
        return [BudgetStatus(cat, Decimal(b), spent.get(cat, Decimal("0.00")))
                for cat, b in sorted(budgets.items())]

    # ---- export ---------------------------------------------------------
    def export_csv(self, path: str | Path, expenses: list[Expense] | None = None) -> int:
        rows = self.list() if expenses is None else expenses
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "date", "amount", "category", "description"])
            for e in sorted(rows, key=lambda x: (x.date, x.id)):
                writer.writerow([e.id, e.date.isoformat(), e.amount, e.category, e.description])
        return len(rows)
