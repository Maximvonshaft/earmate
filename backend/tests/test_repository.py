from __future__ import annotations

import asyncio
from pathlib import Path

from backend.app import schemas
from backend.app.services.executor_service import ExecutionService
from backend.app.storage.repository import AsyncRepository


def test_create_and_list_recordings(tmp_path: Path) -> None:
    async def scenario() -> None:
        repository = AsyncRepository(tmp_path / "test.db")
        await repository.init()

        recording_payload = schemas.RecordingCreate(
            name="Sample flow",
            description="Navigate and extract data",
            steps=[
                schemas.PlaybookStep(
                    id="step-1", action="navigate", target="https://example.com"
                ),
                schemas.PlaybookStep(
                    id="step-2",
                    action="extract",
                    target="h1",
                    metadata={"alias": "title"},
                ),
            ],
        )

        created = await repository.create_recording(recording_payload)
        assert created.id > 0

        recordings = await repository.list_recordings()
        assert len(recordings) == 1
        assert recordings[0].name == "Sample flow"
        assert recordings[0].steps[1].metadata["alias"] == "title"

    asyncio.run(scenario())


def test_execution_service_runs_playbook(tmp_path: Path) -> None:
    async def scenario() -> None:
        repository = AsyncRepository(tmp_path / "runtime.db")
        await repository.init()

        recording_payload = schemas.RecordingCreate(
            name="ETL flow",
            steps=[
                schemas.PlaybookStep(
                    id="navigate", action="navigate", target="https://example.com"
                ),
                schemas.PlaybookStep(
                    id="extract",
                    action="extract",
                    target="h1",
                    metadata={"alias": "headline"},
                ),
                schemas.PlaybookStep(
                    id="transform",
                    action="transform",
                    metadata={"alias": "uppercase", "input": "headline", "expression": "upper"},
                ),
            ],
        )

        recording = await repository.create_recording(recording_payload)
        job_payload = schemas.JobCreate(
            name="Sample schedule",
            recording_id=recording.id,
            description="Convert headline to uppercase",
            schedule=schemas.JobSchedule(cron_expression="*/5 * * * *"),
            payload={"headline": "EarMate"},
        )

        job = await repository.create_job(job_payload)

        service = ExecutionService(repository)
        execution = await service.trigger_execution(job.id)

        assert execution.status == schemas.ExecutionStatus.SUCCESS
        assert "headline" in execution.result.outputs
        assert execution.result.outputs["headline"]["value"] == "EarMate"

    asyncio.run(scenario())
