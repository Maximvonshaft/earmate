from __future__ import annotations

import pytest

from earmate.recorder import (
    InvalidRecorderEvent,
    RecorderRepository,
    RecorderService,
    RecorderSessionValidationError,
)


@pytest.fixture
def service() -> RecorderService:
    return RecorderService(RecorderRepository())


def test_session_event_flow_and_compilation(service: RecorderService) -> None:
    session = service.create_session(name="News Feed")
    service.record_event(
        session.id,
        {"type": "navigate", "payload": {"url": "https://example.com/list"}},
    )
    service.record_event(
        session.id,
        {
            "type": "capture_selector",
            "payload": {"role": "list", "selector": "li.item"},
        },
    )
    service.record_event(
        session.id,
        {
            "type": "capture_selector",
            "payload": {"role": "title", "selector": "a.title"},
        },
    )
    service.record_event(
        session.id,
        {"type": "set_detail_selector", "payload": {"selector": "a.title"}},
    )
    service.record_event(
        session.id,
        {
            "type": "capture_detail_field",
            "payload": {"name": "body", "selector": "div.article"},
        },
    )
    service.record_event(
        session.id,
        {
            "type": "set_pagination",
            "payload": {
                "type": "url",
                "selector": "https://example.com/list?page={page}",
                "max_pages": 2,
            },
        },
    )
    service.record_event(
        session.id,
        {
            "type": "add_action",
            "payload": {"type": "click", "selector": "button.accept"},
        },
    )
    compiled = service.compile_session(session.id)

    assert compiled.entry == "https://example.com/list"
    assert compiled.selectors.list == "li.item"
    assert compiled.selectors.title == "a.title"
    assert compiled.detail is not None
    assert compiled.detail.selector == "a.title"
    assert compiled.pagination is not None
    assert compiled.pagination.max_pages == 2
    assert compiled.actions[0].type == "click"
    assert compiled.metadata["recorder_session"] == session.id

    playback = service.playback(session.id)
    assert len(playback) == service.get_session(session.id).event_count
    assert playback[0]["type"] == "navigate"


def test_invalid_event_is_rejected(service: RecorderService) -> None:
    session = service.create_session()
    with pytest.raises(InvalidRecorderEvent):
        service.record_event(
            session.id,
            {
                "type": "capture_selector",
                "payload": {"role": "unknown", "selector": "a"},
            },
        )


def test_compilation_requires_required_fields(service: RecorderService) -> None:
    session = service.create_session()
    service.record_event(session.id, {"type": "navigate", "payload": {"url": "https://example.com"}})
    with pytest.raises(RecorderSessionValidationError):
        service.compile_session(session.id)


def test_metadata_event_updates_payload(service: RecorderService) -> None:
    session = service.create_session()
    service.record_event(
        session.id,
        {"type": "navigate", "payload": {"url": "https://example.com/list"}},
    )
    service.record_event(
        session.id,
        {
            "type": "capture_selector",
            "payload": {"role": "list", "selector": "li"},
        },
    )
    service.record_event(
        session.id,
        {
            "type": "set_metadata",
            "payload": {"key": "source", "value": "recorder"},
        },
    )

    rule = service.compile_session(session.id, name="Demo")
    assert rule.metadata["source"] == "recorder"
    assert rule.name == "Demo"
