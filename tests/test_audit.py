from datetime import datetime, timezone

import pytest

from earmate import audit_collectors
from earmate.audit import AttemptOutcome, _attempt_single, _summarise_payload, render_markdown
from earmate.collectors.base import CollectorError, CollectorResult
from earmate.collectors.factory import CollectorFactory
from earmate.config import SourceGroup, SourceSpec


class DummyCollector:
    def __init__(self, spec: SourceSpec) -> None:
        self.spec = spec

    def collect(self) -> CollectorResult:
        return CollectorResult(
            category=self.spec.category,
            platform=self.spec.platform,
            source=self.spec.source,
            timestamp=datetime.now(timezone.utc),
            payload={"streams": [{"id": "1", "title": "demo"}]},
            metadata={"interval": None, "throttle": {}, "weight_hint": {}, "tags": []},
        )


def test_summarise_payload_handles_common_structures() -> None:
    summary = _summarise_payload({"streams": [{"id": "1", "title": "demo"}]})
    assert "streams=1" in summary
    assert "示例键" in summary


def test_attempt_single_missing_collector(monkeypatch: pytest.MonkeyPatch) -> None:
    group = SourceGroup(name="test", specs=[])
    spec = SourceSpec(category="demo", platform="Unknown", source="demo")

    def fake_resolve(unused: SourceSpec) -> type[DummyCollector]:
        raise CollectorError("no collector")

    monkeypatch.setattr("earmate.audit.resolve_collector_class", fake_resolve)
    outcome = _attempt_single(CollectorFactory(), group, spec)
    assert outcome.status == "失败"
    assert "未注册采集器" in outcome.detail


def test_attempt_single_success(monkeypatch: pytest.MonkeyPatch) -> None:
    group = SourceGroup(name="test", specs=[])
    spec = SourceSpec(category="demo", platform="X", source="demo")

    monkeypatch.setattr("earmate.audit.resolve_collector_class", lambda _: DummyCollector)
    monkeypatch.setattr(CollectorFactory, "create", lambda self, s: DummyCollector(s))

    outcome = _attempt_single(CollectorFactory(), group, spec)
    assert outcome.status == "成功"
    assert "streams=1" in outcome.detail


def test_render_markdown(tmp_path) -> None:
    output = tmp_path / "report.md"
    outcomes = [
        AttemptOutcome(
            group="g",
            category="c",
            platform="p",
            source="s",
            status="成功",
            detail="streams=1",
        )
    ]
    render_markdown(outcomes, output)
    text = output.read_text(encoding="utf-8")
    assert "采集器覆盖度巡检报告" in text
    assert "streams=1" in text


def test_audit_collectors_uses_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    config_path = tmp_path / "ears.yaml"
    config_path.write_text(
        "social_sources:\n"
        "  - category: demo\n"
        "    platform: X\n"
        "    source: demo\n"
        "    example: [demo]\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "earmate.audit._attempt_single",
        lambda factory, group, spec: AttemptOutcome(
            group=group.name,
            category=spec.category,
            platform=spec.platform,
            source=spec.source,
            status="成功",
            detail="ok",
        ),
    )

    outcomes = audit_collectors(config_path)
    assert outcomes == [
        AttemptOutcome(
            group="social_sources",
            category="demo",
            platform="X",
            source="demo",
            status="成功",
            detail="ok",
        )
    ]
