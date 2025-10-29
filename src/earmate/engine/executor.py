"""Rule execution primitives."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

from earmate.engine.simple_dom import SimpleElement, parse_html
from earmate.rules.schema import Rule

FetchCallable = Callable[[str], str]


def default_fetch(url: str, *, timeout: float = 10.0) -> str:
    """Fetch HTML content from the target URL using the standard library."""

    request = Request(url, headers={"User-Agent": "earmate/0.1"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - trusted input via rules
        return response.read().decode("utf-8", errors="ignore")


@dataclass
class ExecutionResult:
    """Holds data extracted from a rule execution."""

    items: list[dict[str, Any]]
    metadata: dict[str, Any]


class RuleExecutor:
    """Execute rules against HTTP endpoints using a simple HTML parser."""

    def __init__(self, fetcher: FetchCallable | None = None) -> None:
        self._fetcher = fetcher or default_fetch

    def run(self, rule: Rule) -> ExecutionResult:
        """Execute the provided rule and return structured data."""

        pages = self._collect_pages(rule)
        items: list[dict[str, Any]] = []
        for page_index, html in enumerate(pages, start=1):
            root = parse_html(html)
            for element in root.select(rule.selectors.list):
                extracted = self._extract_fields(element, rule)
                if extracted:
                    extracted.setdefault("__page__", page_index)
                    items.append(extracted)
        metadata = {"pages": len(pages), "rule": rule.name}
        return ExecutionResult(items=items, metadata=metadata)

    def _collect_pages(self, rule: Rule) -> list[str]:
        """Collect HTML documents according to the pagination strategy."""

        pagination = rule.pagination
        pages: list[str] = []
        if pagination.type in {"none", "click", "scroll"}:
            pages.append(self._fetcher(rule.entry))
        if pagination.type == "url":
            start = pagination.start_page
            end = start + pagination.max_pages - 1
            for page_number in range(start, end + 1):
                url = pagination.url_template.format(page=page_number)
                pages.append(self._fetcher(url))
        return pages

    def _extract_fields(self, element: SimpleElement, rule: Rule) -> dict[str, Any]:
        """Extract configured fields from an element."""

        data: dict[str, Any] = {}
        for field_name, selector in rule.selectors.resolved_fields.items():
            target = element.select_one(selector)
            if target is None:
                continue
            if field_name == "url":
                data[field_name] = target.get("href") or target.text.strip()
            else:
                data[field_name] = target.text.strip()
        return data

