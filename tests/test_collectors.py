"""Tests for live collectors using mocked upstream responses."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from earmate.collectors.factory import CollectorFactory
from earmate.collectors.platforms import (
    RssCollector,
    TelegramCollector,
    XCollector,
    normalise_platform,
    resolve_collector_class,
)
from earmate.config import SourceGroup, SourceSpec, count_sources, load_sources


class DummyResponse:
    def __init__(self, *, text: str | None = None, json_data: Any | None = None) -> None:
        self.text = text or ""
        self._json_data = json_data

    def json(self) -> Any:
        if self._json_data is None:
            raise ValueError("No JSON data provided")
        return self._json_data


@pytest.fixture(scope="module")
def config_groups() -> list[SourceGroup]:
    return load_sources(Path(__file__).resolve().parents[1] / "ears.yaml")


def test_load_sources_counts(config_groups: list[SourceGroup]) -> None:
    assert count_sources(config_groups) == sum(len(group) for group in config_groups)


def test_normalise_platform_variants() -> None:
    assert normalise_platform("Web/RSS") == "web_rss"
    assert normalise_platform("Discord (public)") == "discord_public"
    assert normalise_platform("Lens/Farcaster") == "lens_farcaster"


def test_resolve_collector_class_prefers_category() -> None:
    spec = SourceSpec(
        category="cex_market_ws",
        platform="WS/API",
        source="binance",
        example=["binance"],
    )
    assert resolve_collector_class(spec).__name__ == "ExchangeWsCollector"


@pytest.mark.parametrize(
    ("collector_cls", "spec", "payload_key"),
    [
        (
            XCollector,
            SourceSpec(
                category="influencers",
                platform="X",
                source="timeline",
                example=["elonmusk"],
                throttle={"rpm": 120},
            ),
            "streams",
        ),
        (
            TelegramCollector,
            SourceSpec(
                category="alerts",
                platform="Telegram",
                source="public",
                example=["binance_announcements"],
            ),
            "streams",
        ),
    ],
)
def test_collectors_return_payload(
    monkeypatch: pytest.MonkeyPatch,
    collector_cls,
    spec: SourceSpec,
    payload_key: str,
) -> None:
    collector = collector_cls(spec)

    if collector_cls is XCollector:
        rss = (
            "<rss><channel>\n"
            "  <item><title>Test</title><link>https://example.com/1</link>"
            "<guid>1</guid><pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate></item>\n"
            "</channel></rss>"
        )
        monkeypatch.setattr(collector, "_http_get", lambda url: DummyResponse(text=rss))
    elif collector_cls is TelegramCollector:
        html = (
            '<div class="tgme_widget_message_wrap" data-post="chan/1">'
            '<div class="tgme_widget_message_text">Alert</div>'
            '<a class="tgme_widget_message_date" href="https://t.me/chan/1">'
            '<time datetime="2024-01-01T00:00:00+00:00"></time>'
            "</a></div>"
        )
        monkeypatch.setattr(collector, "_http_get", lambda url: DummyResponse(text=html))

    result = collector.collect()
    assert payload_key in result.payload
    assert result.payload[payload_key]
    assert result.metadata["throttle"] == spec.throttle


def test_rss_collector_uses_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = SourceSpec(
        category="news",
        platform="Web/RSS",
        source="alias",
        example=["CoinDesk"],
    )
    alias_map = json.dumps({"CoinDesk": "https://example.com/rss"})
    monkeypatch.setenv("EARMATE_RSS_ALIASES", alias_map)

    rss = (
        "<rss><channel>\n"
        "  <item><title>Headline</title><link>https://example.com/a</link>"
        "<pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate></item>\n"
        "</channel></rss>"
    )

    collector = RssCollector(spec)
    monkeypatch.setattr(collector, "_http_get", lambda url: DummyResponse(text=rss))

    payload = collector._generate_payload()
    assert payload["streams"][0]["entries"][0]["title"] == "Headline"


def test_collector_factory_creates_live_collector(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = SourceSpec(
        category="influencers",
        platform="X",
        source="timeline",
        example=["elonmusk"],
    )

    factory = CollectorFactory()
    collector = factory.create(spec)
    assert isinstance(collector, XCollector)

    rss = (
        "<rss><channel>\n"
        "  <item><title>Test</title><link>https://example.com/1</link>"
        "<guid>1</guid></item>\n"
        "</channel></rss>"
    )
    monkeypatch.setattr(collector, "_http_get", lambda url: DummyResponse(text=rss))

    result = collector.collect()
    assert result.payload["streams"][0]["posts"]
