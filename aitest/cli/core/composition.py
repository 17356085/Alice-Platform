"""CLI composition root helpers.

Phase 8 keeps CLI entrypoints on a single resolution path for project,
runtime, and execution services.
"""

from __future__ import annotations

import os
from pathlib import Path

from alice_engine.core.runtime_environment import runtime_environment_scope


def resolve_cli_project_dir(project_path: str | None) -> Path:
    """Resolve the active CLI project directory."""
    if project_path:
        project_dir = Path(project_path)
    else:
        from aitest.cli.config import CLIConfig

        config = CLIConfig()
        active = config.active_project_path
        if not active:
            raise ValueError("未指定项目路径，请使用 --project-path 或 alice project set --id=<id>")
        project_dir = Path(active)

    if not project_dir.exists():
        raise FileNotFoundError(f"项目路径不存在: {project_dir}")
    return project_dir


def resolve_cli_provider(llm_provider: str | None) -> str:
    """Resolve the provider without mutating global env."""
    return llm_provider or os.environ.get("LLM_PROVIDER") or os.environ.get("AITEST_PROVIDER", "deepseek")


def cli_runtime_scope(project_dir: Path, provider: str, mock_llm: bool):
    """Scope runtime settings for a CLI execution."""
    return runtime_environment_scope(
        workstudy=project_dir,
        llm_provider=provider,
        mock_llm=mock_llm,
    )


def get_cli_execution_service():
    """Resolve the shared platform ExecutionService for CLI commands."""
    from aitest.platform.execution_service import ExecutionService

    return ExecutionService()
