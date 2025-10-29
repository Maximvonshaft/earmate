"""Rule schema definitions for the Earmate scraping framework."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass
class RuleSelectors:
    """Selectors describing how to extract data from a list page."""

    list: str
    fields: dict[str, str] = field(default_factory=dict)
    url: str | None = None

    @property
    def resolved_fields(self) -> dict[str, str]:
        mapping = dict(self.fields)
        if self.url is not None:
            mapping.setdefault("url", self.url)
        return mapping


@dataclass
class PaginationConfig:
    """Describe how pagination should be performed."""

    type: Literal["click", "url", "scroll", "none"] = "none"
    selector: str | None = None
    url_template: str | None = None
    start_page: int = 1
    max_pages: int = 1

    def __post_init__(self) -> None:
        if self.type == "url" and not self.url_template:
            msg = "url_template must be provided when pagination type is 'url'"
            raise ValueError(msg)
        if self.type in {"click", "scroll"} and not self.selector:
            msg = "selector must be provided when pagination type requires DOM interaction"
            raise ValueError(msg)
        if self.start_page < 1:
            msg = "start_page must be >= 1"
            raise ValueError(msg)
        if self.max_pages < 1:
            msg = "max_pages must be >= 1"
            raise ValueError(msg)


@dataclass
class DetailConfig:
    """Configuration for optional detail-page extraction."""

    enabled: bool = False
    selector: str | None = None
    fields: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.enabled and not self.selector:
            msg = "selector must be provided when detail extraction is enabled"
            raise ValueError(msg)


@dataclass
class ActionConfig:
    """Describe a low-level action used by the executor."""

    type: Literal["click", "wait", "extract", "scroll", "input"]
    selector: str | None = None
    event: str | None = None
    fields: list[str] | None = None
    value: str | None = None


@dataclass
class ScheduleConfig:
    """Scheduling metadata for a rule."""

    mode: Literal["cron", "interval", "manual"] = "manual"
    expr: str | None = None
    timezone: str | None = None
    interval_seconds: int | None = None

    def __post_init__(self) -> None:
        if self.mode == "cron" and not self.expr:
            msg = "Cron mode requires expr to be set"
            raise ValueError(msg)
        if self.mode == "interval" and not self.interval_seconds:
            msg = "Interval mode requires interval_seconds to be set"
            raise ValueError(msg)


@dataclass
class Rule:
    """Top level rule definition."""

    name: str
    entry: str
    selectors: RuleSelectors
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    detail: DetailConfig = field(default_factory=DetailConfig)
    actions: list[ActionConfig] = field(default_factory=list)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    dedupe: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)

    def model_dump_for_execution(self) -> dict[str, Any]:
        return asdict(self)

