"""In-memory storage helpers for execution results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional
from uuid import uuid4

from .engine import ExecutionResult


@dataclass
class ExecutionRecord:
    """Represents a persisted execution result for a rule."""

    id: str
    rule_id: str
    created_at: datetime
    result: ExecutionResult

    @property
    def item_count(self) -> int:
        """Return the number of top-level records contained in the result."""

        return len(self.result.records)

    @property
    def detail_count(self) -> int:
        """Return the number of detail records contained in the result."""

        return len(self.result.detail_records)


class ExecutionNotFoundError(KeyError):
    """Raised when an execution identifier cannot be found in the repository."""


class ResultRepository:
    """Store execution records in memory and provide basic lookup APIs."""

    def __init__(self) -> None:
        self._records: Dict[str, ExecutionRecord] = {}

    def add(self, rule_id: str, result: ExecutionResult) -> ExecutionRecord:
        """Persist an execution result and return the created record."""

        record = ExecutionRecord(
            id=uuid4().hex,
            rule_id=rule_id,
            created_at=datetime.now(tz=timezone.utc),
            result=result,
        )
        self._records[record.id] = record
        return record

    def get(self, execution_id: str) -> ExecutionRecord:
        """Return a specific execution record by identifier."""

        try:
            return self._records[execution_id]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ExecutionNotFoundError(execution_id) from exc

    def list(self, rule_id: Optional[str] = None) -> Iterable[ExecutionRecord]:
        """List execution records optionally filtered by rule identifier."""

        records: Iterable[ExecutionRecord]
        if rule_id is None:
            records = self._records.values()
        else:
            records = (record for record in self._records.values() if record.rule_id == rule_id)
        return sorted(records, key=lambda record: record.created_at, reverse=True)

    def remove_for_rule(self, rule_id: str) -> None:
        """Remove all execution records for a specific rule."""

        to_delete: List[str] = [
            key
            for key, value in self._records.items()
            if value.rule_id == rule_id
        ]
        for execution_id in to_delete:
            del self._records[execution_id]

