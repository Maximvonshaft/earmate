"""HTTP API for managing scraping rules and triggering executions."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Response, status

from .rule_manager import RuleNotFoundError, RuleRepository, RuleService
from .scheduler import InMemoryScheduler
from .schema import (
    Action,
    DeduplicationConfig,
    DetailField,
    DetailRule,
    OutputConfig,
    PaginationConfig,
    RuleSchema,
    ScheduleConfig,
    SchemaValidationError,
    SelectorConfig,
)


def create_app(
    *,
    service: Optional[RuleService] = None,
    repository: Optional[RuleRepository] = None,
    scheduler: Optional[InMemoryScheduler] = None,
) -> FastAPI:
    """Construct a FastAPI application with in-memory services by default."""

    repo = repository or RuleRepository()
    svc = service or RuleService(repo)
    sched = scheduler or InMemoryScheduler()

    app = FastAPI(title="EarMate API", version="0.1.0")
    app.state.repository = svc.repository
    app.state.service = svc
    app.state.scheduler = sched

    _sync_scheduler(app)

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

    return app


def _sync_scheduler(app: FastAPI) -> None:
    records = app.state.service.list_rules()
    scheduler: InMemoryScheduler = app.state.scheduler
    scheduler.rebuild([])
    for record in records:
        if record.enabled and record.rule.schedule:
            scheduler.add_rule(record.id, record.rule)


def _record_to_dict(record: Any) -> Dict[str, Any]:
    data = {
        "id": record.id,
        "enabled": record.enabled,
        "created_at": _isoformat(record.created_at),
        "updated_at": _isoformat(record.updated_at),
        "rule": _rule_to_dict(record.rule),
    }
    return data


def _rule_to_dict(rule: RuleSchema) -> Dict[str, Any]:
    return asdict(rule)


def _execution_result_to_dict(result: Any) -> Dict[str, Any]:
    return {
        "records": result.records,
        "detail_records": result.detail_records,
        "metadata": result.metadata,
    }


def _parse_rule(payload: Dict[str, Any]) -> RuleSchema:
    try:
        selectors = SelectorConfig(**payload["selectors"])
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="selectors field is required",
        ) from exc
    pagination = _maybe_construct(PaginationConfig, payload.get("pagination"))
    detail_payload = payload.get("detail")
    detail = None
    if detail_payload:
        fields_payload = detail_payload.get("fields", [])
        try:
            fields = [DetailField(**item) for item in fields_payload]
        except (TypeError, SchemaValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        try:
            detail = DetailRule(
                enabled=detail_payload.get("enabled", False),
                selector=detail_payload.get("selector"),
                fields=fields,
            )
        except SchemaValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
    actions_payload = payload.get("actions", [])
    try:
        actions = [Action(**item) for item in actions_payload]
    except (TypeError, SchemaValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    schedule = _maybe_construct(ScheduleConfig, payload.get("schedule"))
    dedupe = _maybe_construct(DeduplicationConfig, payload.get("dedupe"))
    output = _maybe_construct(OutputConfig, payload.get("output"))
    try:
        return RuleSchema(
            name=payload["name"],
            entry=payload["entry"],
            selectors=selectors,
            pagination=pagination,
            detail=detail,
            actions=actions,
            schedule=schedule,
            dedupe=dedupe,
            output=output,
            metadata=payload.get("metadata", {}),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"missing field: {exc.args[0]}",
        ) from exc
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except TypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _maybe_construct(cls, payload: Optional[Dict[str, Any]]):
    if not payload:
        return None
    try:
        return cls(**payload)
    except (SchemaValidationError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _isoformat(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
