"""Populate a demo data file so every command has something to show.

Usage:  python seed_demo_data.py [path/to/demo.json]
"""

import sys
from datetime import date, timedelta

from expense_tracker.service import ExpenseTracker
from expense_tracker.storage import JsonStore

SAMPLE = [
    (1250, "food", "Groceries"), (480, "transport", "Ride to university"),
    (3500, "bills", "Electricity"), (2999, "shopping", "Headphones"),
    (650, "food", "Lunch with friends"), (1800, "education", "Online course"),
    (900, "entertainment", "Cinema"), (300, "transport", "Fuel"),
    (750, "health", "Pharmacy"), (2200, "food", "Weekly groceries"),
    (5200, "bills", "Internet and phone"), (400, "other", "Gift"),
]


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "demo_data.json"
    tracker = ExpenseTracker(JsonStore(path))
    today = date.today()
    for i, (amount, category, note) in enumerate(SAMPLE):
        tracker.add(amount, category, note, today - timedelta(days=i * 9 + 1))
    tracker.set_budget("food", 4000)
    tracker.set_budget("entertainment", 800)
    print(f"Seeded {len(SAMPLE)} expenses into {path}")


if __name__ == "__main__":
    main()
