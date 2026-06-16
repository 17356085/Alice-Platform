"""业务类型配置模块测试

测试层次：
  P0 - 页面加载 & 表格数据
  P1 - 新增弹窗交互
  P2 - 搜索/行级操作
"""
import logging
import os
import sys

import allure
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.production_page.BusinessTypeConfigPage import BusinessTypeConfigPage

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
#  P0 - 页面加载 & 表格
# ══════════════════════════════════════════════════════════════════
class TestBusinessTypeConfigDisplay:

    @pytest.mark.smoke
    @allure.epic("生产管理")
    @allure.feature("业务类型配置")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_page_load_basic_elements(self, business_type_config_page):
        """TC-PROD-BTC-001: 页面基本元素加载验证"""
        case("TC-PROD-BTC-001", "页面基本元素加载验证")
        page = business_type_config_page

        with allure.step("验证搜索区可见"):
            assert page.is_visible(page.INPUT_PLAN_PARAM), "计划参数输入框不可见"
            assert page.is_visible(page.INPUT_FACTORY), "工厂输入框不可见"
            assert page.is_visible(page.INPUT_MATERIAL), "物料编码输入框不可见"
            assert page.is_visible(page.BTN_SEARCH), "搜索按钮不可见"
            assert page.is_visible(page.BTN_RESET), "重置按钮不可见"
            assert page.is_visible(page.BTN_ADD), "新增按钮不可见"

        with allure.step("验证表格有数据"):
            row_count = page.get_row_count()
            logger.info("表格行数: %d", row_count)
            assert row_count > 0, f"表格无数据（预期≥1行）"

        with allure.step("验证表头"):
            headers = page.get_table_headers()
            logger.info("表头: %s", headers)
            for col in ["计划参数", "业务类型", "工厂", "物料编码"]:
                assert any(col in h for h in headers), f"表头缺少列'{col}'，实际: {headers}"

        with allure.step("验证分页"):
            total = page.get_pagination_total()
            logger.info("分页: %s", total)
            assert total, "分页信息为空"

    @pytest.mark.smoke
    @allure.epic("生产管理")
    @allure.feature("业务类型配置")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_delete_initially_disabled(self, business_type_config_page):
        """TC-PROD-BTC-002: 页面级删除按钮初始disabled"""
        case("TC-PROD-BTC-002", "页面级删除按钮初始disabled")
        page = business_type_config_page
        assert not page.is_batch_delete_enabled(), ea(
            "删除按钮初始disabled", "按钮未disabled"
        )


# ══════════════════════════════════════════════════════════════════
#  P0 - 搜索功能
# ══════════════════════════════════════════════════════════════════
class TestBusinessTypeConfigSearch:

    @allure.epic("生产管理")
    @allure.feature("业务类型配置")
    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search_by_factory(self, business_type_config_page):
        """TC-PROD-BTC-003: 按工厂搜索"""
        case("TC-PROD-BTC-003", "按工厂搜索")
        page = business_type_config_page
        page.search(factory="2547")
        row_count = page.get_row_count()
        logger.info("搜索后表格行数: %d", row_count)
        assert row_count > 0, f"按工厂2547搜索无结果（预期≥1行）"

    @allure.epic("生产管理")
    @allure.feature("业务类型配置")
    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_reset_search(self, business_type_config_page):
        """TC-PROD-BTC-004: 重置搜索条件"""
        case("TC-PROD-BTC-004", "重置搜索条件")
        page = business_type_config_page
        page.search(factory="2547")
        page.click_reset()
        factory_val = page.find(page.INPUT_FACTORY).get_attribute("value")
        assert not factory_val, ea("工厂输入框清空", f"仍为: {factory_val}")
        # 重置后应恢复全部数据
        assert page.get_row_count() > 0, "重置后应有数据"


# ══════════════════════════════════════════════════════════════════
#  P1 - 新增弹窗
# ══════════════════════════════════════════════════════════════════
class TestBusinessTypeConfigAdd:

    @allure.epic("生产管理")
    @allure.feature("业务类型配置")
    @allure.story("新增弹窗")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_open_add_dialog(self, business_type_config_page):
        """TC-PROD-BTC-005: 打开新增弹窗"""
        case("TC-PROD-BTC-005", "打开新增弹窗")
        page = business_type_config_page
        page.click_add()

        title = page.get_dialog_title()
        logger.info("弹窗标题: %s", title)
        assert "新增" in title or "业务类型" in title, ea(
            "弹窗标题包含'新增'或'业务类型'", f"标题: {title}"
        )
        page.click_dialog_cancel()

    @allure.epic("生产管理")
    @allure.feature("业务类型配置")
    @allure.story("新增弹窗")
    @allure.severity(allure.severity_level.NORMAL)
    def test_fill_add_form_then_cancel(self, business_type_config_page):
        """TC-PROD-BTC-006: 填写新增表单后取消"""
        case("TC-PROD-BTC-006", "填写新增表单后取消")
        page = business_type_config_page
        page.click_add()

        page.fill_dialog_field("计划参数", "10010001")
        page.fill_dialog_field("工厂", "2547")
        page.fill_dialog_field("物料编码", "600042")
        page.fill_dialog_field("库存地点", "Z001")
        page.fill_dialog_field("工序号", "0010")
        page.fill_dialog_field("工作中心", "CENTER1")

        page.click_dialog_cancel()
        assert not page.is_visible(page.DIALOG, timeout=3), "弹窗应已关闭"


# ══════════════════════════════════════════════════════════════════
#  P1 - 行级操作（只读验证）
# ══════════════════════════════════════════════════════════════════
class TestBusinessTypeConfigRowOps:

    @allure.epic("生产管理")
    @allure.feature("业务类型配置")
    @allure.story("行级操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_click_row_edit(self, business_type_config_page):
        """TC-PROD-BTC-007: 点击行编辑按钮打开弹窗"""
        case("TC-PROD-BTC-007", "点击行编辑按钮打开弹窗")
        page = business_type_config_page
        page.click_row_edit(0)

        title = page.get_dialog_title()
        logger.info("编辑弹窗标题: %s", title)
        assert "编辑" in title or "业务类型" in title, ea(
            "编辑弹窗打开", f"标题: {title}"
        )
        page.click_dialog_cancel()

    @allure.epic("生产管理")
    @allure.feature("业务类型配置")
    @allure.story("复选框")
    @allure.severity(allure.severity_level.NORMAL)
    def test_checkbox_enables_batch_delete(self, business_type_config_page):
        """TC-PROD-BTC-008: 勾选行后批量删除按钮启用"""
        case("TC-PROD-BTC-008", "勾选行后批量删除按钮启用")
        page = business_type_config_page
        page.select_row(0)
        assert page.is_batch_delete_enabled(), ea(
            "批量删除按钮启用", "按钮仍disabled"
        )
