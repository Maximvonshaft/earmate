"""Payload factories for simulated collectors."""
from __future__ import annotations

from collections.abc import Callable
from itertools import islice
from typing import Any, Dict, Mapping

from ..config import SourceSpec


def _limit_examples(spec: SourceSpec, count: int = 2) -> list[str]:
    return list(islice(spec.example, count)) or [spec.source]


def _base_payload(spec: SourceSpec, *, content_type: str, preview: str) -> Dict[str, Any]:
    return {
        "content_type": content_type,
        "platform": spec.platform,
        "category": spec.category,
        "preview": preview,
        "entities": _limit_examples(spec, 3),
    }


def _x_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="microblog", preview="Simulated X timeline"),
        "posts": [
            {
                "author": handle,
                "text": f"{handle} mentions a crypto topic in a simulated post",
            }
            for handle in _limit_examples(spec)
        ],
    }


def _telegram_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="broadcast", preview="Telegram channel digest"),
        "messages": [
            {
                "channel": channel,
                "headline": f"Latest alert from {channel}",
            }
            for channel in _limit_examples(spec)
        ],
    }


def _lens_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="web3_social", preview="Lens snapshots"),
        "casts": [
            {
                "profile": profile,
                "summary": f"New insight shared by {profile}",
            }
            for profile in _limit_examples(spec)
        ],
    }


def _video_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="video", preview="Video channel headlines"),
        "videos": [
            {
                "channel": channel,
                "title": f"{channel} uploads a market recap",
            }
            for channel in _limit_examples(spec)
        ],
    }


def _discord_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="chat", preview="Discord incidents feed"),
        "threads": [
            {
                "server": server,
                "topic": f"Operational update from {server}",
            }
            for server in _limit_examples(spec)
        ],
    }


def _reddit_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="forum", preview="Reddit trending threads"),
        "posts": [
            {
                "subreddit": subreddit,
                "title": f"Trending discussion in {subreddit}",
            }
            for subreddit in _limit_examples(spec)
        ],
    }


def _weibo_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="cn_social", preview="Weibo/Wechat bulletin"),
        "accounts": [
            {
                "account": account,
                "summary": f"Latest bulletin from {account}",
            }
            for account in _limit_examples(spec)
        ],
    }

def _rss_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="news", preview="RSS headlines"),
        "headlines": [
            {
                "feed": feed,
                "title": f"Top story from {feed}",
            }
            for feed in _limit_examples(spec)
        ],
    }


def _ws_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="market_ws", preview="Exchange websocket snapshot"),
        "streams": [
            {
                "name": stream,
                "status": "connected",
            }
            for stream in _limit_examples(spec)
        ],
    }


def _status_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="status", preview="Service status summary"),
        "pages": [
            {
                "endpoint": endpoint,
                "state": "operational",
            }
            for endpoint in _limit_examples(spec)
        ],
    }


def _onchain_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="onchain", preview="On-chain metric probe"),
        "metrics": [
            {
                "name": metric,
                "value": 42,
                "unit": "units",
            }
            for metric in _limit_examples(spec)
        ],
    }


def _stablecoin_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="stablecoin", preview="Stablecoin flow summary"),
        "flows": [
            {
                "metric": metric,
                "change": 1_000_000,
            }
            for metric in _limit_examples(spec)
        ],
    }


def _policy_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="policy", preview="Regulatory alert"),
        "documents": [
            {
                "issuer": issuer,
                "title": f"Regulatory update from {issuer}",
            }
            for issuer in _limit_examples(spec)
        ],
    }


def _legal_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="legal", preview="Legal proceedings digest"),
        "cases": [
            {
                "docket": docket,
                "status": "filed",
            }
            for docket in _limit_examples(spec)
        ],
    }

def _project_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="project", preview="Project announcement summary"),
        "updates": [
            {
                "channel": channel,
                "type": "release_note",
            }
            for channel in _limit_examples(spec)
        ],
    }


def _community_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="community", preview="Community forum digest"),
        "topics": [
            {
                "forum": forum,
                "thread": f"Key discussion on {forum}",
            }
            for forum in _limit_examples(spec)
        ],
    }


def _dao_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="dao", preview="DAO governance tracker"),
        "proposals": [
            {
                "space": space,
                "state": "active",
            }
            for space in _limit_examples(spec)
        ],
    }


def _macro_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="macro", preview="Macro calendar digest"),
        "events": [
            {
                "event": event,
                "importance": "high",
            }
            for event in _limit_examples(spec)
        ],
    }


def _research_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="research", preview="Research publications"),
        "reports": [
            {
                "publisher": publisher,
                "title": f"New research from {publisher}",
            }
            for publisher in _limit_examples(spec)
        ],
    }


def _default_payload(spec: SourceSpec) -> Dict[str, Any]:
    return {
        **_base_payload(spec, content_type="generic", preview="Generic feed placeholder"),
        "items": _limit_examples(spec, 5),
    }


PAYLOAD_FACTORIES: Mapping[str, Callable[[SourceSpec], Dict[str, Any]]] = {
    "x": _x_payload,
    "telegram": _telegram_payload,
    "lens_farcaster": _lens_payload,
    "youtube_tiktok": _video_payload,
    "discord_public": _discord_payload,
    "reddit": _reddit_payload,
    "weibo_wechat": _weibo_payload,
    "web_rss": _rss_payload,
    "ws_api": _ws_payload,
    "status_api": _status_payload,
    "node_api": _onchain_payload,
    "stablecoin_flows_api": _stablecoin_payload,
    "regulators_web_rss": _policy_payload,
    "docs_rss": _legal_payload,
    "blog_github_medium": _project_payload,
    "forums": _community_payload,
    "snapshot_forum": _dao_payload,
    "calendars_api": _macro_payload,
    "institutional_research": _research_payload,
    "courts_enforcement_docs_rss": _legal_payload,
}


def normalise_platform(value: str, category: str | None = None) -> str:
    """Normalise a platform string for lookup."""

    cleaned = value.lower().replace("/", "_").replace(" ", "_")
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = cleaned.replace("__", "_")
    if cleaned == "api" and category:
        # differentiate API usage via category context
        return f"{category.lower()}_api"
    return cleaned


def resolve_payload_factory(spec: SourceSpec) -> Callable[[SourceSpec], Dict[str, Any]]:
    """Return an appropriate payload factory for the given spec."""

    platform_key = normalise_platform(spec.platform, spec.category)
    if platform_key not in PAYLOAD_FACTORIES:
        platform_key = f"{spec.category.lower().replace('/', '_')}_{platform_key}"
    if platform_key not in PAYLOAD_FACTORIES:
        platform_key = spec.category.lower().replace("/", "_")
    return PAYLOAD_FACTORIES.get(platform_key, _default_payload)
