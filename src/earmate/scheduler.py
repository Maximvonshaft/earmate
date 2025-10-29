"""Simplified in-memory scheduler for rule execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from heapq import heapify, heappop, heappush
from typing import Callable, List, Optional

from .schema import RuleSchema, ScheduleConfig


@dataclass(order=True)
class ScheduledRule:
    """Represents a scheduled execution of a rule."""

    next_run: datetime
    rule_id: str
    rule: RuleSchema


class SchedulerEmpty(Exception):
    """Raised when attempting to pop from an empty scheduler."""


class InMemoryScheduler:
    """Priority-queue based scheduler managing :class:`ScheduledRule` entries."""

    def __init__(self, time_provider: Optional[Callable[[], datetime]] = None) -> None:
        self._queue: List[ScheduledRule] = []
        self._time_provider = time_provider or (lambda: datetime.now(tz=timezone.utc))

    def add_rule(self, rule_id: str, rule: RuleSchema) -> ScheduledRule:
        next_run = _compute_next_run(rule.schedule, self._time_provider())
        entry = ScheduledRule(next_run=next_run, rule_id=rule_id, rule=rule)
        heappush(self._queue, entry)
        return entry

    def pop_due(self) -> List[ScheduledRule]:
        now = self._time_provider()
        due: List[ScheduledRule] = []
        while self._queue and self._queue[0].next_run <= now:
            entry = heappop(self._queue)
            due.append(entry)
            rescheduled = _reschedule(entry, now)
            if rescheduled:
                heappush(self._queue, rescheduled)
        return due

    def peek(self) -> ScheduledRule:
        if not self._queue:
            raise SchedulerEmpty("no rules scheduled")
        return self._queue[0]

    def rebuild(self, entries: List[ScheduledRule]) -> None:
        self._queue = entries[:]
        heapify(self._queue)


def _reschedule(entry: ScheduledRule, reference: datetime) -> Optional[ScheduledRule]:
    if not entry.rule.schedule or entry.rule.schedule.mode == "immediate":
        return None
    next_run = _compute_next_run(entry.rule.schedule, reference)
    return ScheduledRule(next_run=next_run, rule_id=entry.rule_id, rule=entry.rule)


def _compute_next_run(schedule: Optional[ScheduleConfig], reference: datetime) -> datetime:
    if schedule is None or schedule.mode == "immediate":
        return reference
    if schedule.mode != "cron":
        raise ValueError(f"unsupported schedule mode: {schedule.mode}")
    expr = schedule.expr or "* * * * *"
    return _next_cron_time(expr, reference)


def _next_cron_time(expr: str, reference: datetime) -> datetime:
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError("cron expression must contain five fields")
    minute_values = _parse_cron_field(fields[0], 0, 59)
    hour_values = _parse_cron_field(fields[1], 0, 23)
    dom_values = _parse_cron_field(fields[2], 1, 31)
    month_values = _parse_cron_field(fields[3], 1, 12)
    dow_values = _parse_cron_field(fields[4], 0, 6)

    candidate = (reference + timedelta(minutes=1)).replace(second=0, microsecond=0)
    limit = candidate + timedelta(days=366)

    while candidate < limit:
        if (
            candidate.minute in minute_values
            and candidate.hour in hour_values
            and candidate.day in dom_values
            and candidate.month in month_values
            and _cron_weekday(candidate) in dow_values
        ):
            return candidate
        candidate += timedelta(minutes=1)

    raise ValueError("unable to compute next cron time within search window")


def _parse_cron_field(field: str, minimum: int, maximum: int) -> List[int]:
    values: List[int] = []
    for part in field.split(","):
        token = part.strip()
        if not token:
            continue
        if token in {"*", "?"}:
            return list(range(minimum, maximum + 1))
        if token.startswith("*/"):
            step = int(token[2:])
            if step <= 0:
                raise ValueError("cron step must be positive")
            return list(range(minimum, maximum + 1, step))
        if "-" in token:
            start_str, end_str = token.split("-", 1)
            start = int(start_str)
            end = int(end_str)
            if start > end or start < minimum or end > maximum:
                raise ValueError("invalid cron range")
            values.extend(range(start, end + 1))
            continue
        value = int(token)
        if value < minimum or value > maximum:
            raise ValueError("cron value out of range")
        values.append(value)
    if not values:
        raise ValueError("cron field produced no values")
    return sorted(set(values))


def _cron_weekday(moment: datetime) -> int:
    # datetime.weekday(): Monday=0 ... Sunday=6 -> convert to cron where Sunday=0
    weekday = moment.weekday()  # Monday=0
    return (weekday + 1) % 7
