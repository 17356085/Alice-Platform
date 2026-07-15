"""ModelProvider ORM Model — backward compatibility re-export.

Moved: 2026-07-14 to aitest.infra.models.model_provider (Step 2.1 - eliminate infra → platform dependency)
This file re-exports for backward compatibility.
"""

from aitest.infra.models.model_provider import ModelProviderModel

__all__ = ["ModelProviderModel"]
