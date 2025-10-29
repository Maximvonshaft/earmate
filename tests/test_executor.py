from __future__ import annotations

from dataclasses import replace
from typing import Dict

import pytest

from earmate.engine import RuleExecutor
from earmate.schema import DetailField, DetailRule, RuleSchema, SelectorConfig


@pytest.fixture
def sample_rule() -> RuleSchema:
    return RuleSchema(
        name="sample",
        entry="https://example.com/list",
        selectors=SelectorConfig(
            list="article.item",
            title="h2 a",
            url="h2 a",
            summary="p.summary",
            time="time",
        ),
        detail=DetailRule(
            enabled=True,
            selector="h2 a",
            fields=[
                DetailField(name="content", selector="div.content"),
                DetailField(name="author", selector="span.author"),
            ],
        ),
    )


@pytest.fixture
def html_documents() -> Dict[str, str]:
    return {
        "https://example.com/list": """
            <html>
              <body>
                <article class=\"item\">
                  <h2><a href=\"https://example.com/detail-1\">Item 1</a></h2>
                  <p class=\"summary\">Summary 1</p>
                  <time datetime=\"2024-01-01\">2024-01-01</time>
                </article>
                <article class=\"item\">
                  <h2><a href=\"https://example.com/detail-2\">Item 2</a></h2>
                  <p class=\"summary\">Summary 2</p>
                  <time>Manual date</time>
                </article>
              </body>
            </html>
        """,
        "https://example.com/detail-1": """
            <html>
              <body>
                <div class=\"content\">Detail 1</div>
                <span class=\"author\">Alice</span>
              </body>
            </html>
        """,
        "https://example.com/detail-2": """
            <html>
              <body>
                <div class=\"content\">Detail 2</div>
                <span class=\"author\">Bob</span>
              </body>
            </html>
        """,
    }


@pytest.fixture
def fetcher(html_documents: Dict[str, str]):
    def _fetcher(url: str) -> str:
        return html_documents[url]

    return _fetcher


def test_rule_executor_extracts_list_and_detail(sample_rule: RuleSchema, fetcher) -> None:
    executor = RuleExecutor(sample_rule, fetcher=fetcher)

    result = executor.run()

    assert result.metadata == {"item_count": "2", "detail_count": "2"}
    assert result.records == [
        {
            "title": "Item 1",
            "url": "https://example.com/detail-1",
            "summary": "Summary 1",
            "time": "2024-01-01",
        },
        {
            "title": "Item 2",
            "url": "https://example.com/detail-2",
            "summary": "Summary 2",
            "time": "Manual date",
        },
    ]
    assert result.detail_records == [
        {"content": "Detail 1", "author": "Alice"},
        {"content": "Detail 2", "author": "Bob"},
    ]


def test_executor_handles_missing_detail_anchor(sample_rule: RuleSchema, fetcher) -> None:
    modified_rule = replace(
        sample_rule,
        detail=DetailRule(enabled=True, selector="a.missing", fields=[]),
    )

    executor = RuleExecutor(modified_rule, fetcher=fetcher)
    result = executor.run()

    assert result.detail_records == []
