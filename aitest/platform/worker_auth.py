"""HMAC bearer tokens for remote Worker API calls."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass


class WorkerAuthError(ValueError):
    """Raised when a Worker token is missing or invalid."""


@dataclass(frozen=True)
class WorkerClaims:
    worker_id: str
    org_id: str
    expires_at: int


def auth_required() -> bool:
    return os.environ.get("AITEST_WORKER_AUTH_REQUIRED", "0").lower() in {"1", "true", "yes"}


def issue_token(worker_id: str, org_id: str, ttl_seconds: int = 3600) -> str:
    secret = os.environ.get("AITEST_WORKER_AUTH_SECRET", "")
    if not secret:
        raise WorkerAuthError("AITEST_WORKER_AUTH_SECRET is not configured")
    payload = {
        "worker_id": worker_id,
        "org_id": org_id,
        "exp": int(time.time()) + max(60, ttl_seconds),
    }
    encoded = _encode(payload)
    signature = _sign(encoded, secret)
    return f"{encoded}.{signature}"


def verify_token(token: str, worker_id: str, org_id: str) -> WorkerClaims:
    secret = os.environ.get("AITEST_WORKER_AUTH_SECRET", "")
    if not secret:
        raise WorkerAuthError("Worker authentication is enabled without a shared secret")
    try:
        encoded, provided = token.split(".", 1)
    except (ValueError, AttributeError) as exc:
        raise WorkerAuthError("Malformed Worker token") from exc
    expected = _sign(encoded, secret)
    if not hmac.compare_digest(provided, expected):
        raise WorkerAuthError("Invalid Worker token signature")
    try:
        payload = json.loads(_decode(encoded))
        claims = WorkerClaims(str(payload["worker_id"]), str(payload["org_id"]), int(payload["exp"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise WorkerAuthError("Malformed Worker token") from exc
    if claims.expires_at <= int(time.time()):
        raise WorkerAuthError("Worker token expired")
    if claims.worker_id != worker_id or claims.org_id != org_id:
        raise WorkerAuthError("Worker token scope mismatch")
    return claims


def validate_request_token(token: str | None, worker_id: str, org_id: str) -> WorkerClaims | None:
    if not auth_required():
        return None
    if not token:
        raise WorkerAuthError("Bearer Worker token is required")
    return verify_token(token, worker_id, org_id)


def _encode(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode(encoded: str) -> str:
    return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode("utf-8")


def _sign(encoded: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
