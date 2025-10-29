"""In-memory tracking for task execution states, logs and metrics."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from enum import Enum
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional
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

    def summary(self, rule_id: Optional[str] = None) -> Dict[str, object]:
        totals: Dict[str, int] = {status.value: 0 for status in TaskStatus}
        runs = list(self.list_runs(rule_id)) if rule_id is not None else list(self._runs.values())
        for run in runs:
            totals[run.status.value] += 1
        return {
            "total": len(runs),
            "by_status": totals,
        }

    def aggregate_daily(self, rule_id: Optional[str] = None) -> List["DailyRunAggregate"]:
        buckets: Dict[date, List[TaskRun]] = defaultdict(list)
        for run in self.list_runs(rule_id) if rule_id is not None else self._runs.values():
            buckets[run.created_at.date()].append(run)
        aggregates = [
            DailyRunAggregate.from_runs(day, runs)
            for day, runs in buckets.items()
        ]
        return sorted(aggregates, key=lambda aggregate: aggregate.date)

    def metric_series(self, rule_id: Optional[str] = None) -> List[Dict[str, Any]]:
        series: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        runs = self.list_runs(rule_id) if rule_id is not None else self._runs.values()
        for run in runs:
            if not run.metrics:
                continue
            timestamp = (run.finished_at or run.updated_at).isoformat().replace("+00:00", "Z")
            for key, value in run.metrics.items():
                series[key].append({
                    "run_id": run.id,
                    "value": value,
                    "timestamp": timestamp,
                })
        return [
            {"name": name, "points": points}
            for name, points in sorted(series.items())
        ]

    def export_state(self) -> Dict[str, Any]:
        return {
            "runs": [
                _serialize_run(run)
                for run in sorted(self._runs.values(), key=lambda item: item.created_at)
            ]
        }

    def import_state(self, state: Dict[str, Any]) -> None:
        runs_payload = state.get("runs", [])
        self._runs = {}
        for payload in runs_payload:
            run = _deserialize_run(payload)
            self._runs[run.id] = run

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

    def summary(self, rule_id: Optional[str] = None) -> Dict[str, object]:
        return self.repository.summary(rule_id)

    def dashboard(self, rule_id: Optional[str] = None) -> Dict[str, Any]:
        aggregates = [
            aggregate.to_payload()
            for aggregate in self.repository.aggregate_daily(rule_id)
        ]
        return {
            "summary": self.summary(rule_id),
            "daily": aggregates,
            "series": self.repository.metric_series(rule_id),
        }

    def export_state(self) -> Dict[str, Any]:
        return self.repository.export_state()

    def import_state(self, state: Dict[str, Any]) -> None:
        self.repository.import_state(state)


@dataclass(frozen=True)
class DailyRunAggregate:
    """Aggregate statistics for a given day."""

    date: date
    totals: Dict[str, int]
    avg_duration_ms: Optional[float]
    metrics: Dict[str, float]

    @classmethod
    def from_runs(cls, day: date, runs: Iterable[TaskRun]) -> "DailyRunAggregate":
        totals: Dict[str, int] = {status.value: 0 for status in TaskStatus}
        durations: List[float] = []
        metric_values: Dict[str, List[float]] = defaultdict(list)
        for run in runs:
            totals[run.status.value] += 1
            if run.duration_ms is not None:
                durations.append(run.duration_ms)
            for key, value in run.metrics.items():
                metric_values[key].append(value)
        avg_duration = mean(durations) if durations else None
        aggregated_metrics = {key: mean(values) for key, values in metric_values.items()}
        return cls(
            date=day,
            totals=totals,
            avg_duration_ms=avg_duration,
            metrics=aggregated_metrics,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "date": self.date.isoformat(),
            "by_status": dict(self.totals),
            "total": sum(self.totals.values()),
            "avg_duration_ms": self.avg_duration_ms,
        }
        if self.metrics:
            payload["metrics"] = self.metrics
        return payload


def _serialize_run(run: TaskRun) -> Dict[str, Any]:
    return {
        "id": run.id,
        "rule_id": run.rule_id,
        "status": run.status.value,
        "created_at": run.created_at.isoformat().replace("+00:00", "Z"),
        "updated_at": run.updated_at.isoformat().replace("+00:00", "Z"),
        "started_at": (
            run.started_at.isoformat().replace("+00:00", "Z")
            if run.started_at
            else None
        ),
        "finished_at": (
            run.finished_at.isoformat().replace("+00:00", "Z")
            if run.finished_at
            else None
        ),
        "metrics": dict(run.metrics),
        "error_message": run.error_message,
        "execution_id": run.execution_id,
        "logs": [
            {
                "timestamp": entry.timestamp.isoformat().replace("+00:00", "Z"),
                "level": entry.level,
                "message": entry.message,
            }
            for entry in run.logs
        ],
    }


def _deserialize_run(payload: Dict[str, Any]) -> TaskRun:
    def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
        if value is None:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    logs = [
        TaskLogEntry(
            timestamp=datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")),
            level=entry["level"],
            message=entry["message"],
        )
        for entry in payload.get("logs", [])
    ]
    return TaskRun(
        id=payload["id"],
        rule_id=payload["rule_id"],
        status=TaskStatus(payload["status"]),
        created_at=datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(payload["updated_at"].replace("Z", "+00:00")),
        started_at=_parse_timestamp(payload.get("started_at")),
        finished_at=_parse_timestamp(payload.get("finished_at")),
        logs=logs,
        metrics=dict(payload.get("metrics", {})),
        error_message=payload.get("error_message"),
        execution_id=payload.get("execution_id"),
    )

