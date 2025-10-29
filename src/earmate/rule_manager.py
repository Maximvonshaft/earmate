"""In-memory rule repository and service helpers for the scraping engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional
from uuid import uuid4

from .engine import ExecutionResult, HtmlFetcher, RuleExecutor
from .monitoring import MonitoringService, TaskStatus
from .schema import RuleSchema
from .storage import ExecutionNotFoundError, ExecutionRecord, ResultRepository


@dataclass
class RuleRecord:
    """Metadata wrapper around a :class:`RuleSchema`."""

    id: str
    rule: RuleSchema
    created_at: datetime
    updated_at: datetime
    enabled: bool = True


class RuleNotFoundError(KeyError):
    """Raised when a rule identifier cannot be found in the repository."""


class RuleRepository:
    """Stores :class:`RuleRecord` instances in memory."""

    def __init__(self) -> None:
        self._records: Dict[str, RuleRecord] = {}

    def create(self, rule: RuleSchema) -> RuleRecord:
        now = datetime.now(tz=timezone.utc)
        record = RuleRecord(id=uuid4().hex, rule=rule, created_at=now, updated_at=now)
        self._records[record.id] = record
        return record

    def update(self, rule_id: str, rule: RuleSchema) -> RuleRecord:
        if rule_id not in self._records:
            raise RuleNotFoundError(rule_id)
        existing = self._records[rule_id]
        updated = RuleRecord(
            id=existing.id,
            rule=rule,
            created_at=existing.created_at,
            updated_at=datetime.now(tz=timezone.utc),
            enabled=existing.enabled,
        )
        self._records[rule_id] = updated
        return updated

    def get(self, rule_id: str) -> RuleRecord:
        try:
            return self._records[rule_id]
        except KeyError as exc:
            raise RuleNotFoundError(rule_id) from exc

    def delete(self, rule_id: str) -> None:
        if rule_id not in self._records:
            raise RuleNotFoundError(rule_id)
        del self._records[rule_id]

    def list(self) -> Iterable[RuleRecord]:
        return sorted(self._records.values(), key=lambda record: record.created_at)

    def set_enabled(self, rule_id: str, enabled: bool) -> RuleRecord:
        record = self.get(rule_id)
        updated = RuleRecord(
            id=record.id,
            rule=record.rule,
            created_at=record.created_at,
            updated_at=datetime.now(tz=timezone.utc),
            enabled=enabled,
        )
        self._records[rule_id] = updated
        return updated


class RuleService:
    """High-level CRUD facade combining repository access with the executor."""

    def __init__(
        self,
        repository: RuleRepository,
        fetcher: Optional[HtmlFetcher] = None,
        result_repository: Optional[ResultRepository] = None,
        monitoring: Optional[MonitoringService] = None,
    ) -> None:
        self.repository = repository
        self.fetcher = fetcher
        self.result_repository = result_repository
        self.monitoring = monitoring

    def create_rule(self, rule: RuleSchema) -> RuleRecord:
        return self.repository.create(rule)

    def list_rules(self) -> List[RuleRecord]:
        return list(self.repository.list())

    def get_rule(self, rule_id: str) -> RuleRecord:
        return self.repository.get(rule_id)

    def update_rule(self, rule_id: str, rule: RuleSchema) -> RuleRecord:
        return self.repository.update(rule_id, rule)

    def delete_rule(self, rule_id: str) -> None:
        self.repository.delete(rule_id)
        if self.result_repository:
            self.result_repository.remove_for_rule(rule_id)

    def set_enabled(self, rule_id: str, enabled: bool) -> RuleRecord:
        return self.repository.set_enabled(rule_id, enabled)

    def run_rule(self, rule_id: str) -> ExecutionResult:
        record = self.repository.get(rule_id)
        if not record.enabled:
            raise RuleNotFoundError(f"rule {rule_id} is disabled")
        monitoring_run = None
        if self.monitoring is not None:
            monitoring_run = self.monitoring.create_run(rule_id)
            self.monitoring.append_log(monitoring_run.id, "info", "queued execution")
            self.monitoring.mark_running(monitoring_run.id)
            self.monitoring.append_log(monitoring_run.id, "info", "execution started")

        executor = RuleExecutor(record.rule, fetcher=self.fetcher)
        try:
            result = executor.run()
        except Exception as exc:
            if monitoring_run is not None:
                self.monitoring.append_log(monitoring_run.id, "error", str(exc))
                self.monitoring.mark_failure(monitoring_run.id, str(exc))
            raise

        execution_id = None
        if self.result_repository:
            execution_record = self.result_repository.add(rule_id, result)
            execution_id = execution_record.id

        if monitoring_run is not None:
            metrics = {
                "items": float(len(result.records)),
                "detail_items": float(len(result.detail_records)),
            }
            if execution_id:
                self.monitoring.attach_execution(monitoring_run.id, execution_id)
            self.monitoring.append_log(monitoring_run.id, "info", "execution finished")
            self.monitoring.mark_success(monitoring_run.id, metrics)
            result.metadata.setdefault("run_id", monitoring_run.id)

        if execution_id and "execution_id" not in result.metadata:
            result.metadata["execution_id"] = execution_id

        result.metadata.setdefault("status", TaskStatus.SUCCEEDED.value)
        return result

    def test_run(self, rule: RuleSchema) -> ExecutionResult:
        executor = RuleExecutor(rule, fetcher=self.fetcher)
        return executor.run()

    def list_executions(self, rule_id: Optional[str] = None) -> List[ExecutionRecord]:
        if not self.result_repository:
            return []
        return list(self.result_repository.list(rule_id))

    def get_execution(self, execution_id: str) -> ExecutionRecord:
        if not self.result_repository:
            raise ExecutionNotFoundError(execution_id)
        return self.result_repository.get(execution_id)
