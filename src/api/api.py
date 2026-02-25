
from dotenv import load_dotenv
from fastapi import FastAPI
from typing import Any, Dict, List, cast
from enum import Enum
import re

from pydantic import BaseModel, Field, create_model

from src.api.api_routes import ENDPOINTS
from src.api import endpoints as _endpoints  # noqa: F401

print("Loading API routes...")
print(f"Registered endpoints: {list(ENDPOINTS.keys())}")

load_dotenv()
app = FastAPI(
    title="Salary Agent API service",
    version="1.0.0",
    description="Salary agent endpoints for health checks, report download, and email sending.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

def _route_tags(name: str) -> List[str | Enum]:
    if name.startswith("health"):
        return ["system"]
    if name.startswith("email/"):
        return ["email"]
    if name.startswith("download/"):
        return ["report"]
    return ["api"]


def _make_get_dispatch(handler):
    async def get_dispatch():
        return await handler({})

    return get_dispatch


def _model_name(route_name: str) -> str:
    parts = [part for part in re.split(r"[^a-zA-Z0-9]+", route_name) if part]
    joined = "".join(part.capitalize() for part in parts)
    return f"{joined or 'Dynamic'}Request"


def _build_request_model(route_name: str, required_keys: set[str], optional_defaults: Dict[str, Any]) -> type[BaseModel]:
    fields: Dict[str, tuple[Any, Any]] = {}

    for key in sorted(required_keys):
        fields[key] = (Any, Field(..., description="Required field"))

    for key, default in optional_defaults.items():
        if key in required_keys:
            continue
        fields[key] = (Any, Field(default=default, description="Optional field"))

    if not fields:
        fields["payload"] = (Dict[str, Any] | None, Field(default=None, description="Optional payload object"))

    return create_model(_model_name(route_name), **cast(dict[str, Any], fields))


def _make_body_dispatch(handler, request_model: type[BaseModel]):
    async def body_dispatch(data):
        payload = data.model_dump() if isinstance(data, BaseModel) else data
        if isinstance(payload, dict) and set(payload.keys()) == {"payload"} and payload.get("payload") is None:
            payload = {}
        return await handler(payload)

    body_dispatch.__annotations__["data"] = request_model

    return body_dispatch


def _add_dynamic_route(
    method: str,
    path: str,
    route_name: str,
    handler,
    required_keys: set[str],
    optional_defaults: Dict[str, Any],
    include_in_schema: bool = True,
):
    endpoint_name = route_name.replace("/", "_")
    summary = f"{method} {route_name}"

    if method == "GET":
        get_dispatch = _make_get_dispatch(handler)
        app.add_api_route(
            path,
            get_dispatch,
            methods=["GET"],
            tags=_route_tags(route_name),
            summary=summary,
            name=endpoint_name,
            include_in_schema=include_in_schema,
        )
    elif method == "POST":
        request_model = _build_request_model(route_name, required_keys, optional_defaults)
        post_dispatch = _make_body_dispatch(handler, request_model)
        app.add_api_route(
            path,
            post_dispatch,
            methods=["POST"],
            tags=_route_tags(route_name),
            summary=summary,
            name=endpoint_name,
            include_in_schema=include_in_schema,
        )
    elif method == "PUT":
        request_model = _build_request_model(route_name, required_keys, optional_defaults)
        put_dispatch = _make_body_dispatch(handler, request_model)
        app.add_api_route(
            path,
            put_dispatch,
            methods=["PUT"],
            tags=_route_tags(route_name),
            summary=summary,
            name=endpoint_name,
            include_in_schema=include_in_schema,
        )
    elif method == "DELETE":
        request_model = _build_request_model(route_name, required_keys, optional_defaults)
        delete_dispatch = _make_body_dispatch(handler, request_model)
        app.add_api_route(
            path,
            delete_dispatch,
            methods=["DELETE"],
            tags=_route_tags(route_name),
            summary=summary,
            name=endpoint_name,
            include_in_schema=include_in_schema,
        )
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

# Dynamically add routes based on registered handlers
for name, info in ENDPOINTS.items():
    method = info["method"]
    handler = info["handler"]
    required_keys = info.get("required_keys", set())
    optional_defaults = info.get("optional_defaults", {})

    # Primary namespaced route (shown in Swagger)
    _add_dynamic_route(method, f"/api/{name}", name, handler, required_keys, optional_defaults, include_in_schema=True)
  
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Salary Agent API service.",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }

# register all of 
