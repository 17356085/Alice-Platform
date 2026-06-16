"""班次班组配置模块测试

测试层次：
  P0 - 页面加载 & 搜索区展示
  P1 - 新增弹窗交互
  P2 - 搜索/重置功能
"""
import logging
import os
import sys

import allure
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.production_page.ShiftTeamConfigPage import ShiftTeamConfigPage

logger = logging.getLogger(__name__)


def step(text):
    try:
        with allure.step(text):
            pass
    except Exception:
        pass


def case(case_id, title):
    logger.info("========== 用例 %s：%s ==========", case_id, title)
    try:
        allure.dynamic.title(f"{case_id} {title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


# ══════════════════════════════════════════════════════════════════
#  P0 - 页面加载
# ══════════════════════════════════════════════════════════════════
class TestShiftTeamConfigDisplay:

    @pytest.mark.smoke
    @allure.epic("生产管理")
    @allure.feature("班次班组配置")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_page_load_basic_elements(self, shift_team_config_page):
        """TC-PROD-STC-001: 页面基本元素加载验证"""
        case("TC-PROD-STC-001", "页面基本元素加载验证")
        page = shift_team_config_page

        with allure.step("验证搜索区可见"):
            assert page.is_visible(page.INPUT_FACTORY), "工厂输入框不可见"
            assert page.is_visible(page.INPUT_TEAM), "班组输入框不可见"
            assert page.is_visible(page.INPUT_SHIFT), "班次输入框不可见"
            assert page.is_visible(page.BTN_SEARCH), "搜索按钮不可见"
            assert page.is_visible(page.BTN_RESET), "重置按钮不可见"
            assert page.is_visible(page.BTN_ADD), "新增按钮不可见"

        with allure.step("验证表格可见"):
            assert page.is_visible(page.TABLE), "表格不可见"

        with allure.step("验证表头"):
            headers = page.get_table_headers()
            logger.info("表头: %s", headers)
            for col in ["工厂", "排班类型", "班组", "班次"]:
                assert any(col in h for h in headers), f"表头缺少列'{col}'，实际: {headers}"


# ══════════════════════════════════════════════════════════════════
#  P1 - 新增弹窗
# ══════════════════════════════════════════════════════════════════
class TestShiftTeamConfigAdd:

    @allure.epic("生产管理")
    @allure.feature("班次班组配置")
    @allure.story("新增弹窗")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_open_add_dialog(self, shift_team_config_page):
        """TC-PROD-STC-002: 打开新增弹窗"""
        case("TC-PROD-STC-002", "打开新增弹窗")
        page = shift_team_config_page
        page.click_add()

        title = page.get_dialog_title()
        logger.info("弹窗标题: %s", title)
        assert "新增" in title or "班次班组" in title, ea(
            "弹窗标题包含'新增'或'班次班组'", f"标题: {title}"
        )
        page.click_dialog_cancel()

    @allure.epic("生产管理")
    @allure.feature("班次班组配置")
    @allure.story("新增弹窗")
    @allure.severity(allure.severity_level.NORMAL)
    def test_fill_add_form_then_cancel(self, shift_team_config_page):
        """TC-PROD-STC-003: 填写新增表单后取消"""
        case("TC-PROD-STC-003", "填写新增表单后取消")
        page = shift_team_config_page
        page.click_add()

        page.fill_dialog_field("工厂", "1000")
        page.fill_dialog_field("时段", "08:00-20:00")
        page.fill_dialog_field("日期", "20260612")
        page.fill_dialog_field("班组", "白班")
        page.fill_dialog_field("班次", "运行一部")

        # 取消 → 弹窗关闭，数据不保存
        page.click_dialog_cancel()
        assert not page.is_visible(page.DIALOG, timeout=3), "弹窗应已关闭"


# ══════════════════════════════════════════════════════════════════
#  P2 - 搜索功能
# ══════════════════════════════════════════════════════════════════
class TestShiftTeamConfigSearch:

    @allure.epic("生产管理")
    @allure.feature("班次班组配置")
    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_by_factory(self, shift_team_config_page):
        """TC-PROD-STC-004: 按工厂搜索"""
        case("TC-PROD-STC-004", "按工厂搜索")
        page = shift_team_config_page
        page.search(factory="1000")
        logger.info("搜索后表格行数: %d", page.get_row_count())
        # 无论有无数据，搜索不报错即通过
        assert page.is_visible(page.TABLE), "搜索后表格应可见"

    @allure.epic("生产管理")
    @allure.feature("班次班组配置")
    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_reset_search(self, shift_team_config_page):
        """TC-PROD-STC-005: 重置搜索条件"""
        case("TC-PROD-STC-005", "重置搜索条件")
        page = shift_team_config_page
        page.search(factory="1000")
        page.click_reset()
        # 重置后输入框应清空
        factory_val = page.find(page.INPUT_FACTORY).get_attribute("value")
        assert not factory_val, ea("工厂输入框清空", f"仍为: {factory_val}")
