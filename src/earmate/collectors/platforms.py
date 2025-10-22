"""Live collector implementations for upstream platforms."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from html.parser import HTMLParser
from typing import Any, Dict, List, Tuple

from ..config import SourceSpec
from .base import Collector, CollectorError, ConfigurationError, LiveCollector

__all__ = [
    "Collector",
    "LiveCollector",
    "normalise_platform",
    "resolve_collector_class",
]


def _clean_examples(spec: SourceSpec) -> List[str]:
    entries = [str(item).strip() for item in spec.example if str(item).strip()]
    if not entries:
        entries = [spec.source]
    return entries


def _limit_items(items: Sequence[Any], limit: int = 5) -> List[Any]:
    return list(items[:limit]) if len(items) > limit else list(items)


def normalise_platform(platform: str) -> str:
    cleaned = platform.lower()
    cleaned = cleaned.replace("/", "_")
    cleaned = re.sub(r"[^a-z0-9_]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")


def _iter_feed_elements(text: str) -> List[ET.Element]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{*}entry")
    return items


def _child_text(element: ET.Element, names: Sequence[str]) -> str | None:
    lowered = {name.lower() for name in names}
    for child in element:
        local = child.tag.split("}")[-1].lower()
        if local in lowered:
            text = (child.text or "").strip()
            if text:
                return html.unescape(text)
            href = child.attrib.get("href")
            if href:
                return html.unescape(href.strip())
    for name in lowered:
        attr = element.attrib.get(name)
        if attr:
            return html.unescape(attr.strip())
    return None


def _parse_rss_items(text: str, *, limit: int = 5) -> List[Dict[str, Any]]:
    entries = []
    for element in _iter_feed_elements(text)[:limit]:
        entries.append(
            {
                "id": _child_text(element, ("guid", "id", "videoId")),
                "title": _child_text(element, ("title",)),
                "summary": _child_text(element, ("summary", "description", "content")),
                "link": _child_text(element, ("link",)),
                "published": _child_text(element, ("published", "pubDate", "updated")),
            }
        )
    return entries


class _TelegramHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.messages: List[Dict[str, Any]] = []
        self._current: Dict[str, Any] | None = None
        self._capture_text = False
        self._text_parts: List[str] = []
        self._wrap_depth: int | None = None
        self._stack: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        attrs_dict = {key: value for key, value in attrs}
        classes_value = attrs_dict.get("class") or ""
        class_tokens = str(classes_value).split()
        if tag == "div" and "tgme_widget_message_wrap" in class_tokens:
            self._current = {
                "id": attrs_dict.get("data-post"),
                "text": "",
                "timestamp": None,
                "link": None,
            }
            self._wrap_depth = len(self._stack)
        if self._current is not None:
            if tag == "div" and "tgme_widget_message_text" in class_tokens:
                self._capture_text = True
                self._text_parts = []
            elif tag == "a" and "tgme_widget_message_date" in class_tokens:
                self._current["link"] = attrs_dict.get("href")
            elif tag == "time":
                timestamp = attrs_dict.get("datetime") or attrs_dict.get("title")
                if timestamp:
                    self._current["timestamp"] = timestamp
        self._stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self._capture_text and tag == "div":
            text = html.unescape("".join(self._text_parts).strip())
            if self._current is not None:
                self._current["text"] = text
            self._capture_text = False
            self._text_parts = []
        if (
            self._current is not None
            and self._wrap_depth is not None
            and len(self._stack) == self._wrap_depth + 1
            and tag == "div"
        ):
            if not self._current.get("text"):
                self._current["text"] = html.unescape("".join(self._text_parts).strip())
            self.messages.append(self._current)
            self._current = None
            self._wrap_depth = None
            self._text_parts = []
            self._capture_text = False
        if self._stack:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if self._capture_text:
            self._text_parts.append(data)


def _parse_telegram_messages(text: str, *, limit: int = 8) -> List[Dict[str, Any]]:
    parser = _TelegramHTMLParser()
    parser.feed(text)
    parser.close()
    return parser.messages[:limit]


class XCollector(LiveCollector):
    """Collect timelines from public Nitter RSS mirrors."""

    rss_template = "https://r.jina.ai/https://nitter.net/{handle}/rss"

    def _parse_feed(self, url: str) -> List[Dict[str, Any]]:
        response = self._http_get(url)
        return _parse_rss_items(response.text, limit=5)

    def _generate_payload(self) -> Dict[str, Any]:
        handles = [entry.lstrip("@") for entry in _clean_examples(self.spec)]
        streams: List[Dict[str, Any]] = []
        for handle in handles:
            url = self.rss_template.format(handle=handle)
            posts = self._parse_feed(url)
            streams.append({"handle": handle, "posts": posts})
        return {
            "content_type": "microblog",
            "platform": "X",
            "entities": handles,
            "streams": streams,
        }


class TelegramCollector(LiveCollector):
    """Scrape Telegram channel preview pages via jina.ai relay."""

    channel_template = "https://r.jina.ai/https://t.me/s/{channel}"

    def _parse_channel(self, channel: str) -> List[Dict[str, Any]]:
        response = self._http_get(self.channel_template.format(channel=channel))
        return _parse_telegram_messages(response.text, limit=8)

    def _generate_payload(self) -> Dict[str, Any]:
        channels = [entry.lstrip("@") for entry in _clean_examples(self.spec)]
        streams = []
        for channel in channels:
            messages = self._parse_channel(channel)
            streams.append({"channel": channel, "messages": messages})
        return {
            "content_type": "broadcast",
            "platform": "Telegram",
            "entities": channels,
            "streams": streams,
        }


class LensCollector(LiveCollector):
    """Query Lens API for recent publications."""

    api_url = "https://api-v2.lens.dev/"
    query = """
    query ProfileFeed($handle: Handle!) {
      publications(request: { where: { from: [$handle] }, limit: 5 }) {
        items {
          __typename
          ... on Post {
            id
            createdAt
            metadata {
              content
            }
          }
        }
      }
    }
    """

    def _fetch_profile(self, handle: str) -> List[Dict[str, Any]]:
        payload = {"query": self.query, "variables": {"handle": handle}}
        response = self._http_post(self.api_url, json=payload)
        data = response.json()
        publications = (
            data.get("data", {})
            .get("publications", {})
            .get("items", [])
        )
        items: List[Dict[str, Any]] = []
        for entry in _limit_items(publications, 5):
            metadata = entry.get("metadata", {})
            items.append(
                {
                    "id": entry.get("id"),
                    "created_at": entry.get("createdAt"),
                    "content": metadata.get("content"),
                }
            )
        return items

    def _normalise_handle(self, entry: str) -> str:
        entry = entry.strip()
        if not entry:
            return entry
        if "." not in entry:
            return f"{entry}.lens"
        return entry

    def _generate_payload(self) -> Dict[str, Any]:
        handles = [self._normalise_handle(entry) for entry in _clean_examples(self.spec)]
        streams = []
        for handle in handles:
            posts = self._fetch_profile(handle)
            streams.append({"handle": handle, "posts": posts})
        return {
            "content_type": "web3_social",
            "platform": "Lens",
            "entities": handles,
            "streams": streams,
        }


class VideoCollector(LiveCollector):
    """Collect RSS feeds for video platforms (YouTube/TikTok)."""

    youtube_user_template = "https://www.youtube.com/feeds/videos.xml?user={name}"
    youtube_channel_template = "https://www.youtube.com/feeds/videos.xml?channel_id={identifier}"

    def _resolve_feed(self, identifier: str) -> str:
        if identifier.startswith("http"):
            return identifier
        if identifier.startswith("UC"):
            return self.youtube_channel_template.format(identifier=identifier)
        name = identifier.lstrip("@")
        return self.youtube_user_template.format(name=name)

    def _parse_feed(self, url: str) -> List[Dict[str, Any]]:
        response = self._http_get(url)
        items = _parse_rss_items(response.text, limit=5)
        videos: List[Dict[str, Any]] = []
        for entry in items:
            videos.append(
                {
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "published": entry.get("published"),
                }
            )
        return videos

    def _generate_payload(self) -> Dict[str, Any]:
        channels = _clean_examples(self.spec)
        streams = []
        for channel in channels:
            feed_url = self._resolve_feed(channel)
            videos = self._parse_feed(feed_url)
            streams.append({"channel": channel, "feed": feed_url, "videos": videos})
        return {
            "content_type": "video",
            "platform": "YouTube/TikTok",
            "entities": channels,
            "streams": streams,
        }


class DiscordCollector(LiveCollector):
    """Query Discord guild widgets using configured guild IDs."""

    widget_template = "https://discord.com/api/guilds/{guild_id}/widget.json"
    env_var = "EARMATE_DISCORD_WIDGET_IDS"

    def _resolve_guilds(self) -> List[Tuple[str, str]]:
        mapping = {str(k): str(v) for k, v in self.require_json_env(self.env_var).items()}
        guilds = []
        for server in _clean_examples(self.spec):
            key = server
            if key not in mapping:
                key = server.lower()
            guild_id = mapping.get(key)
            if not guild_id:
                raise ConfigurationError(
                    f"Discord server '{server}' missing in {self.env_var} mapping"
                )
            guilds.append((server, guild_id))
        return guilds

    def _generate_payload(self) -> Dict[str, Any]:
        guilds = self._resolve_guilds()
        streams: List[Dict[str, Any]] = []
        for name, guild_id in guilds:
            response = self._http_get(self.widget_template.format(guild_id=guild_id))
            data = response.json()
            channels = data.get("channels", [])
            members = data.get("members", [])
            streams.append(
                {
                    "server": name,
                    "guild_id": guild_id,
                    "channels": _limit_items(channels, 10),
                    "members": _limit_items(members, 10),
                }
            )
        return {
            "content_type": "chat",
            "platform": "Discord",
            "entities": [name for name, _ in guilds],
            "streams": streams,
        }


class RedditCollector(LiveCollector):
    """Use Reddit's public JSON endpoints."""

    subreddit_template = "https://www.reddit.com/{path}/new.json?limit=5"

    def _fetch_subreddit(self, subreddit: str) -> List[Dict[str, Any]]:
        path = subreddit.lstrip("/")
        if not path.startswith("r/"):
            path = f"r/{path}"
        response = self._http_get(
            self.subreddit_template.format(path=path),
            headers={"User-Agent": self.user_agent},
        )
        data = response.json()
        posts = data.get("data", {}).get("children", [])
        items: List[Dict[str, Any]] = []
        for child in posts:
            post = child.get("data", {})
            items.append(
                {
                    "id": post.get("id"),
                    "title": post.get("title"),
                    "permalink": post.get("permalink"),
                    "created_utc": post.get("created_utc"),
                }
            )
        return items

    def _generate_payload(self) -> Dict[str, Any]:
        subreddits = _clean_examples(self.spec)
        streams = []
        for subreddit in subreddits:
            posts = self._fetch_subreddit(subreddit)
            streams.append({"subreddit": subreddit, "posts": posts})
        return {
            "content_type": "forum",
            "platform": "Reddit",
            "entities": subreddits,
            "streams": streams,
        }


