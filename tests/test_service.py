import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from expense_tracker.service import ExpenseTracker, NotFoundError
from expense_tracker.storage import JsonStore, StorageError
from expense_tracker.models import ValidationError


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "data.json"
        self.tracker = ExpenseTracker(JsonStore(self.path))


class TestCrud(ServiceTestCase):
    def test_add_persists_and_increments_id(self):
        a = self.tracker.add("100", "food", "lunch", "2025-01-10")
        b = self.tracker.add("50", "bills", on="2025-01-11")
        self.assertEqual((a.id, b.id), (1, 2))
        reloaded = ExpenseTracker(JsonStore(self.path)).list()
        self.assertEqual(len(reloaded), 2)

    def test_ids_never_reused_after_delete(self):
        self.tracker.add("10", "food", on="2025-01-01")
        self.tracker.delete(1)
        self.assertEqual(self.tracker.add("10", "food", on="2025-01-02").id, 2)

    def test_delete_missing(self):
        with self.assertRaises(NotFoundError):
            self.tracker.delete(99)

    def test_invalid_input_not_saved(self):
        with self.assertRaises(ValidationError):
            self.tracker.add("-5", "food")
        self.assertEqual(self.tracker.list(), [])


class TestQueries(ServiceTestCase):
    def setUp(self):
        super().setUp()
        for amount, cat, day in [("100", "food", "2025-01-05"), ("250", "bills", "2025-01-20"),
                                 ("75.50", "food", "2025-02-02"), ("40", "transport", "2025-02-14")]:
            self.tracker.add(amount, cat, on=day)

    def test_filters(self):
        self.assertEqual(len(self.tracker.list(category="food")), 2)
        self.assertEqual(len(self.tracker.list(month="2025-02")), 2)
        self.assertEqual(len(self.tracker.list(start="2025-01-10", end="2025-02-05")), 2)

    def test_sorted_newest_first(self):
        dates = [e.date for e in self.tracker.list()]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_totals(self):
        expenses = self.tracker.list()
        self.assertEqual(self.tracker.total(expenses), Decimal("465.50"))
        self.assertEqual(self.tracker.by_category(expenses)[0], ("bills", Decimal("250.00")))
        self.assertEqual(self.tracker.monthly_totals(expenses),
                         [("2025-01", Decimal("350.00")), ("2025-02", Decimal("115.50"))])

    def test_empty_total_is_zero(self):
        self.assertEqual(ExpenseTracker.total([]), Decimal("0.00"))


class TestBudgets(ServiceTestCase):
    def test_budget_status(self):
        self.tracker.set_budget("food", 150)
        self.tracker.add("100", "food", on="2025-03-01")
        self.tracker.add("80", "food", on="2025-03-09")
        (status,) = self.tracker.budget_status("2025-03")
        self.assertEqual(status.spent, Decimal("180.00"))
        self.assertEqual(status.remaining, Decimal("-30.00"))
        self.assertTrue(status.exceeded)
        self.assertEqual(status.percent_used, Decimal("120.0"))

    def test_other_months_not_counted(self):
        self.tracker.set_budget("food", 150)
        self.tracker.add("100", "food", on="2025-03-01")
        (status,) = self.tracker.budget_status("2025-04")
        self.assertEqual(status.spent, Decimal("0.00"))
        self.assertFalse(status.exceeded)


class TestStorageAndExport(ServiceTestCase):
    def test_corrupt_file_raises(self):
        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(StorageError):
            self.tracker.list()

    def test_missing_file_is_empty(self):
        self.assertEqual(self.tracker.list(), [])

    def test_csv_export(self):
        self.tracker.add("12.5", "food", "Tea, with milk", "2025-01-01")
        out = Path(self._tmp.name) / "out.csv"
        self.assertEqual(self.tracker.export_csv(out), 1)
        lines = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "id,date,amount,category,description")
        self.assertEqual(lines[1], '1,2025-01-01,12.50,food,"Tea, with milk"')


if __name__ == "__main__":
    unittest.main()
