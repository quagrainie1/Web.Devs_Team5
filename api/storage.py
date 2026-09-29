"""
api/storage.py

In-memory data store for the MoMo Transactions API.

Loads data/transactions.json (produced by dsa/parse_xml.py) once at startup
into two structures:
  - a list of transactions, in original order (used for the linear-search
    DSA comparison in dsa/search.py)
  - a dict keyed by transaction id (used for O(1) lookups by the API and
    for the dictionary-lookup half of the DSA comparison)

All CRUD operations in api/server.py go through this module so there's a
single source of truth for "the data" while the server is running.
"""

import json
import threading
from pathlib import Path

# Resolve paths relative to this file, not the current working directory,
# so the server works no matter where you launch it from.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "transactions.json"

_lock = threading.Lock()
_transactions_by_id: dict[int, dict] = {}
_next_id = 1


def load() -> None:
    """Load transactions.json into memory. Call once at server startup."""
    global _transactions_by_id, _next_id

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    with _lock:
        _transactions_by_id = {r["id"]: r for r in records}
        _next_id = (max(_transactions_by_id.keys()) + 1) if _transactions_by_id else 1


def list_all() -> list[dict]:
    """Return all transactions as a list, in id order."""
    with _lock:
        return [_transactions_by_id[k] for k in sorted(_transactions_by_id.keys())]


def get(transaction_id: int) -> dict | None:
    """O(1) dictionary lookup by id. Returns None if not found."""
    with _lock:
        return _transactions_by_id.get(transaction_id)


def create(data: dict) -> dict:
    """Insert a new transaction, auto-assigning the next id."""
    global _next_id
    with _lock:
        new_record = dict(data)
        new_record["id"] = _next_id
        _transactions_by_id[_next_id] = new_record
        _next_id += 1
        return new_record


def update(transaction_id: int, data: dict) -> dict | None:
    """Replace fields on an existing transaction. Returns the updated
    record, or None if the id doesn't exist."""
    with _lock:
        if transaction_id not in _transactions_by_id:
            return None
        existing = _transactions_by_id[transaction_id]
        updated = {**existing, **data, "id": transaction_id}  # id is immutable
        _transactions_by_id[transaction_id] = updated
        return updated


def delete(transaction_id: int) -> bool:
    """Remove a transaction by id. Returns True if it existed."""
    with _lock:
        if transaction_id in _transactions_by_id:
            del _transactions_by_id[transaction_id]
            return True
        return False


def count() -> int:
    with _lock:
        return len(_transactions_by_id)