class WeiboCollector(LiveCollector):
    """Fetch CN social feeds via configured RSS endpoints."""

    env_var = "EARMATE_CN_FEEDS"

    def _resolve_feeds(self) -> List[Tuple[str, str]]:
        mapping = {str(k): str(v) for k, v in self.require_json_env(self.env_var).items()}
        feeds: List[Tuple[str, str]] = []
        for account in _clean_examples(self.spec):
            url = mapping.get(account) or mapping.get(account.lower())
            if not url:
                raise ConfigurationError(
                    f"Feed URL for '{account}' missing in {self.env_var}"
                )
            feeds.append((account, url))
        return feeds

    def _parse_feed(self, url: str) -> List[Dict[str, Any]]:
        response = self._http_get(url)
        entries = _parse_rss_items(response.text, limit=6)
        items: List[Dict[str, Any]] = []
        for entry in entries:
            items.append(
                {
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "published": entry.get("published"),
                }
            )
        return items

    def _generate_payload(self) -> Dict[str, Any]:
        feeds = self._resolve_feeds()
        streams = []
        for name, url in feeds:
            items = self._parse_feed(url)
            streams.append({"account": name, "feed": url, "items": items})
        return {
            "content_type": "cn_social",
            "platform": "Weibo/Wechat",
            "entities": [name for name, _ in feeds],
            "streams": streams,
        }


