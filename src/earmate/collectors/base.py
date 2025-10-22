"""Collector base abstractions with retry & rate limiting."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, MutableMapping
from urllib import error as urllib_error
from urllib import request as urllib_request

from ..config import SourceSpec


class CollectorError(RuntimeError):
    """Raised when a collector cannot return data."""


class ConfigurationError(CollectorError):
    """Raised when mandatory runtime configuration is missing."""


@dataclass(slots=True)
class CollectorResult:
    """Result returned by a collector run."""

    category: str
    platform: str
    source: str
    timestamp: datetime
    payload: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a JSON serialisable dict."""

        return {
            "category": self.category,
            "platform": self.platform,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata,
        }


class Collector:
    """Base class for collectors."""

    def __init__(self, spec: SourceSpec) -> None:
        self.spec = spec

    def collect(self) -> CollectorResult:
        """Collect data once using the provided generator."""

        payload = self._generate_payload()
        metadata = {
            "interval": self.spec.interval,
            "throttle": self.spec.throttle,
            "weight_hint": self.spec.weight_hint,
            "tags": self.spec.tags,
        }
        return CollectorResult(
            category=self.spec.category,
            platform=self.spec.platform,
            source=self.spec.source,
            timestamp=datetime.now(timezone.utc),
            payload=payload,
            metadata=metadata,
        )

    def _generate_payload(self) -> Dict[str, Any]:
        raise NotImplementedError


class RateLimiter:
    """Simple sleep-based rate limiter derived from spec throttle hints."""

    def __init__(self, min_interval: float = 0.0) -> None:
        self._min_interval = max(min_interval, 0.0)
        self._last_acquire = 0.0

    @classmethod
    def from_throttle(cls, throttle: Mapping[str, Any]) -> "RateLimiter":
        interval = 0.0
        rpm = throttle.get("rpm")
        rps = throttle.get("rps")
        if isinstance(rpm, (int, float)) and rpm > 0:
            interval = max(interval, 60.0 / float(rpm))
        if isinstance(rps, (int, float)) and rps > 0:
            interval = max(interval, 1.0 / float(rps))
        return cls(interval)

    def acquire(self) -> None:
        if self._min_interval <= 0:
            return
        now = time.monotonic()
        delta = now - self._last_acquire
        if delta < self._min_interval:
            time.sleep(self._min_interval - delta)
        self._last_acquire = time.monotonic()


@dataclass(slots=True)
class RetryConfig:
    """Retry policy used by :class:`LiveCollector`."""

    max_attempts: int = 3
    backoff_factor: float = 0.75
    max_backoff: float = 8.0

    def compute_sleep(self, attempt: int) -> float:
        return min(self.backoff_factor * (2 ** max(attempt - 1, 0)), self.max_backoff)


class HTTPResponse:
    """Minimal response wrapper for urllib results."""

    def __init__(self, body: bytes, headers: Mapping[str, Any], status: int) -> None:
        self._body = body
        self.headers = dict(headers)
        self.status = status

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.text)


class LiveCollector(Collector):
    """Collector that talks to remote services with retries & rate limiting."""

    user_agent = "EarMateBot/0.2"

    def __init__(
        self,
        spec: SourceSpec,
        *,
        retry: RetryConfig | None = None,
    ) -> None:
        super().__init__(spec)
        self._retry = retry or RetryConfig()
        self._rate_limiter = RateLimiter.from_throttle(spec.throttle)
        self._default_headers: Dict[str, str] = {"User-Agent": self.user_agent}

    # -- HTTP helpers ----------------------------------------------------
    def _http_request(self, method: str, url: str, **kwargs: Any) -> HTTPResponse:
        timeout = kwargs.pop("timeout", 15)
        for attempt in range(1, self._retry.max_attempts + 1):
            self._rate_limiter.acquire()
            try:
                response = self._perform_request(method, url, timeout=timeout, **kwargs)
            except CollectorError:  # pragma: no cover - network failures
                if attempt >= self._retry.max_attempts:
                    raise
                time.sleep(self._retry.compute_sleep(attempt))
                continue

            if response.status >= 500:
                if attempt >= self._retry.max_attempts:
                    raise CollectorError(f"Server error {response.status} for {url}")
                time.sleep(self._retry.compute_sleep(attempt))
                continue
            if 400 <= response.status < 500:
                raise CollectorError(f"HTTP error {response.status} for {url}")
            return response
        raise CollectorError(f"Failed to request {url}")

    def _perform_request(self, method: str, url: str, **kwargs: Any) -> HTTPResponse:
        headers = dict(self._default_headers)
        extra_headers = kwargs.pop("headers", None) or {}
        headers.update({str(key): str(value) for key, value in extra_headers.items()})
        data = kwargs.pop("data", None)
        json_payload = kwargs.pop("json", None)
        timeout = kwargs.pop("timeout", 15)
        if json_payload is not None:
            data = json.dumps(json_payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if isinstance(data, str):
            data = data.encode("utf-8")
        if data is not None and not isinstance(data, (bytes, bytearray)):
            raise TypeError("Request body must be bytes, bytearray, or str")

        request_obj = urllib_request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib_request.urlopen(request_obj, timeout=timeout) as response:
                body = response.read()
                status = getattr(response, "status", 200)
                header_map = dict(response.headers.items())
                return HTTPResponse(body, header_map, status)
        except urllib_error.HTTPError as exc:  # pragma: no cover - network failures
            body = exc.read() if hasattr(exc, "read") else b""
            header_items = getattr(exc, "headers", {})
            header_map = dict(header_items.items()) if hasattr(header_items, "items") else {}
            return HTTPResponse(body, header_map, exc.code)
        except urllib_error.URLError as exc:  # pragma: no cover - network failures
            raise CollectorError(str(exc)) from exc

    def _http_get(self, url: str, **kwargs: Any) -> HTTPResponse:
        return self._http_request("GET", url, **kwargs)

    def _http_post(self, url: str, **kwargs: Any) -> HTTPResponse:
        return self._http_request("POST", url, **kwargs)

    # -- configuration helpers ------------------------------------------
    @staticmethod
    def require_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ConfigurationError(f"Environment variable '{name}' is required")
        return value

    @staticmethod
    def require_json_env(name: str) -> MutableMapping[str, Any]:
        raw = LiveCollector.require_env(name)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                f"Environment variable '{name}' must contain valid JSON"
            ) from exc
        if not isinstance(parsed, MutableMapping):
            raise ConfigurationError(f"Environment variable '{name}' must be a JSON object")
        return parsed

    @staticmethod
    def optional_json_env(name: str) -> MutableMapping[str, Any]:
        raw = os.getenv(name)
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                f"Environment variable '{name}' must contain valid JSON"
            ) from exc
        if not isinstance(parsed, MutableMapping):
            raise ConfigurationError(f"Environment variable '{name}' must be a JSON object")
        return parsed
