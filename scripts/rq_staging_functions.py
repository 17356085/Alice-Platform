"""Importable local functions used by the RQ staging probe."""


def stage_success(
    agent_name: str,
    provider: str = "mock",
    module: str = "",
    page: str = "",
    mode: str = "full",
) -> dict:
    return {
        "agent_name": agent_name,
        "provider": provider,
        "module": module,
        "page": page,
        "mode": mode,
    }


def stage_failure(
    agent_name: str,
    provider: str = "mock",
    module: str = "",
    page: str = "",
    mode: str = "full",
) -> dict:
    raise RuntimeError(f"staging failure mode={mode}")
