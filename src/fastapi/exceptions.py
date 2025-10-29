from __future__ import annotations


class HTTPException(Exception):
    """Minimal representation of :class:`fastapi.HTTPException`."""

    def __init__(self, status_code: int, detail: str | None = None) -> None:
        super().__init__(detail or "HTTPException")
        self.status_code = status_code
        self.detail = detail or "HTTPException"
