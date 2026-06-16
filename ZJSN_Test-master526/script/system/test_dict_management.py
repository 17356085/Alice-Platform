"""字典管理模块测试 — 企业级重构版

测试策略：
  - 闭环数据：创建 → 搜索验证 → 编辑 → 搜索验证 → 删除 → 搜索确认无
  - Session 级 fixture：共享浏览器实例，减少启动开销
  - 全局变量共享测试数据：同一 session 内用例间传递字典标签
"""
import os
import sys
import pytest
import allure
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.cleanup_tracker import get_cleanup_tracker
from page.system_page.DictManagePage import DictManagePage


# ==================================================================
#  测试辅助
# ==================================================================
def step(text):
    """Allure 步骤包装器（兼容无 Allure 环境）"""
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")


def case(case_id, title):
    """用例信息输出"""
    print(f"\n========== 用例 {case_id}：{title} ==========")
    try:
        allure.dynamic.title(f"{case_id} {title}")
        allure.dynamic.description(f"用例编号：{case_id}\n用例说明：{title}")
    except Exception:
        pass


def ea(expected, actual):
    """格式化预期与实际结果对比"""
    return f"预期结果：{expected}；实际结果：{actual}"


def _generate_dict_label(suffix=""):
    """生成唯一字典标签"""
    return f"test{datetime.now().strftime('%Y%m%d%H%M%S%f')}{suffix}"


# ==================================================================
#  测试数据共享（session 内跨用例传递）
# ==================================================================
CREATED_DICT_LABEL_05 = None   # SY-DICT-02 新增的数据
CREATED_DICT_LABEL_06 = None   # SY-DICT-03 新增的数据
UPDATED_DICT_LABEL_08 = None   # SY-DICT-08 修改后的标签


# ==================================================================
#  Fixture（module 级，覆盖 conftest 同名 fixture）
# ==================================================================
@pytest.fixture(scope="module")
def driver_setup():
    """Module 级：登录 + 导航到字典管理"""
    base = BaseDriver()
    driver = base.open_browser()
    try:
        step("登录系统")
        ensure_logged_in(driver)
        step("进入字典管理页面")
        DictManagePage(driver).navigate_to_dict_management()
        yield driver
    finally:
        base.close_browser()


