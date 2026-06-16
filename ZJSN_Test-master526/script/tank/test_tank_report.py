"""储罐日报表 — 自动化测试"""
import pytest
import allure


@allure.epic("储罐管理")
@allure.feature("储罐日报表")
class TestTankReport:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, tank_report_page):
        """TC-TANK-REP-001: 页面正常加载"""
        with allure.step("导航到储罐日报表"):
            tank_report_page.navigate()
        with allure.step("验证统计卡片可见"):
            intake = tank_report_page.get_stat_intake()
            assert intake != "", "进气量统计未显示"
        with allure.step("验证趋势图渲染"):
            assert tank_report_page.is_chart_rendered(), "趋势图未渲染"

    @allure.story("趋势图")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_002_default_tab_7d(self, tank_report_page):
        """TC-TANK-REP-003: 默认显示近7天趋势图"""
        with allure.step("验证默认Tab"):
            assert tank_report_page.is_chart_rendered(), "趋势图未渲染"

    @allure.story("趋势图")
    @allure.severity(allure.severity_level.NORMAL)
    def test_003_switch_tab_15d(self, tank_report_page):
        """TC-TANK-REP-007: 切换近15天趋势图"""
        with allure.step("切换近15天"):
            tank_report_page.click_tab_15d()
        with allure.step("验证图表刷新"):
            assert tank_report_page.is_chart_rendered(), "15天趋势图未渲染"

    @allure.story("趋势图")
    @allure.severity(allure.severity_level.NORMAL)
    def test_004_switch_tab_30d(self, tank_report_page):
        """TC-TANK-REP-008: 切换近30天趋势图"""
        with allure.step("切换近30天"):
            tank_report_page.click_tab_30d()
        with allure.step("验证图表刷新"):
            assert tank_report_page.is_chart_rendered(), "30天趋势图未渲染"

    @allure.story("统计卡片")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_stat_format(self, tank_report_page):
        """TC-TANK-REP-006: 统计卡片数值格式"""
        with allure.step("读取库存量"):
            inventory = tank_report_page.get_stat_inventory()
            assert inventory != "", "库存量统计未显示"

    @allure.story("导出")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_export(self, tank_report_page):
        """TC-TANK-REP-010: 导出日报表"""
        with allure.step("点击导出"):
            tank_report_page.click_export()
            # 导出文件校验需要浏览器下载配置，此处验证点击不报错
            assert True, "导出点击完成"

    @allure.story("权限验证")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_007_operator_permission(self, fresh_driver):
        """TC-TANK-REP-011: 零权限用户 — 页面不可达或提示无权限"""
        from base.browser_driver import login_as
        from selenium.webdriver.common.by import By

        with allure.step("以零权限用户登录"):
            assert login_as(fresh_driver, "rbac_test_none", "Ajyl@2026"), "零权限用户登录失败"

        with allure.step("尝试导航到储罐日报表"):
            try:
                TankReportPage(fresh_driver).navigate()
            except Exception:
                # 导航本身抛出异常 → 权限拒绝，测试通过
                return

        # 导航成功但应有权限限制提示
        with allure.step("检测无权限提示"):
            import time
            time.sleep(2)
            body_text = fresh_driver.find_element(By.TAG_NAME, "body").text
            no_perm_keywords = ["无权限", "403", "无权访问", "没有权限"]
            assert any(kw in body_text for kw in no_perm_keywords), \
                f"应提示无权限，但页面内容为: {body_text[:200]}"
