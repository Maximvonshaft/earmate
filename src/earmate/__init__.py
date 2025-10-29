"""EarMate core package."""

from .engine import ExecutionResult, RuleExecutor
from .rule_manager import RuleNotFoundError, RuleRecord, RuleRepository, RuleService
from .scheduler import InMemoryScheduler, ScheduledRule, SchedulerEmpty
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
    "RuleRepository",
    "RuleService",
    "RuleRecord",
    "RuleNotFoundError",
    "InMemoryScheduler",
    "ScheduledRule",
    "SchedulerEmpty",
]
