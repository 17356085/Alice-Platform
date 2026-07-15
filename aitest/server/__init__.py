"""AI Test Platform — FastAPI 服务层。"""

from importlib import import_module


def __getattr__(name):
    """Lazily expose ``aitest.server.main`` for tooling and compatibility."""
    if name == "main":
        module = import_module(".main", __name__)
        globals()[name] = module
        return module
    raise AttributeError(name)


__all__ = ["main"]
