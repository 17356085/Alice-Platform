"""Small, platform-independent environment loader for the standalone SDK."""

from __future__ import annotations

from pathlib import Path


def load_environment() -> None:
    """Load the nearest project ``.env`` without overriding process values.

    The platform has its own runtime configuration loader, but the SDK is
    also used directly.  Keeping this helper inside ``alice_engine`` avoids a
    reverse dependency on ``aitest`` while making direct provider usage match
    the platform's local-development behavior.
    """
    try:
        from dotenv import find_dotenv, load_dotenv
    except ImportError:
        # python-dotenv is a declared SDK dependency, but a graceful no-op
        # keeps imports useful in deliberately minimal installations.
        return

    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path, override=False)

