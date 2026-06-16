"""储罐监控管理 — 自动化测试"""
import pytest
import allure
from page.tank_page.TankMonitorPage import TankMonitorPage


@allure.epic("储罐管理")
@allure.feature("储罐监控管理")
class TestTankMonitor:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, tank_monitor_page):
        """TC-TANK-MON-001: 页面正常加载"""
        with allure.step("导航到储罐监控管理"):
            tank_monitor_page.navigate()
        with allure.step("验证统计卡片"):
            assert tank_monitor_page.get_stat_card_count() >= 4, "统计卡片未完整加载"
        with allure.step("验证表格"):
            headers = tank_monitor_page.get_table_headers_text()
            assert len(headers) >= 10, f"表头列数不足: {len(headers)}"

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.NORMAL)
    def test_002_stat_cards(self, tank_monitor_page):
        """TC-TANK-MON-002: 统计卡片数值显示"""
        with allure.step("获取统计卡片值"):
            values = tank_monitor_page.get_stat_values()
        with allure.step("验证储罐总数存在"):
            assert values.get("储罐总数", "") != "", "储罐总数未显示"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_003_search_by_tank_id(self, tank_monitor_page):
        """TC-TANK-MON-003: 按储罐编号精确搜索"""
        with allure.step("搜索 TANK-LNG-001"):
            tank_monitor_page.search("TANK-LNG-001")
        with allure.step("验证搜索结果"):
            count = tank_monitor_page.get_table_row_count()
            assert count > 0, "搜索结果为空"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_004_search_by_keyword(self, tank_monitor_page):
        """TC-TANK-MON-004: 按名称模糊搜索"""
        with allure.step("输入关键词"):
            tank_monitor_page.search("LNG")
        with allure.step("验证结果不为空"):
            assert tank_monitor_page.get_table_row_count() > 0, "搜索结果为空"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_search_no_match(self, tank_monitor_page):
        """TC-TANK-MON-008: 搜索无匹配结果"""
        with allure.step("搜索不存在的关键词"):
            tank_monitor_page.search("xyz_not_exist_tank_999")
        with allure.step("验证空数据"):
            assert tank_monitor_page.is_table_empty(), "应显示空数据"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_reset_search(self, tank_monitor_page):
        """TC-TANK-MON-009: 重置搜索条件"""
        with allure.step("先搜索再重置"):
            tank_monitor_page.search("LNG")
            count_before = tank_monitor_page.get_table_row_count()
            tank_monitor_page.reset_search()
        with allure.step("验证重置后数据恢复"):
            count_after = tank_monitor_page.get_table_row_count()
            assert count_after >= count_before, "重置后数据不应少于搜索时"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_007_search_special_chars(self, tank_monitor_page):
        """TC-TANK-MON-010: 特殊字符搜索"""
        with allure.step("输入 XSS 注入字符串"):
            tank_monitor_page.search("<script>alert(1)</script>")
        with allure.step("验证页面无崩溃"):
            assert tank_monitor_page.is_visible(tank_monitor_page.TABLE, timeout=3), "表格应存在"

    @allure.story("表格验证")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_008_table_headers(self, tank_monitor_page):
        """TC-TANK-MON-011: 表头列验证"""
        with allure.step("读取表头"):
            headers = tank_monitor_page.get_table_headers_text()
        with allure.step("验证核心列存在"):
            core_columns = ["储罐编号", "储罐名称", "运行状态", "操作"]
            for col in core_columns:
                assert col in headers, f"缺少核心列: {col}"

    @allure.story("查看详情")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_009_view_detail(self, tank_monitor_page):
        """TC-TANK-MON-013: 查看储罐详情"""
        with allure.step("先重置搜索确保有数据"):
            tank_monitor_page.reset_search()
        with allure.step("点击第一行查看按钮"):
            row_count = tank_monitor_page.get_table_row_count()
            if row_count > 0:
                tank_monitor_page.click_view()
                dialog = tank_monitor_page.wait_dialog_visible(timeout=5)
                assert dialog is not None, "详情弹窗未出现"
            else:
                pytest.skip("无数据可查看")

    @allure.story("分页")
    @allure.severity(allure.severity_level.NORMAL)
    def test_010_pagination(self, tank_monitor_page):
        """TC-TANK-MON-016: 分页控件显示"""
        with allure.step("验证分页控件"):
            assert tank_monitor_page.get_current_page() >= 1, "分页控件未显示"

    @allure.story("权限验证")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_011_operator_permission(self, fresh_driver):
        """TC-TANK-MON-015: 操作工登录 — 表格可见，增删改导入导出按钮隐藏"""
        from base.browser_driver import login_as
        from selenium.webdriver.common.by import By

        with allure.step("以只读用户登录"):
            assert login_as(fresh_driver, "rbac_test_ro", "Ajyl@2026"), "只读用户登录失败"

        page = TankMonitorPage(fresh_driver)

        with allure.step("导航到储罐监控管理"):
            page.navigate()

        with allure.step("验证表格可见"):
            assert page.get_table_row_count() > 0, "表格应对只读用户可见"

        with allure.step("验证新增储罐按钮隐藏"):
            assert not page.is_visible(page.ADD_BTN, timeout=2), "新增按钮应对只读用户隐藏"

        with allure.step("验证导入按钮隐藏"):
            assert not page.is_visible(page.IMPORT_BTN, timeout=2), "导入按钮应隐藏"

        with allure.step("验证导出按钮隐藏"):
            assert not page.is_visible(page.EXPORT_BTN, timeout=2), "导出按钮应隐藏"

        with allure.step("验证编辑按钮不可见"):
            rows = page.find_all(page.TABLE_ROWS)
            if rows:
                btns = rows[0].find_elements(By.TAG_NAME, "button")
                edit_visible = any(
                    "编辑" in (b.text or "") and b.is_displayed()
                    for b in btns
                )
                assert not edit_visible, "编辑按钮应对只读用户隐藏"

    @allure.story("新增弹窗字段")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_012_add_dialog_fields(self, tank_monitor_page):
        """TD-TANK-MON-012: 打开新增弹窗 → 验证表单字段完整"""
        with allure.step("点击新增储罐按钮"):
            tank_monitor_page.click(tank_monitor_page.ADD_BTN)
        with allure.step("等待弹窗出现"):
            assert tank_monitor_page.wait_dialog_visible(timeout=5) is not None, "新增弹窗未出现"
        with allure.step("验证弹窗标题"):
            title = tank_monitor_page.get_dialog_title()
            assert "新增" in title, f"弹窗标题异常: {title}"
        with allure.step("验证必填字段存在"):
            for label in tank_monitor_page.REQUIRED_FIELDS:
                try:
                    tank_monitor_page._get_dialog_form_item(label, timeout=3)
                except Exception:
                    pytest.fail(f"必填字段缺失: {label}")
        with allure.step("验证可选字段存在"):
            optional = [tank_monitor_page.FIELD_LABEL_AREA,
                        tank_monitor_page.FIELD_LABEL_COMMISSION_DATE,
                        tank_monitor_page.FIELD_LABEL_CHECK_DATE,
                        tank_monitor_page.FIELD_LABEL_REMARK]
            for label in optional:
                try:
                    tank_monitor_page._get_dialog_form_item(label, timeout=3)
                except Exception:
                    pytest.fail(f"可选字段缺失: {label}")
        with allure.step("关闭弹窗"):
            tank_monitor_page.close_dialog()

    @allure.story("新增储罐")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_013_add_tank_success(self, tank_monitor_page):
        """TD-TANK-MON-013: 填写有效数据 → 提交成功"""
        import time
        ts = str(int(time.time()))[-6:]

        with allure.step("点击新增储罐"):
            tank_monitor_page.click(tank_monitor_page.ADD_BTN)
            assert tank_monitor_page.wait_dialog_visible(timeout=5) is not None

        with allure.step("填写表单"):
            tank_monitor_page.fill_dialog_input("储罐编号", f"TEST-{ts}")
            tank_monitor_page.fill_dialog_input("储罐名称", f"AutoTank_{ts}")
            tank_monitor_page.fill_dialog_input("设计容量", "5000")

        with allure.step("点击保存（使用 BasePage click_dialog_save 避免遮挡）"):
            tank_monitor_page.click_dialog_save()

        with allure.step("验证提交成功"):
            toast = tank_monitor_page.get_toast_text(timeout=5)
            assert "成功" in toast, f"未显示成功提示: {toast}"

        # 清理：搜索并删除测试数据（如果支持删除）
        with allure.step("搜索确认记录已创建"):
            tank_monitor_page.search(f"TEST-{ts}")
            assert tank_monitor_page.get_table_row_count() >= 1, "新增记录未出现在表格"

    @allure.story("新增弹窗字段")
    @allure.severity(allure.severity_level.NORMAL)
    def test_014_required_field_validation(self, tank_monitor_page):
        """TD-TANK-MON-014: 必填项为空 → 校验错误"""
        with allure.step("点击新增储罐"):
            tank_monitor_page.click(tank_monitor_page.ADD_BTN)
            assert tank_monitor_page.wait_dialog_visible(timeout=5) is not None

        with allure.step("不填写任何必填项，直接提交"):
            tank_monitor_page.click_dialog_save()

        with allure.step("验证校验错误提示"):
            try:
                error = tank_monitor_page.get_form_error(timeout=3)
                assert error != "", "应显示校验错误"
            except Exception:
                # 兜底：检查 body 中是否有校验关键字
                body = tank_monitor_page.driver.find_element(
                    "tag name", "body"
                ).text
                assert any(kw in body for kw in ["不能为空", "请输入", "必填"]), \
                    f"未检测到校验错误提示: {body[:200]}"

        with allure.step("关闭弹窗"):
            tank_monitor_page.close_dialog()

    @allure.story("新增弹窗字段")
    @allure.severity(allure.severity_level.NORMAL)
    def test_015_double_click_submit(self, tank_monitor_page):
        """TD-TANK-MON-015: 双击提交 → 仅一次提交"""
        import time
        ts = str(int(time.time()))[-6:]

        with allure.step("点击新增储罐"):
            tank_monitor_page.click(tank_monitor_page.ADD_BTN)
            assert tank_monitor_page.wait_dialog_visible(timeout=5) is not None

        with allure.step("填写表单"):
            tank_monitor_page.fill_dialog_input("储罐编号", f"DC-{ts}")
            tank_monitor_page.fill_dialog_input("储罐名称", f"DoubleClick_{ts}")
            tank_monitor_page.fill_dialog_input("设计容量", "3000")

        with allure.step("双击保存按钮"):
            btn = tank_monitor_page.find(tank_monitor_page.DIALOG_CONFIRM)
            tank_monitor_page._js_click_el(btn)
            tank_monitor_page.wait_vue_stable()
            # 验证按钮是否被禁用（防重复提交）
            try:
                tank_monitor_page._js_click_el(btn)
            except Exception:
                pass  # 二次点击可能因按钮 disabled 而失败，符合预期
            tank_monitor_page.wait_vue_stable()

        with allure.step("搜索验证仅创建一条记录"):
            tank_monitor_page.search(f"DC-{ts}")
            count = tank_monitor_page.get_table_row_count()
            assert count <= 1, f"双击导致重复创建: 发现 {count} 条记录"

    @allure.story("导出")
    @allure.severity(allure.severity_level.NORMAL)
    def test_016_export_verify(self, tank_monitor_page):
        """TC-TANK-MON-017: 导出 Excel → 验证文件下载成功"""
        import os
        from base.file_util import wait_for_download

        download_dir = getattr(tank_monitor_page.driver, "download_dir", "")

        with allure.step("点击导出按钮"):
            tank_monitor_page.click(tank_monitor_page.EXPORT_BTN)

        with allure.step("等待文件下载完成"):
            file_path = wait_for_download(download_dir, timeout=30, file_pattern="*.xlsx")

        with allure.step("验证文件存在且非空"):
            assert file_path is not None, "导出文件未下载"
            assert os.path.exists(file_path), f"文件路径无效: {file_path}"
            assert os.path.getsize(file_path) > 0, "导出的文件为空"

        with allure.step("清理下载文件"):
            try:
                os.remove(file_path)
            except Exception:
                pass

    @allure.story("导入")
    @allure.severity(allure.severity_level.NORMAL)
    def test_017_import_verify(self, tank_monitor_page):
        """TC-TANK-MON-018: 导出模板 → 上传导入 → 验证结果"""
        import os
        from base.file_util import wait_for_download

        download_dir = getattr(tank_monitor_page.driver, "download_dir", "")

        # Step 1: 导出模板
        with allure.step("导出文件作为导入模板"):
            tank_monitor_page.click(tank_monitor_page.EXPORT_BTN)
            template = wait_for_download(download_dir, timeout=30, file_pattern="*.xlsx")
            assert template is not None and os.path.getsize(template) > 0, "模板下载失败"

        # Step 2: 导入
        with allure.step("上传并导入"):
            tank_monitor_page.click_import_open()
            tank_monitor_page.upload_import_file(template)
            tank_monitor_page.click_start_import()

        with allure.step("等待导入结果"):
            result = tank_monitor_page.wait_import_result(timeout=30)
            assert result != "", "未显示导入结果"

        with allure.step("验证导入结束"):
            tank_monitor_page.close_dialog()

        with allure.step("清理"):
            try:
                os.remove(template)
            except Exception:
                pass
