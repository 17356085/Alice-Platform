"""双/多浏览器 fixture — 支持跨会话端到端测试

用途：
  - 角色权限即时生效验证（admin 修改权限 → target user 刷新验证）
  - 工作流端到端审批（申请人提交 → 审批人登录审批）

使用方式：
  def test_xxx(dual_driver):
      admin_drv, target_drv = dual_driver
      ...

  def test_xxx(triple_driver):
      admin_drv, user_a, user_b = triple_driver
      ...

注意：
  - 每个 fixture 是 function 级别，用例结束后自动关闭所有浏览器
  - admin 已登录，target 浏览器仅打开页面不登录（由用例决定登录时机）
"""
import logging
import pytest

from base.browser_driver import BaseDriver, ensure_logged_in

logger = logging.getLogger(__name__)


def _open_and_login_admin():
    """打开浏览器并以 admin 登录"""
    base = BaseDriver()
    driver = base.open_browser()
    try:
        driver.maximize_window()
        ensure_logged_in(driver)
        return driver, base
    except Exception:
        try:
            base.close_browser()
        except Exception:
            pass
        raise


def _open_browser_blank():
    """打开空白浏览器（不登录），由用例决定后续操作"""
    base = BaseDriver()
    driver = base.open_browser()
    driver.maximize_window()
    return driver, base


def _close_all(*drivers_and_bases):
    """安全关闭所有浏览器"""
    for item in drivers_and_bases:
        if item is None:
            continue
        if isinstance(item, tuple):
            driver, base = item
        else:
            driver, base = item, None
        try:
            if driver:
                driver.quit()
        except Exception:
            pass
        try:
            if base:
                base.close_browser()
        except Exception:
            pass


@pytest.fixture(scope="function")
def dual_driver():
    """双浏览器 fixture — admin(logged in) + target(blank)

    Returns:
        tuple: (admin_driver, target_driver)
            admin_driver  — 已登录 admin 账号
            target_driver — 空白浏览器，由用例决定登录哪个测试用户
    """
    admin_pair = target_pair = None
    admin_drv = target_drv = None
    try:
        admin_drv, admin_base = _open_and_login_admin()
        admin_pair = (admin_drv, admin_base)
        target_drv, target_base = _open_browser_blank()
        target_pair = (target_drv, target_base)
        logger.info("dual_driver ready: admin=%s, target=%s",
                     admin_drv.session_id, target_drv.session_id)
        yield (admin_drv, target_drv)
    finally:
        _close_all(admin_pair, target_pair)


@pytest.fixture(scope="function")
def triple_driver():
    """三浏览器 fixture — admin + user_a + user_b

    Returns:
        tuple: (admin_driver, user_a_driver, user_b_driver)
            admin_driver — 已登录 admin 账号
            user_a_driver — 空白浏览器
            user_b_driver — 空白浏览器
    """
    pairs = []
    drivers = []
    try:
        admin_drv, admin_base = _open_and_login_admin()
        pairs.append((admin_drv, admin_base))
        drivers.append(admin_drv)

        for label in ("user_a", "user_b"):
            drv, base = _open_browser_blank()
            pairs.append((drv, base))
            drivers.append(drv)
            logger.info("triple_driver: %s ready (session=%s)", label, drv.session_id)

        yield tuple(drivers)
    finally:
        _close_all(*pairs)
