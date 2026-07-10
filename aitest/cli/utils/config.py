"""
CLI 配置优先级统一工具。

优先级顺序: CLI 参数 > 环境变量 > 配置文件 > 默认值
"""

import os
from typing import Any, Optional
from pathlib import Path
import yaml


class ConfigResolver:
    """统一配置解析器。"""

    def __init__(self, config_file: Optional[Path] = None):
        """
        初始化配置解析器。

        Args:
            config_file: 配置文件路径（默认: ~/.aitest/config.yaml）
        """
        self.config_file = config_file or Path.home() / ".aitest" / "config.yaml"
        self._config_data = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件。"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def resolve(
        self,
        cli_value: Any,
        env_var: Optional[str] = None,
        config_key: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        统一配置解析逻辑。

        优先级: CLI 参数 > 环境变量 > 配置文件 > 默认值

        Args:
            cli_value: CLI 参数值（可能为 None）
            env_var: 环境变量名
            config_key: 配置文件键（支持嵌套，如 "defaults.llm_provider"）
            default: 默认值

        Returns:
            解析后的配置值

        Example:
            >>> resolver = ConfigResolver()
            >>> resolver.resolve(
            ...     cli_value=None,
            ...     env_var="AITEST_LLM_PROVIDER",
            ...     config_key="defaults.llm_provider",
            ...     default="claude"
            ... )
            'claude'
        """
        # 1. CLI 参数优先级最高
        if cli_value is not None:
            return cli_value

        # 2. 环境变量次之
        if env_var:
            env_value = os.getenv(env_var)
            if env_value is not None:
                return self._cast_type(env_value, type(default) if default is not None else str)

        # 3. 配置文件
        if config_key:
            config_value = self._get_nested_config(config_key)
            if config_value is not None:
                return config_value

        # 4. 默认值
        return default

    def _get_nested_config(self, key: str) -> Any:
        """
        获取嵌套配置键。

        Args:
            key: 嵌套键，如 "defaults.llm_provider"

        Returns:
            配置值，如果不存在返回 None
        """
        keys = key.split('.')
        value = self._config_data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value

    def _cast_type(self, value: str, target_type: type) -> Any:
        """
        类型转换（用于环境变量）。

        Args:
            value: 字符串值
            target_type: 目标类型

        Returns:
            转换后的值
        """
        if target_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        else:
            return value

    def set(self, key: str, value: Any):
        """
        设置配置值（写入配置文件）。

        Args:
            key: 配置键（支持嵌套，如 "defaults.llm_provider"）
            value: 配置值
        """
        keys = key.split('.')
        data = self._config_data

        # 导航到目标位置
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        # 设置值
        data[keys[-1]] = value

        # 写回文件
        self._save_config()

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值。

        Args:
            key: 配置键（支持嵌套）
            default: 默认值

        Returns:
            配置值
        """
        value = self._get_nested_config(key)
        return value if value is not None else default

    def reset(self, key: Optional[str] = None):
        """
        重置配置。

        Args:
            key: 要重置的键（None 表示重置全部）
        """
        if key is None:
            self._config_data = {}
        else:
            keys = key.split('.')
            data = self._config_data
            for k in keys[:-1]:
                if k not in data:
                    return  # 键不存在，无需重置
                data = data[k]
            if keys[-1] in data:
                del data[keys[-1]]

        self._save_config()

    def _save_config(self):
        """保存配置到文件。"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self._config_data, f, default_flow_style=False)


# 全局单例
_resolver: Optional[ConfigResolver] = None


def get_resolver() -> ConfigResolver:
    """获取全局配置解析器。"""
    global _resolver
    if _resolver is None:
        _resolver = ConfigResolver()
    return _resolver
