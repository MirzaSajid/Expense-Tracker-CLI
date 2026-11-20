# Expense Tracker CLI

![tests](https://github.com/YOUR-USERNAME/expense-tracker-cli/actions/workflows/tests.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

A command-line tool to record, analyse and export personal expenses.
Built with **pure Python (standard library only)** as the Module 02 mini project
of the AI & Python program.

## Features

- Add, list and delete expenses with category, date and description
- Filter by category, month or date range
- Summary with total, average, largest expense and a per-category bar chart
- Monthly spending trend
- Per-category **monthly budgets** with over-budget warnings
- **CSV export** for Excel / Google Sheets
- Exact money arithmetic with `Decimal` (no floating-point rounding errors)
- Atomic JSON saves, so a crash can never corrupt your data
- Strict input validation with clear error messages and proper exit codes
- 24 unit tests, plus CI on Python 3.9, 3.11 and 3.12

## Installation

```bash
git clone https://github.com/YOUR-USERNAME/expense-tracker-cli.git
cd expense-tracker-cli

# Option A: run directly, nothing to install
python -m expense_tracker --help

# Option B: install the `expense-tracker` command
pip install -e .
expense-tracker --help
```

Requires Python 3.9 or newer. No third-party dependencies.

## Usage

```bash
# Record expenses (date defaults to today)
expense-tracker add 1250 food -d "Groceries"
expense-tracker add 3500 bills -d "Electricity" --date 2025-01-15

# View and filter
expense-tracker list
expense-tracker list -c food -m 2025-01
expense-tracker list --start 2025-01-01 --end 2025-01-31

# Analyse
expense-tracker summary
expense-tracker summary -m 2025-01
expense-tracker monthly

# Budgets
expense-tracker budget set food 4000
expense-tracker budget status

# Export and cleanup
expense-tracker export report.csv -m 2025-01
expense-tracker delete 3
```

Categories: `food, transport, bills, shopping, health, education, entertainment, other`

### Try it with demo data

```bash
python seed_demo_data.py demo_data.json
expense-tracker --file demo_data.json summary
```

### Example output

```
Summary (all time)
==================
Total spent:  PKR 21,929.00
Transactions: 13
Average:      PKR 1,686.85
Largest:      PKR 5,200.00 (bills, 2026-08-21)

By category
  bills          ##########..............  39.7%  PKR 8,700.00
  food           ######..................  25.5%  PKR 5,600.00
  shopping       ###.....................  13.7%  PKR 2,999.00
  education      ##......................   8.2%  PKR 1,800.00
```

```
Category               Budget          Spent           Left  Used
entertainment          800.00           0.00         800.00  0.0%
food                 4,000.00       2,750.00       1,250.00  68.8%
```

## Configuration

| Setting | How | Default |
|---------|-----|---------|
| Data file | `--file PATH` or env `EXPENSE_TRACKER_FILE` | `~/.expense_tracker/data.json` |
| Currency label | env `EXPENSE_CURRENCY` | `PKR` |

## Project Structure

```
expense-tracker-cli/
├── expense_tracker/
│   ├── models.py      # Expense dataclass + validation (Decimal money, dates, categories)
│   ├── storage.py     # JSON persistence with atomic writes
│   ├── service.py     # Business logic: CRUD, filters, aggregation, budgets, CSV export
│   ├── cli.py         # argparse interface and output formatting only
│   └── __main__.py    # enables `python -m expense_tracker`
├── tests/             # unit tests for models, service and CLI
├── seed_demo_data.py  # sample data generator
├── pyproject.toml     # packaging and the `expense-tracker` entry point
└── .github/workflows/tests.yml
```

### Design decisions

- **Separation of concerns.** The CLI contains no business logic, so the same
  `ExpenseTracker` class could power a web or GUI front end without changes.
- **`Decimal` for money.** Floats give `0.1 + 0.2 = 0.30000000000000004`; a finance
  tool must not. Amounts are stored as strings in JSON to preserve exactness.
- **Atomic writes.** Data is written to a temp file and swapped in with
  `os.replace`, so an interruption never leaves a half-written file.
- **Immutable records.** `Expense` is a frozen dataclass; IDs are never reused
  after deletion, keeping references stable.
- **Fail loudly and clearly.** Invalid input raises typed exceptions that the CLI
  turns into readable messages and a non-zero exit code (useful in scripts).

## Running the Tests

```bash
python -m unittest discover -s tests -v
```

The suite covers parsing and validation edge cases (NaN, negative, malformed
dates, future dates), CRUD and ID behaviour, filtering and aggregation,
budget calculations, corrupt/missing data files, CSV escaping, and
end-to-end CLI behaviour including exit codes.

## Possible Extensions

- Recurring expenses and income tracking
- Charts with Matplotlib
- SQLite backend or a REST API
- Multi-currency support

## License

MIT. See [LICENSE](LICENSE).
