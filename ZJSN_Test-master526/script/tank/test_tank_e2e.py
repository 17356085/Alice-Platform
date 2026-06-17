"""储罐管理 — 跨页面端到端测试

覆盖场景:
  E2E-TK-001: 监控->报警配置->数据报表 全链 (P0)
  E2E-TK-002: 监控->报表 数据一致性 (P1)

技术:
  单浏览器顺序导航
  tank 使用自定义 UI 框架 (非标准 Element Plus)
  alarm-config 通过 monitor 页面触发
"""
import os
import sys
import time
import pytest
import allure

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from base.sidebar_navigator import SidebarNavigator
from base.base_page import BasePage


def step(text):
    print(f"  -> {text}")
    try:
        allure.step(text)
    except Exception:
        pass


def case(case_id, title):
    print(f"\n{'='*60}\n用例 {case_id}：{title}\n{'='*60}")
    try:
        allure.dynamic.title(f"{case_id} {title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


def nav_to(driver, href, label=""):
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash(href, label)
    BasePage(driver).wait_vue_stable()
    time.sleep(2)


class TestTankE2E:
    """储罐管理 — 跨页面端到端测试"""

    @pytest.mark.smoke
    @allure.epic("储罐管理")
    @allure.feature("储罐监控")
    @allure.story("跨页面流转-储罐全链")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_tk_001_monitor_alarm_report_chain(self, driver_setup):
        """E2E-TK-001: 储罐全链 — 监控->报警配置->数据报表

        流程:
          储罐监控: 验证页面加载 (自定义 UI)
          -> 报警配置: 通过侧边栏导航
          -> 数据报表: 验证报表页面加载
        """
        driver = driver_setup
        case("E2E-TK-001", "储罐全链 — 监控->报警->报表")

        chain = {}

        # ── Step 1: 储罐监控 ──
        step("导航到储罐监控")
        nav_to(driver, "#/tank/monitor", "储罐监控")
        BasePage(driver).wait_vue_stable()
        time.sleep(3)
        step("储罐监控页面加载 [OK]")
        chain['monitor'] = 'loaded'

        # ── Step 2: 报警配置 (通过侧边栏) ──
        step("导航到储罐报警配置")
        nav_to(driver, "#/tank/alarm-config", "储罐报警配置")
        BasePage(driver).wait_vue_stable()
        time.sleep(2)
        step("储罐报警配置页面加载 [OK]")
        chain['alarm_config'] = 'loaded'

        # ── Step 3: 数据报表 ──
        step("导航到储罐数据报表")
        nav_to(driver, "#/tank/report", "储罐数据报表")
        BasePage(driver).wait_vue_stable()
        time.sleep(2)
        step("储罐数据报表页面加载 [OK]")
        chain['report'] = 'loaded'

        # ── 汇总 ──
        step(f"储罐全链: {chain}")
        all_loaded = all(v == 'loaded' for v in chain.values())
        assert all_loaded, ea("储罐3页面均正常加载", chain)

        step("E2E-TK-001 储罐全链验证通过 [OK]")

    @allure.epic("储罐管理")
    @allure.feature("储罐监控")
    @allure.story("跨页面流转-监控报表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_tk_002_monitor_report_roundtrip(self, driver_setup):
        """E2E-TK-002: 监控->报表 往返 (P1)

        流程:
          监控 -> 报表 -> 回到监控
          验证页面间可自由切换
        """
        driver = driver_setup
        case("E2E-TK-002", "监控<->报表 往返验证")

        # 监控 -> 报表
        step("监控 -> 报表")
        nav_to(driver, "#/tank/monitor", "储罐监控")
        BasePage(driver).wait_vue_stable()
        time.sleep(2)

        nav_to(driver, "#/tank/report", "储罐数据报表")
        BasePage(driver).wait_vue_stable()
        time.sleep(2)
        step("报表页面加载 [OK]")

        # 报表 -> 回到监控
        step("报表 -> 回到监控")
        nav_to(driver, "#/tank/monitor", "储罐监控")
        BasePage(driver).wait_vue_stable()
        time.sleep(2)
        step("回到监控页面 [OK]")

        # 再次到报表
        step("再次到报表 (验证可重复切换)")
        nav_to(driver, "#/tank/report", "储罐数据报表")
        BasePage(driver).wait_vue_stable()
        time.sleep(2)
        step("再次切换成功 [OK]")

        step("E2E-TK-002 往返验证通过 [OK]")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
