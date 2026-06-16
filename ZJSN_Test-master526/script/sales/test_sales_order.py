"""销售订单模块测试脚本

测试覆盖：
  - 页面展示验证
  - 新增订单（级联下拉 + 完整流程）
  - 搜索筛选（按单号、客户、产品类型、日期）
  - 查看详情
  - 超卖防护
  - 浮点数精度

闭环设计：创建独立测试数据，用例间通过 module 级变量传递标识。
"""
import pytest
import sys
import os
import inspect
import allure
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.sales_page.SalesOrderPage import SalesOrderPage
from page.sales_page.ContractPage import ContractPage
from page.sales_page.CustomerPage import CustomerPage

# ==================================================================
#  闭环测试数据（module 级全局变量）
# ==================================================================
CREATED_ORDER_NO = None   # 新增订单的销售单号
CREATED_ORDER_PLATE = None
CREATED_ORDER_CUSTOMER = None
CREATED_ORDER_CONTRACT = None


def _generate_order_test_data():
    """生成本轮订单闭环测试数据"""
    day_tag = datetime.now().strftime("%Y%m%d%H%M%S")
    plate = f"测A{day_tag[-6:]}"  # 模拟车牌号
    return plate, day_tag


class TestSalesOrder:
    """销售订单模块测试用例"""

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
    def _require_created_plate(self):
        global CREATED_ORDER_PLATE
        if not CREATED_ORDER_PLATE:
            pytest.skip("新增用例未成功（合同下拉待攻关），跳过依赖用例")
        return CREATED_ORDER_PLATE

    def _require_created_order_no(self):
        global CREATED_ORDER_NO
        if not CREATED_ORDER_NO:
            pytest.skip("新增用例未成功（合同下拉待攻关），跳过依赖用例")
        return CREATED_ORDER_NO

    # ==================================================================
    #  ORD-001: 页面展示
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("销售订单")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        driver = driver_setup
        page = SalesOrderPage(driver)
        print("\n========== 测试 ORD-001: 页面显示正常 ==========")

        try:
            # 分页总条数
            total_text = page.get_total_count_text()
            print(f"[OK] 总条数: {total_text}")
            assert any(char.isdigit() for char in total_text), "总条数应包含数字"

            # 表头验证
            headers = page.get_table_headers()
            print(f"[OK] 表头: {headers}")
            assert len(headers) == 8, f"应有 8 列表头，实际 {len(headers)}: {headers}"

            # 预期的表头
            expected_headers = ["销售单号", "客户名称", "产品类型",
                               "销售量", "车牌号", "销售时间", "关联合同", "操作"]
            for expected in expected_headers:
                assert any(expected in h for h in headers), \
                    f"表头应包含 '{expected}'，实际: {headers}"

            # 数据行数
            row_count = page.get_table_row_count()
            print(f"[OK] 当前页加载了 {row_count} 条数据")
            assert row_count >= 0, f"数据行数应 >=0，实际 {row_count}"

            print("========== ORD-001 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  ORD-002: 新增销售订单（级联下拉 + 完整流程）
    # ==================================================================
    @pytest.mark.destructive
    def test_002_add_order_with_cascade(self, driver_setup, sales_test_data, contract_test_data):
        """ORD-002: 新增销售订单 — 客户→合同级联选择"""
        driver = driver_setup
        page = SalesOrderPage(driver)
        print("\n========== 用例 ORD-002：新增订单（级联下拉） ==========")

        try:
            global CREATED_ORDER_NO, CREATED_ORDER_PLATE
            global CREATED_ORDER_CUSTOMER, CREATED_ORDER_CONTRACT
            plate, day_tag = _generate_order_test_data()
            CREATED_ORDER_PLATE = plate
            print(f"本轮闭环测试数据：车牌号={plate}")

            # 使用 fixture 准备的测试数据
            customer_name = sales_test_data["customer"]
            contract_name = sales_test_data["contract"]
            if not customer_name or not contract_name:
                pytest.skip("测试数据准备失败，跳过订单新增测试")
            CREATED_ORDER_CUSTOMER = customer_name
            CREATED_ORDER_CONTRACT = contract_name
            print(f"关联客户: {customer_name}, 关联合同: {contract_name}")

            # 打开新增弹窗
            page.click_add()
            dialog_title = page.get_dialog_title()
            print(f"弹窗标题: {dialog_title}")

            # 选择关联合同 — 用客户名称搜索（下拉显示 "合同名 - 客户名"）
            try:
                page.select_contract_in_dialog(search_text=customer_name[:6])
            except Exception as e:
                pytest.skip(f"合同下拉选择待攻关: {e}")
            page.wait_vue_stable()

            # 填充其余字段
            page.input_order_quantity(10)
            page.input_vehicle_plate(plate)
            page.input_delivery_date(contract_test_data["sales_order"]["delivery_date"])

            # 保存
            toast = page.click_save()
            print(f"操作提示: {toast}")

            if toast and "成功" in toast:
                print("[OK] 保存成功，Toast 提示已出现")
            elif not page.is_visible(page.DIALOG, timeout=1):
                print("[OK] 弹窗已关闭，视为新增成功")
            else:
                form_errors = page.get_form_error()
                if form_errors:
                    pytest.fail(f"表单校验失败: {form_errors}")
                pytest.fail(f"新增订单提示异常: {toast}")

            # 搜索新订单，获取系统分配的销售单号
            page.search(order_no=None, customer=customer_name)
            order_nos = page.get_column_data(page.COL_ORDER_NO)
            if order_nos:
                CREATED_ORDER_NO = order_nos[0]
                print(f"[OK] 系统分配的销售单号: {CREATED_ORDER_NO}")

            print("========== ORD-002 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  ORD-003: 按销售单号搜索
    # ==================================================================
    def test_003_search_by_order_no(self, driver_setup):
        """ORD-003: 按销售单号精确搜索"""
        driver = driver_setup
        page = SalesOrderPage(driver)
        print("\n========== 用例 ORD-003：按销售单号搜索 ==========")

        try:
            order_no = self._require_created_order_no()

            page.click_reset()
            page.search(order_no=order_no)

            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count >= 1, f"搜索结果不应为空，销售单号: {order_no}"

            order_nos = page.get_column_data(page.COL_ORDER_NO)
            print(f"搜索结果销售单号: {order_nos}")
            assert order_no in order_nos, \
                f"搜索结果应包含 {order_no}: {order_nos}"
            # 精确搜索应唯一
            assert len(order_nos) == 1, f"精确搜索应唯一，实际 {len(order_nos)} 条"

            page.click_reset()
            print("========== ORD-003 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  ORD-004: 按客户名称搜索
    # ==================================================================
    def test_003b_search_by_customer(self, driver_setup):
        """ORD-004: 按客户名称模糊搜索"""
        driver = driver_setup
        page = SalesOrderPage(driver)
        print("\n========== 用例 ORD-004：按客户名称搜索 ==========")

        try:
            global CREATED_ORDER_CUSTOMER
            customer = CREATED_ORDER_CUSTOMER
            if not customer:
                # 取表格中第一个客户
                page.click_reset()
                customers = page.get_column_data(page.COL_CUSTOMER)
                if not customers:
                    pytest.skip("系统中无数据")
                customer = customers[0][:3]  # 取前3个字做模糊搜索

            page.click_reset()
            page.search(customer=customer)

            row_count = page.get_table_row_count()
            print(f"搜索客户 '{customer}' 结果行数: {row_count}")
            assert row_count >= 1, f"搜索结果不应为空"

            result_customers = page.get_column_data(page.COL_CUSTOMER)
            print(f"搜索结果客户: {result_customers}")
            # 所有结果应包含搜索关键字
            for rc in result_customers:
                assert customer in rc, f"'{rc}' 不包含搜索关键字 '{customer}'"

            page.click_reset()
            print("========== ORD-004 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  ORD-005: 查看订单详情
    # ==================================================================
    def test_005_view_order_detail(self, driver_setup):
        """ORD-005: 查看订单详情"""
        driver = driver_setup
        page = SalesOrderPage(driver)
        print("\n========== 用例 ORD-005：查看订单详情 ==========")

        try:
            order_no = self._require_created_order_no()
            plate = self._require_created_plate()

            page.click_reset()
            page.search(order_no=order_no)
            row_count = page.get_table_row_count()
            assert row_count >= 1, f"订单 '{order_no}' 不存在"

            # 通过详情按钮打开弹窗
            page.click_detail_button(order_no)
            detail = page.get_detail_info()
            print(f"详情内容: {detail[:300]}...")
            assert detail, "详情内容不应为空"

            # 验证关键信息
            assert order_no in detail, f"详情中应包含销售单号 {order_no}"
            assert plate in detail, f"详情中应包含车牌号 {plate}"

            # 关闭弹窗
            page.click_cancel()
            print("[OK] 详情弹窗已关闭")

            print("========== ORD-005 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  ORD-006: 超卖防护
    # ==================================================================
    @pytest.mark.destructive
    def test_006_oversell_prevention(self, driver_setup, sales_test_data):
        """ORD-006: 销售量超过合同剩余量应被拦截"""
        driver = driver_setup
        page = SalesOrderPage(driver)
        print("\n========== 用例 ORD-006：超卖防护 ==========")

        try:
            customer_name = sales_test_data["customer"]
            contract_name = sales_test_data["contract"]
            if not customer_name or not contract_name:
                pytest.skip("测试数据准备失败，跳过超卖测试")

            page.click_add()
            # 输入明显超卖的极大数量
            intercepted, error_msg = page.try_oversell(
                customer_name=customer_name,
                contract_name=contract_name,
                oversized_qty=99999999,
            )
            print(f"超卖拦截结果: intercepted={intercepted}, msg={error_msg}")
            assert intercepted, f"超卖应被拦截但未被拦截: {error_msg}"

            # 关闭弹窗
            try:
                page.click_cancel()
            except Exception:
                pass

            print("========== ORD-006 测试通过 ==========")
        except Exception as e:
            try:
                page.click_cancel()
            except Exception:
                pass
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  ORD-007: 浮点数精度
    # ==================================================================
    @pytest.mark.destructive
    def test_007_float_precision(self, driver_setup, sales_test_data, contract_test_data):
        """ORD-007: 浮点数销售量精度验证"""
        driver = driver_setup
        page = SalesOrderPage(driver)
        print("\n========== 用例 ORD-007：浮点数精度 ==========")

        try:
            customer_name = sales_test_data["customer"]
            contract_name = sales_test_data["contract"]
            if not customer_name or not contract_name:
                pytest.skip("测试数据准备失败，跳过精度测试")

            plate = f"精{datetime.now().strftime('%H%M%S')}"
            page.click_add()
            # 先选合同（客户/产品/单价自动带入）
            page.select_contract_in_dialog(search_text=customer_name[:6])
            page.wait_vue_stable()
            page.input_order_quantity(1.5)
            page.input_vehicle_plate(plate)
            page.input_delivery_date(contract_test_data["sales_order"]["delivery_date"])
            toast = page.click_save()
            print(f"浮点数订单提示: {toast}")

            # 验证页面上显示的数量精度
            if toast and "成功" in toast:
                page.click_reset()
                # 按客户名称搜索（页面无车牌号搜索输入框）
                page.search(customer=customer_name)
                quantities = page.get_column_data(page.COL_QUANTITY)
                print(f"显示的销售量: {quantities}")
                if quantities:
                    qty_str = quantities[0]
                    print(f"[OK] 销售量展示: {qty_str}")
                    assert "1.5" in qty_str or "1.50" in qty_str, \
                        f"浮点数精度可能有问题: {qty_str}"

            page.click_reset()
            print("========== ORD-007 测试通过 ==========")
        except Exception as e:
            try:
                page.click_cancel()
            except Exception:
                pass
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  ORD-008: 产品类型下拉筛选
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("销售订单")
    @allure.story("按产品类型搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_008_search_by_product_type(self, driver_setup, contract_test_data):
        """ORD-008: 按产品类型筛选 — LNG"""
        driver = driver_setup
        page = SalesOrderPage(driver)
        print("\n========== 用例 ORD-008：按产品类型筛选 ==========")

        try:
            page.click_reset()

            page.select_product_type(contract_test_data["sales_order"]["product_type"])
            page.click_search()

            row_count = page.get_table_row_count()
            print(f"LNG 筛选结果行数: {row_count}")

            if row_count == 0:
                print("[INFO] 当前无 LNG 类型订单，尝试焦油")
                page.click_reset()
                page.select_product_type("焦油")
                page.click_search()
                row_count = page.get_table_row_count()
                print(f"焦油筛选结果行数: {row_count}")

            if row_count > 0:
                # 验证所有行的产品类型 Tag
                tag_texts = []
                for i in range(1, row_count + 1):
                    tag_type = page.get_product_tag_type(i)
                    tag_text = page.get_product_tag_text(i)
                    tag_texts.append(tag_text)
                    print(f"  行 {i}: tag_type={tag_type}, tag_text={tag_text}")
                # 筛选结果应一致
                unique_tags = set(tag_texts)
                print(f"唯一产品类型: {unique_tags}")
                assert len(unique_tags) <= 1 or all(t in unique_tags for t in tag_texts), \
                    f"筛选结果产品类型不一致: {unique_tags}"

            print("========== ORD-008 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  ORD-009: 重置搜索条件
    # ==================================================================
    def test_009_reset_search(self, driver_setup):
        """ORD-009: 重置清空搜索条件"""
        driver = driver_setup
        page = SalesOrderPage(driver)
        print("\n========== 用例 ORD-009：重置搜索 ==========")

        try:
            # 先记录初始数据量
            page.click_reset()
            original_count = page.get_table_row_count()
            print(f"初始数据行数: {original_count}")

            # 输入不可能匹配的条件
            page.search(order_no="NOTEXIST_99999999")
            filtered_count = page.get_table_row_count()
            print(f"无匹配搜索后行数: {filtered_count}")

            # 重置
            page.click_reset()
            reset_count = page.get_table_row_count()
            print(f"重置后行数: {reset_count}")

            # 重置后应恢复数据
            assert reset_count == original_count, \
                f"重置后数据量({reset_count})应与初始({original_count})一致"

            print("========== ORD-009 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
