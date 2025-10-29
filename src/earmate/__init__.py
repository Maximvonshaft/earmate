"""EarMate core package."""

from .api import create_app
from .engine import ExecutionResult, RuleExecutor
from .monitoring import MonitoringRepository, MonitoringService, TaskStatus
from .recorder import RecorderRepository, RecorderService
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
from .storage import ExecutionNotFoundError, ExecutionRecord, ResultRepository

__all__ = [
    "ExecutionResult",
    "RuleExecutor",
    "create_app",
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
    "ResultRepository",
    "ExecutionRecord",
    "ExecutionNotFoundError",
    "MonitoringRepository",
    "MonitoringService",
    "TaskStatus",
    "RecorderRepository",
    "RecorderService",
]
