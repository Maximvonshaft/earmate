from __future__ import annotations

import json
from typing import Any


class Response:
    """Simple response object compatible with the testing client."""

    def __init__(self, content: Any | None = None, status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code

    def render(self) -> bytes:
        if self.content is None:
            return b""
        if isinstance(self.content, (bytes, bytearray)):
            return bytes(self.content)
        if isinstance(self.content, str):
            return self.content.encode("utf-8")
        return json.dumps(self.content, ensure_ascii=False).encode("utf-8")
