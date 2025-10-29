from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException

from . import config, schemas
from .services.executor_service import ExecutionService
from .services.recorder_service import RecorderService
from .services.scheduler_service import SchedulerService
from .storage.repository import AsyncRepository

app = FastAPI(
    title="Earmate Data Automation Platform",
    description=(
        "Programmable data collection platform that orchestrates visual recordings, backend "
        "execution, and persistent scheduling."
    ),
    version="0.1.0",
)

_repository = AsyncRepository(config.get_database_path())
_recorder_service = RecorderService(_repository)
_execution_service = ExecutionService(_repository)
_scheduler_service = SchedulerService(_repository, _execution_service)


def get_recorder_service() -> RecorderService:
    return _recorder_service


def get_execution_service() -> ExecutionService:
    return _execution_service


@app.on_event("startup")
async def on_startup() -> None:
    await _repository.init()
    await _scheduler_service.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await _scheduler_service.shutdown()


@app.get("/", summary="Platform readiness probe")
async def root() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recordings", response_model=schemas.Recording, summary="Create a new recording")
async def create_recording(
    payload: schemas.RecordingCreate,
    service: RecorderService = Depends(get_recorder_service),
) -> schemas.Recording:
    return await service.register_recording(payload)


@app.get("/recordings", response_model=list[schemas.Recording], summary="List recordings")
async def list_recordings(
    service: RecorderService = Depends(get_recorder_service),
) -> list[schemas.Recording]:
    return await service.list_recordings()


@app.post("/jobs", response_model=schemas.Job, summary="Create a scheduled job")
async def create_job(
    payload: schemas.JobCreate,
    service: RecorderService = Depends(get_recorder_service),
) -> schemas.Job:
    recording = await service.get_recording(payload.recording_id)
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    job = await _repository.create_job(payload)
    await _scheduler_service.schedule_job(job)
    return job


@app.get("/jobs", response_model=list[schemas.Job], summary="List jobs")
async def list_jobs() -> list[schemas.Job]:
    return await _repository.list_jobs()


@app.post(
    "/jobs/{job_id}/run",
    response_model=schemas.Execution,
    summary="Trigger an execution for a job",
)
async def run_job(
    job_id: int,
    execution_service: ExecutionService = Depends(get_execution_service),
) -> schemas.Execution:
    try:
        return await execution_service.trigger_execution(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/executions", response_model=list[schemas.Execution], summary="List executions")
async def list_executions() -> list[schemas.Execution]:
    return await _repository.list_executions()
