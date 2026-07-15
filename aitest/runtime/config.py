"""Backward-compatible runtime configuration import path."""

from aitest.config import Config, RuntimeConfig, _env, _env_int, config

__all__ = ["Config", "RuntimeConfig", "config", "_env", "_env_int"]
