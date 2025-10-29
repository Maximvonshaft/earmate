from __future__ import annotations

import asyncio
from collections.abc import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .. import schemas
from ..storage.repository import AsyncRepository
from .executor_service import ExecutionService


class SchedulerService:
    """Thin wrapper around APScheduler that keeps persistence in sync."""

    def __init__(
        self,
        repository: AsyncRepository,
        executor_service: ExecutionService,
        scheduler: AsyncIOScheduler | None = None,
    ) -> None:
        self._repository = repository
        self._executor = executor_service
        self._scheduler = scheduler or AsyncIOScheduler()

    async def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            await self.reload_jobs()

    async def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def reload_jobs(self) -> None:
        jobs = await self._repository.list_jobs()
        existing = {job.id for job in jobs}
        for scheduled in list(self._scheduler.get_jobs()):
            if scheduled.id and scheduled.id.startswith("job-"):
                job_id = int(scheduled.id.split("-", maxsplit=1)[1])
                if job_id not in existing:
                    self._scheduler.remove_job(scheduled.id)
        for job in jobs:
            self._upsert_job(job)

    async def schedule_job(self, job: schemas.Job) -> None:
        self._upsert_job(job)

    def _upsert_job(self, job: schemas.Job) -> None:
        trigger = CronTrigger.from_crontab(
            job.schedule.cron_expression,
            timezone=job.schedule.timezone,
        )
        job_id = f"job-{job.id}"
        callable_ref = self._build_job_callable(job.id)
        if self._scheduler.get_job(job_id):
            self._scheduler.reschedule_job(job_id, trigger=trigger)
        else:
            self._scheduler.add_job(callable_ref, trigger=trigger, id=job_id, replace_existing=True)

    def _build_job_callable(self, job_id: int) -> Callable[[], None]:
        def runner() -> None:
            asyncio.create_task(self._executor.trigger_execution(job_id))

        return runner
