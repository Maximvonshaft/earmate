from __future__ import annotations

import pytest

from earmate.rule_manager import RuleNotFoundError, RuleRepository, RuleService
from earmate.schema import RuleSchema, SelectorConfig
from earmate.storage import ResultRepository


@pytest.fixture
def simple_rule() -> RuleSchema:
    return RuleSchema(
        name="list",
        entry="https://example.com/list",
        selectors=SelectorConfig(list="article", title="h2", url="h2 a"),
    )


def test_repository_crud(simple_rule: RuleSchema) -> None:
    repository = RuleRepository()

    created = repository.create(simple_rule)
    assert created.id
    assert created.rule is simple_rule

    listed = list(repository.list())
    assert len(listed) == 1

    updated_rule = RuleSchema(
        name="list-updated",
        entry="https://example.com/list",
        selectors=SelectorConfig(list="article", title="h2", url="h2 a"),
    )
    repository.update(created.id, updated_rule)
    assert repository.get(created.id).rule.name == "list-updated"

    repository.set_enabled(created.id, False)
    assert repository.get(created.id).enabled is False

    repository.delete(created.id)
    assert list(repository.list()) == []

    with pytest.raises(RuleNotFoundError):
        repository.get(created.id)


def test_service_runs_rule(simple_rule: RuleSchema, fetcher) -> None:
    repository = RuleRepository()
    results = ResultRepository()
    service = RuleService(repository, fetcher=fetcher, result_repository=results)

    created = service.create_rule(simple_rule)
    result = service.run_rule(created.id)

    assert len(result.records) == 2
    assert result.metadata["item_count"] == "2"
    executions = service.list_executions()
    assert len(executions) == 1
    assert executions[0].rule_id == created.id


def test_service_respects_enable_flag(simple_rule: RuleSchema, fetcher) -> None:
    repository = RuleRepository()
    service = RuleService(repository, fetcher=fetcher)
    created = service.create_rule(simple_rule)
    service.set_enabled(created.id, False)

    with pytest.raises(RuleNotFoundError):
        service.run_rule(created.id)


def test_service_test_run(fetcher) -> None:
    service = RuleService(RuleRepository(), fetcher=fetcher)
    rule = RuleSchema(
        name="temp",
        entry="https://example.com/list-full",
        selectors=SelectorConfig(list="article", title="h2", url="h2 a"),
    )

    result = service.test_run(rule)
    assert len(result.records) == 3


def test_delete_rule_removes_persisted_results(simple_rule: RuleSchema, fetcher) -> None:
    repository = RuleRepository()
    results = ResultRepository()
    service = RuleService(repository, fetcher=fetcher, result_repository=results)
    created = service.create_rule(simple_rule)
    service.run_rule(created.id)

    assert service.list_executions(created.id)

    service.delete_rule(created.id)

    assert service.list_executions(created.id) == []
