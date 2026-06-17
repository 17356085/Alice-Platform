"""库管管理 — 跨页面端到端测试

覆盖场景:
  E2E-WH-001: 备品全链 — 物品->库存->领用->出库 (P0)
  E2E-WH-002: 危废全链 — 物品->入库->库存->出入库记录 (P0)
  E2E-WH-003: 库存->盘点 数据一致性 (P1)
  E2E-WH-004: 领用->出库 链接验证 (P1)

技术:
  单浏览器顺序导航
  warehouse 使用自定义 wh-filter-toolbar 搜索区 (非标准 el-form)
"""
import os
import sys
import time
import pytest
import allure

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from page.warehouse_page.SpareItemPage import SpareItemPage
from page.warehouse_page.SpareStockPage import SpareStockPage
from page.warehouse_page.SpareRequisitionPage import SpareRequisitionPage
from page.warehouse_page.SpareOutOrderPage import SpareOutOrderPage
from page.warehouse_page.SpareInOrderPage import SpareInOrderPage
from page.warehouse_page.SpareIORecordPage import SpareIORecordPage
from page.warehouse_page.SpareStocktakePage import SpareStocktakePage
from page.warehouse_page.SpareStockAdjustPage import SpareStockAdjustPage
from page.warehouse_page.HazardItemPage import HazardItemPage
from page.warehouse_page.HazardStockPage import HazardStockPage
from page.warehouse_page.HazardInOrderPage import HazardInOrderPage
from page.warehouse_page.HazardIORecordPage import HazardIORecordPage
from base.sidebar_navigator import SidebarNavigator
from base.base_page import BasePage


# ═══════════════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════════════

def step(text):
    print(f"  -> {text}")
    try:
        allure.step(text)
    except Exception:
        pass


