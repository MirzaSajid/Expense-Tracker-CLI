import unittest
from datetime import date, timedelta
from decimal import Decimal

from expense_tracker.models import (Expense, ValidationError, parse_amount,
                                    parse_category, parse_date, parse_month)


class TestParsing(unittest.TestCase):
    def test_amount_valid(self):
        self.assertEqual(parse_amount("1,250.5"), Decimal("1250.50"))
        self.assertEqual(parse_amount(10), Decimal("10.00"))

    def test_amount_invalid(self):
        for bad in ("abc", "", "-5", "0", "nan", "inf"):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                parse_amount(bad)

    def test_decimal_precision(self):
        self.assertEqual(parse_amount("0.1") + parse_amount("0.2"), Decimal("0.30"))

    def test_date(self):
        self.assertEqual(parse_date("2024-02-29"), date(2024, 2, 29))
        self.assertEqual(parse_date(None), date.today())
        with self.assertRaises(ValidationError):
            parse_date("29-02-2024")
        with self.assertRaises(ValidationError):
            parse_date(date.today() + timedelta(days=1))

    def test_category_and_month(self):
        self.assertEqual(parse_category("  FOOD "), "food")
        with self.assertRaises(ValidationError):
            parse_category("games")
        self.assertEqual(parse_month("2025-03"), (2025, 3))
        with self.assertRaises(ValidationError):
            parse_month("2025-13")

    def test_roundtrip(self):
        e = Expense(1, date(2025, 1, 5), Decimal("99.99"), "food", "Pizza")
        self.assertEqual(Expense.from_dict(e.to_dict()), e)


if __name__ == "__main__":
    unittest.main()
