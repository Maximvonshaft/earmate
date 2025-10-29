"""HTTP API for managing scraping rules and triggering executions."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Response, status

from .contracts import ContractValidationError, ExecutionResultContract, RuleContract
from .monitoring import MonitoringRepository, MonitoringService, TaskRunNotFoundError
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

    app = FastAPI(title="EarMate API", version="0.1.0")
    app.state.repository = svc.repository
    app.state.service = svc
    app.state.scheduler = sched
    app.state.results = results
    app.state.monitoring = monitoring_service
    app.state.monitoring_repository = monitoring_repo

    _sync_scheduler(app)

    @app.get("/contracts/rule")
    def rule_contract_schema() -> Dict[str, Any]:
        return {"json_schema": RuleContract.json_schema()}

    @app.get("/contracts/test-run")
    def execution_result_schema() -> Dict[str, Any]:
        return {"json_schema": ExecutionResultContract.json_schema()}

    @app.get("/rules")
    def list_rules() -> Dict[str, Any]:
        records = [
            _record_to_dict(record)
            for record in app.state.service.list_rules()
        ]
        return {"items": records, "count": len(records)}

    @app.post("/rules", status_code=status.HTTP_201_CREATED)
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

    @app.put("/rules/{rule_id}")
    def update_rule(rule_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        rule = _parse_rule(payload)
        try:
            record = app.state.service.update_rule(rule_id, rule)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        _sync_scheduler(app)
        return _record_to_dict(record)

    @app.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
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

    @app.post("/rules/{rule_id}/enable")
    def enable_rule(rule_id: str) -> Dict[str, Any]:
        try:
            record = app.state.service.set_enabled(rule_id, True)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        _sync_scheduler(app)
        return _record_to_dict(record)

    @app.post("/rules/{rule_id}/disable")
    def disable_rule(rule_id: str) -> Dict[str, Any]:
        try:
            record = app.state.service.set_enabled(rule_id, False)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        _sync_scheduler(app)
        return _record_to_dict(record)

    @app.post("/rules/{rule_id}/run")
    def run_rule(rule_id: str) -> Dict[str, Any]:
        try:
            result = app.state.service.run_rule(rule_id)
        except RuleNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return _execution_result_to_dict(result)

    @app.post("/rules/test-run")
    def test_run(payload: Dict[str, Any]) -> Dict[str, Any]:
        rule = _parse_rule(payload)
        result = app.state.service.test_run(rule)
        return _execution_result_to_dict(result)

    @app.post("/scheduler/trigger")
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
    def monitoring_summary() -> Dict[str, Any]:
        return app.state.monitoring.summary()

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
