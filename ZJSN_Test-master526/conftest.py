"""Pytest shared configuration — 路径注入 + 日志初始化 + 失败截图.

pytest >= 8 no longer supports defining pytest_plugins in non-top-level conftest files.
Ref: https://docs.pytest.org/en/stable/deprecations.html#pytest-plugins-in-non-top-level-conftest-files
"""
import logging
import os
import re
import shutil
import sys
from datetime import datetime

import pytest

# ══════════════════════════════════════════════════════════════════════
# 从子目录 conftest 迁移：pytest >= 8 仅允许顶层定义
# ══════════════════════════════════════════════════════════════════════
pytest_plugins = ["script.system.conftest_dual"]

# ── 项目根路径注入 ──────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

FAILURE_ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "failures")
ALLURE_RESULTS_DIR = os.path.join(PROJECT_ROOT, "allure-results")


def pytest_sessionstart(session):
    """每次测试会话启动时，自动清理上一次的产物（控制堆积）。"""
    dirs_to_clean = [ALLURE_RESULTS_DIR, FAILURE_ARTIFACTS_DIR]
    for d in dirs_to_clean:
        if os.path.isdir(d):
            try:
                shutil.rmtree(d)
            except PermissionError:
                pass  # 目录被其他进程占用，跳过清理
            os.makedirs(d, exist_ok=True)

# ── 日志初始化（所有模块通过 logging.getLogger(__name__) 获取）──
from config import LOGGING_CONFIG

logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG.get("level", "INFO")),
    format=LOGGING_CONFIG.get("format"),
    datefmt=LOGGING_CONFIG.get("datefmt"),
    force=True,
)

# 降低第三方库日志噪音
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def _safe_artifact_name(nodeid):
    name = re.sub(r"[^\w\-.]+", "_", nodeid)
    return name[:200]


def _resolve_driver_from_item(item):
    """遍历用例的所有 fixture，通过属性特征自动识别 WebDriver，无需维护名称白名单。"""
    for name in item.fixturenames:
        try:
            value = item.funcargs.get(name)
        except Exception:
            continue
        if value is None:
            continue
        # Page Object：持有 .driver 属性，且该属性具备截图能力
        if hasattr(value, "driver") and hasattr(value.driver, "save_screenshot"):
            return value.driver
        # 裸 WebDriver 实例
        if hasattr(value, "save_screenshot"):
            return value
    return None


def _capture_failure_artifacts(driver, nodeid):
    os.makedirs(FAILURE_ARTIFACTS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{_safe_artifact_name(nodeid)}_{stamp}"
    prefix = os.path.join(FAILURE_ARTIFACTS_DIR, base_name)

    try:
        from base.base_page import BasePage

        BasePage(driver).save_debug_snapshot(prefix)
        logger.error("失败诊断已保存: %s.png / %s.html", prefix, prefix)
    except Exception as exc:
        logger.warning("BasePage 诊断保存失败，尝试直接截图: %s", exc)
        try:
            png_path = f"{prefix}.png"
            driver.save_screenshot(png_path)
            logger.error("失败截图已保存: %s", png_path)
        except Exception as exc2:
            logger.warning("截图保存失败: %s", exc2)

    try:
        import allure

        png_path = f"{prefix}.png"
        if os.path.isfile(png_path):
            allure.attach.file(
                png_path,
                name="失败截图",
                attachment_type=allure.attachment_type.PNG,
            )
        html_path = f"{prefix}.html"
        if os.path.isfile(html_path):
            with open(html_path, encoding="utf-8") as f:
                allure.attach(
                    f.read(),
                    name="失败页面 HTML",
                    attachment_type=allure.attachment_type.HTML,
                )
    except Exception:
        pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败时自动保存截图与页面 HTML"""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    driver = _resolve_driver_from_item(item)
    if driver is None:
        logger.warning("用例失败但未找到 WebDriver fixture: %s", item.nodeid)
        return
    _capture_failure_artifacts(driver, item.nodeid)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    """会话结束时检查是否有残留未清理的数据"""
    from base.cleanup_tracker import get_cleanup_tracker
    tracker = get_cleanup_tracker()
    remaining = tracker.pop_all()
    if remaining:
        logger.warning("⚠ 会话结束时有 %d 条数据未清理: %s",
                       len(remaining),
                       [f"{r['entity_type']}({r['entity_name']})" for r in remaining])
