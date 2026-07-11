"""P3-5 Worker Lease/Heartbeat 测试

覆盖:
1. WorkerLeaseStore: 注册/注销/心跳/drain/查询/僵尸检测
2. ExecutionWorker 心跳集成（懒加载 + 不阻塞）
3. HTTP API: GET /workers, GET /workers/:id, POST /workers/:id/drain, POST /workers/cleanup
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from aitest.platform.worker_lease import WorkerLease
from aitest.platform.worker_lease_store import WorkerLeaseStore


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def db_session():
    """内存 SQLite Session（不依赖真实 DB）"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from aitest.infra.db import Base
    from aitest.platform.worker_lease_models import WorkerLeaseModel  # noqa: F401 — registers table

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def store(db_session):
    """WorkerLeaseStore with in-memory session"""
    return WorkerLeaseStore(db_session)


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: 注册 / 注销
# ─────────────────────────────────────────────────────────────────────────────

def test_register_worker(store):
    """注册新 Worker"""
    lease = store.register("worker-001", hostname="host-a", pid=12345)

    assert lease.worker_id == "worker-001"
    assert lease.hostname == "host-a"
    assert lease.pid == 12345
    assert lease.status == "running"
    assert lease.claimed_requests == []


def test_register_worker_defaults_hostname_and_pid(store):
    """注册时自动填写 hostname 和 pid"""
    import socket, os
    lease = store.register("worker-auto")

    assert lease.hostname == socket.gethostname()
    assert lease.pid == os.getpid()


def test_register_existing_worker_revives_it(store):
    """重新注册已停止的 Worker 应复活"""
    store.register("worker-002", hostname="host-b", pid=100)
    store.deregister("worker-002")

    revived = store.register("worker-002", hostname="host-b-new", pid=200)
    assert revived.status == "running"
    assert revived.hostname == "host-b-new"
    assert revived.pid == 200


def test_deregister_worker(store):
    """注销 Worker 应设置为 stopped"""
    store.register("worker-003")
    result = store.deregister("worker-003")

    assert result is True
    lease = store.get("worker-003")
    assert lease.status == "stopped"


def test_deregister_nonexistent_worker(store):
    """注销不存在的 Worker 应返回 False"""
    result = store.deregister("nonexistent-worker")
    assert result is False


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: 心跳
# ─────────────────────────────────────────────────────────────────────────────

def test_heartbeat_updates_timestamp(store):
    """心跳应更新 last_heartbeat_at"""
    store.register("worker-hb")
    before = datetime.now(timezone.utc)
    time.sleep(0.01)

    result = store.heartbeat("worker-hb")
    assert result is True

    lease = store.get("worker-hb")
    assert lease.last_heartbeat_at > before


def test_heartbeat_updates_stats(store):
    """心跳应同步 stats"""
    store.register("worker-stats")
    store.heartbeat(
        "worker-stats",
        stats={"claimed": 10, "completed": 8, "failed": 2},
    )

    lease = store.get("worker-stats")
    assert lease.stats["claimed"] == 10
    assert lease.stats["completed"] == 8


def test_heartbeat_updates_claimed_requests(store):
    """心跳应同步 claimed_requests"""
    store.register("worker-claimed")
    store.heartbeat(
        "worker-claimed",
        claimed_requests=["req-1", "req-2"],
    )

    lease = store.get("worker-claimed")
    assert "req-1" in lease.claimed_requests
    assert "req-2" in lease.claimed_requests


def test_heartbeat_revives_dead_worker(store, db_session):
    """对已 dead 的 Worker 发送心跳应恢复为 running"""
    store.register("worker-dead")
    # 手动把心跳时间设置到很久以前
    from aitest.platform.worker_lease_models import WorkerLeaseModel
    model = db_session.query(WorkerLeaseModel).filter_by(worker_id="worker-dead").first()
    model.last_heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=200)
    db_session.commit()

    # 标记为 dead
    store.mark_dead_workers(timeout_seconds=60)
    lease = store.get("worker-dead")
    assert lease.status == "dead"

    # 发送心跳 → 复活
    store.heartbeat("worker-dead")
    lease = store.get("worker-dead")
    assert lease.status == "running"


def test_heartbeat_unknown_worker_returns_false(store):
    """对不存在的 Worker 发送心跳应返回 False"""
    result = store.heartbeat("nonexistent")
    assert result is False


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Drain（优雅停止）
# ─────────────────────────────────────────────────────────────────────────────

def test_drain_running_worker(store):
    """drain running Worker 应设置为 draining"""
    store.register("worker-drain")
    result = store.drain("worker-drain")

    assert result is True
    lease = store.get("worker-drain")
    assert lease.status == "draining"


