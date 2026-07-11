"""WorkerLeaseStore — Worker 租约 CRUD 操作 (P3-5)

职责:
1. Worker 注册/注销
2. 心跳更新
3. 僵尸 Worker 检测与清理
4. 查询接口（供 HTTP API 使用）
"""

from __future__ import annotations

import logging
import socket
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session

from aitest.platform.worker_lease import WorkerLease
from aitest.platform.worker_lease_models import WorkerLeaseModel

logger = logging.getLogger(__name__)

# 默认心跳超时：3 倍心跳间隔（90 秒）
DEFAULT_HEARTBEAT_TIMEOUT_SECONDS = 90


class WorkerLeaseStore:
    """Worker 租约存储——CRUD + 心跳更新 + 僵尸检测"""

    def __init__(self, session: Session):
        self.session = session

    # ─────────────────────────────────────────────────────────────
    # 注册 / 注销
    # ─────────────────────────────────────────────────────────────

    def register(
        self,
        worker_id: str,
        *,
        hostname: str = "",
        pid: int = 0,
        heartbeat_interval_seconds: int = 30,
        metadata: dict = None,
        org_id: str = "default-org",
    ) -> WorkerLease:
        """注册新 Worker（或复活已停止的 Worker）

        Args:
            worker_id: Worker 唯一 ID
            hostname: 主机名（默认自动检测）
            pid: 进程 ID（默认自动检测）
            heartbeat_interval_seconds: 心跳间隔（秒）
            metadata: 附加元数据
            org_id: 组织 ID

        Returns:
            WorkerLease 对象
        """
        now = datetime.now(timezone.utc)
        hostname = hostname or socket.gethostname()
        pid = pid or os.getpid()
        metadata = metadata or {}

        existing = self.session.query(WorkerLeaseModel).filter_by(worker_id=worker_id).first()
        if existing:
            # 复活：更新已有记录
            existing.hostname = hostname
            existing.pid = pid
            existing.status = "running"
            existing.started_at = now
            existing.last_heartbeat_at = now
            existing.heartbeat_interval_seconds = heartbeat_interval_seconds
            existing.claimed_requests = []
            existing.stats = {}
            existing.metadata_json = metadata
            self.session.commit()
            logger.info(f"[WorkerLeaseStore] Re-registered worker: {worker_id}")
        else:
            model = WorkerLeaseModel(
                worker_id=worker_id,
                hostname=hostname,
                pid=pid,
                status="running",
                started_at=now,
                last_heartbeat_at=now,
                heartbeat_interval_seconds=heartbeat_interval_seconds,
                claimed_requests=[],
                stats={},
                metadata_json=metadata,
                org_id=org_id,
            )
            self.session.add(model)
            self.session.commit()
            logger.info(f"[WorkerLeaseStore] Registered worker: {worker_id}")

        return self.get(worker_id)

    def deregister(self, worker_id: str) -> bool:
        """注销 Worker（设置为 stopped）

        Args:
            worker_id: Worker ID

        Returns:
            True 如果成功注销
        """
        model = self.session.query(WorkerLeaseModel).filter_by(worker_id=worker_id).first()
        if not model:
            return False

        model.status = "stopped"
        model.last_heartbeat_at = datetime.now(timezone.utc)
        model.claimed_requests = []
        self.session.commit()
        logger.info(f"[WorkerLeaseStore] Deregistered worker: {worker_id}")
        return True

    # ─────────────────────────────────────────────────────────────
    # 心跳
    # ─────────────────────────────────────────────────────────────

    def heartbeat(
        self,
        worker_id: str,
        *,
        stats: dict = None,
        claimed_requests: list[str] = None,
    ) -> bool:
        """更新 Worker 心跳

        Args:
            worker_id: Worker ID
            stats: 最新统计（claimed/completed/failed 等）
            claimed_requests: 当前持有的 request_id 列表

        Returns:
            True 如果更新成功，False 如果 worker 不存在
        """
        model = self.session.query(WorkerLeaseModel).filter_by(worker_id=worker_id).first()
        if not model:
            logger.warning(f"[WorkerLeaseStore] Heartbeat for unknown worker: {worker_id}")
            return False

        model.last_heartbeat_at = datetime.now(timezone.utc)
        if stats is not None:
            model.stats = stats
        if claimed_requests is not None:
            model.claimed_requests = claimed_requests
        # 如果曾经被标记为 dead，恢复为 running
        if model.status == "dead":
            model.status = "running"

        self.session.commit()
        return True

    # ─────────────────────────────────────────────────────────────
    # Drain（优雅停止）
    # ─────────────────────────────────────────────────────────────

    def drain(self, worker_id: str) -> bool:
        """将 Worker 设置为 draining（不再 claim 新任务，等待当前任务完成）

        Args:
            worker_id: Worker ID

        Returns:
            True 如果成功设置
        """
        model = self.session.query(WorkerLeaseModel).filter_by(worker_id=worker_id).first()
        if not model:
            return False
        if model.status not in ("running",):
            logger.warning(f"[WorkerLeaseStore] Cannot drain worker in status: {model.status}")
            return False

        model.status = "draining"
        self.session.commit()
        logger.info(f"[WorkerLeaseStore] Worker set to draining: {worker_id}")
        return True

    # ─────────────────────────────────────────────────────────────
    # 查询
    # ─────────────────────────────────────────────────────────────

    def get(self, worker_id: str) -> Optional[WorkerLease]:
        """获取单个 Worker

        Args:
            worker_id: Worker ID

        Returns:
            WorkerLease 或 None
        """
        model = self.session.query(WorkerLeaseModel).filter_by(worker_id=worker_id).first()
        if not model:
            return None
        return _model_to_lease(model)

    def list_all(self, org_id: str = None) -> List[WorkerLease]:
        """列出所有 Worker

        Args:
            org_id: 按组织过滤（None = 所有）

        Returns:
            WorkerLease 列表
        """
        q = self.session.query(WorkerLeaseModel)
        if org_id:
            q = q.filter_by(org_id=org_id)
        q = q.order_by(WorkerLeaseModel.started_at.desc())
        return [_model_to_lease(m) for m in q.all()]

    def list_alive(self, timeout_seconds: int = DEFAULT_HEARTBEAT_TIMEOUT_SECONDS) -> List[WorkerLease]:
        """列出存活的 Worker（心跳在超时阈值内）

        Args:
            timeout_seconds: 心跳超时阈值

        Returns:
            WorkerLease 列表（仅 running/draining 状态且心跳正常）
        """
        threshold = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        q = (
            self.session.query(WorkerLeaseModel)
            .filter(WorkerLeaseModel.status.in_(["running", "draining"]))
            .filter(WorkerLeaseModel.last_heartbeat_at >= threshold)
            .order_by(WorkerLeaseModel.started_at.desc())
        )
        return [_model_to_lease(m) for m in q.all()]

    # ─────────────────────────────────────────────────────────────
    # 僵尸清理
    # ─────────────────────────────────────────────────────────────

    def mark_dead_workers(
        self, timeout_seconds: int = DEFAULT_HEARTBEAT_TIMEOUT_SECONDS
    ) -> List[str]:
        """将心跳超时的 running/draining Worker 标记为 dead

        通常由后台任务定期调用。

        Args:
            timeout_seconds: 心跳超时阈值（超过此时间无心跳 → dead）

        Returns:
            被标记为 dead 的 worker_id 列表
        """
        threshold = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        stale = (
            self.session.query(WorkerLeaseModel)
            .filter(WorkerLeaseModel.status.in_(["running", "draining"]))
            .filter(WorkerLeaseModel.last_heartbeat_at < threshold)
            .all()
        )

        dead_ids = []
        for model in stale:
            model.status = "dead"
            dead_ids.append(model.worker_id)
            logger.warning(
                f"[WorkerLeaseStore] Marking worker as dead (no heartbeat): {model.worker_id} "
                f"(last seen: {model.last_heartbeat_at})"
            )

        if dead_ids:
            self.session.commit()

        return dead_ids


