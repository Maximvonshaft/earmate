"""Minimal HTML parsing helpers used by the executor."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class SimpleElement:
    """Lightweight tree node with very small CSS selector support."""

    tag: str
    attrs: dict[str, str]
    parent: SimpleElement | None
    children: list[SimpleElement] = field(default_factory=list)
    _text_chunks: list[str] = field(default_factory=list)

    def append_child(self, child: SimpleElement) -> None:
        self.children.append(child)

    def append_text(self, text: str) -> None:
        self._text_chunks.append(text)

    def select(self, selector: str) -> list[SimpleElement]:
        tokens = [token for token in selector.strip().split() if token]
        current: list[SimpleElement] = [self]
        for token in tokens:
            matched: list[SimpleElement] = []
            for node in current:
                matched.extend(_match_descendants(node, token))
            current = matched
        return current

    def select_one(self, selector: str) -> SimpleElement | None:
        matches = self.select(selector)
        return matches[0] if matches else None

    def iter_descendants(self) -> Iterable[SimpleElement]:
        for child in self.children:
            yield child
            yield from child.iter_descendants()

    @property
    def text(self) -> str:
        parts: list[str] = []
        parts.extend(self._text_chunks)
        for child in self.children:
            parts.append(child.text)
        return "".join(parts)

    def get(self, attr: str, default: str | None = None) -> str | None:
        return self.attrs.get(attr, default)

    @property
    def classes(self) -> set[str]:
        value = self.attrs.get("class", "")
        return {item for item in value.split() if item}


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = SimpleElement(tag="document", attrs={}, parent=None)
        self._stack: list[SimpleElement] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {name: (value or "") for name, value in attrs}
        element = SimpleElement(tag=tag, attrs=attr_dict, parent=self._stack[-1])
        self._stack[-1].append_child(element)
        self._stack.append(element)

    def handle_endtag(self, tag: str) -> None:  # noqa: D401 - HTMLParser API
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                break

    def handle_data(self, data: str) -> None:  # noqa: D401 - HTMLParser API
        if data:
            self._stack[-1].append_text(data)


def parse_html(html: str) -> SimpleElement:
    parser = _TreeBuilder()
    parser.feed(html)
    parser.close()
    return parser.root


def _match_descendants(node: SimpleElement, token: str) -> list[SimpleElement]:
    matches: list[SimpleElement] = []
    for candidate in node.iter_descendants():
        if _matches_token(candidate, token):
            matches.append(candidate)
    if _matches_token(node, token):
        matches.insert(0, node)
    return matches


def _matches_token(element: SimpleElement, token: str) -> bool:
    if token == "*":
        return True
    tag, classes = _parse_token(token)
    if tag and element.tag != tag:
        return False
    if classes and not classes.issubset(element.classes):
        return False
    return True


def _parse_token(token: str) -> tuple[str | None, set[str]]:
    if token.startswith("."):
        tag = None
        class_part = token[1:]
    else:
        parts = token.split(".")
        tag = parts[0] if parts[0] else None
        class_part = "".join(parts[1:]) if len(parts) > 1 else ""
    classes = {item for item in class_part.split(".") if item}
    return tag, classes