def test_drain_stopped_worker_fails(store):
    """drain 已停止的 Worker 应失败"""
    store.register("worker-stopped")
    store.deregister("worker-stopped")

    result = store.drain("worker-stopped")
    assert result is False


def test_drain_nonexistent_worker_fails(store):
    """drain 不存在的 Worker 应返回 False"""
    result = store.drain("nonexistent")
    assert result is False


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: 查询
# ─────────────────────────────────────────────────────────────────────────────

def test_list_all_workers(store):
    """list_all 应返回所有 Worker"""
    store.register("worker-a")
    store.register("worker-b")
    store.register("worker-c")

    workers = store.list_all()
    ids = [w.worker_id for w in workers]
    assert "worker-a" in ids
    assert "worker-b" in ids
    assert "worker-c" in ids


def test_list_alive_workers_excludes_stale(store, db_session):
    """list_alive 应排除心跳超时的 Worker"""
    from aitest.platform.worker_lease_models import WorkerLeaseModel

    store.register("worker-alive")
    store.register("worker-stale")

    # 将 worker-stale 的心跳时间设为很久以前
    model = db_session.query(WorkerLeaseModel).filter_by(worker_id="worker-stale").first()
    model.last_heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=200)
    db_session.commit()

    alive = store.list_alive(timeout_seconds=60)
    alive_ids = [w.worker_id for w in alive]

    assert "worker-alive" in alive_ids
    assert "worker-stale" not in alive_ids


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: 僵尸检测
# ─────────────────────────────────────────────────────────────────────────────

def test_mark_dead_workers(store, db_session):
    """mark_dead_workers 应标记心跳超时的 Worker"""
    from aitest.platform.worker_lease_models import WorkerLeaseModel

    store.register("worker-fresh")
    store.register("worker-zombie")

    # zombie 心跳很久以前
    model = db_session.query(WorkerLeaseModel).filter_by(worker_id="worker-zombie").first()
    model.last_heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=200)
    db_session.commit()

    dead_ids = store.mark_dead_workers(timeout_seconds=60)

    assert "worker-zombie" in dead_ids
    assert "worker-fresh" not in dead_ids

    # 验证状态
    zombie = store.get("worker-zombie")
    fresh = store.get("worker-fresh")
    assert zombie.status == "dead"
    assert fresh.status == "running"


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: WorkerLease.is_alive()
# ─────────────────────────────────────────────────────────────────────────────

def test_worker_is_alive_fresh_heartbeat():
    """刚注册的 Worker 应该是存活的"""
    lease = WorkerLease(worker_id="w", hostname="h", pid=1)
    assert lease.is_alive() is True


def test_worker_is_alive_old_heartbeat():
    """心跳很久以前的 Worker 不应该是存活的"""
    lease = WorkerLease(
        worker_id="w",
        hostname="h",
        pid=1,
        last_heartbeat_at=datetime.now(timezone.utc) - timedelta(seconds=200)
    )
    assert lease.is_alive(timeout_seconds=60) is False


def test_worker_stopped_is_not_alive():
    """stopped 状态的 Worker 不应该是存活的"""
    lease = WorkerLease(worker_id="w", hostname="h", pid=1, status="stopped")
    assert lease.is_alive() is False


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: ExecutionWorker 心跳集成
# ─────────────────────────────────────────────────────────────────────────────

def test_execution_worker_heartbeat_disabled_by_default_for_test():
    """enable_heartbeat=False 时不应触发任何 DB 操作"""
    from aitest.platform.execution_worker import ExecutionWorker

    mock_service = MagicMock()
    mock_store = MagicMock()
    mock_store.claim_next_request.return_value = None

    worker = ExecutionWorker(
        service=mock_service,
        store=mock_store,
        worker_id="test-worker",
        poll_interval=999,
        enable_heartbeat=False,  # 测试时关闭
    )

    # 启动不应抛出 DB 错误
    worker.start()
    time.sleep(0.05)
    worker.stop()

    # 不应有任何 WorkerLeaseStore 调用
    assert worker._heartbeat_store is None


