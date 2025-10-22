"""Configuration loader for ears.yaml sources."""
from __future__ import annotations

from ast import literal_eval
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List


@dataclass(slots=True)
class SourceSpec:
    """Normalized definition for a single upstream source."""

    category: str
    platform: str
    source: str
    example: List[str] = field(default_factory=list)
    method: str | None = None
    interval: str | None = None
    throttle: Dict[str, Any] = field(default_factory=dict)
    weight_hint: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    notes: str | None = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.example, str):
            self.example = [self.example]
        if isinstance(self.tags, str):
            self.tags = [self.tags]
        self.raw = {
            "category": self.category,
            "platform": self.platform,
            "source": self.source,
            "example": self.example,
            "method": self.method,
            "interval": self.interval,
            "throttle": self.throttle,
            "weight_hint": self.weight_hint,
            "tags": self.tags,
            "notes": self.notes,
        }


@dataclass(slots=True)
class SourceGroup:
    """Group of sources under a top-level key (e.g., social_sources)."""

    name: str
    specs: List[SourceSpec]

    def __iter__(self) -> Iterable[SourceSpec]:  # pragma: no cover - convenience helper
        return iter(self.specs)

    def __len__(self) -> int:
        return len(self.specs)


def _parse_inline_dict(value: str) -> Dict[str, Any]:
    inner = value.strip()[1:-1].strip()
    if not inner:
        return {}

    items: List[str] = []
    depth = 0
    current: List[str] = []
    for char in inner:
        if char == "," and depth == 0:
            items.append("".join(current).strip())
            current = []
            continue
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth = max(depth - 1, 0)
        current.append(char)
    if current:
        items.append("".join(current).strip())

    result: Dict[str, Any] = {}
    for item in items:
        if not item:
            continue
        if ":" not in item:
            continue
        key, raw_value = item.split(":", 1)
        key = key.strip().strip('"')
        result[key] = _parse_value(raw_value.strip())
    return result


def _parse_value(value: str) -> Any:
    if not value:
        return None
    if value.startswith("{") and value.endswith("}"):
        return _parse_inline_dict(value)
    if value.startswith("[") and value.endswith("]"):
        try:
            return literal_eval(value)
        except (SyntaxError, ValueError):
            return [part.strip() for part in value.strip("[]").split(",") if part.strip()]
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return literal_eval(value)
    except (SyntaxError, ValueError, NameError):
        return value


def _parse_config_text(text: str) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    current_group: str | None = None
    current_entry: Dict[str, Any] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and stripped.endswith(":"):
            current_group = stripped[:-1]
            groups[current_group] = []
            current_entry = None
            continue
        if current_group is None:
            continue
        if stripped.startswith("- "):
            current_entry = {}
            groups[current_group].append(current_entry)
            remainder = stripped[2:]
            if remainder:
                if ":" in remainder:
                    key, value = remainder.split(":", 1)
                    current_entry[key.strip()] = _parse_value(value.strip())
            continue
        if current_entry is None:
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        current_entry[key.strip()] = _parse_value(value.strip())
    return groups


def _normalize_source(entry: Dict[str, Any]) -> SourceSpec:
    """Normalize a raw YAML entry into a :class:`SourceSpec`."""

    cleaned_entry = dict(entry)
    example = cleaned_entry.get("example", []) or []
    tags = cleaned_entry.get("tags", []) or []
    throttle = cleaned_entry.get("throttle", {}) or {}
    weight_hint = cleaned_entry.get("weight_hint", {}) or {}

    return SourceSpec(
        category=str(cleaned_entry.get("category", "unknown")),
        platform=str(cleaned_entry.get("platform", "unknown")),
        source=str(cleaned_entry.get("source", "unknown")),
        example=list(example) if isinstance(example, list) else [example],
        method=cleaned_entry.get("method"),
        interval=cleaned_entry.get("interval"),
        throttle=dict(throttle),
        weight_hint=dict(weight_hint),
        tags=list(tags) if isinstance(tags, list) else [tags],
        notes=cleaned_entry.get("notes"),
    )


def load_sources(config_path: Path | str) -> List[SourceGroup]:
    """Load the YAML file and return a list of :class:`SourceGroup` objects."""

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    data = _parse_config_text(path.read_text(encoding="utf-8"))

    groups: List[SourceGroup] = []
    for name, entries in data.items():
        if not entries:
            continue
        specs = [_normalize_source(entry) for entry in entries]
        groups.append(SourceGroup(name=name, specs=specs))
    return groups


def count_sources(groups: Iterable[SourceGroup]) -> int:
    """Helper that counts how many sources are defined across groups."""

    return sum(len(group) for group in groups)
