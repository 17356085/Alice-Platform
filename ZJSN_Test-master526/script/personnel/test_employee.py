"""
测试脚本: 员工管理 (Employee)
模块: personnel
页面: employee
"""
import pytest
import allure
from base.cleanup_tracker import get_cleanup_tracker

@allure.epic("人员管理")
@allure.feature("员工管理")
class TestEmployee:
    """员工管理页面的测试类"""

    @allure.story("页面加载与展示")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, employee_page):
        """TC-EMP-001: 页面正常加载"""
        with allure.step("导航到员工管理页面"):
            employee_page.navigate()
        with allure.step("验证页面标题"):
            assert employee_page.is_title_displayed(), "员工管理页面标题未显示"
    
    @allure.story("空数据状态")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_empty_table(self, employee_page):
        """TC-EMP-002: 空数据状态展示"""
        with allure.step("导航到员工管理页面"):
            employee_page.navigate()
        with allure.step("验证空数据提示"):
            assert employee_page.is_empty_state_displayed(), "空数据状态提示未显示"

    @allure.story("页面搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_003_search_by_name(self, employee_page):
        """TC-EMP-004: 按姓名精确搜索"""
        search_name = "张三"
        with allure.step(f"输入搜索关键词: {search_name}"):
            employee_page.enter_search_keyword(search_name)
        with allure.step("点击搜索按钮"):
            employee_page.click_search()
        with allure.step("验证搜索结果"):
            search_results = employee_page.get_table_data()
            assert len(search_results) == 1, f"搜索 {search_name} 后，预期结果数量为1，实际为 {len(search_results)}"
            assert any("张三" in row for row in search_results), f"搜索结果中未包含预期员工: 张三"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_004_search_by_department(self, employee_page):
        """TC-EMP-005: 按部门筛选"""
        department = "技术部"
        with allure.step(f"选择部门筛选条件: {department}"):
            employee_page.select_department(department)
        with allure.step("点击搜索按钮"):
            employee_page.click_search()
        with allure.step("验证搜索结果"):
            search_results = employee_page.get_table_data()
            assert len(search_results) > 0, f"筛选部门 {department} 后，搜索结果为空"

    @allure.story("搜索功能 - 重置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_reset_search(self, employee_page):
        """TC-EMP-007: 重置筛选条件"""
        with allure.step("先执行一个筛选"):
            employee_page.select_department("技术部")
            employee_page.click_search()
        with allure.step("点击重置按钮"):
            employee_page.click_reset_search()
        with allure.step("验证恢复默认状态"):
            assert employee_page.is_search_default(), "重置后搜索条件未恢复默认"

    @allure.story("表格操作 - 分页")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_006_pagination(self, employee_page):
        """TC-EMP-012: 分页功能"""
        with allure.step("导航到员工管理页面"):
            employee_page.navigate()
        with allure.step("验证分页控件可见"):
            assert employee_page.is_pagination_visible(), "分页控件未显示"
        with allure.step("验证首页与页码范围"):
            assert employee_page.get_current_page() == 1, "应为第一页"
            total_pages = employee_page.get_total_pages()
            assert total_pages >= 1, "总页数应大于等于1"

    @allure.story("新增操作 - 弹窗")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_007_open_add_dialog(self, employee_page):
        """TC-EMP-014: 打开新增弹窗"""
        with allure.step("点击新增员工按钮"):
            employee_page.click_add_button()
        with allure.step("验证弹窗显示"):
            assert employee_page.is_add_dialog_visible(), "新增员工弹窗未显示"

    @allure.story("新增操作 - 必填校验")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_008_add_required_fields(self, employee_page):
        """TC-EMP-015: 必填项校验"""
        with allure.step("打开新增弹窗"):
            employee_page.click_add_button()
            assert employee_page.is_add_dialog_visible(), "新增弹窗未出现"
        with allure.step("不填写任何必填项，直接点击保存"):
            employee_page.click_save_without_data()
        with allure.step("验证必填项提示"):
            assert employee_page.are_required_field_errors_visible(), "必填项校验提示未显示"
        with allure.step("关闭弹窗"):
            employee_page.click_add_dialog_cancel()

    @allure.story("新增操作 - 唯一性校验")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_009_add_duplicate_id_card(self, employee_page):
        """TC-EMP-016: 身份证号唯一性校验"""
        duplicate_id = "110101199003071234"
        with allure.step("输入已存在的身份证号"):
            employee_page.click_add_button()
            employee_page.fill_employee_info(id_card=duplicate_id)
        with allure.step("点击保存"):
            employee_page.click_save()
        with allure.step("验证唯一性错误提示"):
            assert employee_page.is_duplicate_error_visible(), "重复身份证号未给出错误提示"
        with allure.step("关闭弹窗"):
            employee_page.click_add_dialog_cancel()

    @allure.story("新增操作 - 成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_010_add_employee_success(self, employee_page):
        """TC-EMP-017: 新增员工成功"""
        test_name = "TC-EMP-017"  # 用于数据清理追踪
        employee_data = {
            "name": test_name,
            "department": "技术部",
            "id_card": f"TEST{self._generate_timestamp_id()}"  # 生成测试用唯一身份证号
        }
        with allure.step("打开新增弹窗并填写完整信息"):
            employee_page.click_add_button()
            employee_page.fill_employee_info(**employee_data)
        with allure.step("点击保存"):
            employee_page.click_save()
        with allure.step("验证成功提示"):
            assert employee_page.is_success_message_visible(), "新增员工成功提示未显示"
        with allure.step("验证数据出现在列表中"):
            employee_page.enter_search_keyword(test_name)
            employee_page.click_search()
            search_results = employee_page.get_table_data()
            assert any(test_name in row for row in search_results), "新增的员工未出现在列表中"
    
    def _generate_timestamp_id(self):
        """生成基于时间戳的唯一ID，避免身份证号冲突"""
        import time
        return str(int(time.time()))[-8:]

    @allure.story("编辑操作 - 弹出编辑框")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_011_edit_dialog(self, employee_page):
        """TC-EMP-019: 编辑员工"""
        with allure.step("选中第一个员工行"):
            employee_page.select_first_row()
        with allure.step("点击编辑按钮"):
            employee_page.click_edit()
        with allure.step("验证编辑弹窗显示"):
            assert employee_page.is_edit_dialog_visible(), "编辑弹窗未显示"

    @allure.story("删除操作")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_012_delete_employee(self, employee_page):
        """TC-EMP-022: 删除员工"""
        test_name = "TC-EMP-012"
        with allure.step("确认存在可删除的员工"):
            # 先确保有一个可删除的测试员工
            # 这里假设我们已有一个名为 test_name 的员工
            employee_page.enter_search_keyword(test_name)
            employee_page.click_search()
            assert employee_page.get_table_data_count() > 0, f"未找到可删除的员工 {test_name}"
        with allure.step("选中要删除的员工"):
            employee_page.select_first_row()
        with allure.step("点击删除按钮"):
            employee_page.click_delete()
        with allure.step("确认删除操作"):
            employee_page.confirm_delete()
        with allure.step("验证删除成功"):
            assert employee_page.is_delete_success_message_visible(), "删除成功提示未显示"

    @allure.story("页面导出功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_013_export_data(self, employee_page):
        """TC-EMP-023: 导出员工数据"""
        with allure.step("点击导出按钮"):
            employee_page.click_export()
        with allure.step("等待文件下载完成"):
            # 注意：Page Object 中已处理文件下载逻辑
            assert employee_page.is_download_completed(), "员工数据导出文件未下载成功"

    @allure.story("权限验证")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_014_permission_denied(self, employee_page):
        """TC-EMP-003: 无权限用户访问"""
        with allure.step("尝试以无权限用户访问页面"):
            # 注意：员工页面 fixture 在 conftest 中已处理权限控制
            employee_page.navigate()
        with allure.step("验证权限不足提示"):
            assert employee_page.is_permission_denied_displayed(), "页面对无权限用户未显示403或跳转提示"

    @allure.story("搜索-超长文本")
    @allure.severity(allure.severity_level.NORMAL)
    def test_015_search_long_text(self, employee_page):
        """TC-EMP-009: 超长搜索词限制"""
        long_keyword = "A" * 2000
        with allure.step(f"输入超长搜索文本 (长度为 {len(long_keyword)})"):
            employee_page.enter_search_keyword(long_keyword)
        with allure.step("验证搜索框限制输入字符数"):
            actual_value = employee_page.get_search_input_value()
            assert len(actual_value) <= 100, f"搜索框允许输入的字符数超过限制, 实际长度为 {len(actual_value)}"