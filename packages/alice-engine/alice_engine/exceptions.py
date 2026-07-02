"""Alice Engine 异常层次。"""


class AliceError(Exception):
    """Alice Engine 基础异常。"""


class ConfigError(AliceError):
    """配置错误。"""


class ProjectNotFoundError(ConfigError):
    """项目目录不存在或缺少 project.yaml。"""


class ModuleNotFoundError(AliceError):
    """模块不存在。"""


class ExecutionError(AliceError):
    """SOP 执行失败。"""


class LLMProviderError(AliceError):
    """LLM Provider 错误。"""


class ExtensionError(AliceError):
    """Extension 执行错误。"""
