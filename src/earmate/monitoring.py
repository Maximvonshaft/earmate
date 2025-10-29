"""In-memory tracking for task execution states, logs and metrics."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Iterable, List, Optional
from uuid import uuid4


class TaskStatus(str, Enum):
    """Lifecycle states for a scraping task execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class TaskLogEntry:
    """Single log entry associated with a task execution."""

    timestamp: datetime
    level: str
    message: str


@dataclass(frozen=True)
class TaskRun:
    """Represents the lifecycle of a single task execution."""

    id: str
    rule_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    logs: List[TaskLogEntry] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_id: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[float]:
        """Return the execution duration in milliseconds if available."""

        if self.started_at is None or self.finished_at is None:
            return None
        delta = self.finished_at - self.started_at
        return delta.total_seconds() * 1000


class TaskRunNotFoundError(KeyError):
    """Raised when a task execution identifier cannot be found."""


class MonitoringRepository:
    """Store :class:`TaskRun` objects in memory and provide query APIs."""

    def __init__(self) -> None:
        self._runs: Dict[str, TaskRun] = {}

    # ------------------------------------------------------------------
    # Run lifecycle management
    # ------------------------------------------------------------------
    def create_run(self, rule_id: str) -> TaskRun:
        now = datetime.now(tz=timezone.utc)
        run = TaskRun(
            id=uuid4().hex,
            rule_id=rule_id,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        self._runs[run.id] = run
        return run

    def mark_running(self, run_id: str) -> TaskRun:
        run = self._get(run_id)
        now = datetime.now(tz=timezone.utc)
        updated = replace(
            run,
            status=TaskStatus.RUNNING,
            started_at=now,
            updated_at=now,
        )
        self._runs[run_id] = updated
        return updated

    def mark_completed(
        self,
        run_id: str,
        *,
        status: TaskStatus,
        metrics: Optional[Dict[str, float]] = None,
        error_message: Optional[str] = None,
        execution_id: Optional[str] = None,
    ) -> TaskRun:
        if status not in {TaskStatus.SUCCEEDED, TaskStatus.FAILED}:
            raise ValueError("completion status must be succeeded or failed")
        run = self._get(run_id)
        now = datetime.now(tz=timezone.utc)
        updated = replace(
            run,
            status=status,
            finished_at=now,
            updated_at=now,
            metrics=metrics or run.metrics,
            error_message=error_message,
            execution_id=execution_id or run.execution_id,
        )
        self._runs[run_id] = updated
        return updated

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def append_log(self, run_id: str, level: str, message: str) -> TaskRun:
        run = self._get(run_id)
        now = datetime.now(tz=timezone.utc)
        entry = TaskLogEntry(timestamp=now, level=level.upper(), message=message)
        updated_logs = run.logs + [entry]
        updated = replace(run, logs=updated_logs, updated_at=now)
        self._runs[run_id] = updated
        return updated

    def attach_execution(self, run_id: str, execution_id: str) -> TaskRun:
        run = self._get(run_id)
        now = datetime.now(tz=timezone.utc)
        updated = replace(run, execution_id=execution_id, updated_at=now)
        self._runs[run_id] = updated
        return updated

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def get(self, run_id: str) -> TaskRun:
        return self._get(run_id)

    def list_runs(self, rule_id: Optional[str] = None) -> Iterable[TaskRun]:
        if rule_id is None:
            runs: Iterable[TaskRun] = self._runs.values()
        else:
            runs = (run for run in self._runs.values() if run.rule_id == rule_id)
        return sorted(runs, key=lambda run: run.created_at, reverse=True)

    def summary(self) -> Dict[str, object]:
        totals: Dict[str, int] = {status.value: 0 for status in TaskStatus}
        for run in self._runs.values():
            totals[run.status.value] += 1
        return {
            "total": len(self._runs),
            "by_status": totals,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get(self, run_id: str) -> TaskRun:
        try:
            return self._runs[run_id]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise TaskRunNotFoundError(run_id) from exc


class MonitoringService:
    """High-level facade around :class:`MonitoringRepository`."""

    def __init__(self, repository: MonitoringRepository) -> None:
        self.repository = repository

    def create_run(self, rule_id: str) -> TaskRun:
        return self.repository.create_run(rule_id)

    def mark_running(self, run_id: str) -> TaskRun:
        return self.repository.mark_running(run_id)

    def mark_success(self, run_id: str, metrics: Optional[Dict[str, float]] = None) -> TaskRun:
        return self.repository.mark_completed(
            run_id,
            status=TaskStatus.SUCCEEDED,
            metrics=metrics,
        )

    def mark_failure(self, run_id: str, message: str) -> TaskRun:
        return self.repository.mark_completed(
            run_id,
            status=TaskStatus.FAILED,
            error_message=message,
        )

    def append_log(self, run_id: str, level: str, message: str) -> TaskRun:
        return self.repository.append_log(run_id, level, message)

    def attach_execution(self, run_id: str, execution_id: str) -> TaskRun:
        return self.repository.attach_execution(run_id, execution_id)

    def get(self, run_id: str) -> TaskRun:
        return self.repository.get(run_id)

    def list_runs(self, rule_id: Optional[str] = None) -> Iterable[TaskRun]:
        return self.repository.list_runs(rule_id)

    def summary(self) -> Dict[str, object]:
        return self.repository.summary()