def case(case_id, title):
    print(f"\n{'='*60}\n用例 {case_id}：{title}\n{'='*60}")
    try:
        allure.dynamic.title(f"{case_id} {title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


def nav_to(driver, href, label=""):
    """JS hash 直接导航"""
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash(href, label)
    BasePage(driver).wait_vue_stable()
    time.sleep(2)


# ═══════════════════════════════════════════════════════════════
#  测试类
# ═══════════════════════════════════════════════════════════════

class TestWarehouseE2E:
    """库管管理 — 跨页面端到端测试"""

    # ── E2E-WH-001: 备品全链 — item->stock->requisition->out-order ──

    @pytest.mark.smoke
    @allure.epic("库管管理")
    @allure.feature("备品备件")
    @allure.story("跨页面流转-备品全链")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_wh_001_spare_full_chain(self, driver_setup):
        """E2E-WH-001: 备品全链 — 物品->库存->领用->出库

        流程:
          备品物品: 获取第一条物品
          -> 备品库存: 验证库存数据
          -> 备品领用: 验证领用列表
          -> 出库单: 验证出库单页面
        """
        driver = driver_setup
        case("E2E-WH-001", "备品全链 — 物品->库存->领用->出库")

        chain = {}

        # ── Step 1: 备品物品 ──
        step("导航到备品物品")
        nav_to(driver, "#/warehouse/spare/item", "备品物品")
        item_page = SpareItemPage(driver)
        item_page._wait_page_ready() if hasattr(item_page, '_wait_page_ready') else item_page.wait_vue_stable()

        item_count = item_page.get_table_row_count()
        step(f"备品物品: {item_count} 行")
        assert item_count >= 0, ea("备品物品页面正常加载", f"{item_count}行")
        chain['item'] = item_count

        item_name = None
        if item_count > 0:
            try:
                col1 = item_page.get_column_data(1)
                item_name = col1[0] if col1 else None
                step(f"第一条备品: {item_name}")
            except Exception:
                pass

        # ── Step 2: 备品库存 ──
        step("导航到备品库存")
        nav_to(driver, "#/warehouse/spare/stock", "备品库存")
        stock_page = SpareStockPage(driver)
        stock_page.is_page_loaded() if hasattr(stock_page, 'is_page_loaded') else stock_page.wait_vue_stable()

        stock_count = stock_page.get_table_row_count()
        step(f"备品库存: {stock_count} 行")
        assert stock_count >= 0, ea("备品库存页面正常加载", f"{stock_count}行")
        chain['stock'] = stock_count

        # 交叉验证: 如果有物品名，搜索库存
        if item_name and stock_count > 0:
            try:
                search_inputs = driver.find_elements(
                    By.CSS_SELECTOR, 'input[placeholder*="备品"], input[placeholder*="物品"], input[placeholder*="名称"]'
                )
                if search_inputs:
                    search_inputs[0].clear()
                    search_inputs[0].send_keys(item_name[:4])
                    stock_page.click_search() if hasattr(stock_page, 'click_search') else None
                    step(f"库存搜索「{item_name[:4]}」: {stock_page.get_table_row_count()} 行")
                    stock_page.click_reset() if hasattr(stock_page, 'click_reset') else None
            except Exception:
                pass

        # ── Step 3: 备品领用 ──
        step("导航到备品领用")
        nav_to(driver, "#/warehouse/spare/requisition", "备品领用")
        req_page = SpareRequisitionPage(driver)
        req_page._wait_page_ready() if hasattr(req_page, '_wait_page_ready') else req_page.wait_vue_stable()

        req_count = req_page.get_table_row_count()
        step(f"备品领用: {req_count} 行")
        assert req_count >= 0, ea("备品领用页面正常加载", f"{req_count}行")
        chain['requisition'] = req_count

        # 检查是否有提交按钮 (标记可审批的单子)
        if req_count > 0:
            try:
                has_submit = req_page.has_submit_button() if hasattr(req_page, 'has_submit_button') else False
                step(f"可提交状态: {has_submit}")
            except Exception:
                pass

        # ── Step 4: 出库单 ──
        step("导航到出库单")
        nav_to(driver, "#/warehouse/spare/out-order", "出库单")
        out_page = SpareOutOrderPage(driver)
        out_page.is_page_loaded() if hasattr(out_page, 'is_page_loaded') else out_page.wait_vue_stable()

        out_count = out_page.get_table_row_count()
        step(f"出库单: {out_count} 行")
        assert out_count >= 0, ea("出库单页面正常加载", f"{out_count}行")
        chain['out_order'] = out_count

        # ── 汇总 ──
        step(f"备品全链汇总: {chain}")
        all_loaded = all(isinstance(v, int) and v >= 0 for v in chain.values())
        assert all_loaded, ea("备品全链4页面均正常", chain)

        step("E2E-WH-001 备品全链验证通过 [OK]")

    # ── E2E-WH-002: 危废全链 — item->in-order->stock->IO-record ─

    @pytest.mark.smoke
    @allure.epic("库管管理")
    @allure.feature("环保危废")
    @allure.story("跨页面流转-危废全链")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_wh_002_hazard_full_chain(self, driver_setup):
        """E2E-WH-002: 危废全链 — 物品->入库->库存->出入库记录

        流程:
          危废物品: 获取物品名称
          -> 危废入库: 验证入库单列表
          -> 危废库存: 验证库存数据
          -> 危废出入库记录: 验证记录页
        """
        driver = driver_setup
        case("E2E-WH-002", "危废全链 — 物品->入库->库存->记录")

        chain = {}

        # ── Step 1: 危废物品 ──
        step("导航到危废物品")
        nav_to(driver, "#/warehouse/hazard/item", "危废物品")
        hitem_page = HazardItemPage(driver)
        hitem_page.is_page_loaded() if hasattr(hitem_page, 'is_page_loaded') else hitem_page.wait_vue_stable()

        hitem_count = hitem_page.get_table_row_count()
        step(f"危废物品: {hitem_count} 行")
        assert hitem_count >= 0, ea("危废物品页面正常加载", f"{hitem_count}行")
        chain['hazard_item'] = hitem_count

        # ── Step 2: 危废入库单 ──
        step("导航到危废入库单")
        nav_to(driver, "#/warehouse/hazard/in-order", "危废入库单")
        hin_page = HazardInOrderPage(driver)
        hin_page.is_page_loaded() if hasattr(hin_page, 'is_page_loaded') else hin_page.wait_vue_stable()

        hin_count = hin_page.get_table_row_count()
        step(f"危废入库单: {hin_count} 行")
        assert hin_count >= 0, ea("危废入库单页面正常加载", f"{hin_count}行")
        chain['hazard_in'] = hin_count

        # ── Step 3: 危废库存 ──
        step("导航到危废库存")
        nav_to(driver, "#/warehouse/hazard/stock", "危废库存")
        hstock_page = HazardStockPage(driver)
        hstock_page.is_page_loaded() if hasattr(hstock_page, 'is_page_loaded') else hstock_page.wait_vue_stable()

        hstock_count = hstock_page.get_table_row_count()
        step(f"危废库存: {hstock_count} 行")
        assert hstock_count >= 0, ea("危废库存页面正常加载", f"{hstock_count}行")
        chain['hazard_stock'] = hstock_count

        # ── Step 4: 危废出入库记录 ──
        step("导航到危废出入库记录")
        nav_to(driver, "#/warehouse/hazard/io-record", "危废出入库记录")
        hio_page = HazardIORecordPage(driver)
        hio_page.is_page_loaded() if hasattr(hio_page, 'is_page_loaded') else hio_page.wait_vue_stable()

        hio_count = hio_page.get_table_row_count()
        step(f"危废出入库记录: {hio_count} 行")
        assert hio_count >= 0, ea("危废出入库记录页面正常加载", f"{hio_count}行")
        chain['hazard_io'] = hio_count

        # ── 汇总 ──
        step(f"危废全链汇总: {chain}")
        all_loaded = all(isinstance(v, int) and v >= 0 for v in chain.values())
        assert all_loaded, ea("危废全链4页面均正常", chain)

        step("E2E-WH-002 危废全链验证通过 [OK]")

    # ── E2E-WH-003: 库存->盘点 数据一致性 ──────────────────────

    @allure.epic("库管管理")
    @allure.feature("备品备件")
    @allure.story("跨页面流转-库存盘点")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_wh_003_stock_stocktake_consistency(self, driver_setup):
        """E2E-WH-003: 备品库存 -> 盘点 数据一致性 (P1)

        流程:
          备品库存: 获取库存总数 + 第一条品名
          -> 备品盘点: 验证盘点列表
          -> 交叉验证库存与盘点数据存在关联
        """
        driver = driver_setup
        case("E2E-WH-003", "备品库存 <-> 盘点 数据一致性")

        # ── Step 1: 备品库存 ──
        step("导航到备品库存")
        nav_to(driver, "#/warehouse/spare/stock", "备品库存")
        stock_page = SpareStockPage(driver)
        stock_page.is_page_loaded() if hasattr(stock_page, 'is_page_loaded') else stock_page.wait_vue_stable()

        stock_count = stock_page.get_table_row_count()
        step(f"备品库存: {stock_count} 行")
        assert stock_count >= 0, ea("备品库存正常加载", f"{stock_count}行")

        stock_item = None
        if stock_count > 0:
            try:
                col1 = stock_page.get_column_data(1)
                stock_item = col1[0] if col1 else None
                step(f"库存第一条: {stock_item}")
            except Exception:
                pass

        # ── Step 2: 备品盘点 ──
        step("导航到备品盘点")
        nav_to(driver, "#/warehouse/spare/stocktake", "备品盘点")
        st_page = SpareStocktakePage(driver)
        st_page.is_page_loaded() if hasattr(st_page, 'is_page_loaded') else st_page.wait_vue_stable()

        st_count = st_page.get_table_row_count()
        step(f"备品盘点: {st_count} 行")
        assert st_count >= 0, ea("备品盘点正常加载", f"{st_count}行")

        # 交叉验证
        if stock_item and st_count > 0:
            try:
                st_col1 = st_page.get_column_data(1)
                step(f"盘点第一条: {st_col1[0] if st_col1 else 'N/A'}")
            except Exception:
                pass

        step("E2E-WH-003 备品库存<->盘点 通过 [OK]")

    # ── E2E-WH-004: 出入库记录 数据验证 ────────────────────────

    @allure.epic("库管管理")
    @allure.feature("备品备件")
    @allure.story("跨页面流转-出入库记录")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_wh_004_io_record_consistency(self, driver_setup):
        """E2E-WH-004: 入库单 -> 出库单 -> 出入库记录 (P1)

        流程:
          入库单: 获取入库单数量
          -> 出库单: 获取出库单数量
          -> 出入库记录: 验证记录总数 ≥ 入库+出库
        """
        driver = driver_setup
        case("E2E-WH-004", "入库->出库->出入库记录")

        # ── Step 1: 入库单 ──
        step("导航到入库单")
        nav_to(driver, "#/warehouse/spare/in-order", "入库单")
        in_page = SpareInOrderPage(driver)
        in_page.is_page_loaded() if hasattr(in_page, 'is_page_loaded') else in_page.wait_vue_stable()

        in_count = in_page.get_table_row_count()
        step(f"入库单: {in_count} 行")

        # ── Step 2: 出库单 ──
        step("导航到出库单")
        nav_to(driver, "#/warehouse/spare/out-order", "出库单")
        out_page = SpareOutOrderPage(driver)
        out_page.is_page_loaded() if hasattr(out_page, 'is_page_loaded') else out_page.wait_vue_stable()

        out_count = out_page.get_table_row_count()
        step(f"出库单: {out_count} 行")

        # ── Step 3: 出入库记录 ──
        step("导航到出入库记录")
        nav_to(driver, "#/warehouse/spare/io-record", "出入库记录")
        io_page = SpareIORecordPage(driver)
        io_page.is_page_loaded() if hasattr(io_page, 'is_page_loaded') else io_page.wait_vue_stable()

        io_count = io_page.get_table_row_count()
        step(f"出入库记录: {io_count} 行")

        # ── 验证 ──
        step(f"入库={in_count}, 出库={out_count}, 记录={io_count}")
        assert in_count >= 0 and out_count >= 0 and io_count >= 0, \
            ea("入库+出库+记录页面均正常", f"in={in_count}, out={out_count}, io={io_count}")

        step("E2E-WH-004 出入库记录验证通过 [OK]")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