def test_execution_worker_tracks_claimed_requests():
    """ExecutionWorker 应在 _handle_request 中追踪 claimed_requests"""
    from aitest.platform.execution_worker import ExecutionWorker

    mock_service = MagicMock()
    mock_store = MagicMock()

    # 模拟一个 request
    mock_request = MagicMock()
    mock_request.request_id = "req-track-test"
    mock_request.agent = "test-agent"
    mock_request.workspace_id = "ws-1"
    mock_request.triggered_by = "user-1"
    mock_request.org_id = "org-1"
    mock_request.module = "module-1"
    mock_request.pages = ["page-1"]
    mock_request.mode = "full"
    mock_request.provider = "claude"
    mock_request.priority = 5
    mock_request.trigger_type = "manual"

    mock_service._run_request_flow = MagicMock()
    mock_store.claim_next_request.return_value = mock_request
    mock_store.load_request.return_value = MagicMock(status="completed")

    worker = ExecutionWorker(
        service=mock_service,
        store=mock_store,
        worker_id="test-track-worker",
        enable_heartbeat=False,
    )

    # 在执行期间检查 claimed_requests
    original_run_flow = mock_service._run_request_flow.side_effect

    def check_during_execution(*args, **kwargs):
        # 执行期间 request 应在 claimed_requests 中
        assert "req-track-test" in worker._claimed_requests

    mock_service._run_request_flow.side_effect = check_during_execution

    worker.run_once()

    # 执行完成后应从 claimed_requests 中移除
    assert "req-track-test" not in worker._claimed_requests


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: HTTP API（通过 TestClient）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def test_client(db_session):
    """FastAPI TestClient with in-memory DB"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.workers_v1 import workers_router

    app = FastAPI()

    # 覆盖 get_session 依赖
    def override_get_session():
        yield db_session

    from aitest.infra.db import get_session
    app.dependency_overrides[get_session] = override_get_session
    app.include_router(workers_router)

    return TestClient(app)


def test_api_list_workers_empty(test_client):
    """GET /api/v1/workers 应返回空列表"""
    resp = test_client.get("/api/v1/workers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["workers"] == []


def test_api_list_workers_with_data(test_client, db_session):
    """GET /api/v1/workers 应返回已注册的 Worker"""
    store = WorkerLeaseStore(db_session)
    store.register("api-worker-1", hostname="host-1")
    store.register("api-worker-2", hostname="host-2")

    resp = test_client.get("/api/v1/workers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2


def test_api_get_worker(test_client, db_session):
    """GET /api/v1/workers/:id 应返回 Worker 详情"""
    store = WorkerLeaseStore(db_session)
    store.register("api-get-worker", hostname="host-get", pid=9999)

    resp = test_client.get("/api/v1/workers/api-get-worker")
    assert resp.status_code == 200
    data = resp.json()
    assert data["worker_id"] == "api-get-worker"
    assert data["hostname"] == "host-get"
    assert data["pid"] == 9999
    assert data["status"] == "running"


def test_api_get_worker_not_found(test_client):
    """GET /api/v1/workers/:id 对不存在的 Worker 应返回 404"""
    resp = test_client.get("/api/v1/workers/nonexistent-xxx")
    assert resp.status_code == 404


def test_api_drain_worker(test_client, db_session):
    """POST /api/v1/workers/:id/drain 应设置 Worker 为 draining"""
    store = WorkerLeaseStore(db_session)
    store.register("api-drain-worker")

    resp = test_client.post("/api/v1/workers/api-drain-worker/drain")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    # 验证状态
    lease = store.get("api-drain-worker")
    assert lease.status == "draining"


def test_api_drain_nonexistent_worker(test_client):
    """POST /api/v1/workers/:id/drain 对不存在的 Worker 应返回 404"""
    resp = test_client.post("/api/v1/workers/nonexistent-yyy/drain")
    assert resp.status_code == 404


def test_api_cleanup_dead_workers(test_client, db_session):
    """POST /api/v1/workers/cleanup 应标记僵尸 Worker"""
    from aitest.platform.worker_lease_models import WorkerLeaseModel

    store = WorkerLeaseStore(db_session)
    store.register("zombie-1")
    store.register("zombie-2")

    # 将两个 Worker 的心跳时间设为很久以前
    for wid in ["zombie-1", "zombie-2"]:
        model = db_session.query(WorkerLeaseModel).filter_by(worker_id=wid).first()
        model.last_heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=300)
    db_session.commit()

    resp = test_client.post("/api/v1/workers/cleanup?timeout_seconds=60")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert "zombie-1" in data["dead_workers"]
    assert "zombie-2" in data["dead_workers"]


def test_api_filter_workers_by_status(test_client, db_session):
    """GET /api/v1/workers?status=running 应过滤状态"""
    store = WorkerLeaseStore(db_session)
    store.register("running-worker")
    store.register("stopped-worker")
    store.deregister("stopped-worker")

    resp = test_client.get("/api/v1/workers?status=running")
    assert resp.status_code == 200
    data = resp.json()
    ids = [w["worker_id"] for w in data["workers"]]
    assert "running-worker" in ids
    assert "stopped-worker" not in ids
