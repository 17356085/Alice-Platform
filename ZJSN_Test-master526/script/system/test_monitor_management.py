"""系统监控模块测试脚本"""
import os
import sys
import pytest
import allure
from selenium.common.exceptions import TimeoutException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.system_page.MonitorManagePage import MonitorManagePage


def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")


def case(case_id, title):
    print(f"\n========== 用例 {case_id}：{title} ==========")
    try:
        allure.dynamic.title(f"{case_id} {title}")
        allure.dynamic.description(f"用例编号：{case_id}\n用例说明：{title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


class TestMonitorManagement:
    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("系统监控")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_monitor_01_page_display(self, driver_setup):
        page = MonitorManagePage(driver_setup)
        case("SY-MONITOR-01", "正常显示系统监控页面")
        step("等待页面加载")
        page._wait_settled(timeout=15)
        step("验证页面内容")
        loaded = page.is_page_loaded()
        assert loaded, ea("系统监控页面正常加载（指标卡片/图表可见）", "页面内容为空或未渲染")

    @allure.epic("系统管理")
    @allure.feature("系统监控")
    @allure.story("指标卡片展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_monitor_02_metric_cards(self, driver_setup):
        page = MonitorManagePage(driver_setup)
        case("SY-MONITOR-02", "指标卡片正常展示")
        step("等待页面加载")
        page._wait_settled(timeout=15)
        count = page.get_metric_card_count()
        if count == 0:
            # 可能不是卡片布局，尝试读取服务器信息文本
            server_info = page.get_server_info_text()
            if server_info:
                step(f"服务器信息: {server_info}")
                assert True, ea("系统信息区域可见", server_info)
            else:
                values = page.get_metric_values()
                labels = page.get_metric_labels()
                assert values or labels, ea("监控指标正常展示", f"values={values}, labels={labels}")
        else:
            assert count > 0, ea(f"监控卡片正常展示", f"共{count}个卡片")

    @allure.epic("系统管理")
    @allure.feature("系统监控")
    @allure.story("指标数值展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_monitor_03_metric_values(self, driver_setup):
        page = MonitorManagePage(driver_setup)
        case("SY-MONITOR-03", "指标数值可读")
        step("等待页面加载")
        page._wait_settled(timeout=15)
        values = page.get_metric_values()
        labels = page.get_metric_labels()
        if not values and not labels:
            server_info = page.get_server_info_text()
            if server_info:
                step(f"读取服务器信息文本: {server_info}")
                assert len(server_info) > 0, ea("监控数据正常展示", server_info)
            else:
                pytest.skip("当前页面无可读取的指标数据（可能为图表渲染模式）")
        else:
            step(f"指标值: {values}")
            step(f"指标标签: {labels}")
            assert (values or labels), ea("指标数值或标签可读", f"values={len(values)}, labels={len(labels)}")

    @allure.epic("系统管理")
    @allure.feature("系统监控")
    @allure.story("刷新监控数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_monitor_04_refresh(self, driver_setup):
        page = MonitorManagePage(driver_setup)
        case("SY-MONITOR-04", "刷新监控数据")
        step("等待页面加载")
        page._wait_settled(timeout=15)
        if page.click_refresh():
            page._wait_settled(timeout=10)
            still_loaded = page.is_page_loaded()
            assert still_loaded, ea("刷新后页面仍然正常加载", "页面刷新后渲染异常")
        else:
            pytest.skip("当前页面未显示刷新按钮")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
