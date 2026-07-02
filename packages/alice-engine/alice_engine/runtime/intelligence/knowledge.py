"""KnowledgeStore — 知识检索与沉淀 (Runtime Capability)。

Engine 主动调用:
  - run() 前: search() 检索历史知识，注入上下文
  - run() 后: ingest() 沉淀新知识

用户实现此接口即可接入任意存储后端。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeItem:
    """单条知识。"""

    module: str = ""
    page: str = ""
    content: str = ""
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class KnowledgeStore(ABC):
    """知识存储接口。

    用户实现此接口即可接入任意存储:
      - 内存 dict
      - JSON 文件
      - SQLite
      - ChromaDB
      - 任意向量数据库

    用法:
        class MyStore(KnowledgeStore):
            def search(self, module, page, limit=5):
                return [KnowledgeItem(content="...")]

            def ingest(self, module, result):
                # 保存到数据库
                ...
    """

    @abstractmethod
    def search(self, module: str, page: str, limit: int = 5) -> list[KnowledgeItem]:
        """检索相关知识。

        Args:
            module: 模块名
            page: 页面名
            limit: 返回数量限制

        Returns:
            相关知识列表
        """
        ...

    @abstractmethod
    def ingest(self, module: str, result) -> None:
        """沉淀新知识。

        Args:
            module: 模块名
            result: RunResult
        """
        ...


class InMemoryKnowledgeStore(KnowledgeStore):
    """内存知识存储 — 用于测试和演示。"""

    def __init__(self):
        self._items: list[KnowledgeItem] = []

    def search(self, module: str, page: str, limit: int = 5) -> list[KnowledgeItem]:
        """从内存检索。"""
        results = [
            item for item in self._items
            if item.module == module and (not page or item.page == page)
        ]
        return results[:limit]

    def ingest(self, module: str, result) -> None:
        """存入内存。"""
        for page in (result.pages or []):
            self._items.append(KnowledgeItem(
                module=module,
                page=page,
                content=f"Run {result.run_id}: {result.status}",
                metadata={
                    "elapsed": result.elapsed_seconds,
                    "phases": result.completed_phases,
                },
            ))
