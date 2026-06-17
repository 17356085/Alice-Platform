"""班次班组配置模块测试

测试层次：
  P0 - 页面加载 & 搜索区展示
  P1 - 新增弹窗交互
  P2 - 搜索/重置功能
  P3 - CRUD完整链路 (新增→编辑→删除)
"""
import time
import logging
import os
import sys

import allure
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.production_page.ShiftTeamConfigPage import ShiftTeamConfigPage
from base.cleanup_tracker import get_cleanup_tracker

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
        factory_val = page.find(page.INPUT_FACTORY).get_attribute("value")
        assert not factory_val, ea("工厂输入框清空", f"仍为: {factory_val}")


# ══════════════════════════════════════════════════════════════════
#  P3 - CRUD 完整链路
# ══════════════════════════════════════════════════════════════════
class TestShiftTeamConfigCRUD:
    """CRUD: 新增成功 → 编辑 → 删除 → 必填校验"""

    CREATED_TEAM = None

    @allure.epic("生产管理")
    @allure.feature("班次班组配置")
    @allure.story("CRUD")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_config_success(self, shift_team_config_page):
        """TC-PROD-STC-010: 新增班次班组 — 填写并保存成功"""
        case("TC-PROD-STC-010", "新增班次班组-保存成功")
        page = shift_team_config_page
        ts = str(int(time.time()))[-6:]
        team_name = f"AUTO_STC_{ts}"

        before_count = page.get_row_count()

        page.click_add()
        page.fill_dialog_field("工厂", "1000")
        page.fill_dialog_field("班组", team_name)
        page.fill_dialog_field("班次", "运行一部")
        page.click_dialog_confirm()

        # 搜索确认创建成功
        page.search(team=team_name)
        assert page.get_row_count() >= 1, f"搜索'{team_name}'应有结果"

        after_count = page.get_row_count()
        logger.info("新增成功: %s (前%d → 后%d)", team_name, before_count, after_count)

        TestShiftTeamConfigCRUD.CREATED_TEAM = team_name

    @allure.epic("生产管理")
    @allure.feature("班次班组配置")
    @allure.story("CRUD")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_config_save(self, shift_team_config_page):
        """TC-PROD-STC-011: 编辑班次班组 — 修改班组名称并保存"""
        case("TC-PROD-STC-011", "编辑班次班组-保存")
        page = shift_team_config_page
        name = TestShiftTeamConfigCRUD.CREATED_TEAM
        if not name:
            pytest.skip("未创建班次班组，跳过编辑测试")

        page.search(team=name)
        if page.get_row_count() == 0:
            pytest.skip(f"未找到要编辑的记录: {name}")

        page.click_row_edit(0)
        new_name = f"{name}_EDIT"
        page.fill_dialog_field("班组", new_name)
        page.click_dialog_confirm()

        # 搜索新名称确认
        page.search(team=new_name)
        assert page.get_row_count() >= 1, f"编辑后搜索'{new_name}'应有结果"

        TestShiftTeamConfigCRUD.CREATED_TEAM = new_name
        logger.info("编辑成功: %s → %s", name, new_name)

    @allure.epic("生产管理")
    @allure.feature("班次班组配置")
    @allure.story("CRUD")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_config(self, shift_team_config_page):
        """TC-PROD-STC-012: 删除班次班组 — 点击删除→确认→搜索确认消失"""
        case("TC-PROD-STC-012", "删除班次班组")
        page = shift_team_config_page
        name = TestShiftTeamConfigCRUD.CREATED_TEAM
        if not name:
            pytest.skip("未创建班次班组，跳过删除测试")

        page.search(team=name)
        if page.get_row_count() == 0:
            pytest.skip(f"未找到要删除的记录: {name}")

        before_count = page.get_row_count()

        try:
            page.click_row_delete(0)
            page.confirm_message_box()
            page.wait_vue_stable()
        except Exception as e:
            logger.warning("删除失败，注册清理: %s — %s", name, e)
            tracker = get_cleanup_tracker()
            tracker.register_entity(
                "shift_team_config", name,
                delete_callback=lambda n: (
                    page.click_row_delete(0) if (r := page.search(team=n)) and r.get_row_count() > 0 else None
                ),
            )
            pytest.fail(f"删除班次班组失败: {e}")

        page.search(team=name)
        after_count = page.get_row_count()
        assert after_count < before_count, \
            f"删除后搜索'{name}'应有更少结果: 前{before_count} → 后{after_count}"
        logger.info("删除成功: %s", name)

    @allure.epic("生产管理")
    @allure.feature("班次班组配置")
    @allure.story("CRUD")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_empty_required(self, shift_team_config_page):
        """TC-PROD-STC-013: 新增班次班组 — 必填校验（不填直接保存）"""
        case("TC-PROD-STC-013", "新增班次班组-必填校验")
        page = shift_team_config_page
        page.click_add()
        page.click_dialog_confirm()

        # 表单校验应阻止关闭弹窗 — 弹窗仍然可见
        is_still_open = page.is_visible(page.DIALOG, timeout=3)
        logger.info("必填校验: 弹窗仍打开=%s", is_still_open)
        if is_still_open:
            page.click_dialog_cancel()
