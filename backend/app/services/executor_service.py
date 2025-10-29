from __future__ import annotations

import asyncio
from typing import Any

from .. import schemas
from ..storage.repository import AsyncRepository


class ExecutionEngine:
    """Lightweight engine that replays recorded steps and produces structured outputs."""

    async def run(
        self,
        recording: schemas.Recording,
        context: dict[str, Any] | None = None,
    ) -> schemas.ExecutionResult:
        ctx = context or {}
        logs: list[str] = []
        outputs: dict[str, Any] = {}

        for idx, step in enumerate(recording.steps, start=1):
            logs.append(self._describe_step(idx, step))
            await asyncio.sleep(0)  # yield control in asyncio applications
            if step.action == "extract":
                key = step.metadata.get("alias") or step.id
                outputs[key] = {
                    "selector": step.target,
                    "value": ctx.get(key, step.value or ""),
                }
            elif step.action == "transform":
                key = step.metadata.get("alias") or step.id
                expression = step.metadata.get("expression") or ""
                outputs[key] = {
                    "expression": expression,
                    "input": outputs.get(step.metadata.get("input")),
                }
            elif step.action == "http_request":
                key = step.metadata.get("alias") or step.id
                outputs[key] = {
                    "request": {
                        "method": step.metadata.get("method", "GET"),
                        "url": step.target,
                    },
                    "status_code": 200,
                    "body": f"Simulated response for {step.target}",
                }

        return schemas.ExecutionResult(logs=logs, outputs=outputs)

    def _describe_step(self, order: int, step: schemas.PlaybookStep) -> str:
        target = f" target={step.target}" if step.target else ""
        value = f" value={step.value}" if step.value else ""
        return f"[{order}] action={step.action}{target}{value}"


class ExecutionService:
    """Coordinates execution lifecycle and persistence of job runs."""

    def __init__(self, repository: AsyncRepository, engine: ExecutionEngine | None = None):
        self._repository = repository
        self._engine = engine or ExecutionEngine()

    async def trigger_execution(
        self,
        job_id: int,
        context: dict[str, Any] | None = None,
    ) -> schemas.Execution:
        job = await self._repository.get_job(job_id)
        if job is None:
            msg = f"Job {job_id} not found"
            raise ValueError(msg)

        recording = await self._repository.get_recording(job.recording_id)
        if recording is None:
            msg = f"Recording {job.recording_id} missing for job {job_id}"
            raise RuntimeError(msg)

        execution = await self._repository.create_execution(job_id, schemas.ExecutionStatus.RUNNING)
        try:
            result = await self._engine.run(recording, context or job.payload or {})
            updated = await self._repository.update_execution(
                execution.id,
                schemas.ExecutionStatus.SUCCESS,
                result=result,
            )
        except Exception as exc:  # pragma: no cover - defensive programming
            error_result = schemas.ExecutionResult(
                logs=execution.result.logs + [f"Execution failed: {exc}"],
                outputs=execution.result.outputs,
            )
            updated = await self._repository.update_execution(
                execution.id,
                schemas.ExecutionStatus.FAILED,
                result=error_result,
            )
        return updated

    async def replay_recording(
        self,
        recording_id: int,
        context: dict[str, Any] | None = None,
    ) -> schemas.ExecutionResult:
        recording = await self._repository.get_recording(recording_id)
        if recording is None:
            msg = f"Recording {recording_id} not found"
            raise ValueError(msg)
        return await self._engine.run(recording, context=context)
