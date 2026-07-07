"""文件内容缓存 (LRU 策略)。

缓存最近访问的文件内容，避免重复读取磁盘。

配置:
  - max_files: 最大文件数 (默认 50)
  - max_size_mb: 最大大小 (默认 10MB)
"""

from collections import OrderedDict
from typing import Optional


class FileCache:
    """文件内容缓存 (LRU 策略)。"""

    def __init__(self, max_files: int = 50, max_size_mb: int = 10):
        """初始化文件缓存。

        Args:
            max_files: 最大文件数
            max_size_mb: 最大大小 (MB)
        """
        self.max_files = max_files
        self.max_size = max_size_mb * 1024 * 1024
        self.cache: OrderedDict[str, str] = OrderedDict()
        self.current_size = 0

    def get(self, file_path: str) -> Optional[str]:
        """获取缓存的文件内容。

        Args:
            file_path: 文件路径

        Returns:
            缓存的文件内容，如果不存在则返回 None
        """
        if file_path in self.cache:
            # 移动到最近使用
            self.cache.move_to_end(file_path)
            return self.cache[file_path]
        return None

    def put(self, file_path: str, content: str):
        """缓存文件内容。

        Args:
            file_path: 文件路径
            content: 文件内容
        """
        content_size = len(content.encode("utf-8"))

        # 如果文件已存在，先移除旧缓存
        if file_path in self.cache:
            old_content = self.cache.pop(file_path)
            self.current_size -= len(old_content.encode("utf-8"))

        # 淘汰旧缓存直到有足够空间
        while (len(self.cache) >= self.max_files or
               self.current_size + content_size > self.max_size):
            if not self.cache:
                break
            _, old_content = self.cache.popitem(last=False)
            self.current_size -= len(old_content.encode("utf-8"))

        # 添加新缓存
        self.cache[file_path] = content
        self.current_size += content_size

    def remove(self, file_path: str):
        """移除缓存。

        Args:
            file_path: 文件路径
        """
        if file_path in self.cache:
            content = self.cache.pop(file_path)
            self.current_size -= len(content.encode("utf-8"))

    def clear(self):
        """清空缓存。"""
        self.cache.clear()
        self.current_size = 0

    @property
    def file_count(self) -> int:
        """当前缓存的文件数。"""
        return len(self.cache)

    @property
    def size_mb(self) -> float:
        """当前缓存大小 (MB)。"""
        return self.current_size / (1024 * 1024)
