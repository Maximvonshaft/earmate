from __future__ import annotations

from .. import schemas
from ..storage.repository import AsyncRepository


class RecorderService:
    """High-level orchestrator for persisting visual recording sessions."""

    def __init__(self, repository: AsyncRepository):
        self._repository = repository

    async def register_recording(self, payload: schemas.RecordingCreate) -> schemas.Recording:
        return await self._repository.create_recording(payload)

    async def list_recordings(self) -> list[schemas.Recording]:
        return await self._repository.list_recordings()

    async def get_recording(self, recording_id: int) -> schemas.Recording | None:
        return await self._repository.get_recording(recording_id)
