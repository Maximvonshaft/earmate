"""EarMate core package."""

from .engine import ExecutionResult, RuleExecutor
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

__all__ = [
    "ExecutionResult",
    "RuleExecutor",
    "Action",
    "DeduplicationConfig",
    "DetailField",
    "DetailRule",
    "OutputConfig",
    "PaginationConfig",
    "RuleSchema",
    "SchemaValidationError",
    "ScheduleConfig",
    "SelectorConfig",
]
