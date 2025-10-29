from __future__ import annotations

from earmate.api import create_app
from earmate.rule_manager import RuleRepository, RuleService
from earmate.scheduler import InMemoryScheduler
from fastapi.testclient import TestClient

HTML_FIXTURE = """
<html>
  <body>
    <ul>
      <li class="item">
        <a class="title" href="https://example.com/a">Item A</a>
        <p class="summary">Summary A</p>
      </li>
    </ul>
  </body>
</html>
""".strip()


RULE_PAYLOAD = {
    "name": "Example",
    "entry": "https://example.com/list",
    "selectors": {
        "list": "li.item",
        "title": "a.title",
        "summary": "p.summary",
    },
}


def build_client() -> TestClient:
    def fake_fetcher(_url: str) -> str:  # pragma: no cover - simple stub
        return HTML_FIXTURE

    repository = RuleRepository()
    service = RuleService(repository, fetcher=fake_fetcher)
    scheduler = InMemoryScheduler()
    app = create_app(service=service, repository=repository, scheduler=scheduler)
    return TestClient(app)


def test_create_and_list_rules() -> None:
    client = build_client()

    response = client.post("/rules", json=RULE_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    rule_id = data["id"]
    assert data["rule"]["name"] == "Example"

    list_response = client.get("/rules")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["id"] == rule_id

    get_response = client.get(f"/rules/{rule_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == rule_id


def test_update_and_run_rule() -> None:
    client = build_client()
    create_response = client.post("/rules", json=RULE_PAYLOAD)
    rule_id = create_response.json()["id"]

    update_payload = dict(RULE_PAYLOAD)
    update_payload["metadata"] = {"source": "unit-test"}
    update_response = client.put(f"/rules/{rule_id}", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["rule"]["metadata"]["source"] == "unit-test"

    run_response = client.post(f"/rules/{rule_id}/run")
    assert run_response.status_code == 200
    run_data = run_response.json()
    assert run_data["records"][0]["title"] == "Item A"


def test_test_run_returns_execution_result() -> None:
    client = build_client()

    response = client.post("/rules/test-run", json=RULE_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["metadata"]["item_count"] == "1"


def test_scheduler_trigger_runs_due_rules() -> None:
    client = build_client()
    payload = dict(RULE_PAYLOAD)
    payload["schedule"] = {"mode": "immediate"}

    rule_id = client.post("/rules", json=payload).json()["id"]

    trigger_response = client.post("/scheduler/trigger")
    assert trigger_response.status_code == 200
    trigger_data = trigger_response.json()
    assert trigger_data["count"] == 1
    assert trigger_data["executions"][0]["rule_id"] == rule_id


def test_disable_rule_removes_from_scheduler() -> None:
    client = build_client()
    payload = dict(RULE_PAYLOAD)
    payload["schedule"] = {"mode": "immediate"}

    rule_id = client.post("/rules", json=payload).json()["id"]
    disable_response = client.post(f"/rules/{rule_id}/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["enabled"] is False

    trigger_response = client.post("/scheduler/trigger")
    assert trigger_response.status_code == 200
    assert trigger_response.json()["count"] == 0


def test_contract_schemas_are_exposed() -> None:
    client = build_client()

    rule_contract = client.get("/contracts/rule")
    assert rule_contract.status_code == 200
    rule_schema = rule_contract.json()["json_schema"]
    assert "entry" in rule_schema["properties"]
    assert rule_schema["properties"]["entry"]["format"] == "uri"

    execution_contract = client.get("/contracts/test-run")
    assert execution_contract.status_code == 200
    execution_schema = execution_contract.json()["json_schema"]
    assert "records" in execution_schema["properties"]


def test_create_rule_returns_validation_errors() -> None:
    client = build_client()
    payload = dict(RULE_PAYLOAD)
    payload.pop("selectors")

    response = client.post("/rules", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["selectors"]
