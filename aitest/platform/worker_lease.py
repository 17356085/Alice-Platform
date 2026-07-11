"""WorkerLease — Worker 心跳与租约数据模型 (P3-5)

职责:
1. Worker 注册/注销
2. 心跳状态跟踪
3. Worker 健康检查
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any


@dataclass
class WorkerLease:
    """Worker 租约与心跳状态

    Attributes:
        worker_id: Worker 唯一标识（如 worker-abc123）
        hostname: Worker 主机名（用于运维定位）
        pid: Worker 进程 ID
        status: Worker 状态（running | draining | stopped | dead）
        started_at: 启动时间
        last_heartbeat_at: 最后心跳时间
        heartbeat_interval_seconds: 心跳间隔（秒）
        claimed_requests: 当前 claim 的 request_id 列表
        stats: Worker 统计信息（claimed/completed/failed 等）
        metadata: 扩展字段（版本号、区域等）
        org_id: 组织 ID（多租户）
    """
    worker_id: str
    hostname: str
    pid: int
    status: str = "running"  # running | draining | stopped | dead
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    heartbeat_interval_seconds: int = 30
    claimed_requests: list[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    org_id: str = "default-org"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 API 响应）"""
        return {
            "worker_id": self.worker_id,
            "hostname": self.hostname,
            "pid": self.pid,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "last_heartbeat_at": self.last_heartbeat_at.isoformat(),
            "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
            "claimed_requests": self.claimed_requests,
            "stats": self.stats,
            "metadata": self.metadata,
            "org_id": self.org_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> WorkerLease:
        """从字典创建（用于 ORM 转换）"""
        return WorkerLease(
            worker_id=data["worker_id"],
            hostname=data["hostname"],
            pid=data["pid"],
            status=data.get("status", "running"),
            started_at=datetime.fromisoformat(data["started_at"]) if isinstance(data["started_at"], str) else data["started_at"],
            last_heartbeat_at=datetime.fromisoformat(data["last_heartbeat_at"]) if isinstance(data["last_heartbeat_at"], str) else data["last_heartbeat_at"],
            heartbeat_interval_seconds=data.get("heartbeat_interval_seconds", 30),
            claimed_requests=data.get("claimed_requests", []),
            stats=data.get("stats", {}),
            metadata=data.get("metadata", {}),
            org_id=data.get("org_id", "default-org"),
        )

    def is_alive(self, timeout_seconds: int = 90) -> bool:
        """判断 Worker 是否存活（基于心跳超时）

        Args:
            timeout_seconds: 心跳超时阈值（默认 90 秒 = 3 倍心跳间隔）

        Returns:
            True 如果最后心跳在超时阈值内
        """
        if self.status in ("stopped", "dead"):
            return False

        now = datetime.now(timezone.utc)
        elapsed = (now - self.last_heartbeat_at).total_seconds()
        return elapsed < timeout_seconds

    def update_heartbeat(self) -> None:
        """更新心跳时间戳"""
        self.last_heartbeat_at = datetime.now(timezone.utc)
        if self.status == "dead":
            self.status = "running"  # 死亡的 worker 重新上线
