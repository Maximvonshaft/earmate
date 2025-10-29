from __future__ import annotations

from dataclasses import replace

import pytest

from earmate.engine import RuleExecutor
from earmate.schema import (
    Action,
    DetailField,
    DetailRule,
    PaginationConfig,
    RuleSchema,
    SelectorConfig,
)


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


def test_rule_executor_extracts_list_and_detail(sample_rule: RuleSchema, fetcher) -> None:
    executor = RuleExecutor(sample_rule, fetcher=fetcher)

    result = executor.run()

    assert result.metadata == {"item_count": "2", "pages": "1", "detail_count": "2"}
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


def test_executor_handles_url_template_pagination(fetcher) -> None:
    rule = RuleSchema(
        name="pagination",
        entry="https://example.com/list",
        selectors=SelectorConfig(list="article", title="h2", url="h2 a"),
        pagination=PaginationConfig(
            type="url",
            selector="https://example.com/list?page={page}",
            max_pages=2,
        ),
    )

    executor = RuleExecutor(rule, fetcher=fetcher)
    result = executor.run()

    urls = [record["url"] for record in result.records]
    assert urls == ["https://example.com/detail-1", "https://example.com/detail-2", "https://example.com/detail-3"]
    assert result.metadata["pages"] == "2"


def test_executor_handles_click_pagination(fetcher) -> None:
    rule = RuleSchema(
        name="click-pagination",
        entry="https://example.com/list-with-next",
        selectors=SelectorConfig(list="article", title="h2", url="h2 a"),
        pagination=PaginationConfig(type="click", selector="a.next", max_pages=2),
    )

    executor = RuleExecutor(rule, fetcher=fetcher)
    result = executor.run()

    assert result.metadata["pages"] == "2"
    assert len(result.records) == 3


def test_executor_runs_click_actions(fetcher) -> None:
    rule = RuleSchema(
        name="action",
        entry="https://example.com/entry",
        selectors=SelectorConfig(list="article", title="h2", url="h2 a"),
        actions=[Action(type="click", selector="a.jump")],
    )

    executor = RuleExecutor(rule, fetcher=fetcher)
    result = executor.run()

    assert [record["url"] for record in result.records] == [
        "https://example.com/detail-1",
        "https://example.com/detail-2",
        "https://example.com/detail-3",
    ]
