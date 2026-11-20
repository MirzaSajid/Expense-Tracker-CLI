"""Command-line interface (argparse). Contains presentation only, no business logic."""

from __future__ import annotations

import argparse
import os
import sys
from decimal import Decimal

from . import __version__
from .models import CATEGORIES, Expense, ValidationError
from .service import ExpenseTracker, NotFoundError
from .storage import JsonStore, StorageError

CURRENCY = os.environ.get("EXPENSE_CURRENCY", "PKR")
BAR_WIDTH = 24


def money(value: Decimal) -> str:
    return f"{CURRENCY} {value:,.2f}"


def print_table(expenses: list[Expense]) -> None:
    if not expenses:
        print("No expenses found.")
        return
    print(f"{'ID':>4}  {'Date':<10}  {'Category':<14}  {'Amount':>14}  Description")
    print("-" * 70)
    for e in expenses:
        print(f"{e.id:>4}  {e.date.isoformat():<10}  {e.category:<14}  "
              f"{e.amount:>14,.2f}  {e.description}")
    print("-" * 70)
    print(f"{'Total':>32}  {ExpenseTracker.total(expenses):>14,.2f}  ({len(expenses)} records)")


def bar(fraction: float) -> str:
    filled = round(fraction * BAR_WIDTH)
    return "#" * filled + "." * (BAR_WIDTH - filled)


# ---- command handlers ----------------------------------------------------
def cmd_add(tracker: ExpenseTracker, args) -> None:
    e = tracker.add(args.amount, args.category, args.description or "", args.date)
    print(f"Added #{e.id}: {money(e.amount)} on {e.category} ({e.date.isoformat()})")


def cmd_list(tracker: ExpenseTracker, args) -> None:
    print_table(tracker.list(args.category, args.month, args.start, args.end))


def cmd_delete(tracker: ExpenseTracker, args) -> None:
    e = tracker.delete(args.id)
    print(f"Deleted #{e.id}: {money(e.amount)} ({e.category})")


def cmd_summary(tracker: ExpenseTracker, args) -> None:
    expenses = tracker.list(month=args.month)
    if not expenses:
        print("No expenses found.")
        return
    total = tracker.total(expenses)
    title = f"Summary for {args.month}" if args.month else "Summary (all time)"
    print(f"{title}\n{'=' * len(title)}")
    print(f"Total spent:  {money(total)}")
    print(f"Transactions: {len(expenses)}")
    print(f"Average:      {money((total / len(expenses)).quantize(Decimal('0.01')))}")
    biggest = max(expenses, key=lambda e: e.amount)
    print(f"Largest:      {money(biggest.amount)} ({biggest.category}, {biggest.date.isoformat()})")
    print("\nBy category")
    for category, amount in tracker.by_category(expenses):
        share = amount / total
        print(f"  {category:<14} {bar(float(share))} {share:>6.1%}  {money(amount)}")


def cmd_monthly(tracker: ExpenseTracker, args) -> None:
    totals = tracker.monthly_totals(tracker.list())
    if not totals:
        print("No expenses found.")
        return
    peak = max(v for _, v in totals)
    print("Monthly spending")
    for month, amount in totals:
        print(f"  {month}  {bar(float(amount / peak))}  {money(amount)}")


def cmd_budget(tracker: ExpenseTracker, args) -> None:
    if args.action == "set":
        if not (args.category and args.amount):
            raise ValidationError("Usage: budget set <category> <amount>")
        tracker.set_budget(args.category, args.amount)
        print(f"Monthly budget for {args.category}: {money(Decimal(args.amount))}")
        return
    statuses = tracker.budget_status(args.month)
    if not statuses:
        print("No budgets set. Use: budget set <category> <amount>")
        return
    print(f"{'Category':<14} {'Budget':>14} {'Spent':>14} {'Left':>14}  Used")
    for s in statuses:
        flag = "  OVER BUDGET" if s.exceeded else ""
        print(f"{s.category:<14} {s.budget:>14,.2f} {s.spent:>14,.2f} "
              f"{s.remaining:>14,.2f}  {s.percent_used}%{flag}")


def cmd_export(tracker: ExpenseTracker, args) -> None:
    count = tracker.export_csv(args.output, tracker.list(month=args.month))
    print(f"Exported {count} records to {args.output}")


# ---- parser --------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="expense-tracker", description="Track, analyse and export personal expenses.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--file", help="path to the data file (default: ~/.expense_tracker/data.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add", help="record a new expense")
    p.add_argument("amount")
    p.add_argument("category", help=f"one of: {', '.join(CATEGORIES)}")
    p.add_argument("-d", "--description")
    p.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list", help="list expenses")
    p.add_argument("-c", "--category")
    p.add_argument("-m", "--month", help="YYYY-MM")
    p.add_argument("--start", help="YYYY-MM-DD")
    p.add_argument("--end", help="YYYY-MM-DD")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("delete", help="delete an expense by id")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("summary", help="totals, average and category breakdown")
    p.add_argument("-m", "--month", help="YYYY-MM")
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("monthly", help="spending trend by month")
    p.set_defaults(func=cmd_monthly)

    p = sub.add_parser("budget", help="set or check monthly budgets")
    p.add_argument("action", choices=["set", "status"])
    p.add_argument("category", nargs="?")
    p.add_argument("amount", nargs="?")
    p.add_argument("-m", "--month", help="YYYY-MM (status only, default: current month)")
    p.set_defaults(func=cmd_budget)

    p = sub.add_parser("export", help="export expenses to CSV")
    p.add_argument("output", help="destination .csv file")
    p.add_argument("-m", "--month", help="YYYY-MM")
    p.set_defaults(func=cmd_export)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tracker = ExpenseTracker(JsonStore(args.file))
    try:
        args.func(tracker, args)
    except (ValidationError, NotFoundError, StorageError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
