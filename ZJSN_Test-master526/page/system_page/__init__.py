"""系统管理模块 Page Object

⚠️ RoleManagePage 已迁移至 page.system_role_page。
   此处保留 re-export 以兼容 tools/ 旧脚本，后续版本将移除。
"""
import warnings
warnings.warn(
    "page.system_page.RoleManagePage is deprecated, use page.system_role_page.RoleManagePage",
    DeprecationWarning,
    stacklevel=2,
)
from page.system_role_page.RoleManagePage import RoleManagePage  # noqa: F401 — 向后兼容 shim
