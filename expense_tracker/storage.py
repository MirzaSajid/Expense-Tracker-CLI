"""JSON persistence with atomic writes so a crash can never corrupt the data file."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

DEFAULT_PATH = Path.home() / ".expense_tracker" / "data.json"


class StorageError(RuntimeError):
    """Raised when the data file cannot be read or written."""


def empty_state() -> dict:
    return {"next_id": 1, "expenses": [], "budgets": {}}


class JsonStore:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path or os.environ.get("EXPENSE_TRACKER_FILE") or DEFAULT_PATH)

    def load(self) -> dict:
        if not self.path.exists():
            return empty_state()
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                state = json.load(fh)
        except json.JSONDecodeError as exc:
            raise StorageError(f"Data file is corrupted ({self.path}): {exc}") from exc
        except OSError as exc:
            raise StorageError(f"Cannot read {self.path}: {exc}") from exc
        for key, default in empty_state().items():
            state.setdefault(key, default)
        return state

    def save(self, state: dict) -> None:
        """Write to a temp file in the same directory, then atomically replace."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(state, fh, indent=2, ensure_ascii=False)
                os.replace(tmp_name, self.path)
            except BaseException:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
                raise
        except OSError as exc:
            raise StorageError(f"Cannot write {self.path}: {exc}") from exc
