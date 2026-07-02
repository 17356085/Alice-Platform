"""MemoryStore — 执行记忆 (Runtime Capability)。

Engine 主动调用:
  - run() 前: get_last() 获取上次执行结果
  - run() 后: remember() 记录本次执行结果
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MemoryRecord:
    """单条记忆。"""

    run_id: str = ""
    module: str = ""
    pages: list[str] = field(default_factory=list)
    status: str = ""
    elapsed_seconds: float = 0.0
    completed_phases: list[str] = field(default_factory=list)
    failed_phases: list[str] = field(default_factory=list)


class MemoryStore(ABC):
    """执行记忆接口。

    记住历史执行结果，供后续 Run 参考。

    用法:
        class MyMemory(MemoryStore):
            def remember(self, module, result):
                # 保存到数据库
                ...

            def get_last(self, module):
                # 查询最后一次
                return MemoryRecord(...)

            def get_history(self, module, limit=10):
                # 查询历史
                return [...]
    """

    @abstractmethod
    def remember(self, module: str, result) -> None:
        """记录执行结果。

        Args:
            module: 模块名
            result: RunResult
        """
        ...

    @abstractmethod
    def get_last(self, module: str) -> MemoryRecord | None:
        """获取某模块最后一次执行记录。"""
        ...

    @abstractmethod
    def get_history(self, module: str | None = None, limit: int = 10) -> list[MemoryRecord]:
        """获取历史记录。

        Args:
            module: 模块名过滤 (None=全部)
            limit: 返回数量
        """
        ...


class InMemoryMemoryStore(MemoryStore):
    """内存记忆存储 — 用于测试和演示。"""

    def __init__(self):
        self._records: list[MemoryRecord] = []

    def remember(self, module: str, result) -> None:
        """记录到内存。"""
        record = MemoryRecord(
            run_id=result.run_id,
            module=module,
            pages=result.pages,
            status=result.status,
            elapsed_seconds=result.elapsed_seconds,
            completed_phases=result.completed_phases,
            failed_phases=result.failed_phases,
        )
        self._records.append(record)

    def get_last(self, module: str) -> MemoryRecord | None:
        """获取最后一次。"""
        for r in reversed(self._records):
            if r.module == module:
                return r
        return None

    def get_history(self, module: str | None = None, limit: int = 10) -> list[MemoryRecord]:
        """获取历史。"""
        records = self._records
        if module:
            records = [r for r in records if r.module == module]
        return records[-limit:]


class FileMemoryStore(MemoryStore):
    """文件记忆存储 — 持久化到 JSON 文件。"""

    def __init__(self, storage_path: str | Path):
        self.storage_path = Path(storage_path)
        self._records: list[MemoryRecord] = []

        if self.storage_path.exists():
            self._load()

    def remember(self, module: str, result) -> None:
        """记录并保存到文件。"""
        record = MemoryRecord(
            run_id=result.run_id,
            module=module,
            pages=result.pages,
            status=result.status,
            elapsed_seconds=result.elapsed_seconds,
            completed_phases=result.completed_phases,
            failed_phases=result.failed_phases,
        )
        self._records.append(record)
        self._save()

    def get_last(self, module: str) -> MemoryRecord | None:
        """获取最后一次。"""
        for r in reversed(self._records):
            if r.module == module:
                return r
        return None

    def get_history(self, module: str | None = None, limit: int = 10) -> list[MemoryRecord]:
        """获取历史。"""
        records = self._records
        if module:
            records = [r for r in records if r.module == module]
        return records[-limit:]

    def _load(self):
        """从文件加载。"""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._records = [MemoryRecord(**r) for r in data]
        except Exception as e:
            logger.warning("Memory load failed: %s", e)

    def _save(self):
        """保存到文件。"""
        try:
            data = [
                {
                    "run_id": r.run_id,
                    "module": r.module,
                    "pages": r.pages,
                    "status": r.status,
                    "elapsed_seconds": r.elapsed_seconds,
                    "completed_phases": r.completed_phases,
                    "failed_phases": r.failed_phases,
                }
                for r in self._records
            ]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("Memory save failed: %s", e)
