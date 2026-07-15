"""Quality Loop Resources — backward compatibility re-export.

Moved: 2026-07-14 to aitest.infra.models.quality (Step 2.1 - eliminate infra → platform dependency)
This file re-exports for backward compatibility.
"""

from aitest.infra.models.quality import DatasetModel, EvaluationModel, ExperimentModel

__all__ = ["DatasetModel", "EvaluationModel", "ExperimentModel"]
