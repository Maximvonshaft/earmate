"""Collector base abstractions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from ..config import SourceSpec


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


class SimulatedCollector(Collector):
    """Collector that uses a payload factory to simulate upstream data."""

    def __init__(self, spec: SourceSpec, payload_factory: Callable[[SourceSpec], Dict[str, Any]]) -> None:
        super().__init__(spec)
        self._payload_factory = payload_factory

    def _generate_payload(self) -> Dict[str, Any]:
        return self._payload_factory(self.spec)
