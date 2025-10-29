"""Recording session primitives bridging front-end recorder and rule schemas."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

from .schema import (
    Action,
    DetailField,
    DetailRule,
    PaginationConfig,
    RuleSchema,
    SchemaValidationError,
    SelectorConfig,
)


class RecorderSessionError(Exception):
    """Base error for recorder related operations."""


class RecorderSessionNotFoundError(KeyError, RecorderSessionError):
    """Raised when a session identifier cannot be resolved."""


class InvalidRecorderEvent(ValueError, RecorderSessionError):
    """Raised when an incoming event payload is invalid."""


class RecorderSessionValidationError(ValueError, RecorderSessionError):
    """Raised when attempting to compile an incomplete session."""


@dataclass(frozen=True)
class RecorderEvent:
    """Immutable event captured by the recorder."""

    type: str
    payload: Dict[str, Any]
    timestamp: datetime


@dataclass(frozen=True)
class RecorderPagination:
    """Lightweight representation of pagination captured during recording."""

    type: str
    selector: Optional[str] = None
    max_pages: Optional[int] = None


@dataclass(frozen=True)
class RecorderSession:
    """Aggregate state of a recording session."""

    id: str
    created_at: datetime
    updated_at: datetime
    name: Optional[str] = None
    entry: Optional[str] = None
    selectors: Dict[str, str] = field(default_factory=dict)
    detail_selector: Optional[str] = None
    detail_fields: Dict[str, str] = field(default_factory=dict)
    pagination: Optional[RecorderPagination] = None
    actions: List[Action] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    events: List[RecorderEvent] = field(default_factory=list)

    @property
    def event_count(self) -> int:
        return len(self.events)


class RecorderRepository:
    """Simple in-memory store for :class:`RecorderSession`."""

    def __init__(self) -> None:
        self._sessions: Dict[str, RecorderSession] = {}

    def create(
        self,
        *,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> RecorderSession:
        now = datetime.now(tz=timezone.utc)
        session = RecorderSession(
            id=uuid4().hex,
            created_at=now,
            updated_at=now,
            name=name,
            metadata=dict(metadata or {}),
        )
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> RecorderSession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise RecorderSessionNotFoundError(session_id) from exc

    def save(self, session: RecorderSession) -> RecorderSession:
        self._sessions[session.id] = session
        return session

    def list(self) -> Iterable[RecorderSession]:
        return sorted(self._sessions.values(), key=lambda item: item.created_at, reverse=True)


_ALLOWED_SELECTOR_ROLES = {"list", "title", "url", "summary", "time"}


class RecorderService:
    """High-level facade orchestrating recorder sessions and compilation."""

    def __init__(self, repository: RecorderRepository) -> None:
        self.repository = repository

    # ------------------------------------------------------------------
    # Session lifecycle helpers
    # ------------------------------------------------------------------
    def create_session(
        self,
        *,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> RecorderSession:
        return self.repository.create(name=name, metadata=metadata)

    def get_session(self, session_id: str) -> RecorderSession:
        return self.repository.get(session_id)

    def list_sessions(self) -> Iterable[RecorderSession]:
        return self.repository.list()

    # ------------------------------------------------------------------
    # Event ingestion & playback
    # ------------------------------------------------------------------
    def record_event(self, session_id: str, payload: Dict[str, Any]) -> RecorderSession:
        session = self.get_session(session_id)
        event = self._build_event(payload)
        updated = self._apply_event(session, event)
        return self.repository.save(updated)

    def playback(self, session_id: str) -> List[Dict[str, Any]]:
        session = self.get_session(session_id)
        steps: List[Dict[str, Any]] = []
        for index, event in enumerate(session.events):
            steps.append(
                {
                    "index": index,
                    "type": event.type,
                    "payload": event.payload,
                    "timestamp": event.timestamp.isoformat().replace("+00:00", "Z"),
                }
            )
        return steps

    # ------------------------------------------------------------------
    # Compilation
    # ------------------------------------------------------------------
    def compile_session(self, session_id: str, *, name: Optional[str] = None) -> RuleSchema:
        session = self.get_session(session_id)
        rule_name = name or session.name
        if not rule_name:
            raise RecorderSessionValidationError("rule name is required before compilation")
        if not session.entry:
            raise RecorderSessionValidationError("entry URL is required before compilation")
        list_selector = session.selectors.get("list")
        if not list_selector:
            raise RecorderSessionValidationError("list selector is required before compilation")

        selectors = SelectorConfig(
            list=list_selector,
            title=session.selectors.get("title"),
            url=session.selectors.get("url"),
            summary=session.selectors.get("summary"),
            time=session.selectors.get("time"),
        )

        pagination: Optional[PaginationConfig] = None
        if session.pagination is not None:
            pagination_kwargs: Dict[str, Any] = {"type": session.pagination.type}
            if session.pagination.selector is not None:
                pagination_kwargs["selector"] = session.pagination.selector
            if session.pagination.max_pages is not None:
                pagination_kwargs["max_pages"] = session.pagination.max_pages
            pagination = PaginationConfig(**pagination_kwargs)  # type: ignore[arg-type]

        detail: Optional[DetailRule] = None
        if session.detail_selector or session.detail_fields:
            fields = [
                DetailField(name=name, selector=selector)
                for name, selector in session.detail_fields.items()
            ]
            detail = DetailRule(
                enabled=bool(session.detail_selector),
                selector=session.detail_selector,
                fields=fields,
            )

        metadata = dict(session.metadata)
        metadata.setdefault("recorder_session", session.id)
        metadata.setdefault("recorder_events", str(session.event_count))

        try:
            return RuleSchema(
                name=rule_name,
                entry=session.entry,
                selectors=selectors,
                pagination=pagination,
                detail=detail,
                actions=list(session.actions),
                metadata=metadata,
            )
        except SchemaValidationError as exc:  # pragma: no cover - relies on schema tests
            raise RecorderSessionValidationError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_event(self, payload: Dict[str, Any]) -> RecorderEvent:
        event_type = payload.get("type")
        if not isinstance(event_type, str) or not event_type.strip():
            raise InvalidRecorderEvent("event type must be a non-empty string")
        event_payload = payload.get("payload", {})
        if not isinstance(event_payload, dict):
            raise InvalidRecorderEvent("event payload must be an object")
        timestamp = datetime.now(tz=timezone.utc)
        return RecorderEvent(type=event_type, payload=event_payload, timestamp=timestamp)

    def _apply_event(self, session: RecorderSession, event: RecorderEvent) -> RecorderSession:
        handler = getattr(self, f"_handle_{event.type.replace('-', '_')}", None)
        if handler is None:
            raise InvalidRecorderEvent(f"unsupported event type: {event.type}")
        updated = handler(session, event.payload)
        events = list(session.events) + [event]
        return replace(updated, events=events, updated_at=event.timestamp)

    def _handle_navigate(
        self,
        session: RecorderSession,
        payload: Dict[str, Any],
    ) -> RecorderSession:
        url = payload.get("url")
        if not isinstance(url, str) or not url.strip():
            raise InvalidRecorderEvent("navigate event requires url")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InvalidRecorderEvent("navigate event url must be HTTP/HTTPS")
        return replace(session, entry=url)

    def _handle_set_name(
        self,
        session: RecorderSession,
        payload: Dict[str, Any],
    ) -> RecorderSession:
        name = payload.get("name")
        if not isinstance(name, str) or not name.strip():
            raise InvalidRecorderEvent("set_name event requires non-empty name")
        return replace(session, name=name.strip())

    def _handle_capture_selector(
        self,
        session: RecorderSession,
        payload: Dict[str, Any],
    ) -> RecorderSession:
        role = payload.get("role")
        selector = payload.get("selector")
        if role not in _ALLOWED_SELECTOR_ROLES:
            raise InvalidRecorderEvent("capture_selector role is not supported")
        if not isinstance(selector, str) or not selector.strip():
            raise InvalidRecorderEvent("capture_selector requires selector")
        selectors = dict(session.selectors)
        selectors[role] = selector.strip()
        return replace(session, selectors=selectors)

    def _handle_set_detail_selector(
        self,
        session: RecorderSession,
        payload: Dict[str, Any],
    ) -> RecorderSession:
        selector = payload.get("selector")
        if selector is None:
            return replace(session, detail_selector=None)
        if not isinstance(selector, str) or not selector.strip():
            raise InvalidRecorderEvent("set_detail_selector requires selector string")
        return replace(session, detail_selector=selector.strip())

    def _handle_capture_detail_field(
        self,
        session: RecorderSession,
        payload: Dict[str, Any],
    ) -> RecorderSession:
        name = payload.get("name")
        selector = payload.get("selector")
        if not isinstance(name, str) or not name.strip():
            raise InvalidRecorderEvent("capture_detail_field requires name")
        if not isinstance(selector, str) or not selector.strip():
            raise InvalidRecorderEvent("capture_detail_field requires selector")
        fields = dict(session.detail_fields)
        fields[name.strip()] = selector.strip()
        return replace(session, detail_fields=fields)

    def _handle_set_pagination(
        self,
        session: RecorderSession,
        payload: Dict[str, Any],
    ) -> RecorderSession:
        pagination_type = payload.get("type")
        if not isinstance(pagination_type, str) or not pagination_type.strip():
            raise InvalidRecorderEvent("set_pagination requires type")
        pagination_type = pagination_type.strip()
        selector = payload.get("selector")
        if selector is not None and (not isinstance(selector, str) or not selector.strip()):
            raise InvalidRecorderEvent("pagination selector must be string when provided")
        max_pages_value = payload.get("max_pages")
        if max_pages_value is not None:
            if not isinstance(max_pages_value, int) or max_pages_value < 1:
                raise InvalidRecorderEvent("max_pages must be positive integer")
        pagination = RecorderPagination(
            type=pagination_type,
            selector=selector.strip() if isinstance(selector, str) else None,
            max_pages=max_pages_value,
        )
        return replace(session, pagination=pagination)

    def _handle_add_action(
        self,
        session: RecorderSession,
        payload: Dict[str, Any],
    ) -> RecorderSession:
        action_type = payload.get("type")
        if not isinstance(action_type, str) or not action_type.strip():
            raise InvalidRecorderEvent("add_action requires type")
        selector_value = payload.get("selector")
        if selector_value is not None and (
            not isinstance(selector_value, str) or not selector_value.strip()
        ):
            raise InvalidRecorderEvent("action selector must be string when provided")
        event_value = payload.get("event")
        if event_value is not None and (
            not isinstance(event_value, str) or not event_value.strip()
        ):
            raise InvalidRecorderEvent("action event must be string when provided")
        fields_value = payload.get("fields")
        fields: List[str]
        if fields_value is None:
            fields = []
        elif isinstance(fields_value, list) and all(isinstance(item, str) for item in fields_value):
            fields = [item for item in fields_value if item]
        else:
            raise InvalidRecorderEvent("action fields must be a list of strings")
        try:
            action = Action(
                type=action_type.strip(),
                selector=selector_value.strip() if isinstance(selector_value, str) else None,
                event=event_value.strip() if isinstance(event_value, str) else None,
                fields=fields,
            )
        except SchemaValidationError as exc:
            raise InvalidRecorderEvent(str(exc)) from exc
        return replace(session, actions=list(session.actions) + [action])

    def _handle_set_metadata(
        self,
        session: RecorderSession,
        payload: Dict[str, Any],
    ) -> RecorderSession:
        key = payload.get("key")
        value = payload.get("value")
        if not isinstance(key, str) or not key.strip():
            raise InvalidRecorderEvent("metadata key must be a non-empty string")
        if not isinstance(value, str):
            raise InvalidRecorderEvent("metadata value must be a string")
        metadata = dict(session.metadata)
        metadata[key.strip()] = value
        return replace(session, metadata=metadata)

    # Graceful aliases -------------------------------------------------
    def _handle_clear_pagination(
        self,
        session: RecorderSession,
        _payload: Dict[str, Any],
    ) -> RecorderSession:
        return replace(session, pagination=None)

    def _handle_clear_detail(
        self,
        session: RecorderSession,
        _payload: Dict[str, Any],
    ) -> RecorderSession:
        return replace(session, detail_selector=None, detail_fields={})

    def _handle_remove_detail_field(
        self,
        session: RecorderSession,
        payload: Dict[str, Any],
    ) -> RecorderSession:
        name = payload.get("name")
        if not isinstance(name, str) or not name.strip():
            raise InvalidRecorderEvent("remove_detail_field requires name")
        fields = dict(session.detail_fields)
        fields.pop(name.strip(), None)
        return replace(session, detail_fields=fields)

    def _handle_remove_last_action(
        self,
        session: RecorderSession,
        _payload: Dict[str, Any],
    ) -> RecorderSession:
        if not session.actions:
            return session
        return replace(session, actions=session.actions[:-1])


def summarise_events(events: Iterable[RecorderEvent]) -> Dict[str, Any]:
    """Produce quick analytics about a set of events."""

    count = 0
    types: Dict[str, int] = {}
    durations: List[float] = []
    ordered = list(events)
    for event in ordered:
        count += 1
        types[event.type] = types.get(event.type, 0) + 1
    if len(ordered) >= 2:
        timestamps = [event.timestamp.timestamp() for event in ordered]
        durations.append(max(timestamps) - min(timestamps))
    average_duration = mean(durations) if durations else 0.0
    return {"count": count, "types": types, "duration_seconds": average_duration}
