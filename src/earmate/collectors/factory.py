"""Collector factory mapping specs to live implementations."""
from __future__ import annotations

from typing import List

from ..config import SourceGroup, SourceSpec
from .base import Collector
from .platforms import resolve_collector_class


class CollectorFactory:
    """Factory that wires source specs to collector instances."""

    def create(self, spec: SourceSpec) -> Collector:
        collector_cls = resolve_collector_class(spec)
        return collector_cls(spec)

    def create_for_group(self, group: SourceGroup) -> List[Collector]:
        return [self.create(spec) for spec in group]

    def create_all(self, groups: List[SourceGroup]) -> List[Collector]:
        collectors: List[Collector] = []
        for group in groups:
            collectors.extend(self.create_for_group(group))
        return collectors


def build_collectors(groups: List[SourceGroup]) -> List[Collector]:
    """Convenience helper for callers that just need every collector."""

    factory = CollectorFactory()
    return factory.create_all(groups)
