from __future__ import annotations

from earmate.contracts import ExecutionResultContract, RuleContract
from earmate.engine import ExecutionResult


def build_contract_payload() -> dict:
    return {
        "name": "Recorder Sample",
        "entry": "https://example.com/list",
        "selectors": {
            "list": "li.item",
            "title": "a.title",
            "summary": "p.summary",
        },
        "pagination": {"type": "url", "selector": "https://example.com?page={page}"},
        "detail": {
            "enabled": True,
            "selector": "a.title",
            "fields": [
                {"name": "body", "selector": "div.article"},
            ],
        },
        "actions": [{"type": "click", "selector": "button.accept"}],
        "schedule": {"mode": "immediate"},
        "dedupe": {"type": "url"},
        "output": {"target": "memory"},
        "metadata": {"source": "recorder"},
    }


def test_rule_contract_roundtrip() -> None:
    payload = build_contract_payload()
    contract = RuleContract.from_payload(payload)
    schema = contract.to_rule_schema()

    assert schema.name == payload["name"]
    assert schema.selectors.list == payload["selectors"]["list"]

    regenerated = RuleContract(rule=schema)
    regenerated_payload = regenerated.to_payload()
    selectors_payload = regenerated_payload["selectors"]
    for key, value in payload["selectors"].items():
        assert selectors_payload[key] == value
    assert regenerated_payload["metadata"] == payload["metadata"]
    assert regenerated_payload["detail"]["fields"] == payload["detail"]["fields"]
    assert regenerated_payload["pagination"]["type"] == payload["pagination"]["type"]


def test_execution_result_contract_conversion() -> None:
    result = ExecutionResult(
        records=[{"title": "Item", "url": "https://example.com/a"}],
        detail_records=[{"body": "Content"}],
        metadata={"item_count": "1"},
    )

    contract = ExecutionResultContract.from_execution_result(result)

    assert contract.result == result
    payload = contract.to_payload()
    assert payload["records"] == result.records
    assert payload["detail_records"] == result.detail_records
    assert payload["metadata"] == result.metadata
