"""
Onboarding package — project auto-discovery from URL to ready-to-test.

Phase B: User provides URL + credentials → TLO auto-discovers app structure.

Modules:
  project_onboarding_agent.py   Main orchestrator
"""

from .project_onboarding_agent import (
    ProjectOnboardingAgent,
    OnboardingState,
    OnboardingStep,
    get_session,
)