# ==================================================================
#  测试类
# ==================================================================
class TestDictManage:
    """字典管理 — 字典数据 Tab 测试"""

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("字典管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_dict_01_page_display(self, driver_setup):
        """SY-DICT-01: 正常显示字典列表以及相关字段"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-01", "正常显示字典列表以及相关字段")

        # Debug: check URL and table
        WebDriverWait(driver_setup, 5).until(lambda d: d.execute_script("return window.location.hash;") != "")
        url = driver_setup.execute_script("return window.location.hash;")
        th = driver_setup.execute_script("return document.querySelectorAll('.el-table__header-wrapper th').length;")
        print(f"DEBUG: URL={url}, th_count={th}")

        step("获取字典列表表头并校验")
        headers = page.get_table_headers()
        expected = {"字典标签", "字典键值", "排序", "状态", "备注", "创建时间", "操作"}
        assert expected.issubset(set(headers)), \
            ea(f"字典列表表头包含：{sorted(expected)}", headers)

    # ------------------------------------------------------------------
    def test_sy_dict_02_add_required(self, driver_setup):
        """SY-DICT-02: 新增字典（仅必选字段）"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-02", "新增字典（必选）")

        global CREATED_DICT_LABEL_05
        CREATED_DICT_LABEL_05 = _generate_dict_label("新增")

        step("点击新增")
        page.click_add()

        step(f"填写表单 — 字典标签: {CREATED_DICT_LABEL_05}")
        page.fill_dict_form(
            label=CREATED_DICT_LABEL_05,
            key_value=3,
            status="停用",
        )

        step("点击保存")
        page.click_dialog_save()
        msg = page.wait_for_toast_text(timeout=8)
        print(f"  [DEBUG] Toast消息: {msg!r}")

        # 注册清理
        get_cleanup_tracker().register(
            entity_type="dict", entity_name=CREATED_DICT_LABEL_05,
            cleanup_method="api"
        )

        step(f"搜索验证 — 字典标签: {CREATED_DICT_LABEL_05}")
        page.click_reset()
        page.input_dict_label(CREATED_DICT_LABEL_05)
        page.click_search()
        labels = page.get_column_data_by_header("字典标签")
        assert any(CREATED_DICT_LABEL_05 in x for x in labels), \
            ea(f"列表中存在 {CREATED_DICT_LABEL_05}",
               labels or page.get_empty_text() or "暂无数据")

    # ------------------------------------------------------------------
    def test_sy_dict_03_add_required_optional(self, driver_setup):
        """SY-DICT-03: 新增字典（必选 + 非必选全部字段）"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-03", "新增字典（必选+非必选）")

        global CREATED_DICT_LABEL_06
        CREATED_DICT_LABEL_06 = _generate_dict_label("新增全字段")

        step("点击新增")
        page.click_add()

        step("填写完整表单")
        page.fill_dict_form(
            label=CREATED_DICT_LABEL_06,
            key_value=3,
            status="启用",
            sort_value=2,
            remark="自动化测试备注",
        )

        step("点击保存")
        page.click_dialog_save()
        msg = page.wait_for_toast_text(timeout=8)
        print(f"  [DEBUG] Toast消息: {msg!r}")

        get_cleanup_tracker().register(
            entity_type="dict", entity_name=CREATED_DICT_LABEL_06,
            cleanup_method="api"
        )

        step(f"搜索验证 — 字典标签: {CREATED_DICT_LABEL_06}")
        page.click_reset()
        page.input_dict_label(CREATED_DICT_LABEL_06)
        page.click_search()
        labels = page.get_column_data_by_header("字典标签")
        assert any(CREATED_DICT_LABEL_06 in x for x in labels), \
            ea(f"列表中存在 {CREATED_DICT_LABEL_06}",
               labels or page.get_empty_text() or "暂无数据")

    # ------------------------------------------------------------------
    def test_sy_dict_04_search_by_dict_name(self, driver_setup):
        """SY-DICT-04: 按字典名称搜索"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-04", "按字典名称搜索（新增数据）")

        global CREATED_DICT_LABEL_05
        if not CREATED_DICT_LABEL_05:
            pytest.skip("未获取到新增字典标签，请先执行 SY-DICT-02")

        step("点击重置")
        page.click_reset()

        target = CREATED_DICT_LABEL_05
        step(f"输入字典标签: {target}")
        page.input_dict_label(target)

        step("点击搜索")
        page.click_search()
        labels = page.get_column_data_by_header("字典标签")
        assert labels, ea("显示符合条件的数据项", page.get_empty_text() or "暂无数据")
        assert any(target in x for x in labels), ea(f"结果包含「{target}」", labels)

    # ------------------------------------------------------------------
    def test_sy_dict_05_search_by_status(self, driver_setup):
        """SY-DICT-05: 按状态搜索"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-05", "按状态搜索")

        step("点击重置，清空搜索条件")
        page.click_reset()
        page.input_dict_label("")

        step("选择状态: 启用")
        page.select_status("启用")

        step("点击搜索")
        page.click_search()
        status_col = page.get_column_data_by_header("状态")
        assert status_col, ea("显示符合条件的数据项", page.get_empty_text() or "暂无数据")
        assert all("启用" in s for s in status_col), \
            ea("筛选结果状态列都为启用", status_col)

    # ------------------------------------------------------------------
    def test_sy_dict_06_reset_button(self, driver_setup):
        """SY-DICT-06: 重置按钮功能正常"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-06", "重置按钮功能正常")

        step("输入筛选条件")
        page.input_dict_label("待考试")
        page.select_status("启用")

        step("点击重置")
        page.click_reset()
        assert page.get_dict_label_value() == "", \
            ea("所有筛选条件清空", page.get_dict_label_value())

        step("点击搜索验证列表正常加载")
        page.click_search()
        assert page.get_table_row_count() > 0, \
            ea("正常加载字典列表", page.get_empty_text() or "暂无数据")

    # ------------------------------------------------------------------
    def test_sy_dict_07_export(self, driver_setup):
        """SY-DICT-07: 导出表格数据"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-07", "导出表格数据")

        step("点击导出")
        export_confirmed = page.click_export()
        msg = page.wait_for_toast_text(timeout=6)
        assert export_confirmed or any(k in (msg or "") for k in ["成功", "导出", "确认", "已"]), \
            ea("导出成功提示", msg or "未获取到提示")

    # ------------------------------------------------------------------
    def test_sy_dict_08_edit(self, driver_setup):
        """SY-DICT-08: 编辑字典数据项"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-08", "编辑数据项目信息")

        global CREATED_DICT_LABEL_06, UPDATED_DICT_LABEL_08
        if not CREATED_DICT_LABEL_06:
            pytest.skip("未获取到 SY-DICT-03 新增的字典标签，请先执行新增用例")

        step(f"搜索目标数据: {CREATED_DICT_LABEL_06}")
        page.click_reset()
        page.input_dict_label(CREATED_DICT_LABEL_06)
        page.click_search()
        labels = page.get_column_data_by_header("字典标签")
        assert labels, ea(f"已存在数据: {CREATED_DICT_LABEL_06}",
                          page.get_empty_text() or "暂无数据")

        step("点击编辑按钮")
        page.click_row_action(CREATED_DICT_LABEL_06, "编辑")

        UPDATED_DICT_LABEL_08 = _generate_dict_label("修改")
        step(f"修改字典标签为: {UPDATED_DICT_LABEL_08}")
        page.fill_dict_form(
            label=UPDATED_DICT_LABEL_08,
            key_value=4,
            status="启用",
            sort_value=6,
            remark="修改后的备注",
        )

        step("点击保存")
        page.click_dialog_save()
        msg = page.wait_for_toast_text(timeout=10)
        print(f"  [DEBUG] 编辑Toast: {msg!r}")

        step(f"搜索验证修改结果: {UPDATED_DICT_LABEL_08}")
        page.click_reset()
        page.input_dict_label(UPDATED_DICT_LABEL_08)
        page.click_search()
        labels = page.get_column_data_by_header("字典标签")
        assert any(UPDATED_DICT_LABEL_08 in x for x in labels), \
            ea("用户数据已修改", labels or page.get_empty_text() or "暂无数据")

    # ------------------------------------------------------------------
    def test_sy_dict_09_delete(self, driver_setup):
        """SY-DICT-09: 删除数据项（闭环清理）"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-09", "删除数据项")

        global CREATED_DICT_LABEL_05, CREATED_DICT_LABEL_06, UPDATED_DICT_LABEL_08

        # 收集所有待删除的标签
        targets = []
        for lbl in [UPDATED_DICT_LABEL_08, CREATED_DICT_LABEL_06, CREATED_DICT_LABEL_05]:
            if lbl:
                targets.append(lbl)
        if not targets:
            pytest.skip("未获取到需删除的字典标签，请先执行新增/编辑用例")

        for target in targets:
            step(f"搜索并删除: {target}")
            page.click_reset()
            page.input_dict_label(target)
            page.click_search()

            labels = page.get_column_data_by_header("字典标签")
            if not labels:
                # 可能已被前置用例改名/删除（如 SY-DICT-08 改名后原标签不再存在）
                print(f"  [SKIP] {target} 未找到，可能已被改名或删除，跳过")
                continue

            msg = page.delete_by_label(target)
            print(f"  [DEBUG] 删除Toast: {msg!r}")

            step(f"再次搜索确认已删除: {target}")
            page.click_reset()
            page.input_dict_label(target)
            page.click_search()
            labels_after = page.get_column_data_by_header("字典标签")
            # 核心断言：数据确实被删除了（搜不到即成功，Toast 可能偶发不可见）
            assert not any(target in x for x in labels_after), \
                ea(f"删除后列表不再包含 {target}",
                   labels_after or page.get_empty_text() or "暂无数据")


class TestDictCategory:
    """字典管理 — 字典分类 Tab 测试"""

    def test_sy_dict_10_switch_categories(self, driver_setup):
        """SY-DICT-10: 字典分类进入不同分类"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-10", "字典分类进入不同分类")

        step("切换到字典分类 Tab")
        page.switch_to_category_tab()

        step("点击「全部」筛选")
        page.click_category_filter("全部")

        step("确保分类「考试」存在（非系统）")
        page.ensure_category_exists("考试", code="KS001", is_system=False,
                                    sort_value=1, remark="auto")

        step("确保分类「测试系统」存在（系统）")
        page.ensure_category_exists("测试系统", code="C123", is_system=True,
                                    sort_value=1, remark="auto")

        step("进入分类「考试」")
        page.select_category("考试")

        step("进入分类「测试系统」")
        page.select_category("测试系统")

    # ------------------------------------------------------------------
    def test_sy_dict_11_category_search(self, driver_setup):
        """SY-DICT-11: 字典分类查询"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-11", "字典分类查询")

        step("切换到字典分类 Tab")
        page.switch_to_category_tab()

        target = "考试"
        step(f"确保分类「{target}」存在")
        page.ensure_category_exists(target, code="KS001", is_system=False,
                                    sort_value=1, remark="auto")

        step(f"在分类搜索框输入: {target}")
        page.input_category_search(target)

        names = page.get_category_names(limit=10)
        assert names, ea("显示包含考试的分类", "搜索后无任何分类可见")
        assert all(target in n for n in names), \
            ea("仅显示符合搜索条件的分类", names)

    # ------------------------------------------------------------------
    def test_sy_dict_13_category_filter_all(self, driver_setup):
        """SY-DICT-13: 字典分类「全部」按钮"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-13", "字典分类全部按钮")

        step("切换到字典分类 Tab")
        page.switch_to_category_tab()

        step("点击「全部」")
        page.click_category_filter("全部")
        page.input_category_search("")

        names = page.get_category_names(limit=10)
        assert names, ea("点击全部后显示分类菜单", "分类列表为空")

    # ------------------------------------------------------------------
    def test_sy_dict_14_category_filter_system(self, driver_setup):
        """SY-DICT-14: 字典分类「系统」按钮"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-14", "字典分类系统按钮")

        step("切换到字典分类 Tab")
        page.switch_to_category_tab()

        step("点击「系统」")
        page.click_category_filter("系统")
        page.input_category_search("")

        names = page.get_category_names(limit=10)
        assert names, ea("点击系统后显示分类菜单", "分类列表为空")

    # ------------------------------------------------------------------
    def test_sy_dict_15_category_filter_custom(self, driver_setup):
        """SY-DICT-15: 字典分类「自定义」按钮"""
        page = DictManagePage(driver_setup)
        case("SY-DICT-15", "字典分类自定义按钮")

        step("切换到字典分类 Tab")
        page.switch_to_category_tab()

        step("点击「自定义」")
        page.click_category_filter("自定义")
        page.input_category_search("")

        names = page.get_category_names(limit=10)
        assert names, ea("点击自定义后显示分类菜单", "分类列表为空")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
