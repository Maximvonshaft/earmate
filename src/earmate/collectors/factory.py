"""Collector factory mapping specs to implementations."""
from __future__ import annotations

from typing import List

from ..config import SourceGroup, SourceSpec
from .base import SimulatedCollector
from .platforms import resolve_payload_factory


class CollectorFactory:
    """Factory that wires source specs to collector instances."""

    def create(self, spec: SourceSpec) -> SimulatedCollector:
        payload_factory = resolve_payload_factory(spec)
        return SimulatedCollector(spec, payload_factory)

    def create_for_group(self, group: SourceGroup) -> List[SimulatedCollector]:
        return [self.create(spec) for spec in group]

    def create_all(self, groups: List[SourceGroup]) -> List[SimulatedCollector]:
        collectors: List[SimulatedCollector] = []
        for group in groups:
            collectors.extend(self.create_for_group(group))
        return collectors


def build_collectors(groups: List[SourceGroup]) -> List[SimulatedCollector]:
    """Convenience helper for callers that just need every collector."""

    factory = CollectorFactory()
    return factory.create_all(groups)
