"""Earmate collector simulation package."""

from .config import load_sources, SourceGroup, SourceSpec
from .runner import run_collectors

__all__ = [
    "load_sources",
    "run_collectors",
    "SourceGroup",
    "SourceSpec",
]
