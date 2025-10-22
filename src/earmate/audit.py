"""Audit helpers to evaluate live collector coverage."""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence

from .collectors.base import CollectorError
from .collectors.factory import CollectorFactory
from .collectors.platforms import resolve_collector_class
from .config import SourceGroup, SourceSpec, load_sources


@dataclass(slots=True)
class AttemptOutcome:
    """Container describing a single collector attempt."""

    group: str
    category: str
    platform: str
    source: str
    status: str
    detail: str


def _summarise_payload(payload: object) -> str:
    if isinstance(payload, dict):
        summary_parts: List[str] = []
        if "streams" in payload and isinstance(payload["streams"], Sequence):
            summary_parts.append(f"streams={len(payload['streams'])}")
            streams = payload["streams"]
            if streams:
                first = streams[0]
                if isinstance(first, dict):
                    summary_parts.append(
                        "示例键:" + ",".join(list(first.keys())[:4])
                    )
        if "entries" in payload and isinstance(payload["entries"], Sequence):
            summary_parts.append(f"entries={len(payload['entries'])}")
        if "summaries" in payload and isinstance(payload["summaries"], Sequence):
            summary_parts.append(f"summaries={len(payload['summaries'])}")
        if "metrics" in payload and isinstance(payload["metrics"], Sequence):
            summary_parts.append(f"metrics={len(payload['metrics'])}")
        if "snapshots" in payload and isinstance(payload["snapshots"], Sequence):
            summary_parts.append(f"snapshots={len(payload['snapshots'])}")
        if "payload" in payload and isinstance(payload["payload"], Sequence):
            summary_parts.append(f"payload={len(payload['payload'])}")
        if not summary_parts:
            summary_parts.append("keys=" + ",".join(list(payload.keys())[:5]))
        return "；".join(summary_parts)
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        return f"items={len(payload)}"
    if isinstance(payload, (str, int, float)):
        text = json.dumps(payload, ensure_ascii=False)
    else:
        text = repr(payload)
    return text[:200]


def audit_collectors(config_path: Path | str) -> List[AttemptOutcome]:
    """Run every configured collector once and capture success/failure."""

    groups = load_sources(config_path)
    factory = CollectorFactory()
    outcomes: List[AttemptOutcome] = []
    for group in groups:
        for spec in group:
            outcomes.append(_attempt_single(factory, group, spec))
    return outcomes


def _attempt_single(
    factory: CollectorFactory,
    group: SourceGroup,
    spec: SourceSpec,
) -> AttemptOutcome:
    trimmed_spec = spec
    if spec.example and len(spec.example) > 1:
        trimmed_spec = replace(spec, example=spec.example[:1])
    try:
        resolve_collector_class(trimmed_spec)
    except CollectorError as exc:
        return AttemptOutcome(
            group=group.name,
            category=spec.category,
            platform=spec.platform,
            source=spec.source,
            status="失败",
            detail=f"未注册采集器: {exc}",
        )

    try:
        collector = factory.create(trimmed_spec)
    except Exception as exc:  # pragma: no cover - defensive guard
        return AttemptOutcome(
            group=group.name,
            category=spec.category,
            platform=spec.platform,
            source=spec.source,
            status="失败",
            detail=f"实例化异常: {type(exc).__name__}: {exc}",
        )

    retry = getattr(collector, "_retry", None)
    if retry is not None:
        try:
            retry.max_attempts = 1
        except Exception:  # pragma: no cover - defensive guard
            pass

    try:
        result = collector.collect()
    except Exception as exc:
        return AttemptOutcome(
            group=group.name,
            category=spec.category,
            platform=spec.platform,
            source=spec.source,
            status="失败",
            detail=f"采集异常: {type(exc).__name__}: {exc}",
        )

    return AttemptOutcome(
        group=group.name,
        category=spec.category,
        platform=spec.platform,
        source=spec.source,
        status="成功",
        detail=_summarise_payload(result.payload),
    )


def render_markdown(outcomes: Iterable[AttemptOutcome], output_path: Path | str) -> Path:
    """Write a markdown summary to *output_path* and return the path."""

    path = Path(output_path)
    lines = [
        "# 采集器覆盖度巡检报告",
        "",
        f"生成时间：{datetime.now(timezone.utc).astimezone().isoformat()}",
        "",
        "| 分组 | 类别 | 平台 | 来源 | 状态 | 详情 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for outcome in outcomes:
        detail = outcome.detail.replace("|", "\\|")
        row = (
            f"| {outcome.group} | {outcome.category} | {outcome.platform} | "
            f"{outcome.source} | {outcome.status} | {detail} |"
        )
        lines.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(config_path: str = "ears.yaml", output: str = "reports/collection_report.md") -> int:
    outcomes = audit_collectors(config_path)
    render_markdown(outcomes, output)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
