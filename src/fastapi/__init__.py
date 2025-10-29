"""Lightweight FastAPI-compatible facade for offline testing environments."""

from . import status
from .app import Depends, FastAPI, Header
from .exceptions import HTTPException
from .responses import Response

__all__ = ["FastAPI", "HTTPException", "Response", "status", "Depends", "Header"]
