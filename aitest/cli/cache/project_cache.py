"""项目上下文持久化缓存。

缓存项目结构信息 (模块列表、页面列表等)，避免每次启动都扫描目录。

存储位置: ~/.alice/cache/<project_id>.json
有效期: 7 天
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

CACHE_DIR = Path.home() / ".alice" / "cache"


class ProjectCache:
    """项目上下文缓存。"""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, project_id: str) -> Optional[dict]:
        """获取缓存的项目上下文。

        Args:
            project_id: 项目 ID

        Returns:
            缓存的项目上下文，如果不存在或过期则返回 None
        """
        cache_file = self._get_cache_file(project_id)
        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if self._is_valid(data):
                return data["context"]
        except (json.JSONDecodeError, KeyError, OSError):
            pass

        return None

    def put(self, project_id: str, context: dict):
        """缓存项目上下文。

        Args:
            project_id: 项目 ID
            context: 项目上下文数据
        """
        cache_file = self._get_cache_file(project_id)
        data = {
            "context": context,
            "updated_at": datetime.now().isoformat(),
            "version": 1,
        }
        cache_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def is_valid(self, project_id: str) -> bool:
        """检查缓存是否有效。

        Args:
            project_id: 项目 ID

        Returns:
            缓存是否有效
        """
        cache_file = self._get_cache_file(project_id)
        if not cache_file.exists():
            return False

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return self._is_valid(data)
        except (json.JSONDecodeError, KeyError, OSError):
            return False

    def invalidate(self, project_id: str):
        """使缓存失效。

        Args:
            project_id: 项目 ID
        """
        cache_file = self._get_cache_file(project_id)
        if cache_file.exists():
            cache_file.unlink()

    def clear(self):
        """清空所有缓存。"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def _get_cache_file(self, project_id: str) -> Path:
        """获取缓存文件路径。"""
        return self.cache_dir / f"{project_id}.json"

    def _is_valid(self, data: dict) -> bool:
        """检查缓存数据是否有效 (7 天内)。"""
        try:
            updated_at = datetime.fromisoformat(data["updated_at"])
            return datetime.now() - updated_at < timedelta(days=7)
        except (KeyError, ValueError):
            return False
