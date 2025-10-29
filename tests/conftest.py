from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


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
        "https://example.com/list?page=2": """
            <html>
              <body>
                <article>
                  <h2><a href=\"https://example.com/detail-3\">Item 3</a></h2>
                </article>
              </body>
            </html>
        """,
        "https://example.com/list-with-next": """
            <html>
              <body>
                <article>
                  <h2><a href=\"https://example.com/detail-1\">Item 1</a></h2>
                </article>
                <article>
                  <h2><a href=\"https://example.com/detail-2\">Item 2</a></h2>
                </article>
                <a class=\"next\" href=\"https://example.com/list-with-next?page=2\">Next</a>
              </body>
            </html>
        """,
        "https://example.com/list-with-next?page=2": """
            <html>
              <body>
                <article>
                  <h2><a href=\"https://example.com/detail-3\">Item 3</a></h2>
                </article>
              </body>
            </html>
        """,
        "https://example.com/entry": """
            <html>
              <body>
                <a class=\"jump\" href=\"https://example.com/list-full\">Go</a>
              </body>
            </html>
        """,
        "https://example.com/list-full": """
            <html>
              <body>
                <article>
                  <h2><a href=\"https://example.com/detail-1\">Item 1</a></h2>
                </article>
                <article>
                  <h2><a href=\"https://example.com/detail-2\">Item 2</a></h2>
                </article>
                <article>
                  <h2><a href=\"https://example.com/detail-3\">Item 3</a></h2>
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
        "https://example.com/detail-3": """
            <html>
              <body>
                <div class=\"content\">Detail 3</div>
                <span class=\"author\">Cara</span>
              </body>
            </html>
        """,
    }


@pytest.fixture
def fetcher(html_documents: Dict[str, str]):
    def _fetcher(url: str) -> str:
        return html_documents[url]

    return _fetcher
