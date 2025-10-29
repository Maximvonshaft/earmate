"""Shared API contracts for front-end recorder integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .engine import ExecutionResult
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


class ContractValidationError(ValueError):
    """Raised when incoming payload violates the recorder contract."""

    def __init__(self, errors: List[Dict[str, Any]]) -> None:
        super().__init__("contract validation failed")
        self.errors = errors


def _error(loc: List[Any], msg: str, err_type: str) -> Dict[str, Any]:
    return {"loc": loc, "msg": msg, "type": err_type}


def _ensure_str(
    source: Dict[str, Any],
    key: str,
    loc: List[Any],
    errors: List[Dict[str, Any]],
    *,
    required: bool = False,
    allow_empty: bool = False,
) -> Optional[str]:
    value = source.get(key)
    if value is None:
        if required:
            errors.append(_error(loc, "field is required", "value_error.missing"))
        return None
    if not isinstance(value, str):
        errors.append(_error(loc, "must be a string", "type_error.str"))
        return None
    if not allow_empty and not value.strip():
        errors.append(_error(loc, "must not be empty", "value_error.empty"))
        return None
    return value


def _ensure_bool(
    source: Dict[str, Any],
    key: str,
    loc: List[Any],
    errors: List[Dict[str, Any]],
    *,
    default: bool = False,
) -> bool:
    value = source.get(key)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    errors.append(_error(loc, "must be a boolean", "type_error.bool"))
    return default


def _ensure_int(
    source: Dict[str, Any],
    key: str,
    loc: List[Any],
    errors: List[Dict[str, Any]],
    *,
    min_value: Optional[int] = None,
) -> Optional[int]:
    value = source.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        errors.append(_error(loc, "must be an integer", "type_error.int"))
        return None
    if min_value is not None and value < min_value:
        errors.append(_error(loc, f"must be >= {min_value}", "value_error"))
        return None
    return value


def _validate_metadata(value: Any, errors: List[Dict[str, Any]]) -> Dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        errors.append(_error(["metadata"], "must be an object", "type_error.dict"))
        return {}
    converted: Dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            errors.append(
                _error(["metadata"], "keys and values must be strings", "type_error.str")
            )
            return {}
        converted[key] = item
    return converted


def _validate_selectors(value: Any, errors: List[Dict[str, Any]]) -> Optional[SelectorConfig]:
    if not isinstance(value, dict):
        errors.append(_error(["selectors"], "must be an object", "type_error.dict"))
        return None
    data: Dict[str, Optional[str]] = {}
    list_selector = _ensure_str(value, "list", ["selectors", "list"], errors, required=True)
    if list_selector is not None:
        data["list"] = list_selector
    for key in ["title", "url", "summary", "time"]:
        optional_value = value.get(key)
        if optional_value is None:
            data[key] = None
            continue
        if isinstance(optional_value, str):
            data[key] = optional_value
        else:
            errors.append(_error(["selectors", key], "must be a string", "type_error.str"))
    if errors:
        return None
    try:
        return SelectorConfig(**data)  # type: ignore[arg-type]
    except SchemaValidationError as exc:
        errors.append(_error(["selectors"], str(exc), "value_error"))
        return None


def _validate_pagination(value: Any, errors: List[Dict[str, Any]]) -> Optional[PaginationConfig]:
    if value is None:
        return None
    if not isinstance(value, dict):
        errors.append(_error(["pagination"], "must be an object", "type_error.dict"))
        return None
    pagination_type = _ensure_str(value, "type", ["pagination", "type"], errors, required=True)
    selector_value = value.get("selector")
    if selector_value is not None and not isinstance(selector_value, str):
        errors.append(_error(["pagination", "selector"], "must be a string", "type_error.str"))
        selector_value = None
    max_pages = _ensure_int(value, "max_pages", ["pagination", "max_pages"], errors, min_value=1)
    data: Dict[str, Any] = {}
    if pagination_type is not None:
        data["type"] = pagination_type
    if selector_value is not None:
        data["selector"] = selector_value
    if max_pages is not None:
        data["max_pages"] = max_pages
    try:
        return PaginationConfig(**data)  # type: ignore[arg-type]
    except SchemaValidationError as exc:
        errors.append(_error(["pagination"], str(exc), "value_error"))
        return None


def _validate_detail(value: Any, errors: List[Dict[str, Any]]) -> Optional[DetailRule]:
    if value is None:
        return None
    if not isinstance(value, dict):
        errors.append(_error(["detail"], "must be an object", "type_error.dict"))
        return None
    enabled = _ensure_bool(value, "enabled", ["detail", "enabled"], errors, default=False)
    selector = _ensure_str(value, "selector", ["detail", "selector"], errors, required=enabled)
    fields_value = value.get("fields") or []
    if not isinstance(fields_value, list):
        errors.append(_error(["detail", "fields"], "must be a list", "type_error.list"))
        fields_value = []
    fields: List[DetailField] = []
    for idx, item in enumerate(fields_value):
        if not isinstance(item, dict):
            errors.append(
                _error(["detail", "fields", idx], "must be an object", "type_error.dict")
            )
            continue
        field_name = _ensure_str(
            item,
            "name",
            ["detail", "fields", idx, "name"],
            errors,
            required=True,
        )
        field_selector = _ensure_str(
            item,
            "selector",
            ["detail", "fields", idx, "selector"],
            errors,
            required=True,
        )
        if field_name is None or field_selector is None:
            continue
        try:
            fields.append(DetailField(name=field_name, selector=field_selector))
        except SchemaValidationError as exc:
            errors.append(_error(["detail", "fields", idx], str(exc), "value_error"))
    if errors:
        return None
    try:
        return DetailRule(enabled=enabled, selector=selector, fields=fields)
    except SchemaValidationError as exc:
        errors.append(_error(["detail"], str(exc), "value_error"))
        return None


def _validate_actions(value: Any, errors: List[Dict[str, Any]]) -> List[Action]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(_error(["actions"], "must be a list", "type_error.list"))
        return []
    actions: List[Action] = []
    for idx, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(_error(["actions", idx], "must be an object", "type_error.dict"))
            continue
        action_type = _ensure_str(item, "type", ["actions", idx, "type"], errors, required=True)
        selector_value = item.get("selector")
        if selector_value is not None and not isinstance(selector_value, str):
            errors.append(
                _error(["actions", idx, "selector"], "must be a string", "type_error.str")
            )
            selector_value = None
        event_value = item.get("event")
        if event_value is not None and not isinstance(event_value, str):
            errors.append(
                _error(["actions", idx, "event"], "must be a string", "type_error.str")
            )
            event_value = None
        fields_value = item.get("fields") or []
        if not isinstance(fields_value, list) or not all(
            isinstance(field, str) for field in fields_value
        ):
            errors.append(
                _error(["actions", idx, "fields"], "must be a list of strings", "type_error.list")
            )
            fields_value = []
        if action_type is None:
            continue
        try:
            actions.append(
                Action(
                    type=action_type,
                    selector=selector_value,
                    event=event_value,
                    fields=list(fields_value),
                )
            )
        except SchemaValidationError as exc:
            errors.append(_error(["actions", idx], str(exc), "value_error"))
    return actions


def _validate_schedule(value: Any, errors: List[Dict[str, Any]]) -> Optional[ScheduleConfig]:
    if value is None:
        return None
    if not isinstance(value, dict):
        errors.append(_error(["schedule"], "must be an object", "type_error.dict"))
        return None
    mode = _ensure_str(value, "mode", ["schedule", "mode"], errors, required=True)
    expr = value.get("expr")
    if expr is not None and not isinstance(expr, str):
        errors.append(_error(["schedule", "expr"], "must be a string", "type_error.str"))
        expr = None
    timezone = value.get("timezone")
    if timezone is not None and not isinstance(timezone, str):
        errors.append(
            _error(["schedule", "timezone"], "must be a string", "type_error.str")
        )
        timezone = None
    data: Dict[str, Any] = {}
    if mode is not None:
        data["mode"] = mode
    if expr is not None:
        data["expr"] = expr
    if timezone is not None:
        data["timezone"] = timezone
    try:
        return ScheduleConfig(**data)  # type: ignore[arg-type]
    except SchemaValidationError as exc:
        errors.append(_error(["schedule"], str(exc), "value_error"))
        return None


def _validate_dedupe(value: Any, errors: List[Dict[str, Any]]) -> Optional[DeduplicationConfig]:
    if value is None:
        return None
    if not isinstance(value, dict):
        errors.append(_error(["dedupe"], "must be an object", "type_error.dict"))
        return None
    dedupe_type = _ensure_str(value, "type", ["dedupe", "type"], errors, required=True)
    threshold = _ensure_int(value, "threshold", ["dedupe", "threshold"], errors, min_value=0)
    data: Dict[str, Any] = {}
    if dedupe_type is not None:
        data["type"] = dedupe_type
    if threshold is not None:
        data["threshold"] = threshold
    try:
        return DeduplicationConfig(**data)  # type: ignore[arg-type]
    except SchemaValidationError as exc:
        errors.append(_error(["dedupe"], str(exc), "value_error"))
        return None


def _validate_output(value: Any, errors: List[Dict[str, Any]]) -> Optional[OutputConfig]:
    if value is None:
        return None
    if not isinstance(value, dict):
        errors.append(_error(["output"], "must be an object", "type_error.dict"))
        return None
    target = _ensure_str(value, "target", ["output", "target"], errors, required=True)
    table = value.get("table")
    if table is not None and not isinstance(table, str):
        errors.append(_error(["output", "table"], "must be a string", "type_error.str"))
        table = None
    data: Dict[str, Any] = {}
    if target is not None:
        data["target"] = target
    if table is not None:
        data["table"] = table
    try:
        return OutputConfig(**data)  # type: ignore[arg-type]
    except SchemaValidationError as exc:
        errors.append(_error(["output"], str(exc), "value_error"))
        return None


def _validate_entry(entry: Optional[str], errors: List[Dict[str, Any]]) -> Optional[str]:
    if entry is None:
        return None
    parsed = urlparse(entry)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors.append(_error(["entry"], "must be a valid HTTP/HTTPS URL", "value_error.url"))
        return None
    return entry


def parse_rule_contract(payload: Dict[str, Any]) -> RuleSchema:
    errors: List[Dict[str, Any]] = []
    if not isinstance(payload, dict):
        raise ContractValidationError([
            _error([], "payload must be an object", "type_error.dict")
        ])

    name = _ensure_str(payload, "name", ["name"], errors, required=True)
    entry = _ensure_str(payload, "entry", ["entry"], errors, required=True)
    entry = _validate_entry(entry, errors)

    selectors = _validate_selectors(payload.get("selectors"), errors)
    pagination = _validate_pagination(payload.get("pagination"), errors)
    detail = _validate_detail(payload.get("detail"), errors)
    actions = _validate_actions(payload.get("actions"), errors)
    schedule = _validate_schedule(payload.get("schedule"), errors)
    dedupe = _validate_dedupe(payload.get("dedupe"), errors)
    output = _validate_output(payload.get("output"), errors)
    metadata = _validate_metadata(payload.get("metadata"), errors)

    if errors:
        raise ContractValidationError(errors)

    if name is None or entry is None or selectors is None:
        raise ContractValidationError([
            _error([], "required fields missing", "value_error")
        ])

    try:
        return RuleSchema(
            name=name,
            entry=entry,
            selectors=selectors,
            pagination=pagination,
            detail=detail,
            actions=actions,
            schedule=schedule,
            dedupe=dedupe,
            output=output,
            metadata=metadata,
        )
    except SchemaValidationError as exc:
        raise ContractValidationError([
            _error([], str(exc), "value_error")
        ]) from exc


def rule_to_contract(rule: RuleSchema) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "name": rule.name,
        "entry": rule.entry,
        "selectors": {
            "list": rule.selectors.list,
            "title": rule.selectors.title,
            "url": rule.selectors.url,
            "summary": rule.selectors.summary,
            "time": rule.selectors.time,
        },
        "actions": [
            {
                "type": action.type,
                "selector": action.selector,
                "event": action.event,
                "fields": list(action.fields),
            }
            for action in rule.actions
        ],
        "metadata": dict(rule.metadata),
    }
    if rule.pagination is not None:
        payload["pagination"] = {
            "type": rule.pagination.type,
            "selector": rule.pagination.selector,
            "max_pages": rule.pagination.max_pages,
        }
    if rule.detail is not None:
        payload["detail"] = {
            "enabled": rule.detail.enabled,
            "selector": rule.detail.selector,
            "fields": [
                {"name": field.name, "selector": field.selector}
                for field in rule.detail.fields
            ],
        }
    if rule.schedule is not None:
        payload["schedule"] = {
            "mode": rule.schedule.mode,
            "expr": rule.schedule.expr,
            "timezone": rule.schedule.timezone,
        }
    if rule.dedupe is not None:
        payload["dedupe"] = {
            "type": rule.dedupe.type,
            "threshold": rule.dedupe.threshold,
        }
    if rule.output is not None:
        payload["output"] = {
            "target": rule.output.target,
            "table": rule.output.table,
        }
    return payload


def execution_result_to_contract(result: ExecutionResult) -> Dict[str, Any]:
    return {
        "records": [dict(item) for item in result.records],
        "detail_records": [dict(item) for item in result.detail_records],
        "metadata": dict(result.metadata),
    }


RULE_CONTRACT_SCHEMA: Dict[str, Any] = {
    "title": "RuleContract",
    "type": "object",
    "required": ["name", "entry", "selectors"],
    "properties": {
        "name": {"type": "string", "description": "Human friendly rule name."},
        "entry": {
            "type": "string",
            "format": "uri",
            "description": "Entry URL captured during recording.",
        },
        "selectors": {
            "type": "object",
            "required": ["list"],
            "properties": {
                "list": {"type": "string"},
                "title": {"type": "string"},
                "url": {"type": "string"},
                "summary": {"type": "string"},
                "time": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "pagination": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["click", "url", "scroll"]},
                "selector": {"type": "string"},
                "max_pages": {"type": "integer", "minimum": 1},
            },
            "required": ["type"],
            "additionalProperties": False,
        },
        "detail": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "selector": {"type": "string"},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "selector"],
                        "properties": {
                            "name": {"type": "string"},
                            "selector": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                },
            },
            "additionalProperties": False,
        },
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {"type": "string"},
                    "selector": {"type": "string"},
                    "event": {"type": "string"},
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "additionalProperties": False,
            },
        },
        "schedule": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["cron", "immediate"]},
                "expr": {"type": "string"},
                "timezone": {"type": "string"},
            },
            "required": ["mode"],
            "additionalProperties": False,
        },
        "dedupe": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["simhash", "url", "none"]},
                "threshold": {"type": "integer", "minimum": 0},
            },
            "required": ["type"],
            "additionalProperties": False,
        },
        "output": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "table": {"type": "string"},
            },
            "required": ["target"],
            "additionalProperties": False,
        },
        "metadata": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


EXECUTION_RESULT_SCHEMA: Dict[str, Any] = {
    "title": "ExecutionResultContract",
    "type": "object",
    "properties": {
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
        },
        "detail_records": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
        },
        "metadata": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
    },
    "required": ["records", "detail_records", "metadata"],
    "additionalProperties": False,
}


@dataclass
class RuleContract:
    """Wrapper around :class:`RuleSchema` with serialization helpers."""

    rule: RuleSchema

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuleContract":
        rule = parse_rule_contract(payload)
        return cls(rule=rule)

    def to_rule_schema(self) -> RuleSchema:
        return self.rule

    def to_payload(self) -> Dict[str, Any]:
        return rule_to_contract(self.rule)

    @staticmethod
    def json_schema() -> Dict[str, Any]:
        return RULE_CONTRACT_SCHEMA


@dataclass
class ExecutionResultContract:
    """Wrapper around :class:`ExecutionResult` providing serialization helpers."""

    result: ExecutionResult

    @classmethod
    def from_execution_result(cls, result: ExecutionResult) -> "ExecutionResultContract":
        return cls(result=result)

    def to_payload(self) -> Dict[str, Any]:
        return execution_result_to_contract(self.result)

    @staticmethod
    def json_schema() -> Dict[str, Any]:
        return EXECUTION_RESULT_SCHEMA
