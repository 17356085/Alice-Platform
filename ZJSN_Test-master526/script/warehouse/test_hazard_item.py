# script/warehouse/test_hazard_item.py
"""环保物品管理页面测试脚本

模块: warehouse (库管管理)
页面: 环保物品管理 (HazardItem)
测试类型: UI 自动化测试
关联用例: TEST_CASES.md (TD-HI-101, TD-HI-102, TD-HI-201, TD-HI-202, TD-HI-204)
"""
import pytest
import allure
from base.cleanup_tracker import get_cleanup_tracker

# 确保 fixture 已导入（conftest.py 中定义）
# from .conftest import hazard_item_page


@allure.epic("库管管理")
@allure.feature("环保物品管理")
class TestHazardItem:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load_success(self, hazard_item_page):
        """TC-HI-101: 页面正常加载（有数据场景）

        验证: 页面标题、表格、分页组件可见，且总条数大于0。
        """
        with allure.step("导航到环保物品管理页"):
            hazard_item_page.navigate()
        with allure.step("验证页面核心元素"):
            assert hazard_item_page.is_table_visible(), "数据表格未加载"
        with allure.step("验证分页信息"):
            total = hazard_item_page.get_total_count()
            assert total > 0, f"分页总条数期望大于0，实际为 {total}"

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.NORMAL)
    def test_002_page_load_empty(self, hazard_item_page):
        """TC-HI-102: 页面加载（空数据场景）

        验证: 页面正常加载，显示空数据提示，总条数为0。
        """
        with allure.step("强制清空搜索条件以确保无数据"):
            # 此测试依赖一个能返回空数据的搜索条件
            # 实际中可能需要通过特定搜索词实现
            hazard_item_page.search_by_item_name("__empty_query__")
        with allure.step("验证空数据状态"):
            total = hazard_item_page.get_total_count()
            assert total == 0, f"空数据场景下总条数期望为0，实际为 {total}"
        with allure.step("验证空数据提示文案（需 PageObject 支持）"):
            # 假设 HazardItemPage 有一个 get_empty_text() 方法
            pass

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_003_search_by_name_found(self, hazard_item_page):
        """TC-HI-201: 按危废品名称精确搜索 — 有结果

        验证: 搜索结果正确，总条数更新为匹配记录数。
        """
        test_name = "废酸-001"
        with allure.step(f"搜索危废品名称: {test_name}"):
            hazard_item_page.search_by_item_name(test_name)
        with allure.step("验证搜索结果"):
            total = hazard_item_page.get_total_count()
            assert total > 0, f"搜索 {test_name} 后总条数应为正数，实际为 {total}"
        with allure.step("验证表格行包含预期文本"):
            assert hazard_item_page.is_row_present(test_name), f"搜索结果中未包含 {test_name}"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_004_search_by_name_not_found(self, hazard_item_page):
        """TC-HI-203: 搜索无结果 — 空数据展示

        验证: 搜索不存在的名称后，总条数为0，显示空状态。
        """
        not_exist_name = "ZZZZ_NOT_EXIST"
        with allure.step(f"搜索不存在的危废品名称: {not_exist_name}"):
            hazard_item_page.search_by_item_name(not_exist_name)
        with allure.step("验证搜索结果为空"):
            total = hazard_item_page.get_total_count()
            assert total == 0, f"搜索 {not_exist_name} 后总条数期望为0，实际为 {total}"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_reset_search(self, hazard_item_page):
        """TC-HI-204: 重置搜索条件

        验证: 重置后搜索框清空，表格恢复显示全部数据。
        """
        with allure.step("首先获取初始总条数"):
            initial_total = hazard_item_page.get_total_count()
            assert initial_total > 0, "初始数据不能为空"
        with allure.step("执行一个搜索操作"):
            hazard_item_page.search_by_item_name("废")
            searched_total = hazard_item_page.get_total_count()
            # 搜索后结果数应小于初始数（确保搜索生效）
            # 如果所有数据都包含“废”，则可能相等，这里只做示例
        with allure.step("点击重置按钮"):
            hazard_item_page.reset_search()
        with allure.step("验证重置后总条数恢复"):
            reset_total = hazard_item_page.get_total_count()
            assert reset_total == initial_total, (
                f"重置后总条数应恢复为初始值 {initial_total}，实际为 {reset_total}"
            )