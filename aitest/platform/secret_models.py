"""Secret ORM Models — backward compatibility re-export.

Moved: 2026-07-14 to aitest.infra.models.secret (Step 2.1 - eliminate infra → platform dependency)
This file re-exports for backward compatibility.
"""

from aitest.infra.models.secret import SecretModel, SecretAuditLogModel

__all__ = ["SecretModel", "SecretAuditLogModel"]
