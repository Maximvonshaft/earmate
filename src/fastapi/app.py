from __future__ import annotations

from dataclasses import dataclass
from inspect import signature
from typing import Any, Callable, Dict, List, Optional

from .exceptions import HTTPException
from .responses import Response


class _AppState:
    """Container for arbitrary attributes assigned by the application."""

    pass


RouteDecorator = Callable[[Callable[..., Any]], Callable[..., Any]]


@dataclass
class _Route:
    path: str
    method: str
    endpoint: Callable[..., Any]
    status_code: int

    def match(self, method: str, path: str) -> Optional[Dict[str, str]]:
        if self.method != method.upper():
            return None
        route_parts = [part for part in self.path.strip("/").split("/") if part]
        request_parts = [part for part in path.strip("/").split("/") if part]
        if len(route_parts) != len(request_parts):
            return None
        params: Dict[str, str] = {}
        for route_part, request_part in zip(route_parts, request_parts, strict=False):
            if route_part.startswith("{") and route_part.endswith("}"):
                params[route_part[1:-1]] = request_part
                continue
            if route_part != request_part:
                return None
        return params


class FastAPI:
    """Very small subset of the FastAPI interface for unit testing."""

    def __init__(self, *, title: str = "App", version: str = "0.1.0") -> None:
        self.title = title
        self.version = version
        self.state = _AppState()
        self._routes: List[_Route] = []

    def get(self, path: str, *, status_code: int = 200) -> RouteDecorator:
        return self._add_route("GET", path, status_code)

    def post(self, path: str, *, status_code: int = 200) -> RouteDecorator:
        return self._add_route("POST", path, status_code)

    def put(self, path: str, *, status_code: int = 200) -> RouteDecorator:
        return self._add_route("PUT", path, status_code)

    def delete(self, path: str, *, status_code: int = 200) -> RouteDecorator:
        return self._add_route("DELETE", path, status_code)

    def _add_route(self, method: str, path: str, status_code: int) -> RouteDecorator:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._routes.append(
                _Route(
                    path=path,
                    method=method.upper(),
                    endpoint=func,
                    status_code=status_code,
                )
            )
            return func

        return decorator

    def handle_request(
        self, method: str, path: str, body: Optional[Dict[str, Any]] = None
    ) -> Response:
        for route in self._routes:
            params = route.match(method, path)
            if params is None:
                continue
            try:
                kwargs = self._build_kwargs(route.endpoint, params, body)
                result = route.endpoint(**kwargs)
            except HTTPException as exc:
                return Response({"detail": exc.detail}, status_code=exc.status_code)
            if isinstance(result, Response):
                return result
            return Response(result, status_code=route.status_code)
        return Response({"detail": "Not Found"}, status_code=404)

    @staticmethod
    def _build_kwargs(
        endpoint: Callable[..., Any], params: Dict[str, str], body: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        kwargs = dict(params)
        sig = signature(endpoint)
        remaining = [name for name in sig.parameters if name not in kwargs]
        if body is not None and remaining:
            kwargs[remaining[0]] = body
            remaining = remaining[1:]
        for name in remaining:
            param = sig.parameters[name]
            if param.default is param.empty:
                raise TypeError(f"missing required parameter: {name}")
        return kwargs
