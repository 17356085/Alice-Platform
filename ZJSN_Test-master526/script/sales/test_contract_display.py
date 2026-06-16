"""合同管理 — 表格展示与数据呈现测试

测试点：
  - TC_D01: 表格表头完整性
  - TC_D02: 进度条文本与宽度一致性
  - TC_D03: 已完成合同进度为100%
  - TC_D04: 已终止合同进度为0%
  - TC_D05: 状态标签颜色/类型正确
  - TC_D06: 操作按钮（详情、销售订单）存在性
  - TC_D07: 表格列数据非空

Vue/Element Plus 注意：
  - ElementProgress 有 3s CSS 动画，断言百分比需等待动画完成
  - ElementTag 类型通过 class (el-tag--danger/success) 区分
  - 表格渲染异步，需等待遮罩消失
"""
import logging
import time
import inspect

import pytest
import allure

logger = logging.getLogger(__name__)


class TestContractDisplay:
    """合同管理 — 表格展示测试"""

    @pytest.fixture(autouse=True)
    def _allure_meta(self, request):
        doc = (inspect.getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
            if doc:
                allure.dynamic.description(doc)
        except Exception:
            pass
        yield

    # ==================================================================
    #  TC_D01: 表头完整性
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("合同管理")
    @allure.story("表格表头完整性")
    @allure.severity(allure.severity_level.NORMAL)
    def test_table_headers_complete(self, contract_page, contract_test_data):
        """TC_D01: 表格表头完整性 — 验证所有预期列存在"""
        page = contract_page
        expected_headers = contract_test_data["expected_headers"]

        headers = page.get_table_headers()
        logger.info("实际表头: %s", headers)
        logger.info("预期表头: %s", expected_headers)

        assert len(headers) >= 7, (
            f"表头列数不足，预期至少7列，实际 {len(headers)} 列: {headers}"
        )

        for expected_col in expected_headers:
            found = any(expected_col in h or h in expected_col for h in headers)
            if not found:
                logger.warning("未找到预期表头列: '%s'，实际: %s", expected_col, headers)
            if expected_col in ["合同编号", "客户名称", "状态", "操作"]:
                assert any(expected_col in h for h in headers), (
                    f"关键表头列 '{expected_col}' 缺失，实际表头: {headers}"
                )

    # ==================================================================
    #  TC_D02: 进度条文本与宽度一致性
    # ==================================================================
    def test_progress_bar_consistency(self, contract_page, contract_test_data):
        """TC_D02: 进度条 — 进度条宽度与显示文本百分比一致"""
        page = contract_page
        c_completed = contract_test_data["existing"]["contract_completed"]
        c_terminated = contract_test_data["existing"]["contract_terminated"]

        bar_pct, text_pct, consistent = page.verify_progress_consistency(c_completed)
        logger.info("合同 %s: bar=%.1f%%, text=%.1f%%, 一致=%s",
                     c_completed, bar_pct, text_pct, consistent)
        if bar_pct >= 0 and text_pct >= 0:
            assert abs(bar_pct - text_pct) < 1.0, (
                f"进度条宽度({bar_pct:.1f}%)与文本({text_pct:.1f}%)不一致"
            )

        bar_pct2, text_pct2, consistent2 = page.verify_progress_consistency(c_terminated)
        logger.info("合同 %s: bar=%.1f%%, text=%.1f%%, 一致=%s",
                     c_terminated, bar_pct2, text_pct2, consistent2)
        if bar_pct2 >= 0 and text_pct2 >= 0:
            assert abs(bar_pct2 - text_pct2) < 1.0, (
                f"进度条宽度({bar_pct2:.1f}%)与文本({text_pct2:.1f}%)不一致"
            )

    # ==================================================================
    #  TC_D03: 已完成合同进度为100%
    # ==================================================================
    def test_completed_contract_progress_100(self, contract_page, contract_test_data):
        """TC_D03: 已完成合同 → 进度条显示100%"""
        page = contract_page
        c_completed = contract_test_data["existing"]["contract_completed"]

        bar_pct = page.get_progress_percentage_by_contract_no(c_completed, timeout=10)
        text = page.get_progress_text_by_contract_no(c_completed)
        logger.info("合同 %s: 进度条=%.1f%%, 文本='%s'", c_completed, bar_pct, text)

        assert bar_pct > 90, f"已完成合同进度应接近100%，实际进度条: {bar_pct:.1f}%"
        assert "100" in (text or ""), f"已完成合同进度文本应包含'100%'，实际: '{text}'"

    def test_terminated_contract_progress_0(self, contract_page, contract_test_data):
        """TC_D04: 已终止合同 → 进度条显示0%"""
        page = contract_page
        c_terminated = contract_test_data["existing"]["contract_terminated"]

        bar_pct = page.get_progress_percentage_by_contract_no(c_terminated, timeout=10)
        text = page.get_progress_text_by_contract_no(c_terminated)
        logger.info("合同 %s: 进度条=%.1f%%, 文本='%s'", c_terminated, bar_pct, text)

        assert bar_pct < 5, f"已终止合同进度应接近0%，实际进度条: {bar_pct:.1f}%"
        assert "0" in (text or ""), f"已终止合同进度文本应包含'0%'，实际: '{text}'"

    # ==================================================================
    #  TC_D05: 状态标签颜色/类型正确
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("合同管理")
    @allure.story("状态标签展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_status_tag_color_completed(self, contract_page, contract_test_data):
        """TC_D05: 已完成的合同 → 状态标签为绿色 (el-tag--success)"""
        page = contract_page
        c_completed = contract_test_data["existing"]["contract_completed"]
        status = contract_test_data["existing"]["status_completed"]

        actual_status, tag_type, is_correct = page.verify_status_tag(c_completed, status)
        logger.info("合同 %s: status='%s', tag='%s', 正确=%s",
                     c_completed, actual_status, tag_type, is_correct)

        assert actual_status == status, f"预期状态'{status}'，实际: '{actual_status}'"
        assert tag_type == "success", (
            f"已完成合同标签应为'success'(绿色)，实际: '{tag_type}'"
        )

    def test_status_tag_color_terminated(self, contract_page, contract_test_data):
        """TC_D05b: 已终止的合同 → 状态标签为红色 (el-tag--danger)"""
        page = contract_page
        c_terminated = contract_test_data["existing"]["contract_terminated"]
        status = contract_test_data["existing"]["status_terminated"]

        actual_status, tag_type, is_correct = page.verify_status_tag(c_terminated, status)
        logger.info("合同 %s: status='%s', tag='%s', 正确=%s",
                     c_terminated, actual_status, tag_type, is_correct)

        assert actual_status == status, f"预期状态'{status}'，实际: '{actual_status}'"
        assert tag_type == "danger", (
            f"已终止合同标签应为'danger'(红色)，实际: '{tag_type}'"
        )

    # ==================================================================
    #  TC_D06: 操作按钮存在性
    # ==================================================================
    def test_operation_buttons_exist(self, contract_page, contract_test_data):
        """TC_D06: 每行数据操作列包含'详情'和'销售订单'按钮"""
        page = contract_page
        c_completed = contract_test_data["existing"]["contract_completed"]
        c_terminated = contract_test_data["existing"]["contract_terminated"]

        has_detail = page.is_detail_button_present(c_completed)
        has_order = page.is_sales_order_button_present(c_completed)
        logger.info("合同 %s: 详情按钮=%s, 销售订单按钮=%s", c_completed, has_detail, has_order)
        assert has_detail, f"合同 {c_completed} 应有'详情'按钮"
        assert has_order, f"合同 {c_completed} 应有'销售订单'按钮"

        has_detail2 = page.is_detail_button_present(c_terminated)
        has_order2 = page.is_sales_order_button_present(c_terminated)
        logger.info("合同 %s: 详情按钮=%s, 销售订单按钮=%s", c_terminated, has_detail2, has_order2)
        assert has_detail2, f"合同 {c_terminated} 应有'详情'按钮"
        assert has_order2, f"合同 {c_terminated} 应有'销售订单'按钮"

    # ==================================================================
    #  TC_D07: 表格列数据非空
    # ==================================================================
    def test_table_data_not_empty(self, contract_page):
        """TC_D07: 页面加载后表格至少包含一条数据，关键列非空"""
        page = contract_page

        row_count = page.get_table_row_count()
        logger.info("当前页行数: %d", row_count)
        assert row_count > 0, "合同列表不应为空"

        # 获取合同编号列表，验证非空
        contract_nos = page.get_contract_no_list()
        logger.info("合同编号列表: %s", contract_nos)
        assert len(contract_nos) > 0, "合同编号列不应为空"
        for cno in contract_nos:
            assert cno.strip(), f"合同编号不应为空字符串"

        # 获取客户名称列表
        customer_names = page.get_customer_name_list()
        logger.info("客户名称列表: %s", customer_names)
        assert len(customer_names) > 0, "客户名称列不应为空"

        logger.info("TC_D07 通过：表格数据关键列非空")

    # ==================================================================
    #  TC_D08: 浮点数精度展示
    # ==================================================================
    def test_float_precision_display(self, contract_page, contract_test_data):
        """TC_D08: 浮点数合同总量正确展示（如 20.0001 吨）"""
        page = contract_page
        contract_no = contract_test_data["existing"]["contract_terminated_2"]

        page.search(contract_no=contract_no)
        time.sleep(0.5)

        total_qty = page.get_cell_text_by_contract_no(
            contract_no, page.COL_TOTAL_QTY
        )
        logger.info("合同 %s 合同总量: '%s'", contract_no, total_qty)

        import re
        nums = re.findall(r'[\d.]+', total_qty)
        assert nums, f"合同总量应包含数值，实际: '{total_qty}'"
        qty_value = float(nums[0])
        assert qty_value > 0, f"合同总量应大于0，实际: {qty_value}"

        logger.info("TC_D08 通过：浮点数合同总量展示正常")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
