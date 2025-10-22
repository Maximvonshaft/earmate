"""Simple built-in linting utilities used when external linters are unavailable."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, List

MAX_LINE_LENGTH = 120


class LintError(RuntimeError):
    """Raised when a lint check fails."""


def _iter_python_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from _iter_python_files(sorted(path.iterdir()))
        elif path.suffix == ".py":
            yield path


def _check_line_length(path: Path) -> List[str]:
    errors: List[str] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if len(line) > MAX_LINE_LENGTH:
            errors.append(f"{path}:{index}: line longer than {MAX_LINE_LENGTH} characters")
        if line.rstrip("\n") != line.rstrip():
            errors.append(f"{path}:{index}: trailing whitespace detected")
    return errors


def _check_syntax(path: Path) -> List[str]:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:  # pragma: no cover - extremely rare
        return [f"{path}:{exc.lineno}: syntax error: {exc.msg}"]
    return []


def lint(paths: Iterable[Path]) -> None:
    errors: List[str] = []
    for file_path in _iter_python_files(paths):
        errors.extend(_check_line_length(file_path))
        errors.extend(_check_syntax(file_path))
    if errors:
        raise LintError("\n".join(errors))


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    try:
        lint([project_root / "src", project_root / "tests"])
    except LintError as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
