"""Execution helpers for running all collectors."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .collectors.base import CollectorResult
from .collectors.factory import build_collectors
from .config import load_sources


def run_collectors(config_path: Path | str) -> List[CollectorResult]:
    """Load the configuration and run every collector once."""

    groups = load_sources(config_path)
    collectors = build_collectors(groups)
    return [collector.collect() for collector in collectors]


def _format_results(results: Iterable[CollectorResult]) -> str:
    return json.dumps([result.to_dict() for result in results], ensure_ascii=False, indent=2)


def main(config_path: str = "ears.yaml") -> int:
    results = run_collectors(config_path)
    print(_format_results(results))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
