from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from .. import schemas


@dataclass
class _RecordingRow:
    id: int
    name: str
    description: str | None
    steps: str
    created_at: str


@dataclass
class _JobRow:
    id: int
    name: str
    description: str | None
    recording_id: int
    cron_expression: str
    timezone: str
    payload: str | None
    created_at: str


@dataclass
class _ExecutionRow:
    id: int
    job_id: int
    status: str
    started_at: str
    finished_at: str | None
    result: str | None


class AsyncRepository:
    """Persistence layer responsible for storing platform state."""

    def __init__(self, database_path: Path):
        self.database_path = database_path

    async def init(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.database_path) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    steps TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    recording_id INTEGER NOT NULL REFERENCES recordings(id) ON DELETE CASCADE,
                    cron_expression TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    payload TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    result TEXT
                );
                """
            )
            await db.commit()

    async def create_recording(self, payload: schemas.RecordingCreate) -> schemas.Recording:
        created_at = datetime.now(UTC)
        steps_json = json.dumps([step.model_dump() for step in payload.steps])
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                "INSERT INTO recordings(name, description, steps, created_at) VALUES (?, ?, ?, ?)",
                (payload.name, payload.description, steps_json, created_at.isoformat()),
            )
            await db.commit()
            recording_id = cursor.lastrowid
        return schemas.Recording(
            id=recording_id,
            name=payload.name,
            description=payload.description,
            steps=payload.steps,
            created_at=created_at,
        )

    async def list_recordings(self) -> list[schemas.Recording]:
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, name, description, steps, created_at FROM recordings ORDER BY id"
            )
            rows = await cursor.fetchall()
        return [self._row_to_recording(_RecordingRow(**dict(row))) for row in rows]

    async def get_recording(self, recording_id: int) -> schemas.Recording | None:
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, name, description, steps, created_at FROM recordings WHERE id = ?",
                (recording_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_recording(_RecordingRow(**dict(row)))

    async def create_job(self, payload: schemas.JobCreate) -> schemas.Job:
        created_at = datetime.now(UTC)
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO jobs(
                    name,
                    description,
                    recording_id,
                    cron_expression,
                    timezone,
                    payload,
                    created_at
                )
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.name,
                    payload.description,
                    payload.recording_id,
                    payload.schedule.cron_expression,
                    payload.schedule.timezone,
                    json.dumps(payload.payload) if payload.payload is not None else None,
                    created_at.isoformat(),
                ),
            )
            await db.commit()
            job_id = cursor.lastrowid
        return schemas.Job(
            id=job_id,
            name=payload.name,
            description=payload.description,
            recording_id=payload.recording_id,
            schedule=payload.schedule,
            payload=payload.payload,
            created_at=created_at,
        )

    async def list_jobs(self) -> list[schemas.Job]:
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    recording_id,
                    cron_expression,
                    timezone,
                    payload,
                    created_at
                FROM jobs
                ORDER BY id
                """
            )
            rows = await cursor.fetchall()
        return [self._row_to_job(_JobRow(**dict(row))) for row in rows]

    async def get_job(self, job_id: int) -> schemas.Job | None:
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    recording_id,
                    cron_expression,
                    timezone,
                    payload,
                    created_at
                FROM jobs
                WHERE id = ?
                """,
                (job_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_job(_JobRow(**dict(row)))

    async def create_execution(
        self, job_id: int, status: schemas.ExecutionStatus
    ) -> schemas.Execution:
        started_at = datetime.now(UTC)
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO executions(job_id, status, started_at, finished_at, result)
                VALUES(?, ?, ?, NULL, ?)
                """,
                (job_id, status.value, started_at.isoformat(), json.dumps({})),
            )
            await db.commit()
            execution_id = cursor.lastrowid
        return schemas.Execution(
            id=execution_id,
            job_id=job_id,
            status=status,
            started_at=started_at,
            finished_at=None,
            result=schemas.ExecutionResult(),
        )

    async def update_execution(
        self,
        execution_id: int,
        status: schemas.ExecutionStatus,
        result: schemas.ExecutionResult | None = None,
    ) -> schemas.Execution:
        finished_at = datetime.now(UTC)
        result_payload = result or schemas.ExecutionResult()
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                """
                UPDATE executions SET status = ?, finished_at = ?, result = ? WHERE id = ?
                """,
                (
                    status.value,
                    finished_at.isoformat(),
                    json.dumps(result_payload.model_dump()),
                    execution_id,
                ),
            )
            await db.commit()
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT job_id, started_at FROM executions WHERE id = ?",
                (execution_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            msg = f"Execution {execution_id} not found for update"
            raise RuntimeError(msg)
        started_at = datetime.fromisoformat(row["started_at"])
        return schemas.Execution(
            id=execution_id,
            job_id=row["job_id"],
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            result=result_payload,
        )

    async def list_executions(self) -> list[schemas.Execution]:
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT
                    id,
                    job_id,
                    status,
                    started_at,
                    finished_at,
                    result
                FROM executions
                ORDER BY id
                """
            )
            rows = await cursor.fetchall()
        return [self._row_to_execution(_ExecutionRow(**dict(row))) for row in rows]

    def _row_to_recording(self, row: _RecordingRow) -> schemas.Recording:
        steps_data: Iterable[dict] = json.loads(row.steps or "[]")
        steps = [schemas.PlaybookStep.model_validate(step) for step in steps_data]
        return schemas.Recording(
            id=row.id,
            name=row.name,
            description=row.description,
            steps=steps,
            created_at=datetime.fromisoformat(row.created_at),
        )

    def _row_to_job(self, row: _JobRow) -> schemas.Job:
        payload_data = json.loads(row.payload) if row.payload else None
        schedule = schemas.JobSchedule(
            cron_expression=row.cron_expression,
            timezone=row.timezone,
        )
        return schemas.Job(
            id=row.id,
            name=row.name,
            description=row.description,
            recording_id=row.recording_id,
            schedule=schedule,
            payload=payload_data,
            created_at=datetime.fromisoformat(row.created_at),
        )

    def _row_to_execution(self, row: _ExecutionRow) -> schemas.Execution:
        if row.result:
            result_data = json.loads(row.result)
            result_payload = schemas.ExecutionResult.model_validate(result_data)
        else:
            result_payload = schemas.ExecutionResult()
        finished_at = datetime.fromisoformat(row.finished_at) if row.finished_at else None
        return schemas.Execution(
            id=row.id,
            job_id=row.job_id,
            status=schemas.ExecutionStatus(row.status),
            started_at=datetime.fromisoformat(row.started_at),
            finished_at=finished_at,
            result=result_payload,
        )

