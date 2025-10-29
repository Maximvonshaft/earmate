from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from earmate.scheduler import InMemoryScheduler, SchedulerEmpty
from earmate.schema import RuleSchema, ScheduleConfig, SelectorConfig


class TimeController:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def advance(self, delta: timedelta) -> None:
        self.current += delta

    def now(self) -> datetime:
        return self.current


def make_rule(schedule: ScheduleConfig | None) -> RuleSchema:
    return RuleSchema(
        name="rule",
        entry="https://example.com/list",
        selectors=SelectorConfig(list="article", title="h2", url="h2 a"),
        schedule=schedule,
    )


def test_scheduler_immediate_runs() -> None:
    controller = TimeController(datetime(2024, 1, 1, tzinfo=timezone.utc))
    scheduler = InMemoryScheduler(time_provider=controller.now)

    scheduler.add_rule("r1", make_rule(ScheduleConfig(mode="immediate")))
    due = scheduler.pop_due()

    assert len(due) == 1
    assert due[0].rule_id == "r1"

    with pytest.raises(SchedulerEmpty):
        scheduler.peek()


def test_scheduler_cron_reschedules() -> None:
    start = datetime(2024, 1, 1, 5, 59, tzinfo=timezone.utc)
    controller = TimeController(start)
    scheduler = InMemoryScheduler(time_provider=controller.now)

    scheduler.add_rule("cron", make_rule(ScheduleConfig(mode="cron", expr="0 6 * * *")))
    assert scheduler.peek().next_run == datetime(2024, 1, 1, 6, 0, tzinfo=timezone.utc)

    controller.advance(timedelta(minutes=1))
    due = scheduler.pop_due()
    assert len(due) == 1
    assert due[0].next_run == datetime(2024, 1, 1, 6, 0, tzinfo=timezone.utc)

    assert scheduler.peek().next_run == datetime(2024, 1, 2, 6, 0, tzinfo=timezone.utc)


def test_scheduler_no_due_entries() -> None:
    controller = TimeController(datetime(2024, 1, 1, tzinfo=timezone.utc))
    scheduler = InMemoryScheduler(time_provider=controller.now)

    scheduler.add_rule("cron", make_rule(ScheduleConfig(mode="cron", expr="0 6 * * *")))
    due = scheduler.pop_due()
    assert due == []
