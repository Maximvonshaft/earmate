from __future__ import annotations

from earmate.engine.executor import RuleExecutor
from earmate.rules.schema import PaginationConfig, Rule, RuleSelectors

SIMPLE_HTML = """
<html>
  <body>
    <article class="item">
      <h2><a href="https://example.com/a">First</a></h2>
      <p class="desc">Alpha</p>
    </article>
    <article class="item">
      <h2><a href="https://example.com/b">Second</a></h2>
      <p class="desc">Beta</p>
    </article>
  </body>
</html>
"""


def fake_fetch(_: str) -> str:
    return SIMPLE_HTML


def test_executor_extracts_fields() -> None:
    rule = Rule(
        name="demo",
        entry="https://example.com",
        selectors=RuleSelectors(
            list="article.item",
            fields={"title": "h2 a", "summary": "p.desc"},
            url="h2 a",
        ),
        pagination=PaginationConfig(type="none"),
    )
    executor = RuleExecutor(fetcher=fake_fetch)
    result = executor.run(rule)

    assert len(result.items) == 2
    assert result.items[0]["title"] == "First"
    assert result.items[0]["summary"] == "Alpha"
    assert result.items[0]["url"] == "https://example.com/a"
    assert result.metadata["pages"] == 1
    assert result.metadata["rule"] == "demo"


def test_url_pagination_fetches_multiple_pages() -> None:
    captured_urls: list[str] = []

    def fetch(url: str) -> str:
        captured_urls.append(url)
        return SIMPLE_HTML.replace("Alpha", url)

    rule = Rule(
        name="demo",
        entry="https://example.com",
        selectors=RuleSelectors(list="article.item", fields={"title": "h2 a"}),
        pagination=PaginationConfig(
            type="url",
            url_template="https://example.com/page/{page}",
            start_page=1,
            max_pages=2,
        ),
    )

    executor = RuleExecutor(fetcher=fetch)
    result = executor.run(rule)

    assert captured_urls == [
        "https://example.com/page/1",
        "https://example.com/page/2",
    ]
    assert len(result.items) == 4
    assert all(item["__page__"] in {1, 2} for item in result.items)
