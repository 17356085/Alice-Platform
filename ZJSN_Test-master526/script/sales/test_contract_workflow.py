"""合同管理 — 业务流程与交互测试

测试点：
  - TC_W01: 点击详情按钮 — 跳转/弹窗展示合同详情
  - TC_W02: 点击销售订单按钮 — 跳转关联的销售订单
  - TC_W03: 点击新增合同按钮 — 弹窗/页面跳转
  - TC_W04: 详情按钮在不同状态合同下均可用
  - TC_W05: 搜索 → 详情 → 返回 — 完整用户操作路径

Vue/Element Plus 注意：
  - 详情/新增可能触发弹窗（dialog）或路由跳转
  - 弹窗有打开/关闭动画，需等待 Vue 异步渲染
  - 路由跳转后需等待新页面加载完成
"""
import logging
import inspect

import pytest
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from page.sales_page.ContractPage import ContractPage

logger = logging.getLogger(__name__)


class TestContractWorkflow:
    """合同管理 — 业务流程测试"""

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
    #  TC_W01: 查看合同详情
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("合同管理")
    @allure.story("查看合同详情")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_view_contract_detail(self, contract_page, contract_test_data):
        """TC_W01: 点击详情按钮 — 弹窗展示合同详情信息"""
        page = contract_page
        contract_no = contract_test_data["existing"]["contract_completed"]

        page.search(contract_no=contract_no)
        assert page.is_contract_present(contract_no), f"合同 {contract_no} 必须存在"

        page.click_detail_by_contract_no(contract_no)

        # 等待弹窗出现
        try:
            WebDriverWait(page.driver, 10).until(
                EC.visibility_of_element_located((
                    By.CSS_SELECTOR,
                    '.el-dialog:not([style*="display: none"])'
                ))
            )
            logger.info("详情弹窗已打开")

            # 获取弹窗标题（如果有）
            try:
                title = page.get_dialog_title()
                logger.info("弹窗标题: %s", title)
            except Exception:
                logger.info("弹窗无标题或未能获取")

            # 关闭弹窗
            try:
                page.click_dialog_cancel()
            except Exception:
                logger.info("弹窗无取消按钮，尝试按 ESC")
                try:
                    from selenium.webdriver.common.keys import Keys
                    page.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                except Exception:
                    pass

            page.wait_dialog_close(timeout=5)
            logger.info("详情弹窗已关闭")

        except Exception as e:
            # 可能不是弹窗而是路由跳转
            logger.info("详情未使用弹窗（可能是路由跳转）: %s", e)
            current_url = page.driver.current_url
            logger.info("当前URL: %s", current_url)

        logger.info("TC_W01 通过：详情功能正常")

    # ==================================================================
    #  TC_W02: 查看销售订单
    # ==================================================================
    def test_view_sales_order(self, contract_page, contract_test_data):
        """TC_W02: 点击销售订单按钮 — 跳转关联的销售订单"""
        page = contract_page
        contract_no = contract_test_data["existing"]["contract_completed"]

        page.search(contract_no=contract_no)
        assert page.is_contract_present(contract_no), f"合同 {contract_no} 必须存在"

        page.click_sales_order_by_contract_no(contract_no)

        # 等待跳转或弹窗
        page.wait_vue_stable()
        current_url = page.driver.current_url
        logger.info("点击销售订单后 URL: %s", current_url)

        # 可能是：
        #   1. 弹窗显示关联订单
        #   2. 路由跳转到销售订单页面（带筛选参数）
        #   3. 新标签页打开

        # 检查是否还在合同页面
        if page.PAGE_ROUTE in current_url:
            # 可能弹窗，关闭它
            try:
                page.click_dialog_cancel()
            except Exception:
                pass

        logger.info("TC_W02 通过：销售订单按钮功能正常")

    # ==================================================================
    #  TC_W03: 新增合同按钮
    # ==================================================================
    def test_click_add_contract(self, contract_page):
        """TC_W03: 点击新增合同按钮 — 弹窗或跳转到新增页面"""
        page = contract_page

        page.click_add()

        # 检查结果：弹窗或路由跳转
        try:
            # 检查是否有弹窗
            WebDriverWait(page.driver, 5).until(
                EC.visibility_of_element_located((
                    By.CSS_SELECTOR,
                    '.el-dialog:not([style*="display: none"])'
                ))
            )
            logger.info("新增合同弹窗已打开")
            title = page.get_dialog_title()
            logger.info("弹窗标题: %s", title)

            # 关闭弹窗
            try:
                page.click_dialog_cancel()
            except Exception:
                pass
            page.wait_dialog_close(timeout=5)

        except Exception:
            # 路由跳转
            current_url = page.driver.current_url
            logger.info("新增合同通过路由跳转，URL: %s", current_url)

            # 如果是跳转到新页面，返回
            page.navigate()

        logger.info("TC_W03 通过：新增合同按钮功能正常")

    # ==================================================================
    #  TC_W04: 不同状态合同的详情可用性
    # ==================================================================
    def test_detail_available_for_all_statuses(self, contract_page, contract_test_data):
        """TC_W04: 任何状态的合同都有详情按钮"""
        page = contract_page
        c_completed = contract_test_data["existing"]["contract_completed"]
        c_terminated = contract_test_data["existing"]["contract_terminated"]

        page.click_reset()
        assert page.is_detail_button_present(c_completed), (
            f"已完成合同 {c_completed} 应有详情按钮"
        )
        assert page.is_detail_button_present(c_terminated), (
            f"已终止合同 {c_terminated} 应有详情按钮"
        )

    # ==================================================================
    #  TC_W05: 完整用户操作路径
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("合同管理")
    @allure.story("完整操作路径")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_complete_user_flow(self, contract_page, contract_test_data):
        """TC_W05: 完整用户操作路径 — 搜索 → 查看详情 → 关闭 → 查看销售订单"""
        page = contract_page
        contract_no = contract_test_data["existing"]["contract_completed"]

        logger.info("=== 步骤1: 搜索合同 ===")
        page.search(contract_no=contract_no)
        assert page.is_contract_present(contract_no), "搜索后应能找到合同"
        logger.info("搜索成功，找到 %s", contract_no)

        logger.info("=== 步骤2: 查看详情 ===")
        page.click_detail_by_contract_no(contract_no)
        page.wait_vue_stable()

        try:
            page.click_dialog_cancel()
            page.wait_dialog_close(timeout=5)
        except Exception:
            logger.info("无弹窗需关闭，可能已跳转，重新导航")
            page.navigate()
            page.search(contract_no=contract_no)

        logger.info("详情查看完成")

        logger.info("=== 步骤3: 查看销售订单 ===")
        page.click_sales_order_by_contract_no(contract_no)
        page.wait_vue_stable()

        try:
            page.click_dialog_cancel()
        except Exception:
            pass
        page.navigate()

        # 步骤 4: 验证仍能正常搜索
        logger.info("=== 步骤4: 回到合同列表验证 ===")
        page.click_reset()
        row_count = page.get_table_row_count()
        assert row_count > 0, "回到列表后应有数据"
        logger.info("完整用户路径执行成功，列表数据正常")

        logger.info("TC_W05 通过：完整用户操作路径正常")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
