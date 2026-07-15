"""Platform config registry — extends infra config with platform-specific settings.

Platform-level configuration that depends on platform modules. Extends the base
PlatformConfig from infra with governance/policy settings.
"""

from aitest.infra.config_registry import PlatformConfig as _BasePlatformConfig, cfg as _base_cfg


class PlatformConfigExtended(_BasePlatformConfig):
    """Extended platform config with governance policy version."""

    @property
    def governance_policy_version(self) -> str:
        """Current governance/policy version used by the runtime."""
        from aitest.platform.versioning import resolve_policy_version
        return resolve_policy_version()


# Singleton instance with extended functionality
cfg = PlatformConfigExtended()

# Re-export base class for backward compatibility
PlatformConfig = _BasePlatformConfig

__all__ = ["PlatformConfig", "cfg"]
