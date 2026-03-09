from __future__ import annotations

from src.api.api_routes import register
from src.dependencies import get_user_repository
from src.service.auth_service import get_current_user, login_user, register_user


@register(
    name="auth/register",
    method="POST",
    required_keys=["name", "email", "password"],
    optional_keys={"role": "user"},
)
async def auth_register(data: dict):
    repository = get_user_repository()
    try:
        return register_user(
            repository=repository,
            name=str(data["name"]),
            email=str(data["email"]),
            password=str(data["password"]),
            role=str(data.get("role") or "user"),
        )
    finally:
        repository.db_session.close()


@register(
    name="auth/login",
    method="POST",
    required_keys=["email", "password"],
    optional_keys={},
)
async def auth_login(data: dict):
    repository = get_user_repository()
    try:
        return login_user(
            repository=repository,
            email=str(data["email"]),
            password=str(data["password"]),
        )
    finally:
        repository.db_session.close()


@register(
    name="auth/me",
    method="GET",
    required_keys=[],
    optional_keys={},
)
async def auth_me(data: dict):
    repository = get_user_repository()
    try:
        token = str(data.get("token") or "").strip()
        return get_current_user(repository=repository, token=token)
    finally:
        repository.db_session.close()
