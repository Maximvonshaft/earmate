from __future__ import annotations

from earmate.api import create_app
from earmate.monitoring import MonitoringRepository, MonitoringService
from earmate.rule_manager import RuleRepository, RuleService
from earmate.scheduler import InMemoryScheduler
from earmate.storage import ResultRepository
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

TEST_API_KEY = "test-key"


def build_client(*, with_api_key: bool = True) -> TestClient:
    def fake_fetcher(_url: str) -> str:  # pragma: no cover - simple stub
        return HTML_FIXTURE

    repository = RuleRepository()
    results = ResultRepository()
    monitoring = MonitoringService(MonitoringRepository())
    service = RuleService(
        repository,
        fetcher=fake_fetcher,
        result_repository=results,
        monitoring=monitoring,
    )
    scheduler = InMemoryScheduler()
    app = create_app(
        service=service,
        repository=repository,
        scheduler=scheduler,
        result_repository=results,
        monitoring=monitoring,
        api_keys={TEST_API_KEY},
    )
    client = TestClient(app)
    if with_api_key:
        client.headers.update({"X-API-Key": TEST_API_KEY})
    return client


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


def test_results_are_persisted_and_retrievable() -> None:
    client = build_client()
    rule_id = client.post("/rules", json=RULE_PAYLOAD).json()["id"]

    run_response = client.post(f"/rules/{rule_id}/run")
    assert run_response.status_code == 200

    list_response = client.get("/results")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["count"] == 1
    execution_id = payload["items"][0]["id"]
    assert payload["items"][0]["item_count"] == 1

    detail_response = client.get(f"/results/{execution_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["result"]["records"][0]["title"] == "Item A"

    export_response = client.get(f"/results/{execution_id}/export/csv")
    assert export_response.status_code == 200
    assert "Item A" in export_response.text

    filter_response = client.get(f"/rules/{rule_id}/results")
    assert filter_response.status_code == 200
    assert filter_response.json()["count"] == 1

    unsupported = client.get(f"/results/{execution_id}/export/xml")
    assert unsupported.status_code == 400


def test_deleting_rule_clears_results() -> None:
    client = build_client()
    rule_id = client.post("/rules", json=RULE_PAYLOAD).json()["id"]
    client.post(f"/rules/{rule_id}/run")

    delete_response = client.delete(f"/rules/{rule_id}")
    assert delete_response.status_code == 204

    list_response = client.get("/results")
    assert list_response.status_code == 200
    assert list_response.json()["count"] == 0


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


def test_monitoring_endpoints_expose_run_state() -> None:
    client = build_client()
    rule_id = client.post("/rules", json=RULE_PAYLOAD).json()["id"]

    run_response = client.post(f"/rules/{rule_id}/run")
    assert run_response.status_code == 200
    run_payload = run_response.json()
    metadata = run_payload["metadata"]
    run_id = metadata["run_id"]

    list_response = client.get("/monitoring/runs")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["count"] == 1
    assert list_payload["items"][0]["id"] == run_id

    detail_response = client.get(f"/monitoring/runs/{run_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["status"] == "succeeded"
    assert detail_payload["metrics"]["items"] == 1.0

    summary_response = client.get("/monitoring/summary")
    assert summary_response.status_code == 200


def test_recorder_session_endpoints() -> None:
    client = build_client()

    create_response = client.post("/recorder/sessions", json={"name": "Recorder Demo"})
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    event_payloads = [
        {"type": "navigate", "payload": {"url": "https://example.com/list"}},
        {"type": "capture_selector", "payload": {"role": "list", "selector": "li.item"}},
        {"type": "capture_selector", "payload": {"role": "title", "selector": "a.title"}},
        {"type": "set_metadata", "payload": {"key": "source", "value": "recorder"}},
    ]
    for payload in event_payloads:
        response = client.post(f"/recorder/sessions/{session_id}/events", json=payload)
        assert response.status_code == 200

    playback_response = client.get(f"/recorder/sessions/{session_id}/playback")
    assert playback_response.status_code == 200
    assert playback_response.json()["count"] == len(event_payloads)

    compile_response = client.post(f"/recorder/sessions/{session_id}/compile", json={})
    assert compile_response.status_code == 200
    payload = compile_response.json()
    assert payload["rule"]["entry"] == "https://example.com/list"
    assert payload["rule"]["selectors"]["list"] == "li.item"
    assert payload["session"]["metadata"]["source"] == "recorder"


def test_publish_session_creates_rule_and_runs_test() -> None:
    client = build_client()

    session_id = client.post("/recorder/sessions", json={"name": "Publish Demo"}).json()["id"]
    events = [
        {"type": "navigate", "payload": {"url": "https://example.com/list"}},
        {"type": "capture_selector", "payload": {"role": "list", "selector": "li.item"}},
        {"type": "capture_selector", "payload": {"role": "title", "selector": "a.title"}},
        {"type": "set_metadata", "payload": {"key": "source", "value": "recorder"}},
    ]
    for event in events:
        event_response = client.post(
            f"/recorder/sessions/{session_id}/events",
            json=event,
        )
        assert event_response.status_code == 200

    publish_response = client.post(
        f"/recorder/sessions/{session_id}/publish",
        json={
            "metadata": {"owner": "qa-team"},
            "overrides": {"metadata": {"category": "news"}},
        },
    )
    assert publish_response.status_code == 201
    payload = publish_response.json()
    assert payload["session"]["id"] == session_id
    rule_metadata = payload["rule"]["rule"]["metadata"]
    assert rule_metadata["recorder_session"] == session_id
    assert rule_metadata["owner"] == "qa-team"
    assert rule_metadata["category"] == "news"
    assert payload["test_run"]["records"][0]["title"] == "Item A"


def test_monitoring_dashboard_endpoint() -> None:
    client = build_client()
    rule_id = client.post("/rules", json=RULE_PAYLOAD).json()["id"]
    client.post(f"/rules/{rule_id}/run")

    dashboard_response = client.get("/monitoring/dashboard")
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["summary"]["total"] >= 1
    assert dashboard["daily"]


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


def test_requests_without_api_key_are_rejected() -> None:
    client = build_client(with_api_key=False)

    missing_header = client.post("/rules", json=RULE_PAYLOAD)
    assert missing_header.status_code == 401

    invalid_header = client.post(
        "/rules",
        json=RULE_PAYLOAD,
        headers={"X-API-Key": "wrong"},
    )
    assert invalid_header.status_code == 401
