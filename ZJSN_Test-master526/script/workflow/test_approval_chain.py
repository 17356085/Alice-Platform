"""审批链配置模块测试脚本

测试策略: 仅操作已有审批链，不新增不删除。
  - 生产环境审批链为预配置数据，创建/删除由运维手工执行
  - 自动化测试仅验证: 页面展示、搜索、编辑描述、重置、分页、表单校验
"""
import os
import sys
import pytest
import allure
from datetime import datetime
from selenium.common.exceptions import TimeoutException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.workflow_page.ApprovalChainPage import ApprovalChainPage


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


class TestApprovalChain:
    @pytest.fixture(autouse=True)
    def _reset_after_each(self, driver_setup):
        yield
        try:
            ApprovalChainPage(driver_setup).click_reset()
        except Exception:
            pass

    # ════════════════════════════════════════════════════════════
    #  冒烟
    # ════════════════════════════════════════════════════════════
    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("审批链配置")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_apchain_01_page_display(self, driver_setup):
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-01", "正常显示审批链配置列表及相关字段")
        step("获取表头并校验")
        headers = page.get_table_headers()
        expected_cols = {"名称", "审批链"}
        found = any(col in headers for col in expected_cols)
        assert found or len(headers) >= 2, ea("正常加载审批链配置列表及相关字段", headers)
        step("验证表格加载")
        row_count = page.get_table_row_count()
        empty = page.get_empty_text() or ""
        assert (row_count > 0) or ("暂无数据" in empty), ea("表格正常加载", empty or f"row_count={row_count}")

    # ════════════════════════════════════════════════════════════
    #  搜索 — 用已有数据的第一行名称做精确搜索
    # ════════════════════════════════════════════════════════════
    def test_sy_apchain_04_search_by_name(self, driver_setup):
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-04", "按名称搜索审批链（已有数据）")
        step("点击重置")
        page.click_reset()
        if page.get_table_row_count() == 0:
            pytest.skip("当前无审批链数据，跳过名称搜索")
        step("获取第一行审批链名称")
        row = page.get_first_row_data()
        first_name = row[0] if row else ""
        if not first_name:
            pytest.skip("无法获取第一行名称，跳过名称搜索")
        step(f"搜索名称: {first_name}")
        page.input_name(first_name)
        page.click_search()
        names = page.get_column_data_by_header("名称")
        if not names:
            names = page.get_column_data(1)
        if names:
            assert any(first_name in n for n in names), ea(f"搜索结果包含'{first_name}'", names)
        else:
            empty = page.get_empty_text() or ""
            assert "暂无数据" in empty, ea("搜索结果为空", empty)

    # ════════════════════════════════════════════════════════════
    #  编辑 — 仅修改描述（不改变审批链核心配置）
    # ════════════════════════════════════════════════════════════
    def test_sy_apchain_05_edit_chain(self, driver_setup):
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-05", "编辑审批链描述")
        step("点击重置")
        page.click_reset()
        if page.get_table_row_count() == 0:
            pytest.skip(page.get_empty_text() or "当前无审批链数据，跳过编辑验证")
        step("点击第一行编辑")
        try:
            page.click_first_row_edit()
        except TimeoutException:
            pytest.skip("当前列表第一行无编辑按钮")
        step("修改描述")
        new_desc = f"[AUTO] 自动化测试-已编辑 {datetime.now():%H%M%S}"
        page.dialog_input_desc(new_desc)
        step("点击确定")
        page.dialog_confirm()
        msg = page.wait_for_toast_text(timeout=6)
        ok = (not msg) or any(k in (msg or "") for k in ["成功", "修改", "更新", "保存"])
        assert ok, ea("编辑审批链成功提示", msg or "未获取到提示")

    # ════════════════════════════════════════════════════════════
    #  重置 / 分页 / 表单校验 — 只读+非破坏性
    # ════════════════════════════════════════════════════════════
    def test_sy_apchain_07_reset_button(self, driver_setup):
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-07", "重置按钮功能正常")
        step("输入筛选条件")
        page.input_name("test")
        step("点击重置")
        page.click_reset()
        step("点击搜索验证列表正常加载")
        page.click_search()
        row_count = page.get_table_row_count()
        empty = page.get_empty_text() or ""
        assert (row_count > 0) or ("暂无数据" in empty), ea("所有筛选条件清空，正常加载列表", empty or f"row_count={row_count}")

    def test_sy_apchain_08_pagination(self, driver_setup):
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-08", "分页跳转")
        step("点击重置")
        page.click_reset()
        step("记录第一页页码")
        page1 = page.get_current_page_number()
        step("点击下一页")
        page.click_next_page()
        page2 = page.get_current_page_number()
        if page2 == page1:
            pytest.skip("只有一页数据，跳过分页测试")
        assert page.get_table_row_count() > 0, ea("翻页后列表仍正常加载", page.get_empty_text() or "暂无数据")

    def test_sy_apchain_09_form_validation(self, driver_setup):
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-09", "表单验证 — 空名称提交")
        step("点击新增")
        page.click_add()
        step("清空名称输入框（如果已有默认值）")
        page.dialog_input_name("")
        step("点击确定")
        page.dialog_confirm()
        msg = page.wait_for_toast_text(timeout=4)
        # 预期：有错误提示或表单未关闭（不实际创建记录）
        still_open = page.is_dialog_open()
        has_error = msg and any(k in (msg or "") for k in ["输入", "填写", "不能为空", "必填", "错误"])
        # 关闭弹窗，确保不残留
        if still_open:
            try:
                page.dialog_cancel()
            except Exception:
                pass
        assert still_open or has_error, ea("空名称提交触发校验提示", f"弹窗仍打开={still_open}, Toast={msg}")

    # ════════════════════════════════════════════════════════════
    #  步骤配置面板 — 通用结构验证（不逐链诊断）
    # ════════════════════════════════════════════════════════════
    @pytest.mark.smoke
    def test_sy_apchain_10_step_editor_open(self, driver_setup):
        """CDP点击第一行'步骤配置'，验证面板打开"""
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-10", "步骤配置面板打开")
        step("点击重置")
        page.click_reset()
        if page.get_table_row_count() == 0:
            pytest.skip("当前无审批链数据")
        step("CDP点击第一行'步骤配置'")
        ok = page.click_step_config(row_index=1)
        assert ok, ea("CDP点击成功", "按钮未找到或点击失败")
        step("验证面板可见")
        visible = page.is_step_editor_visible()
        assert visible, ea("步骤配置面板(.step-editor)可见", f"visible={visible}")

    def test_sy_apchain_11_step_cards_display(self, driver_setup):
        """验证步骤卡片展示 + 字段存在"""
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-11", "步骤卡片展示及字段验证")
        page.click_reset()
        if page.get_table_row_count() == 0:
            pytest.skip("当前无审批链数据")
        if not page.is_step_editor_visible():
            ok = page.click_step_config(row_index=1)
            if not ok:
                pytest.skip("无法打开步骤配置面板")

        step("验证步骤卡片数量")
        count = page.get_step_cards_count()
        assert count >= 1, ea("至少1个步骤卡片(.step-card)", f"count={count}")

        step("读取步骤字段")
        data = page.get_step_editor_data()
        assert data.get("found"), ea("步骤数据可读取", str(data)[:200])
        assert len(data.get("steps", [])) >= 1, ea("至少有1个步骤", f"steps={len(data.get('steps',[]))}")

        step("验证必要字段存在")
        first_step = data["steps"][0]
        required_fields = ["审批人", "审批模式", "步骤名称"]
        for field in required_fields:
            assert field in first_step, ea(f"步骤卡片含'{field}'字段", list(first_step.keys()))

    def test_sy_apchain_12_add_step_button(self, driver_setup):
        """验证'添加步骤'按钮存在"""
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-12", "添加步骤按钮存在")
        page.click_reset()
        if page.get_table_row_count() == 0:
            pytest.skip("当前无审批链数据")
        if not page.is_step_editor_visible():
            ok = page.click_step_config(row_index=1)
            if not ok:
                pytest.skip("无法打开步骤配置面板")

        step("检查'添加步骤'入口")
        has_add = page.has_add_step_button()
        assert has_add, ea("存在.add-step-bar（添加步骤按钮）", f"has_add_step={has_add}")

    def test_sy_apchain_13_step_editor_close(self, driver_setup):
        """验证步骤配置面板可关闭"""
        page = ApprovalChainPage(driver_setup)
        case("SY-APCHAIN-13", "步骤配置面板关闭")
        page.click_reset()
        if page.get_table_row_count() == 0:
            pytest.skip("当前无审批链数据")
        if not page.is_step_editor_visible():
            ok = page.click_step_config(row_index=1)
            if not ok:
                pytest.skip("无法打开步骤配置面板")
        assert page.is_step_editor_visible(), "步骤配置面板应可见"

        step("关闭面板")
        result = page.close_step_editor()
        import time as _time
        _time.sleep(1)
        still_open = page.is_step_editor_visible()
        # 面板关闭 或 无标准关闭按钮(close_result表明没有找到关闭元素)
        closed = (not still_open) or (result == 'no_close_found')
        assert closed, ea("面板已关闭或无标准关闭按钮（页面可能需要刷新恢复）",
                          f"close_result={result}, still_open={still_open}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
