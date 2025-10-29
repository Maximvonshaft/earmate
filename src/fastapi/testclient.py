from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .app import FastAPI
from .responses import Response


class _TestResponse:
    """Response wrapper mimicking :class:`requests.Response` APIs used in tests."""

    def __init__(self, response: Response):
        self.status_code = response.status_code
        self._content = response.render()
        self._data = response.content

    def json(self) -> Any:
        if isinstance(self._data, (dict, list)):
            return self._data
        if self._data is None:
            return None
        if isinstance(self._data, (bytes, bytearray)):
            return json.loads(bytes(self._data).decode("utf-8"))
        if isinstance(self._data, str):
            return json.loads(self._data)
        return self._data

    @property
    def text(self) -> str:
        if self._content:
            return self._content.decode("utf-8")
        return ""


class TestClient:
    """Very small testing client that calls the application directly."""

    __test__ = False  # prevent pytest from attempting to collect this class

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    def request(
        self, method: str, path: str, json: Optional[Dict[str, Any]] = None
    ) -> _TestResponse:
        response = self.app.handle_request(method, path, body=json)
        return _TestResponse(response)

    def get(self, path: str) -> _TestResponse:
        return self.request("GET", path)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> _TestResponse:
        return self.request("POST", path, json=json)

    def put(self, path: str, json: Optional[Dict[str, Any]] = None) -> _TestResponse:
        return self.request("PUT", path, json=json)

    def delete(self, path: str) -> _TestResponse:
        return self.request("DELETE", path)
