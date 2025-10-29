"""Dataclass-based rule schema definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlparse


class SchemaValidationError(ValueError):
    """Raised when schema validation fails."""


@dataclass
class SelectorConfig:
    """CSS selector definitions for the list page."""

    list: str
    title: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    time: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.list:
            raise SchemaValidationError("list selector is required")


@dataclass
class PaginationConfig:
    """Pagination strategy for list pages."""

    type: str
    selector: Optional[str] = None
    max_pages: int = 1

    def __post_init__(self) -> None:
        if self.type not in {"click", "url", "scroll"}:
            raise SchemaValidationError("pagination type must be click, url, or scroll")
        if self.type in {"click", "scroll"} and not self.selector:
            raise SchemaValidationError("selector is required for click or scroll pagination")
        if self.max_pages < 1:
            raise SchemaValidationError("max_pages must be at least 1")


@dataclass
class DetailField:
    """Detail page field definition."""

    name: str
    selector: str

    def __post_init__(self) -> None:
        if not self.name:
            raise SchemaValidationError("detail field name is required")
        if not self.selector:
            raise SchemaValidationError("detail field selector is required")


@dataclass
class DetailRule:
    """Detail page extraction configuration."""

    enabled: bool = False
    selector: Optional[str] = None
    fields: List[DetailField] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.enabled and not self.selector:
            raise SchemaValidationError("detail selector is required when enabled")


@dataclass
class Action:
    """Describes an interaction executed by the engine."""

    type: str
    selector: Optional[str] = None
    event: Optional[str] = None
    fields: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.type:
            raise SchemaValidationError("action type is required")


@dataclass
class ScheduleConfig:
    """Execution schedule for a rule."""

    mode: str
    expr: Optional[str] = None
    timezone: Optional[str] = None

    def __post_init__(self) -> None:
        if self.mode not in {"cron", "immediate"}:
            raise SchemaValidationError("schedule mode must be cron or immediate")
        if self.mode == "cron" and not self.expr:
            raise SchemaValidationError("cron mode requires expr")


@dataclass
class DeduplicationConfig:
    """Deduplication strategy for extracted records."""

    type: str
    threshold: Optional[int] = None

    def __post_init__(self) -> None:
        if self.type not in {"simhash", "url", "none"}:
            raise SchemaValidationError("dedupe type must be simhash, url, or none")
        if self.type == "simhash" and self.threshold is None:
            raise SchemaValidationError("simhash dedupe requires a threshold")


@dataclass
class OutputConfig:
    """Output target for the scraping run."""

    target: str
    table: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.target:
            raise SchemaValidationError("output target is required")


@dataclass
class RuleSchema:
    """Complete scraping rule definition used by the engine."""

    name: str
    entry: str
    selectors: SelectorConfig
    pagination: Optional[PaginationConfig] = None
    detail: Optional[DetailRule] = None
    actions: List[Action] = field(default_factory=list)
    schedule: Optional[ScheduleConfig] = None
    dedupe: Optional[DeduplicationConfig] = None
    output: Optional[OutputConfig] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise SchemaValidationError("rule name is required")
        parsed = urlparse(self.entry)
        if parsed.scheme not in {"http", "https"}:
            raise SchemaValidationError("entry must be an HTTP or HTTPS URL")
        if not parsed.netloc:
            raise SchemaValidationError("entry URL must include a host")
