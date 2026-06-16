"""数据清理追踪器 — 基于注册模式的测试脏数据管理

用法:
    from base.cleanup_tracker import get_cleanup_tracker
    tracker = get_cleanup_tracker()

    # 标准注册 (推荐)
    tracker.register(entity_type="dict", entity_id=42,
                     entity_name="TC-字典", api_delete_url="/api/system/dict/type/{id}")

    # 别名 (兼容 dcs 等旧模块)
    tracker.register_entity("monitor", "TC-监控", delete_callback=lambda n: page.delete(n))

    # 手动触发清理 (通常由 autouse fixture 自动执行)
    tracker.cleanup_all(warn_only=True)

设计要点:
    - 单例模式，跨模块共享
    - 不依赖 Selenium/WebDriver，任何层均可调用
    - 支持 API / UI / callback 三种清理方式
"""
import logging

logger = logging.getLogger(__name__)


class _CleanupTracker:
    """单例：收集所有测试中创建的实体，在 teardown 时统一清理"""

    def __init__(self):
        self._records: list[dict] = []

    # ── 标准注册 API ─────────────────────────────────────────

    def register(
        self,
        entity_type: str,
        entity_id=None,
        entity_name: str = "",
        api_delete_url: str = "",
        cleanup_method: str = "api",
        extra: dict = None,
    ):
        """
        注册一个待清理实体。

        Args:
            entity_type: 实体类型标识，如 "dict", "course", "contract"
            entity_id:   主键 ID（int | str）
            entity_name: 名称（可选，日志用）
            api_delete_url: 删除 API URL，如 /api/system/dict/type/{id}
            cleanup_method: 清理方式 "api" | "ui" | "callback"
            extra:      额外参数（如 UI 清理所需的 page object）
        """
        self._records.append({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "api_delete_url": api_delete_url,
            "cleanup_method": cleanup_method,
            "extra": extra or {},
        })
        logger.debug("注册待清理: %s(id=%s, method=%s)", entity_type, entity_id, cleanup_method)

    # ── 便捷别名 (兼容 dcs 等旧模块的 register_entity 调用) ──

    def register_entity(
        self,
        entity_type: str,
        entity_name: str = "",
        entity_id=None,
        api_delete_url: str = "",
        delete_callback=None,
        extra: dict = None,
    ):
        """
        register() 的便捷别名，兼容旧模块调用风格。

        Args:
            entity_type:     实体类型标识
            entity_name:     实体名称 (用于 UI 搜索删除)
            entity_id:       主键 ID
            api_delete_url:  删除 API URL
            delete_callback: 自定义删除回调 callable(name) → bool
            extra:           额外参数
        """
        rec_extra = extra or {}
        if delete_callback:
            rec_extra["delete_callback"] = delete_callback
            cleanup_method = "callback"
        elif api_delete_url and entity_id:
            cleanup_method = "api"
        else:
            cleanup_method = "ui"

        self._records.append({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "api_delete_url": api_delete_url,
            "cleanup_method": cleanup_method,
            "extra": rec_extra,
        })
        logger.debug("注册待清理(alias): %s(name=%s, method=%s)", entity_type, entity_name, cleanup_method)

    # ── 批量清理 ──────────────────────────────────────────────

    def pop_all(self) -> list[dict]:
        """原子获取并清空所有待清理记录。"""
        records, self._records = self._records, []
        return records

    def cleanup_all(self, warn_only: bool = True) -> int:
        """
        立即执行所有已注册实体的清理（不依赖外部 teardown）。

        Args:
            warn_only: True=清理失败只发 warning；False=清理失败抛异常

        Returns:
            成功清理的条数
        """
        records = self.pop_all()
        if not records:
            return 0

        logger.info("数据清理(cleanup_all): 共 %d 条", len(records))
        cleaned = 0
        for rec in records:
            try:
                self._cleanup_one(rec)
                cleaned += 1
            except Exception as e:
                msg = f"  ⚠ 清理失败: {rec['entity_type']}({rec.get('entity_name') or rec.get('entity_id','?')}) — {e}"
                if warn_only:
                    logger.warning(msg)
                else:
                    logger.error(msg)
                    raise
        if cleaned:
            logger.info("  ✅ 已清理 %d/%d 条", cleaned, len(records))
        return cleaned

    def _cleanup_one(self, rec: dict):
        """清理单条记录（内部方法，供 cleanup_all 和外部 _data_cleanup 使用）"""
        method = rec.get("cleanup_method", "api")

        if method == "callback":
            callback = rec.get("extra", {}).get("delete_callback")
            if callback:
                name = rec.get("entity_name", "")
                callback(name)
                logger.debug("  ✅ callback清理: %s(%s)", rec["entity_type"], name)
                return
            # fallback: 尝试 API 或 UI
            logger.debug("callback 方法无 delete_callback，降级到 API/UI")

        if method in ("api", "callback"):
            if rec.get("api_delete_url") and rec.get("entity_id"):
                from config.cleanup import CLEANUP_CONFIG
                from config import BASE_URL
                import requests
                url = rec["api_delete_url"].format(id=rec["entity_id"])
                if not url.startswith("http"):
                    url = BASE_URL.rstrip("/") + url
                session = self._get_api_session()
                r = session.delete(url, timeout=CLEANUP_CONFIG.get("api_timeout", 10))
                r.raise_for_status()
                logger.debug("  ✅ API删除: %s(id=%s)", rec["entity_type"], rec["entity_id"])
                return

        # 兜底: UI 或搜索删除
        if rec.get("extra") and rec["extra"].get("page"):
            self._cleanup_via_ui(rec)
            return

        raise ValueError(f"无法清理: {rec['entity_type']}({rec.get('entity_name','')}) — 无可用清理方式")

    @staticmethod
    def _cleanup_via_ui(rec: dict):
        """UI 兜底清理"""
        import time
        entity_name = rec.get("entity_name", "")
        page = rec["extra"]["page"]
        delete_method = rec["extra"].get("delete_method", "")
        if delete_method == "search_and_delete" and entity_name:
            page.click_reset_button()
            getattr(page, rec["extra"]["search_method"])(entity_name)
            page.click_search_button()
            time.sleep(1)
            page.click_delete_by_name(entity_name)
            page.confirm_message_box()
            logger.debug("  ✅ UI删除: %s(%s)", rec["entity_type"], entity_name)
            return
        raise ValueError(f"UI 清理不可用: {rec['entity_type']}({entity_name})")

    _api_session = None

    @classmethod
    def _get_api_session(cls):
        """获取已认证的 requests.Session（延迟创建，跨用例复用）"""
        if cls._api_session is None:
            from config import BASE_URL, DEFAULT_USERNAME, DEFAULT_PASSWORD
            import requests
            session = requests.Session()
            r = session.post(f"{BASE_URL}/api/auth/login", json={
                "username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD,
            }, timeout=10)
            r.raise_for_status()
            token = r.json()["data"]["accessToken"]
            session.headers.update({"Authorization": f"Bearer {token}"})
            cls._api_session = session
        return cls._api_session

    # ── 状态查询 ──────────────────────────────────────────────

    @property
    def pending_count(self) -> int:
        return len(self._records)

    def clear(self):
        """清空所有待清理记录（不执行清理）"""
        self._records.clear()


_tracker: _CleanupTracker | None = None


def get_cleanup_tracker() -> _CleanupTracker:
    """获取全局清理追踪器单例。"""
    global _tracker
    if _tracker is None:
        _tracker = _CleanupTracker()
    return _tracker