class RssCollector(LiveCollector):
    """Generic RSS collector for news sources."""

    alias_env = "EARMATE_RSS_ALIASES"

    def _resolve_feed(self, identifier: str) -> str:
        if identifier.startswith("http"):
            return identifier
        aliases = self.optional_json_env(self.alias_env)
        url = aliases.get(identifier) or aliases.get(identifier.lower())
        if not url:
            raise ConfigurationError(
                f"RSS alias '{identifier}' missing and not a URL"
            )
        return str(url)

    def _parse_feed(self, url: str) -> List[Dict[str, Any]]:
        response = self._http_get(url)
        parsed_entries = _parse_rss_items(response.text, limit=8)
        entries: List[Dict[str, Any]] = []
        for entry in parsed_entries:
            entries.append(
                {
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "published": entry.get("published"),
                }
            )
        return entries

    def _generate_payload(self) -> Dict[str, Any]:
        entities = _clean_examples(self.spec)
        streams = []
        for identifier in entities:
            url = self._resolve_feed(identifier)
            entries = self._parse_feed(url)
            streams.append({"source": identifier, "feed": url, "entries": entries})
        return {
            "content_type": "news",
            "platform": self.spec.platform,
            "entities": entities,
            "streams": streams,
        }


class StatusCollector(LiveCollector):
    """Fetch status page summaries."""

    def _resolve_url(self, endpoint: str) -> str:
        if endpoint.startswith("http"):
            return endpoint
        domain = endpoint.rstrip("/")
        if domain.endswith("/status"):
            domain = domain[:-7]
        return f"https://{domain}/api/v2/summary.json"

    def _generate_payload(self) -> Dict[str, Any]:
        endpoints = _clean_examples(self.spec)
        summaries = []
        for endpoint in endpoints:
            url = self._resolve_url(endpoint)
            response = self._http_get(url)
            data = response.json()
            summaries.append({"endpoint": endpoint, "url": url, "status": data})
        return {
            "content_type": "status",
            "platform": "Status",
            "entities": endpoints,
            "summaries": summaries,
        }


