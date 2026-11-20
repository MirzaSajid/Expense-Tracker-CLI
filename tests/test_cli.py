import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from expense_tracker.cli import main


class TestCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.file = str(Path(self._tmp.name) / "d.json")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--file", self.file, *argv])
        return code, out.getvalue(), err.getvalue()

    def test_add_and_list(self):
        code, out, _ = self.run_cli("add", "1500", "food", "-d", "Groceries", "--date", "2025-01-02")
        self.assertEqual(code, 0)
        self.assertIn("Added #1", out)
        code, out, _ = self.run_cli("list")
        self.assertIn("Groceries", out)
        self.assertIn("1,500.00", out)

    def test_invalid_amount_returns_error_code(self):
        code, _, err = self.run_cli("add", "abc", "food")
        self.assertEqual(code, 1)
        self.assertIn("Invalid amount", err)

    def test_delete_missing(self):
        code, _, err = self.run_cli("delete", "42")
        self.assertEqual(code, 1)
        self.assertIn("No expense with id 42", err)

    def test_summary_and_budget(self):
        self.run_cli("add", "800", "food", "--date", "2025-05-01")
        self.run_cli("add", "200", "transport", "--date", "2025-05-02")
        self.run_cli("budget", "set", "food", "500")
        _, out, _ = self.run_cli("summary", "-m", "2025-05")
        self.assertIn("1,000.00", out)
        self.assertIn("80.0%", out)
        _, out, _ = self.run_cli("budget", "status", "-m", "2025-05")
        self.assertIn("OVER BUDGET", out)

    def test_empty_state_messages(self):
        self.assertIn("No expenses", self.run_cli("summary")[1])
        self.assertIn("No budgets", self.run_cli("budget", "status")[1])


if __name__ == "__main__":
    unittest.main()