# ─────────────────────────────────────────────────────────────────────────────
# 工厂函数（单例模式，与其他 store 保持一致）
# ─────────────────────────────────────────────────────────────────────────────

_store_instance: Optional[WorkerLeaseStore] = None


def get_worker_lease_store(session: Session = None) -> WorkerLeaseStore:
    """获取 WorkerLeaseStore 单例（需要传入 session 或依赖注入）

    Args:
        session: SQLAlchemy Session（可选，用于测试注入）
    """
    if session is not None:
        return WorkerLeaseStore(session)

    # 生产路径：从 db 获取 session
    from aitest.infra.db import get_db_session
    return WorkerLeaseStore(get_db_session())


# ─────────────────────────────────────────────────────────────────────────────
# ORM → Dataclass 转换
# ─────────────────────────────────────────────────────────────────────────────

def _model_to_lease(model: WorkerLeaseModel) -> WorkerLease:
    return WorkerLease(
        worker_id=model.worker_id,
        hostname=model.hostname,
        pid=model.pid,
        status=model.status,
        started_at=_as_utc(model.started_at),
        last_heartbeat_at=_as_utc(model.last_heartbeat_at),
        heartbeat_interval_seconds=model.heartbeat_interval_seconds,
        claimed_requests=list(model.claimed_requests or []),
        stats=dict(model.stats or {}),
        metadata=dict(model.metadata_json or {}),
        org_id=model.org_id,
    )


def _as_utc(value: datetime) -> datetime:
    """Normalise SQLite's naive datetimes to the UTC contract used by workers."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
