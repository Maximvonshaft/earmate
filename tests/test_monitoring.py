from __future__ import annotations

import pytest

from earmate.monitoring import MonitoringRepository, MonitoringService, TaskStatus
from earmate.rule_manager import RuleRepository, RuleService
from earmate.schema import RuleSchema, SelectorConfig
from earmate.storage import ResultRepository


@pytest.fixture
def monitoring_service() -> MonitoringService:
    return MonitoringService(MonitoringRepository())


@pytest.fixture
def simple_rule() -> RuleSchema:
    return RuleSchema(
        name="list",
        entry="https://example.com/list",
        selectors=SelectorConfig(list="article", title="h2", url="h2 a"),
    )


def test_repository_lifecycle() -> None:
    repository = MonitoringRepository()
    run = repository.create_run("rule-1")
    assert run.status is TaskStatus.PENDING

    running = repository.mark_running(run.id)
    assert running.status is TaskStatus.RUNNING
    assert running.started_at is not None

    repository.append_log(run.id, "info", "hello world")
    with pytest.raises(ValueError):
        repository.mark_completed(run.id, status=TaskStatus.RUNNING)

    completed = repository.mark_completed(
        run.id,
        status=TaskStatus.SUCCEEDED,
        metrics={"items": 2.0},
    )
    assert completed.status is TaskStatus.SUCCEEDED
    assert completed.finished_at is not None
    assert completed.metrics["items"] == 2.0

    summary = repository.summary()
    assert summary["total"] == 1
    assert summary["by_status"][TaskStatus.SUCCEEDED.value] == 1


def test_rule_service_emits_monitoring_events(
    simple_rule: RuleSchema,
    fetcher,
    monitoring_service: MonitoringService,
) -> None:
    repository = RuleRepository()
    results = ResultRepository()
    service = RuleService(
        repository,
        fetcher=fetcher,
        result_repository=results,
        monitoring=monitoring_service,
    )

    created = service.create_rule(simple_rule)
    result = service.run_rule(created.id)

    assert result.metadata["status"] == TaskStatus.SUCCEEDED.value
    run_id = result.metadata["run_id"]

    runs = list(monitoring_service.list_runs(created.id))
    assert len(runs) == 1
    run = runs[0]
    assert run.id == run_id
    assert run.execution_id == result.metadata["execution_id"]
    assert run.metrics["items"] == pytest.approx(2.0)


def test_rule_service_failure_is_recorded(
    simple_rule: RuleSchema,
    monitoring_service: MonitoringService,
) -> None:
    def failing_fetcher(_url: str) -> str:
        raise RuntimeError("boom")

    repository = RuleRepository()
    service = RuleService(
        repository,
        fetcher=failing_fetcher,
        monitoring=monitoring_service,
    )
    created = service.create_rule(simple_rule)

    with pytest.raises(RuntimeError):
        service.run_rule(created.id)

    runs = list(monitoring_service.list_runs(created.id))
    assert runs
    assert runs[0].status is TaskStatus.FAILED
    assert "boom" in (runs[0].error_message or "")


def test_preview_rule_runs_when_disabled(
    simple_rule: RuleSchema,
    fetcher,
    monitoring_service: MonitoringService,
) -> None:
    repository = RuleRepository()
    results = ResultRepository()
    service = RuleService(
        repository,
        fetcher=fetcher,
        result_repository=results,
        monitoring=monitoring_service,
    )
    created = service.create_rule(simple_rule)
    service.set_enabled(created.id, False)

    result = service.preview_rule(created.id)

    assert result.metadata["status"] == TaskStatus.SUCCEEDED.value
    assert result.metadata["run_id"]
    runs = list(monitoring_service.list_runs(created.id))
    assert runs and runs[0].rule_id == created.id
    executions = list(service.list_executions(created.id))
    assert executions and executions[0].id == result.metadata["execution_id"]


def test_dashboard_aggregates_runs(monitoring_service: MonitoringService) -> None:
    repository = monitoring_service.repository
    run_success = repository.create_run("rule-a")
    repository.mark_running(run_success.id)
    repository.mark_completed(
        run_success.id,
        status=TaskStatus.SUCCEEDED,
        metrics={"items": 3.0},
        execution_id="exec-1",
    )

    run_failed = repository.create_run("rule-a")
    repository.mark_running(run_failed.id)
    repository.mark_completed(run_failed.id, status=TaskStatus.FAILED, error_message="timeout")

    dashboard = monitoring_service.dashboard("rule-a")
    assert dashboard["summary"]["total"] == 2
    assert dashboard["daily"]
    assert dashboard["daily"][0]["by_status"][TaskStatus.SUCCEEDED.value] == 1
    assert dashboard["series"][0]["name"] == "items"
    assert dashboard["series"][0]["points"][0]["run_id"] == run_success.id


def test_export_and_import_state_roundtrip(monitoring_service: MonitoringService) -> None:
    repository = monitoring_service.repository
    run = repository.create_run("rule-x")
    repository.mark_running(run.id)
    repository.append_log(run.id, "info", "start")
    repository.mark_completed(run.id, status=TaskStatus.SUCCEEDED)

    snapshot = monitoring_service.export_state()
    assert snapshot["runs"]

    restored = MonitoringService(MonitoringRepository())
    restored.import_state(snapshot)

    restored_runs = list(restored.list_runs())
    assert restored_runs
    assert restored_runs[0].id == run.id
