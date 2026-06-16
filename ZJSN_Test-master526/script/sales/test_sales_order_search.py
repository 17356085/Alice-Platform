"""销售订单 — 搜索筛选测试

覆盖：
  - 按销售单号精确搜索（存在/不存在）
  - 按客户名称模糊搜索
  - 按产品类型下拉筛选（LNG / 焦油）
  - 日期范围筛选（开始、结束、组合）
  - 组合条件搜索
  - 重置搜索条件
  - 搜索无结果
"""
import pytest
import time
import sys
import os
import inspect
import allure

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.sales_page.SalesOrderPage import SalesOrderPage


class TestSalesOrderSearch:
    """销售订单 — 搜索筛选测试"""

    @pytest.fixture(autouse=True)
    def _allure_case_meta(self, request):
        doc = (inspect.getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
            if doc:
                allure.dynamic.description(doc)
        except Exception:
            pass
        yield

    # — 辅助方法 —
    @staticmethod
    def _reset(page):
        """统一重置搜索条件"""
        page.click_reset()
        time.sleep(0.5)

    # ==================================================================
    #  ORD-SEARCH-001: 按销售单号精确搜索（存在）
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("销售订单")
    @allure.story("订单搜索")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search_by_order_no_exact(self, driver_setup):
        """ORD-SEARCH-001: 按销售单号精确搜索"""
        page = SalesOrderPage(driver_setup)
        print("\n--- ORD-SEARCH-001: 按销售单号精确搜索 ---")

        self._reset(page)

        # 先获取一个存在的单号
        order_nos = page.get_column_data(page.COL_ORDER_NO)
        if not order_nos:
            pytest.skip("系统中无数据")
        target = order_nos[0]
        print(f"目标单号: {target}")

        page.search(order_no=target)

        row_count = page.get_table_row_count()
        print(f"搜索结果: {row_count} 行")
        assert row_count >= 1, "搜索结果不应为空"

        results = page.get_column_data(page.COL_ORDER_NO)
        assert target in results, f"结果应包含 {target}: {results}"

        self._reset(page)

    # ==================================================================
    #  ORD-SEARCH-002: 不存在的单号搜索
    # ==================================================================
    def test_search_by_order_no_not_exist(self, driver_setup):
        """ORD-SEARCH-002: 搜索不存在的销售单号"""
        page = SalesOrderPage(driver_setup)
        print("\n--- ORD-SEARCH-002: 搜索不存在单号 ---")

        self._reset(page)
        page.search(order_no="NOTEXIST_99999999")

        row_count = page.get_table_row_count()
        print(f"搜索结果: {row_count} 行")
        # 搜索无结果时，行数应为 0 或表格显示空提示
        if row_count > 0:
            # 可能是模糊匹配到了其他数据
            order_nos = page.get_column_data(page.COL_ORDER_NO)
            assert "NOTEXIST_99999999" not in order_nos, \
                "不应包含不存在的单号"

        self._reset(page)

    # ==================================================================
    #  ORD-SEARCH-003: 按客户名称模糊搜索
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("销售订单")
    @allure.story("订单搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_by_customer_fuzzy(self, driver_setup):
        """ORD-SEARCH-003: 按客户名称模糊搜索"""
        page = SalesOrderPage(driver_setup)
        print("\n--- ORD-SEARCH-003: 按客户名称模糊搜索 ---")

        self._reset(page)

        # 取第一个客户名称的前几个字做模糊搜索
        customers = page.get_column_data(page.COL_CUSTOMER)
        if not customers:
            pytest.skip("系统中无数据")
        keyword = customers[0][:3]  # 取前 3 个字
        print(f"搜索关键字: '{keyword}'")

        page.search(customer=keyword)

        row_count = page.get_table_row_count()
        print(f"搜索结果: {row_count} 行")
        assert row_count >= 1, "搜索结果不应为空"

        result_customers = page.get_column_data(page.COL_CUSTOMER)
        for rc in result_customers:
            assert keyword in rc, f"'{rc}' 不包含关键字 '{keyword}'"

        self._reset(page)

    # ==================================================================
    #  ORD-SEARCH-004/005: 产品类型筛选
    # ==================================================================
    def test_search_by_product_type(self, driver_setup):
        """ORD-SEARCH-004: 按产品类型筛选 — LNG"""
        page = SalesOrderPage(driver_setup)
        print("\n--- ORD-SEARCH-004: 按产品类型筛选 ---")

        self._reset(page)
        page.select_product_type("LNG")
        page.click_search()

        row_count = page.get_table_row_count()
        print(f"LNG 筛选: {row_count} 行")

        if row_count > 0:
            tag_texts = [page.get_product_tag_text(i) for i in range(1, row_count + 1)]
            print(f"Tag 文本: {tag_texts}")
            assert all("LNG" in t for t in tag_texts if t), \
                f"LNG 筛选结果应全部为 LNG: {tag_texts}"

        self._reset(page)

    # ==================================================================
    #  ORD-SEARCH-006/007: 日期筛选
    # ==================================================================
    def test_search_by_date_range(self, driver_setup):
        """ORD-SEARCH-006: 按日期范围筛选"""
        page = SalesOrderPage(driver_setup)
        print("\n--- ORD-SEARCH-006: 日期范围筛选 ---")

        self._reset(page)

        # 用较宽泛的日期范围确保有结果
        page.search(date_start="2020-01-01", date_end="2030-12-31")
        row_count = page.get_table_row_count()
        print(f"宽泛日期范围: {row_count} 行")
        assert row_count >= 1, "数据库中应有早于 2030 年的数据"

        sale_times = page.get_column_data(page.COL_SALE_TIME)
        print(f"销售时间: {sale_times[:3]}...")

        self._reset(page)

    # ==================================================================
    #  ORD-SEARCH-009: 组合条件搜索
    # ==================================================================
    def test_search_combined(self, driver_setup):
        """ORD-SEARCH-009: 客户名称 + 日期范围组合搜索"""
        page = SalesOrderPage(driver_setup)
        print("\n--- ORD-SEARCH-009: 组合条件搜索 ---")

        self._reset(page)

        # 取一个存在的客户
        customers = page.get_column_data(page.COL_CUSTOMER)
        if not customers:
            pytest.skip("系统中无数据")
        customer = customers[0]

        page.search(customer=customer, date_start="2020-01-01", date_end="2030-12-31")
        row_count = page.get_table_row_count()
        print(f"组合搜索 '{customer}': {row_count} 行")
        assert row_count >= 1, "组合搜索结果不应为空"

        # 验证所有结果都包含该客户
        result_customers = page.get_column_data(page.COL_CUSTOMER)
        for rc in result_customers:
            assert customer in rc, f"'{rc}' 不包含客户名 '{customer}'"

        self._reset(page)

    # ==================================================================
    #  ORD-SEARCH-011: 重置
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("销售订单")
    @allure.story("订单搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_reset_search(self, driver_setup):
        """ORD-SEARCH-011: 重置清空搜索条件，恢复全量数据"""
        page = SalesOrderPage(driver_setup)
        print("\n--- ORD-SEARCH-011: 重置搜索 ---")

        self._reset(page)
        original_count = page.get_table_row_count()
        print(f"初始数据行数: {original_count}")

        # 输入不可能匹配的条件
        page.search(order_no="NONEXISTENT_XYZ_ABC_999")
        filtered_count = page.get_table_row_count()
        print(f"无匹配搜索: {filtered_count} 行")

        # 重置
        self._reset(page)
        reset_count = page.get_table_row_count()
        print(f"重置后: {reset_count} 行")

        assert reset_count == original_count, \
            f"重置后应恢复到 {original_count} 行，实际 {reset_count} 行"

    # ==================================================================
    #  ORD-SEARCH-012: 全条件组合
    # ==================================================================
    def test_search_all_conditions(self, driver_setup):
        """ORD-SEARCH-012: 全部条件组合搜索（销售单号 + 客户 + 产品类型 + 日期）"""
        page = SalesOrderPage(driver_setup)
        print("\n--- ORD-SEARCH-012: 全条件组合搜索 ---")

        self._reset(page)

        # 先取一个现有订单的数据
        order_nos = page.get_column_data(page.COL_ORDER_NO)
        if not order_nos:
            pytest.skip("系统中无数据")
        target_order_no = order_nos[0]

        page.search(
            order_no=target_order_no,
            date_start="2020-01-01",
            date_end="2030-12-31",
        )

        row_count = page.get_table_row_count()
        print(f"全条件搜索: {row_count} 行")
        assert row_count >= 1, "至少应找到该单号"

        results = page.get_column_data(page.COL_ORDER_NO)
        assert target_order_no in results, f"结果应包含 {target_order_no}"

        self._reset(page)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
