"""Compatibility DB-API session — backward compatibility re-export.

get_session() has been moved to aitest.infra.db_session to eliminate circular dependencies.
This file re-exports it for backward compatibility.

Moved: 2026-07-14 (Step 1.1b - circular dependency refactoring)
"""

from aitest.infra.db_session import get_session

__all__ = ["get_session"]
