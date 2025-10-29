"""Simplified execution engine for rule-driven scraping without external dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List
from urllib.parse import urljoin
from urllib.request import urlopen
from xml.etree import ElementTree as ET

from .schema import DetailRule, RuleSchema

HtmlFetcher = Callable[[str], str]


def default_fetcher(url: str) -> str:
    """Fetch HTML content using the standard library."""

    with urlopen(url, timeout=30) as response:  # noqa: S310 - controlled usage
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset)


@dataclass
class ExecutionResult:
    """Container for execution results returned to the caller."""

    records: List[Dict[str, str]]
    detail_records: List[Dict[str, str]]
    metadata: Dict[str, str]


class HtmlDocument:
    """Very small helper around :mod:`xml.etree.ElementTree` for selector queries."""

    def __init__(self, html: str) -> None:
        self.root = ET.fromstring(html)

    def select(self, selector: str) -> List[ET.Element]:
        return list(_select(self.root, selector))

    def select_one(self, selector: str) -> ET.Element | None:
        matches = self.select(selector)
        return matches[0] if matches else None


def _select(root: ET.Element, selector: str) -> List[ET.Element]:
    parts = [_parse_selector_part(part) for part in selector.split() if part]
    if not parts:
        return []

    current = [root]
    for part in parts:
        next_candidates: List[ET.Element] = []
        for candidate in current:
            for element in candidate.iter():
                if _matches(element, part):
                    next_candidates.append(element)
        current = next_candidates
        if not current:
            break
    return current


@dataclass
class _SelectorPart:
    tag: str | None
    class_name: str | None
    attr: str | None
    attr_value: str | None


def _parse_selector_part(raw: str) -> _SelectorPart:
    tag = None
    class_name = None
    attr = None
    attr_value = None

    remainder = raw
    if remainder and remainder[0] not in {".", "["}:
        idx = 0
        while idx < len(remainder) and remainder[idx] not in {".", "["}:
            idx += 1
        tag = remainder[:idx]
        remainder = remainder[idx:]

    if remainder.startswith("."):
        idx = remainder.find("[")
        if idx == -1:
            class_name = remainder[1:]
            remainder = ""
        else:
            class_name = remainder[1:idx]
            remainder = remainder[idx:]

    if remainder.startswith("[") and remainder.endswith("]"):
        content = remainder[1:-1]
        if "=" in content:
            attr, attr_value = content.split("=", 1)
            attr_value = attr_value.strip('"\'')
        else:
            attr = content
            attr_value = None

    return _SelectorPart(
        tag=tag or None,
        class_name=class_name or None,
        attr=attr,
        attr_value=attr_value,
    )


def _matches(element: ET.Element, part: _SelectorPart) -> bool:
    if part.tag and element.tag != part.tag:
        return False
    if part.class_name:
        classes = element.attrib.get("class", "").split()
        if part.class_name not in classes:
            return False
    if part.attr:
        if part.attr_value is None:
            return part.attr in element.attrib
        return element.attrib.get(part.attr) == part.attr_value
    return True


class RuleExecutor:
    """Executes :class:`~earmate.schema.RuleSchema` definitions against HTML pages."""

    def __init__(self, rule: RuleSchema, fetcher: HtmlFetcher | None = None) -> None:
        self.rule = rule
        self.fetcher = fetcher or default_fetcher

    def run(self) -> ExecutionResult:
        current_url = self.rule.entry
        page_index = 1

        records: List[Dict[str, str]] = []
        detail_records: List[Dict[str, str]] = []

        while True:
            list_html = self.fetcher(current_url)
            list_doc = HtmlDocument(list_html)
            list_doc = self._apply_actions(list_doc, current_url)
            list_items = list_doc.select(self.rule.selectors.list)

            for item in list_items:
                record = self._extract_fields(item)
                records.append(record)

                if self.rule.detail and self.rule.detail.enabled:
                    detail_record = self._extract_detail(item, self.rule.detail, current_url)
                    if detail_record:
                        detail_records.append(detail_record)

            if not self._should_continue_pagination(page_index, list_doc, current_url):
                break

            page_index += 1
            pagination_config = self.rule.pagination
            if pagination_config is None:
                break

            if pagination_config.type == "url":
                template = pagination_config.selector or ""
                next_url = _resolve_pagination_url(template, page_index, current_url)
                if not next_url:
                    break
                current_url = next_url
            else:
                next_anchor = list_doc.select_one(pagination_config.selector or "")
                if next_anchor is None:
                    break
                href = _extract_href(next_anchor)
                if not href:
                    break
                current_url = urljoin(current_url, href)

        metadata = {
            "item_count": str(len(records)),
            "pages": str(page_index),
        }
        if self.rule.detail and self.rule.detail.enabled:
            metadata["detail_count"] = str(len(detail_records))

        return ExecutionResult(records=records, detail_records=detail_records, metadata=metadata)

    def _extract_fields(self, item: ET.Element) -> Dict[str, str]:
        selectors = self.rule.selectors
        record: Dict[str, str] = {}

        if selectors.title:
            title_element = _select_single(item, selectors.title)
            record["title"] = _text_content(title_element) if title_element is not None else ""
        if selectors.url:
            url_element = _select_single(item, selectors.url)
            record["url"] = _extract_href(url_element)
        elif selectors.title:
            title_element = _select_single(item, selectors.title)
            record["url"] = _extract_href(title_element)
        if selectors.summary:
            summary_element = _select_single(item, selectors.summary)
            record["summary"] = (
                _text_content(summary_element) if summary_element is not None else ""
            )
        if selectors.time:
            time_element = _select_single(item, selectors.time)
            if time_element is not None:
                record["time"] = time_element.attrib.get("datetime") or _text_content(time_element)
            else:
                record["time"] = ""

        return record

    def _extract_detail(
        self,
        item: ET.Element,
        detail_rule: DetailRule,
        base_url: str,
    ) -> Dict[str, str]:
        if not detail_rule.selector:
            return {}
        anchor = _select_single(item, detail_rule.selector)
        if anchor is None:
            return {}

        href = _extract_href(anchor)
        if not href:
            return {}

        detail_url = urljoin(base_url, href)
        detail_html = self.fetcher(detail_url)
        detail_doc = HtmlDocument(detail_html)

        detail_record: Dict[str, str] = {}
        for field in detail_rule.fields:
            element = detail_doc.select_one(field.selector)
            detail_record[field.name] = _text_content(element) if element is not None else ""
        return detail_record

    def _apply_actions(self, doc: HtmlDocument, current_url: str) -> HtmlDocument:
        for action in self.rule.actions:
            if action.type == "click":
                if not action.selector:
                    continue
                element = doc.select_one(action.selector)
                if element is None:
                    continue
                href = _extract_href(element)
                if not href:
                    continue
                target_url = urljoin(current_url, href)
                html = self.fetcher(target_url)
                doc = HtmlDocument(html)
                current_url = target_url
            elif action.type == "wait":
                # wait is a no-op in the simplified engine but kept for schema compatibility
                continue
            elif action.type == "extract":
                # extraction actions are handled by the core loop; nothing to do here
                continue
        return doc

    def _should_continue_pagination(
        self,
        page_index: int,
        doc: HtmlDocument,
        current_url: str,
    ) -> bool:
        pagination_config = self.rule.pagination
        if not pagination_config:
            return False
        if page_index >= pagination_config.max_pages:
            return False

        if pagination_config.type == "url":
            template = pagination_config.selector or ""
            next_url = _resolve_pagination_url(template, page_index + 1, current_url)
            return bool(next_url)

        if not pagination_config.selector:
            return False
        next_anchor = doc.select_one(pagination_config.selector)
        if next_anchor is None:
            return False
        href = _extract_href(next_anchor)
        return bool(href)


def _select_single(root: ET.Element, selector: str) -> ET.Element | None:
    matches = _select(root, selector)
    return matches[0] if matches else None


def _text_content(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _extract_href(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return element.attrib.get("href", "")


def _resolve_pagination_url(template: str, page_index: int, base_url: str) -> str:
    if not template:
        return ""
    if "{page}" in template:
        try:
            candidate = template.format(page=page_index)
        except KeyError:
            return ""
        if candidate.startswith("http://") or candidate.startswith("https://"):
            return candidate
        return urljoin(base_url, candidate)
    if template.startswith("http://") or template.startswith("https://"):
        return template
    return urljoin(base_url, template)
