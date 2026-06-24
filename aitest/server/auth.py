"""
API Authentication — Bearer token middleware for FastAPI.

Supports:
  1. Static API Key (AITEST_API_KEY env var) — simple, single-key
  2. (Future) SQLite-backed multi-key store with scopes

Usage:
    from aitest.server.auth import auth_middleware, require_auth

    # Middleware: applied globally in main.py
    app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

    # Decorator: require auth on specific routes
    @router.get("/protected")
    @require_auth
    async def protected():
        ...

Security:
  - Exempt paths: /health, /docs, /openapi.json, / (root)
  - Token in Authorization: Bearer <key> header
  - Constant-time comparison to prevent timing attacks
"""

import os
from functools import wraps
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

# ── Exempt paths (no auth required) ───────────────────────────────────
_EXEMPT_PREFIXES = ("/health", "/docs", "/openapi.json", "/static", "/ws/")
_EXEMPT_EXACT = {"/", ""}


def _is_exempt(path: str) -> bool:
    """Check if path is exempt from authentication."""
    if path in _EXEMPT_EXACT:
        return True
    for prefix in _EXEMPT_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _get_api_key() -> str:
    """Get configured API key. Returns empty string if auth is disabled."""
    from aitest.config import config
    return os.environ.get("AITEST_API_KEY", "")


# ── Constant-time comparison ──────────────────────────────────────────

def _secure_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


# ── Auth middleware (for BaseHTTPMiddleware) ──────────────────────────

async def auth_middleware(request: Request, call_next):
    """FastAPI middleware: validate Bearer token on protected routes.

    Auth chain:
      1. Static AITEST_API_KEY env var (global admin key)
      2. Organization API keys via OrganizationManager.validate_api_key()
      3. If neither configured → auth disabled, allow all

    Sets request.state on successful auth:
      - request.state.user_id
      - request.state.org_id
      - request.state.scopes
      - request.state.auth_method ("static" | "org_key")

    Apply in main.py:
        from fastapi.middleware.base import BaseHTTPMiddleware
        app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
    """
    path = request.url.path

    if _is_exempt(path):
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")

    # No auth header → check if auth is required
    if not auth_header.startswith("Bearer "):
        api_key = _get_api_key()
        if not api_key:
            # Auth disabled — allow all requests
            return await call_next(request)
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing Authorization: Bearer <token> header"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header[7:]  # strip "Bearer "

    # 1. Try static admin key first
    static_key = _get_api_key()
    if static_key and _secure_compare(token, static_key):
        request.state.user_id = "admin"
        request.state.org_id = "*"
        request.state.scopes = ["read", "write", "execute", "admin"]
        request.state.auth_method = "static"
        return await call_next(request)

    # 2. Fall through to Organization API keys
    try:
        from aitest.platform.organization import get_org_manager
        org_mgr = get_org_manager()
        result = org_mgr.validate_api_key(token)
        if result:
            request.state.user_id = f"apikey:{result['key_id']}"
            request.state.org_id = result["org_id"]
            request.state.scopes = result.get("scopes", ["read", "execute"])
            request.state.auth_method = "org_key"
            return await call_next(request)
    except Exception:
        pass  # OrgManager unavailable → fall through to 401

    # 3. No valid key found
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid API key"},
        headers={"WWW-Authenticate": "Bearer"},
    )


# ── Decorator for per-route protection ────────────────────────────────

def require_auth(func):
    """Decorator: require valid Bearer token on this route.

    Usage:
        @router.get("/admin")
        @require_auth
        async def admin_endpoint(request: Request):
            ...
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        path = request.url.path
        if _is_exempt(path):
            return await func(request, *args, **kwargs)

        api_key = _get_api_key()
        if not api_key:
            return await func(request, *args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")

        token = auth_header[7:]
        if not _secure_compare(token, api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

        return await func(request, *args, **kwargs)

    return wrapper


# ── Helper: generate a secure API key ─────────────────────────────────

def generate_api_key() -> str:
    """Generate a cryptographically secure API key.

    Usage:
        python -c "from aitest.server.auth import generate_api_key; print(generate_api_key())"
    """
    import secrets
    return "aitest_" + secrets.token_urlsafe(32)
