"""HTTP API for managing scraping rules and triggering executions."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status

from .contracts import (
    ContractValidationError,
    ExecutionResultContract,
    RecorderSessionContract,
    RuleContract,
)
from .dashboard import render_dashboard_page
from .monitoring import (
    MonitoringRepository,
    MonitoringService,
    TaskRunNotFoundError,
    TaskStatus,
)
from .recorder import (
    InvalidRecorderEvent,
    RecorderRepository,
    RecorderService,
    RecorderSessionNotFoundError,
    RecorderSessionValidationError,
)
from .rule_manager import RuleNotFoundError, RuleRepository, RuleService
from .scheduler import InMemoryScheduler
from .schema import RuleSchema
from .storage import ExecutionNotFoundError, ExecutionRecord, ResultRepository


def create_app(
    *,
    service: Optional[RuleService] = None,
    repository: Optional[RuleRepository] = None,
    scheduler: Optional[InMemoryScheduler] = None,
    result_repository: Optional[ResultRepository] = None,
    monitoring: Optional[MonitoringService] = None,
    recorder: Optional[RecorderService] = None,
    api_keys: Optional[Iterable[str]] = None,
) -> FastAPI:
    """Construct a FastAPI application with in-memory services by default."""

    monitoring_service = monitoring
    if monitoring_service is None:
        monitoring_repo = MonitoringRepository()
        monitoring_service = MonitoringService(monitoring_repo)
    else:
        monitoring_repo = monitoring_service.repository

    if service is None:
        repo = repository or RuleRepository()
        results = result_repository or ResultRepository()
        svc = RuleService(repo, result_repository=results, monitoring=monitoring_service)
    else:
        svc = service
        repo = repository or svc.repository
        if result_repository is not None:
            results = result_repository
            svc.result_repository = result_repository
        else:
            results = svc.result_repository or ResultRepository()
            if svc.result_repository is None:
                svc.result_repository = results
        if svc.monitoring is None:
            svc.monitoring = monitoring_service
        monitoring_repo = svc.monitoring.repository
        monitoring_service = svc.monitoring
    sched = scheduler or InMemoryScheduler()

    recorder_service = recorder or RecorderService(RecorderRepository())

    allowed_api_keys = _normalise_api_keys(api_keys)
    require_api_key = _build_api_key_dependency(allowed_api_keys)
    protected = [Depends(require_api_key)]

    app = FastAPI(title="EarMate API", version="0.1.0")
    app.state.repository = svc.repository
    app.state.service = svc
    app.state.scheduler = sched
    app.state.results = results
    app.state.monitoring = monitoring_service
    app.state.monitoring_repository = monitoring_repo
    app.state.recorder = recorder_service
    app.state.api_keys = allowed_api_keys

    _sync_scheduler(app)

    @app.get("/dashboard")
    def dashboard_page() -> str:
        return render_dashboard_page()

    @app.get("/contracts/rule")
    def rule_contract_schema() -> Dict[str, Any]:
        return {"json_schema": RuleContract.json_schema()}

    @app.get("/contracts/test-run")
    def execution_result_schema() -> Dict[str, Any]:
        return {"json_schema": ExecutionResultContract.json_schema()}

    @app.get("/contracts/recorder-session")
    def recorder_session_schema() -> Dict[str, Any]:
        return {
            "session": RecorderSessionContract.json_schema(),
            "event": RecorderSessionContract.event_schema(),
        }

    @app.get("/recorder/sessions")
    def list_sessions() -> Dict[str, Any]:
        sessions = [
            RecorderSessionContract(session=session).to_payload()
            for session in app.state.recorder.list_sessions()
        ]
        return {"items": sessions, "count": len(sessions)}

    @app.post("/recorder/sessions", status_code=status.HTTP_201_CREATED, dependencies=protected)
    def create_session(payload: Dict[str, Any]) -> Dict[str, Any]:
        name = payload.get("name")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="name must be non-empty string",
            )
        metadata = _parse_metadata(payload.get("metadata"))
        session = app.state.recorder.create_session(
            name=name.strip() if isinstance(name, str) else None,
            metadata=metadata,
        )
        return RecorderSessionContract(session=session).to_payload()

    @app.get("/recorder/sessions/{session_id}")
    def get_session(session_id: str) -> Dict[str, Any]:
        try:
            session = app.state.recorder.get_session(session_id)
        except RecorderSessionNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return RecorderSessionContract(session=session).to_payload()

    @app.post(
        "/recorder/sessions/{session_id}/events",
        dependencies=protected,
    )
    def append_event(session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            session = app.state.recorder.record_event(session_id, payload)
        except RecorderSessionNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except InvalidRecorderEvent as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        return RecorderSessionContract(session=session).to_payload()

    @app.get("/recorder/sessions/{session_id}/playback")
    def playback(session_id: str) -> Dict[str, Any]:
        try:
            steps = app.state.recorder.playback(session_id)
        except RecorderSessionNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return {"events": steps, "count": len(steps)}

    @app.post(
        "/recorder/sessions/{session_id}/compile",
        dependencies=protected,
    )
    def compile_session(
        session_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = payload or {}
        name = payload.get("name")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="name must be non-empty string",
            )
        try:
            rule = app.state.recorder.compile_session(
                session_id,
                name=name.strip() if isinstance(name, str) else None,
            )
            session = app.state.recorder.get_session(session_id)
        except RecorderSessionNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except RecorderSessionValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        return {
            "session": RecorderSessionContract(session=session).to_payload(),
            "rule": RuleContract(rule=rule).to_payload(),
        }

    @app.post(
        "/recorder/sessions/{session_id}/publish",
        status_code=status.HTTP_201_CREATED,
        dependencies=protected,
    )
    def publish_session(
        session_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = payload or {}
        name = payload.get("name")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="name must be non-empty string",
            )
        enable_value = payload.get("enable")
        if enable_value is not None and not isinstance(enable_value, bool):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="enable must be a boolean",
            )
        test_run_value = payload.get("test_run", True)
        if not isinstance(test_run_value, bool):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="test_run must be a boolean",
            )
        overrides = payload.get("overrides")
        if overrides is not None and not isinstance(overrides, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="overrides must be an object",
            )

        metadata_override = _parse_metadata(payload.get("metadata"))

        try:
            rule = app.state.recorder.compile_session(
                session_id,
                name=name.strip() if isinstance(name, str) else None,
            )
            session = app.state.recorder.get_session(session_id)
        except RecorderSessionNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except RecorderSessionValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        if overrides:
            base_payload = RuleContract(rule=rule).to_payload()
            merged = _deep_merge_dict(base_payload, overrides)
            rule = _parse_rule(merged)

        if metadata_override:
            rule.metadata.update(metadata_override)

        rule.metadata["recorder_session"] = session.id
        rule.metadata["recorder_events"] = str(session.event_count)

        record = app.state.service.create_rule(rule)
        if enable_value is False:
            record = app.state.service.set_enabled(record.id, False)

        _sync_scheduler(app)

        response: Dict[str, Any] = {
            "session": RecorderSessionContract(session=session).to_payload(),
            "rule": _record_to_dict(record),
        }

        if test_run_value:
            try:
                result = app.state.service.preview_rule(record.id)
            except Exception as exc:  # pragma: no cover - depends on engine runtime
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"test run failed: {exc}",
                ) from exc
            response["test_run"] = _execution_result_to_dict(result)

        return response

    @app.get("/rules")
    def list_rules() -> Dict[str, Any]:
        records = [
            _record_to_dict(record)
            for record in app.state.service.list_rules()
        ]
        return {"items": records, "count": len(records)}

    @app.post("/rules", status_code=status.HTTP_201_CREATED, dependencies=protected)
    def create_rule(payload: Dict[str, Any]) -> Dict[str, Any]:
        rule = _parse_rule(payload)
        record = app.state.service.create_rule(rule)
        _sync_scheduler(app)
        return _record_to_dict(record)

    @app.get("/rules/{rule_id}")
    def get_rule(rule_id: str) -> Dict[str, Any]:
        try:
            record = app.state.service.get_rule(rule_id)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return _record_to_dict(record)

    @app.put("/rules/{rule_id}", dependencies=protected)
    def update_rule(rule_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        rule = _parse_rule(payload)
        try:
            record = app.state.service.update_rule(rule_id, rule)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        _sync_scheduler(app)
        return _record_to_dict(record)

    @app.delete(
        "/rules/{rule_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=protected,
    )
    def delete_rule(rule_id: str) -> Response:
        try:
            app.state.service.delete_rule(rule_id)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        _sync_scheduler(app)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/results")
    def list_results(rule_id: Optional[str] = None) -> Dict[str, Any]:
        records = app.state.service.list_executions(rule_id)
        summaries = [_execution_summary(record) for record in records]
        return {"items": summaries, "count": len(summaries)}

    @app.get("/rules/{rule_id}/results")
    def list_results_for_rule(rule_id: str) -> Dict[str, Any]:
        records = app.state.service.list_executions(rule_id)
        summaries = [_execution_summary(record) for record in records]
        return {"items": summaries, "count": len(summaries)}

    @app.get("/results/{execution_id}")
    def get_result(execution_id: str) -> Dict[str, Any]:
        try:
            record = app.state.service.get_execution(execution_id)
        except ExecutionNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return _execution_detail(record)

    @app.get("/results/{execution_id}/export/{format}")
    def export_result(execution_id: str, format: str) -> Response:
        try:
            record = app.state.service.get_execution(execution_id)
        except ExecutionNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

        if format == "json":
            return _execution_result_to_dict(record.result)

        if format == "csv":
            csv_content = _records_to_csv(record.result.records)
            return Response(content=csv_content)

        raise HTTPException(status_code=400, detail="unsupported format")

    @app.post("/rules/{rule_id}/enable", dependencies=protected)
    def enable_rule(rule_id: str) -> Dict[str, Any]:
        try:
            record = app.state.service.set_enabled(rule_id, True)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        _sync_scheduler(app)
        return _record_to_dict(record)

    @app.post("/rules/{rule_id}/disable", dependencies=protected)
    def disable_rule(rule_id: str) -> Dict[str, Any]:
        try:
            record = app.state.service.set_enabled(rule_id, False)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        _sync_scheduler(app)
        return _record_to_dict(record)

    @app.post("/rules/{rule_id}/run", dependencies=protected)
    def run_rule(rule_id: str) -> Dict[str, Any]:
        try:
            result = app.state.service.run_rule(rule_id)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return _execution_result_to_dict(result)

    @app.post("/rules/test-run", dependencies=protected)
    def test_run(payload: Dict[str, Any]) -> Dict[str, Any]:
        rule = _parse_rule(payload)
        monitoring: Optional[MonitoringService] = getattr(app.state, "monitoring", None)
        run = None
        if monitoring is not None:
            preview_rule_id = _preview_rule_id(rule)
            run = monitoring.create_run(preview_rule_id)
            monitoring.append_log(run.id, "info", "试跑任务已入队")
            monitoring.mark_running(run.id)
            monitoring.append_log(run.id, "info", "试跑开始执行")
        try:
            result = app.state.service.test_run(rule)
        except Exception as exc:  # pragma: no cover - depends on engine runtime
            if run is not None:
                monitoring.append_log(run.id, "error", str(exc))
                monitoring.mark_failure(run.id, str(exc))
            raise

        if run is not None:
            metrics = {
                "items": float(len(result.records)),
                "detail_items": float(len(result.detail_records)),
            }
            monitoring.append_log(run.id, "info", "试跑完成")
            monitoring.mark_success(run.id, metrics)
            result.metadata.setdefault("run_id", run.id)
            result.metadata.setdefault("rule_id", run.rule_id)
            result.metadata.setdefault("status", TaskStatus.SUCCEEDED.value)
        return _execution_result_to_dict(result)

    @app.post("/scheduler/trigger", dependencies=protected)
    def trigger_scheduler() -> Dict[str, Any]:
        due = app.state.scheduler.pop_due()
        executions = []
        for entry in due:
            try:
                result = app.state.service.run_rule(entry.rule_id)
            except RuleNotFoundError:
                continue
            executions.append({
                "rule_id": entry.rule_id,
                "next_run": _isoformat(entry.next_run),
                "result": _execution_result_to_dict(result),
            })
        return {"executions": executions, "count": len(executions)}

    @app.get("/monitoring/runs")
    def list_runs(rule_id: Optional[str] = None) -> Dict[str, Any]:
        runs = list(app.state.monitoring.list_runs(rule_id))
        payload = [_run_to_dict(run) for run in runs]
        return {"items": payload, "count": len(payload)}

    @app.get("/monitoring/runs/{run_id}")
    def get_run(run_id: str) -> Dict[str, Any]:
        try:
            run = app.state.monitoring.get(run_id)
        except TaskRunNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return _run_to_dict(run)

    @app.get("/monitoring/summary")
    def monitoring_summary(rule_id: Optional[str] = None) -> Dict[str, Any]:
        return app.state.monitoring.summary(rule_id)

    @app.get("/monitoring/dashboard")
    def monitoring_dashboard(rule_id: Optional[str] = None) -> Dict[str, Any]:
        return app.state.monitoring.dashboard(rule_id)

    return app


def _sync_scheduler(app: FastAPI) -> None:
    records = app.state.service.list_rules()
    scheduler: InMemoryScheduler = app.state.scheduler
    scheduler.rebuild([])
    for record in records:
        if record.enabled and record.rule.schedule:
            scheduler.add_rule(record.id, record.rule)


def _record_to_dict(record: Any) -> Dict[str, Any]:
    contract = RuleContract(rule=record.rule)
    data = {
        "id": record.id,
        "enabled": record.enabled,
        "created_at": _isoformat(record.created_at),
        "updated_at": _isoformat(record.updated_at),
        "rule": contract.to_payload(),
    }
    return data


def _run_to_dict(run: Any) -> Dict[str, Any]:
    return {
        "id": run.id,
        "rule_id": run.rule_id,
        "status": run.status.value if hasattr(run.status, "value") else run.status,
        "created_at": _isoformat(run.created_at),
        "updated_at": _isoformat(run.updated_at),
        "started_at": _isoformat(run.started_at) if run.started_at else None,
        "finished_at": _isoformat(run.finished_at) if run.finished_at else None,
        "duration_ms": run.duration_ms,
        "metrics": run.metrics,
        "error_message": run.error_message,
        "execution_id": run.execution_id,
        "logs": [
            {
                "timestamp": _isoformat(entry.timestamp),
                "level": entry.level,
                "message": entry.message,
            }
            for entry in run.logs
        ],
    }


def _execution_result_to_dict(result: Any) -> Dict[str, Any]:
    contract = ExecutionResultContract.from_execution_result(result)
    return contract.to_payload()


def _execution_summary(record: ExecutionRecord) -> Dict[str, Any]:
    return {
        "id": record.id,
        "rule_id": record.rule_id,
        "created_at": _isoformat(record.created_at),
        "item_count": record.item_count,
        "detail_count": record.detail_count,
        "metadata": record.result.metadata,
    }


def _execution_detail(record: ExecutionRecord) -> Dict[str, Any]:
    payload = _execution_summary(record)
    payload["result"] = _execution_result_to_dict(record.result)
    return payload


def _preview_rule_id(rule: RuleSchema) -> str:
    metadata = getattr(rule, "metadata", {}) or {}
    session_id = metadata.get("recorder_session") if isinstance(metadata, dict) else None
    if isinstance(session_id, str) and session_id:
        return f"preview:{session_id}"
    name = getattr(rule, "name", None)
    if isinstance(name, str) and name:
        return f"preview:{name}"
    return "preview:adhoc"


def _records_to_csv(records: List[Dict[str, str]]) -> str:
    if not records:
        return ""

    fieldnames = sorted({key for record in records for key in record.keys()})
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
        row = {field: record.get(field, "") for field in fieldnames}
        writer.writerow(row)
    return buffer.getvalue()


def _parse_metadata(value: Any) -> Dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="metadata must be an object with string values",
        )
    metadata: Dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="metadata keys must be non-empty strings",
            )
        if not isinstance(item, str):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="metadata values must be strings",
            )
        metadata[key] = item
    return metadata


def _parse_rule(payload: Dict[str, Any]) -> RuleSchema:
    try:
        contract = RuleContract.from_payload(payload)
    except ContractValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors,
        ) from exc
    return contract.to_rule_schema()


def _isoformat(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _normalise_api_keys(keys: Optional[Iterable[str]]) -> Set[str]:
    if keys is None:
        keys = {"dev-secret"}
    normalised = {item for item in keys if isinstance(item, str) and item}
    if not normalised:
        raise ValueError("api_keys must contain at least one non-empty string")
    return normalised


def _build_api_key_dependency(keys: Set[str], header_name: str = "X-API-Key"):
    def dependency(api_key: Optional[str] = Header(None, alias=header_name)) -> str:
        if not api_key or api_key not in keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid api key",
            )
        return api_key

    return dependency


def _deep_merge_dict(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dict(existing, value)
        else:
            merged[key] = value
    return merged