class ExchangeWsCollector(LiveCollector):
    """Fetch market snapshots from configured REST endpoints."""

    env_var = "EARMATE_MARKET_SNAPSHOTS"

    def _resolve_endpoints(self) -> List[Tuple[str, str]]:
        mapping = {str(k): str(v) for k, v in self.require_json_env(self.env_var).items()}
        pairs = []
        for name in _clean_examples(self.spec):
            url = mapping.get(name) or mapping.get(name.lower())
            if not url:
                raise ConfigurationError(
                    f"Market endpoint for '{name}' missing in {self.env_var}"
                )
            pairs.append((name, url))
        return pairs

    def _generate_payload(self) -> Dict[str, Any]:
        endpoints = self._resolve_endpoints()
        snapshots = []
        for name, url in endpoints:
            response = self._http_get(url)
            data = response.json()
            snapshots.append({"name": name, "url": url, "data": data})
        return {
            "content_type": "market",
            "platform": "Exchange",
            "entities": [name for name, _ in endpoints],
            "snapshots": snapshots,
        }


class OnchainCollector(LiveCollector):
    """Collect on-chain metrics from configured providers."""

    env_var = "EARMATE_ONCHAIN_ENDPOINTS"

    def _resolve_metrics(self) -> List[Tuple[str, str]]:
        mapping = {str(k): str(v) for k, v in self.require_json_env(self.env_var).items()}
        metrics = []
        for metric in _clean_examples(self.spec):
            url = mapping.get(metric) or mapping.get(metric.lower())
            if not url:
                raise ConfigurationError(
                    f"On-chain metric '{metric}' missing in {self.env_var}"
                )
            metrics.append((metric, url))
        return metrics

    def _generate_payload(self) -> Dict[str, Any]:
        metrics = self._resolve_metrics()
        metrics_payload = []
        for metric, url in metrics:
            response = self._http_get(url)
            data = response.json()
            metrics_payload.append({"metric": metric, "url": url, "data": data})
        return {
            "content_type": "onchain",
            "platform": self.spec.platform,
            "entities": [metric for metric, _ in metrics],
            "metrics": metrics_payload,
        }


