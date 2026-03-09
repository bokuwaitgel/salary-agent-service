from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from src.repositories.database import UserRepository

load_dotenv()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def _get_auth_secret() -> str:
    return (
        os.getenv("AUTH_SECRET")
        or os.getenv("API_SECRET")
        or os.getenv("JWT_SECRET")
        or "change-this-auth-secret"
    )


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"{salt}${pwd_hash.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        salt, stored_hash = encoded_hash.split("$", 1)
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return hmac.compare_digest(candidate, stored_hash)


def create_access_token(payload: Dict[str, Any], expires_minutes: int = 60 * 24) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    exp = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    token_payload = {**payload, "exp": int(exp.timestamp())}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(token_payload, separators=(",", ":")).encode("utf-8"))

    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(_get_auth_secret().encode("utf-8"), message, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid token format")

    header_b64, payload_b64, signature_b64 = parts
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(_get_auth_secret().encode("utf-8"), message, hashlib.sha256).digest()

    if not hmac.compare_digest(_b64url_encode(expected_sig), signature_b64):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    exp = int(payload.get("exp", 0))
    if exp <= int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=401, detail="Token expired")

    return payload


def _user_public(user) -> Dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def register_user(repository: UserRepository, name: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
    normalized_email = email.strip().lower()
    if repository.get_by_email(normalized_email):
        raise HTTPException(status_code=409, detail="Email is already registered")

    payload = {
        "id": secrets.token_hex(16),
        "name": name.strip(),
        "email": normalized_email,
        "password_hash": hash_password(password),
        "role": role,
    }

    try:
        user = repository.create(payload)
    except IntegrityError:
        repository.db_session.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered")

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return {"token": token, "token_type": "bearer", "user": _user_public(user)}


def login_user(repository: UserRepository, email: str, password: str) -> Dict[str, Any]:
    normalized_email = email.strip().lower()
    user = repository.get_by_email(normalized_email)
    if not user or not verify_password(password, str(user.password_hash)):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "email": str(user.email), "role": str(user.role)})
    return {"token": token, "token_type": "bearer", "user": _user_public(user)}


def get_current_user(repository: UserRepository, token: str) -> Dict[str, Any]:
    payload = decode_access_token(token.strip())
    user_id = str(payload.get("sub", "")).strip()
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = repository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return _user_public(user)
