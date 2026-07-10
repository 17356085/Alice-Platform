"""Workflow Store — CRUD operations for workflow resources (P8-1)."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from aitest.infra.db import get_db_session
from aitest.platform.workflow_models import WorkflowModel
from aitest.platform.workflow import Workflow, WorkflowGraph


class WorkflowStore:
    """工作流资源存储"""

    def __init__(self):
        self.session = get_db_session()
        self._ensure_workflow_tables()

    def _ensure_workflow_tables(self):
        """确保工作流表存在（自动迁移）"""
        try:
            from sqlalchemy import text
            # 检查 workflows 表是否存在
            result = self.session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='workflows'"
            )).fetchone()

            if not result:
                # 执行迁移脚本
                from pathlib import Path
                migration_file = Path(__file__).parent.parent.parent / "migrations" / "add_workflow_tables_sqlite.sql"
                if migration_file.exists():
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        sql = f.read()
                    # 分割并执行每条 SQL
                    for statement in sql.split(';'):
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            self.session.execute(text(statement))
                    self.session.commit()
        except Exception as e:
            # 迁移失败不阻塞启动
            print(f"[WARN] Workflow tables migration failed: {e}")

    def create_workflow(
        self,
        name: str,
        description: str,
        version: str,
        graph: WorkflowGraph,
        org_id: str = "",
        created_by: str = "",
        status: str = "draft",
    ) -> Workflow:
        """创建工作流"""
        workflow_id = f"wf_{uuid.uuid4().hex[:16]}"

        model = WorkflowModel(
            workflow_id=workflow_id,
            name=name,
            description=description,
            version=version,
            status=status,
            org_id=org_id,
            created_by=created_by,
            graph_json=json.dumps(graph.to_dict()),
        )

        self.session.add(model)
        self.session.commit()

        return self._row_to_workflow(model)

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        model = self.session.query(WorkflowModel).filter_by(workflow_id=workflow_id).first()
        if not model:
            return None
        return self._row_to_workflow(model)

    def list_workflows(
        self,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Workflow]:
        """列出工作流"""
        query = self.session.query(WorkflowModel)

        if org_id:
            query = query.filter_by(org_id=org_id)
        if status:
            query = query.filter_by(status=status)

        models = query.order_by(WorkflowModel.created_at.desc()).limit(limit).all()
        return [self._row_to_workflow(m) for m in models]

    def update_workflow(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        graph: Optional[WorkflowGraph] = None,
    ) -> bool:
        """更新工作流"""
        model = self.session.query(WorkflowModel).filter_by(workflow_id=workflow_id).first()
        if not model:
            return False

        if name:
            model.name = name
        if description:
            model.description = description
        if status:
            model.status = status
        if graph:
            model.graph_json = json.dumps(graph.to_dict())

        model.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return True

    def publish_workflow(self, workflow_id: str, version: str) -> bool:
        """发布工作流新版本"""
        model = self.session.query(WorkflowModel).filter_by(workflow_id=workflow_id).first()
        if not model:
            return False

        model.version = version
        model.status = "published"
        model.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return True

    def _row_to_workflow(self, row: WorkflowModel) -> Workflow:
        """DB row → Workflow dataclass"""
        graph_data = json.loads(row.graph_json)
        graph = WorkflowGraph.from_dict(graph_data)

        return Workflow(
            workflow_id=row.workflow_id,
            name=row.name,
            description=row.description,
            version=row.version,
            status=row.status,
            org_id=row.org_id,
            created_by=row.created_by,
            created_at=row.created_at.isoformat() if row.created_at else "",
            updated_at=row.updated_at.isoformat() if row.updated_at else "",
            graph=graph,
        )


# Singleton instance
_store: Optional[WorkflowStore] = None


def get_workflow_store() -> WorkflowStore:
    """获取 WorkflowStore 单例"""
    global _store
    if _store is None:
        _store = WorkflowStore()
    return _store
