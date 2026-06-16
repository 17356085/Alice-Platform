"""报警配置 — 自动化测试"""
import pytest
import allure
import time
from selenium.webdriver.common.by import By


@allure.epic("储罐管理")
@allure.feature("报警配置")
class TestTankAlarmConfig:

    @allure.story("弹窗加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_dialog_open(self, tank_monitor_page):
        """TC-TANK-ALM-001: 弹窗正常打开"""
        with allure.step("导航到储罐监控管理"):
            tank_monitor_page.navigate()

        with allure.step("点击配置报警按钮（触发弹窗）"):
            # 需要先定位到配置报警按钮并点击
            # 这里假设父页面有"配置报警"按钮，实际定位器需要根据页面调整
            config_btn_locator = (
                tank_monitor_page.driver.find_element(
                    tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
                )
            )
            config_btn_locator.click()

        with allure.step("验证弹窗打开"):
            from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage
            alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
            assert alarm_page.wait_dialog_open(), "弹窗未打开"
            assert "报警配置" in alarm_page.get_dialog_title(), "弹窗标题不正确"

    @allure.story("表单填写")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_002_fill_valid_form(self, tank_monitor_page):
        """TC-TANK-ALM-002: 填写有效表单并提交"""
        from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

        with allure.step("导航并打开弹窗"):
            tank_monitor_page.navigate()
            # 打开弹窗（实际定位器需要根据页面调整）
            config_btn = tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
            config_btn.click()

        alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
        alarm_page.wait_dialog_open()

        with allure.step("填写表单"):
            alarm_page.fill_form(
                alarm_type="液位报警",
                email="test@example.com",
                remark="自动化测试创建"
            )

        with allure.step("验证表单值"):
            values = alarm_page.get_form_values()
            assert "液位报警" in values["alarm_type"], "报警类型未正确填写"
            assert values["alarm_email"] == "test@example.com", "邮箱未正确填写"

    @allure.story("表单验证")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_003_validate_empty_required_fields(self, tank_monitor_page):
        """TC-TANK-ALM-003: 必填字段为空时验证"""
        from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

        with allure.step("打开弹窗"):
            tank_monitor_page.navigate()
            config_btn = tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
            config_btn.click()

        alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
        alarm_page.wait_dialog_open()

        with allure.step("不填写任何字段直接提交"):
            alarm_page.click_save()

        with allure.step("验证表单验证错误"):
            assert alarm_page.has_form_errors(), "应显示表单验证错误"
            errors = alarm_page.get_form_errors()
            assert "报警类型" in errors or "报警邮箱" in errors, "必填字段应有验证提示"

    @allure.story("表单验证")
    @allure.severity(allure.severity_level.NORMAL)
    def test_004_validate_invalid_email(self, tank_monitor_page):
        """TC-TANK-ALM-004: 邮箱格式验证"""
        from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

        with allure.step("打开弹窗"):
            tank_monitor_page.navigate()
            config_btn = tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
            config_btn.click()

        alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
        alarm_page.wait_dialog_open()

        with allure.step("填写无效邮箱"):
            alarm_page.fill_form(
                alarm_type="液位报警",
                email="invalid-email-format",  # 无效邮箱格式
                remark="测试邮箱验证"
            )

        with allure.step("提交并验证错误"):
            alarm_page.click_save()
            time.sleep(0.5)  # 等待验证
            assert alarm_page.has_form_errors(), "应显示邮箱格式错误"

    @allure.story("弹窗控制")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_cancel_dialog(self, tank_monitor_page):
        """TC-TANK-ALM-005: 取消关闭弹窗"""
        from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

        with allure.step("打开弹窗"):
            tank_monitor_page.navigate()
            config_btn = tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
            config_btn.click()

        alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
        alarm_page.wait_dialog_open()

        with allure.step("填写部分数据"):
            alarm_page.input_alarm_email("test@example.com")

        with allure.step("点击取消"):
            alarm_page.click_cancel()

        with allure.step("验证弹窗关闭"):
            assert alarm_page.wait_dialog_close(), "弹窗未关闭"

    @allure.story("表单操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_clear_form(self, tank_monitor_page):
        """TC-TANK-ALM-006: 清空表单"""
        from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

        with allure.step("打开弹窗"):
            tank_monitor_page.navigate()
            config_btn = tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
            config_btn.click()

        alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
        alarm_page.wait_dialog_open()

        with allure.step("填写表单"):
            alarm_page.fill_form(
                alarm_type="液位报警",
                email="test@example.com",
                remark="测试内容"
            )

        with allure.step("清空表单"):
            alarm_page.clear_form()

        with allure.step("验证表单已清空"):
            values = alarm_page.get_form_values()
            assert values["alarm_email"] == "", "邮箱应已清空"
            assert values["remark"] == "", "备注应已清空"

    @allure.story("下拉选择")
    @allure.severity(allure.severity_level.NORMAL)
    def test_007_select_alarm_types(self, tank_monitor_page):
        """TC-TANK-ALM-007: 测试不同报警类型选择"""
        from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

        alarm_types = ["液位报警", "温度报警", "压力报警"]  # 实际选项需要根据页面调整

        with allure.step("打开弹窗"):
            tank_monitor_page.navigate()
            config_btn = tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
            config_btn.click()

        alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
        alarm_page.wait_dialog_open()

        with allure.step("测试每种报警类型"):
            for alarm_type in alarm_types:
                with allure.step(f"选择 {alarm_type}"):
                    alarm_page.select_alarm_type(alarm_type)
                    actual_type = alarm_page.get_alarm_type_value()
                    # 注意：下拉框选中后的显示值可能不同，需要根据实际情况调整断言
                    assert actual_type != "", f"选择 {alarm_type} 后应有值"

    @allure.story("成功提交")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_008_submit_success(self, tank_monitor_page):
        """TC-TANK-ALM-008: 成功提交表单"""
        from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

        with allure.step("打开弹窗"):
            tank_monitor_page.navigate()
            config_btn = tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
            config_btn.click()

        alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
        alarm_page.wait_dialog_open()

        with allure.step("填写完整表单"):
            alarm_page.fill_form(
                alarm_type="液位报警",
                email=f"test_{int(time.time())}@example.com",  # 使用时间戳避免重复
                remark="自动化测试 - 正常提交"
            )

        with allure.step("提交表单"):
            alarm_page.submit_form()

        with allure.step("等待成功提示"):
            success_msg = alarm_page.wait_for_success_toast()
            assert success_msg != "", "应显示成功消息"
            assert "成功" in success_msg or "保存" in success_msg, "消息应包含成功提示"

        with allure.step("验证弹窗关闭"):
            assert alarm_page.wait_dialog_close(), "提交成功后弹窗应关闭"

    @allure.story("长文本处理")
    @allure.severity(allure.severity_level.NORMAL)
    def test_009_long_remark(self, tank_monitor_page):
        """TC-TANK-ALM-009: 长备注文本处理"""
        from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

        long_remark = "这是一段很长的备注文本，用于测试系统对长文本的处理能力。" * 5

        with allure.step("打开弹窗"):
            tank_monitor_page.navigate()
            config_btn = tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
            config_btn.click()

        alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
        alarm_page.wait_dialog_open()

        with allure.step("输入长备注"):
            alarm_page.fill_form(
                alarm_type="液位报警",
                email="test@example.com",
                remark=long_remark
            )

        with allure.step("验证长备注已输入"):
            actual_remark = alarm_page.get_remark_value()
            assert actual_remark == long_remark, "长备注应完整保存"

    @allure.story("特殊字符")
    @allure.severity(allure.severity_level.NORMAL)
    def test_010_special_chars(self, tank_monitor_page):
        """TC-TANK-ALM-010: 特殊字符处理"""
        from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

        special_remark = "测试特殊字符: <script>alert('xss')</script> & 'quotes' \"double\""

        with allure.step("打开弹窗"):
            tank_monitor_page.navigate()
            config_btn = tank_monitor_page.driver.find_element(By.XPATH, '//button[contains(.,"配置报警")]')
            config_btn.click()

        alarm_page = TankAlarmConfigPage(tank_monitor_page.driver)
        alarm_page.wait_dialog_open()

        with allure.step("输入特殊字符"):
            alarm_page.fill_form(
                alarm_type="液位报警",
                email="test@example.com",
                remark=special_remark
            )

        with allure.step("提交并验证"):
            alarm_page.submit_form()
            success_msg = alarm_page.get_toast_message()
            # 验证没有 XSS 错误
            assert "error" not in success_msg.lower(), "特殊字符处理应无错误"