class StablecoinCollector(LiveCollector):
    """Fetch stablecoin flow metrics."""

    env_var = "EARMATE_STABLECOIN_ENDPOINTS"

    def _resolve_streams(self) -> List[Tuple[str, str]]:
        mapping = {str(k): str(v) for k, v in self.require_json_env(self.env_var).items()}
        streams = []
        for name in _clean_examples(self.spec):
            url = mapping.get(name) or mapping.get(name.lower())
            if not url:
                raise ConfigurationError(
                    f"Stablecoin stream '{name}' missing in {self.env_var}"
                )
            streams.append((name, url))
        return streams

    def _generate_payload(self) -> Dict[str, Any]:
        mappings = self._resolve_streams()
        streams = []
        for name, url in mappings:
            response = self._http_get(url)
            data = response.json()
            streams.append({"name": name, "url": url, "data": data})
        return {
            "content_type": "stablecoin",
            "platform": "API",
            "entities": [name for name, _ in mappings],
            "streams": streams,
        }


_COLLECTOR_REGISTRY: Dict[Tuple[str | None, str], type[Collector]] = {
    (None, "x"): XCollector,
    (None, "twitter"): XCollector,
    (None, "telegram"): TelegramCollector,
    (None, "lens_farcaster"): LensCollector,
    (None, "youtube_tiktok"): VideoCollector,
    (None, "discord_public"): DiscordCollector,
    (None, "reddit"): RedditCollector,
    (None, "weibo_wechat"): WeiboCollector,
    (None, "web_rss"): RssCollector,
    (None, "web_api"): RssCollector,
    (None, "status_api"): StatusCollector,
    ("cex_market_ws", "ws_api"): ExchangeWsCollector,
    (None, "ws_api"): ExchangeWsCollector,
    ("onchain_core", "node_api"): OnchainCollector,
    (None, "node_api"): OnchainCollector,
    ("stablecoin_flows", "api"): StablecoinCollector,
    ("crypto_portals", "web_api"): RssCollector,
    ("crypto_portals", "web_rss"): RssCollector,
    ("mainstream_media", "web_rss"): RssCollector,
    ("mainstream_media", "web_api"): RssCollector,
    ("regulators", "web_rss"): RssCollector,
    ("regulators", "web_api"): RssCollector,
}


def resolve_collector_class(spec: SourceSpec) -> type[Collector]:
    platform_key = normalise_platform(spec.platform)
    category_key = spec.category.lower().replace(" ", "_") if spec.category else None
    key: Tuple[str | None, str] = (category_key, platform_key)
    if key in _COLLECTOR_REGISTRY:
        return _COLLECTOR_REGISTRY[key]
    fallback_key = (None, platform_key)
    if fallback_key in _COLLECTOR_REGISTRY:
        return _COLLECTOR_REGISTRY[fallback_key]
    raise CollectorError(
        f"No collector registered for platform='{spec.platform}' category='{spec.category}'"
    )
