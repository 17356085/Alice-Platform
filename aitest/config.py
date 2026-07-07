# Re-export — 原 config.py 已搬到 runtime/config.py，此文件保证向后兼容
# 所有 `from aitest.config import config` 仍然有效
from aitest.runtime.config import RuntimeConfig, config, _env, _env_int  # noqa: F401

# 向后兼容别名
Config = RuntimeConfig
