"""Tests for the simulated collectors."""
from __future__ import annotations

from pathlib import Path

import pytest

from earmate.collectors.factory import CollectorFactory
from earmate.collectors.platforms import normalise_platform, resolve_payload_factory
from earmate.config import count_sources, load_sources
from earmate.runner import run_collectors


@pytest.fixture(scope="module")
def config_groups() -> list:
    return load_sources(Path(__file__).resolve().parents[1] / "ears.yaml")


def test_all_sources_are_loaded(config_groups: list) -> None:
    assert count_sources(config_groups) == sum(len(group) for group in config_groups)


def test_factory_produces_collectors(config_groups: list) -> None:
    factory = CollectorFactory()
    collectors = factory.create_all(config_groups)
    assert len(collectors) == count_sources(config_groups)

    sample = collectors[0].collect()
    assert sample.payload
    assert sample.metadata["tags"]


def test_runner_executes_all_collectors(config_groups: list) -> None:
    results = run_collectors(Path(__file__).resolve().parents[1] / "ears.yaml")
    assert len(results) == count_sources(config_groups)

    timestamps = {result.timestamp for result in results}
    assert len(timestamps) == len(results)


def test_platform_normalisation() -> None:
    assert normalise_platform("Web/RSS") == "web_rss"
    assert normalise_platform("Discord (public)") == "discord_public"
    assert normalise_platform("API", "stablecoin_flows") == "stablecoin_flows_api"


def test_resolve_payload_factory_uses_category_fallback(config_groups: list) -> None:
    for group in config_groups:
        for spec in group:
            factory = resolve_payload_factory(spec)
            payload = factory(spec)
            assert payload["content_type"]
            assert payload["entities"]
