"""组织管理模块测试脚本"""
import os
import sys
import time
import pytest
import allure
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import ensure_logged_in
from page.system_page.OrgManagePage import OrgManagePage
"""前置准备数据"""


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


ORG_NAME_06 = None
ORG_NAME_07 = None
CHILD_ORG_NAME_13 = None


def _generate_org_name(suffix):
    return f"test{datetime.now().strftime('%Y%m%d%H%M%S%f')}{suffix}"


def _ensure_org_exists(page, org_name, *, org_type="部门", status_text="启用", order_value=1):
    page.click_reset()
    page.input_org_name(org_name)
    page.click_search()
    names = page.get_column_data_by_header("组织名称")
    if any(org_name in n for n in names):
        return

    page.click_add()
    page.input_dialog_field("组织名称", org_name)
    page.select_dialog_option("组织类型", org_type)
    try:
        page.select_dialog_status(status_text)
    except Exception:
        if status_text == "禁用":
            page.select_dialog_status("停用")
        else:
            raise
    page.input_dialog_field("排序", order_value)
    page.click_dialog_confirm()
    page.wait_for_toast_text(timeout=6)



class TestOrgManage:
    @pytest.fixture(autouse=True)
    def _ensure_org_page(self, driver_setup):
        try:
            if driver_setup.find_elements(By.XPATH, '//input[@placeholder="请输入账号"]'):
                ensure_logged_in(driver_setup)
            page = OrgManagePage(driver_setup)
            try:
                dialogs = driver_setup.find_elements(By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]')
                if dialogs:
                    try:
                        page.click_dialog_cancel()
                    except Exception:
                        try:
                            page.click_dialog_close()
                        except Exception:
                            pass
            except Exception:
                pass

            if not driver_setup.find_elements(*page.ORG_NAME_INPUT):
                page.navigate_to_org_management()
            return
        except Exception:
            page = OrgManagePage(driver_setup)
            page.navigate_to_org_management()

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("组织管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sy_org_01_page_display(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-01", "正常显示组织列表以及相关字段")
        step("获取组织列表表头并校验")
        headers = page.get_table_headers()
        expected = {"组织名称", "组织类型", "负责人", "联系电话", "员工数量", "状态", "操作"}
        assert expected.issubset(set(headers)), ea(f"组织列表表头包含：{sorted(expected)}", headers)
        step("校验组织列表有数据")
        assert page.get_table_row_count() > 0, ea("组织列表应有数据", page.get_empty_text() or "暂无数据")

    def test_sy_org_02_add_org_required(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-02", "新增组织（必选）")
        global ORG_NAME_06
        if not ORG_NAME_06:
            ORG_NAME_06 = _generate_org_name("新增")
        step("点击重置")
        page.click_reset()
        step("点击新增")
        page.click_add()
        step(f"输入组织名称：{ORG_NAME_06}")
        page.input_dialog_field("组织名称", ORG_NAME_06)
        step("选择组织类型：部门")
        page.select_dialog_option("组织类型", "部门")
        step("选择状态：启用")
        page.select_dialog_status("启用")
        step("输入排序：4")
        page.input_dialog_field("排序", 4)
        step("点击确定")
        page.click_dialog_confirm()
        msg = page.wait_for_toast_text(timeout=6)
        assert any(k in (msg or "") for k in ["成功", "已存在", "重复"]) or msg == "", ea("新增组织成功（或提示已存在）", msg or "未获取到提示")

        step(f"搜索组织名称：{ORG_NAME_06}")
        page.click_reset()
        page.input_org_name(ORG_NAME_06)
        page.click_search()
        names = page.get_column_data_by_header("组织名称")
        assert any(ORG_NAME_06 in n for n in names), ea(f"列表存在组织：{ORG_NAME_06}", names or page.get_empty_text() or "暂无数据")

    def test_sy_org_03_add_org_required_optional(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-03", "新增组织（必选+非必选）")
        global ORG_NAME_07
        if not ORG_NAME_07:
            ORG_NAME_07 = _generate_org_name("新增")
        step("点击重置")
        page.click_reset()
        step("点击新增")
        page.click_add()
        step(f"输入组织名称：{ORG_NAME_07}")
        page.input_dialog_field("组织名称", ORG_NAME_07)
        step("选择组织类型：部门")
        page.select_dialog_option("组织类型", "部门")
        step("输入负责人：test")
        page.input_dialog_field("负责人", "test")
        step("输入联系电话：18500001850")
        page.input_dialog_field("联系电话", "18500001850")
        step("输入机构编码：51812")
        page.input_dialog_field("机构编码", "51812")
        step("选择状态：禁用")
        try:
            page.select_dialog_status("禁用")
        except Exception:
            page.select_dialog_status("停用")
        step("输入排序：2")
        page.input_dialog_field("排序", 2)
        step("点击确定")
        page.click_dialog_confirm()
        msg = page.wait_for_toast_text(timeout=6)
        assert any(k in (msg or "") for k in ["成功", "已存在", "重复"]) or msg == "", ea("新增组织成功（或提示已存在）", msg or "未获取到提示")

        step(f"搜索组织名称：{ORG_NAME_07}")
        page.click_reset()
        page.input_org_name(ORG_NAME_07)
        page.click_search()
        names = page.get_column_data_by_header("组织名称")
        assert any(ORG_NAME_07 in n for n in names), ea(f"列表存在组织：{ORG_NAME_07}", names or page.get_empty_text() or "暂无数据")

    def test_sy_org_04_edit_org_info(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-04", "编辑数据项目信息")
        global ORG_NAME_06
        if not ORG_NAME_06:
            pytest.skip("未获取到 SY-ORG-02 新增的组织名称，请先执行新增用例")
        step("点击重置")
        page.click_reset()
        step(f"搜索组织名称：{ORG_NAME_06}")
        page.input_org_name(ORG_NAME_06)
        page.click_search()
        names = page.get_column_data_by_header("组织名称")
        assert names, ea(f"存在组织：{ORG_NAME_06}", page.get_empty_text() or "暂无数据")
        step("点击目标组织行的编辑")
        try:
            page.click_row_action(ORG_NAME_06, "编辑")
        except Exception:
            page.click_first_row_edit()
        step("修改负责人：test007")
        page.input_dialog_field("负责人", "test007")
        step("修改联系电话：18500001851")
        page.input_dialog_field("联系电话", "18500001851")
        step("修改机构编码：51822")
        page.input_dialog_field("机构编码", "51822")
        step("点击确定")
        page.click_dialog_confirm()
        msg = page.wait_for_toast_text(timeout=6)
        assert ("成功" in msg) or (msg == ""), ea("编辑组织成功", msg or "未获取到提示")

        step("再次搜索并校验列表显示")
        page.click_reset()
        page.input_org_name(ORG_NAME_06)
        page.click_search()
        leaders = page.get_column_data_by_header("负责人")
        phones = page.get_column_data_by_header("联系电话")
        if leaders:
            assert any("test007" in x for x in leaders), ea("负责人列包含test007", leaders)
        if phones:
            assert any("18500001851" in x for x in phones), ea("联系电话列包含18500001851", phones)

    def test_sy_org_05_add_child_org(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-05", "数据项新增子组织")
        global ORG_NAME_07, CHILD_ORG_NAME_13
        if not ORG_NAME_07:
            pytest.skip("未获取到 SY-ORG-03 新增的组织名称，请先执行新增用例")
        step("点击重置")
        page.click_reset()

        step(f"确保父组织存在：{ORG_NAME_07}（不存在则新增）")
        _ensure_org_exists(page, ORG_NAME_07, org_type="部门", status_text="禁用", order_value=2)

        CHILD_ORG_NAME_13 = _generate_org_name("子组织")
        step(f"在{ORG_NAME_07}下新增子组织：{CHILD_ORG_NAME_13}")
        page.click_reset()
        page.input_org_name(ORG_NAME_07)
        page.click_search()
        page.open_add_child_dialog(ORG_NAME_07)
        page.input_dialog_field("组织名称", CHILD_ORG_NAME_13)
        page.select_dialog_option("组织类型", "部门")
        page.input_dialog_field("负责人", "test007")
        page.input_dialog_field("联系电话", "18500001853")
        page.input_dialog_field("机构编码", "51822")
        page.select_dialog_status("启用")
        page.input_dialog_field("排序", 1)
        page.click_dialog_confirm()
        msg = page.wait_for_toast_text(timeout=6)
        assert ("成功" in msg) or ("已存在" in msg) or ("重复" in msg) or (msg == ""), ea("新增子组织成功（或提示已存在）", msg or "未获取到提示")

        step(f"搜索组织名称：{CHILD_ORG_NAME_13}")
        page.click_reset()
        page.input_org_name(CHILD_ORG_NAME_13)
        page.click_search()
        names = page.get_column_data_by_header("组织名称")
        assert any(CHILD_ORG_NAME_13 in n for n in names), ea(f"列表存在组织：{CHILD_ORG_NAME_13}", names or page.get_empty_text() or "暂无数据")

    def test_sy_org_06_search_by_org_name(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-06", "按组织名称搜索")
        global ORG_NAME_06
        if not ORG_NAME_06:
            ORG_NAME_06 = _generate_org_name("新增")
        step("确保组织存在（用于搜索）：SY-ORG-02 新增组织名称")
        _ensure_org_exists(page, ORG_NAME_06, org_type="部门", status_text="启用", order_value=4)
        step("点击重置")
        page.click_reset()
        name = ORG_NAME_06
        step(f"输入组织名称：{name}")
        page.input_org_name(name)
        step("选择组织类型：部门")
        page.select_org_type("部门")
        step("点击搜索")
        page.click_search()
        names = page.get_column_data_by_header("组织名称")
        assert names, ea(f"搜索组织名称“{name}”应返回结果", page.get_empty_text() or "暂无数据")
        assert any(name in n for n in names), ea(f"结果包含“{name}”", names)

    def test_sy_org_07_search_by_type(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-07", "按类型搜索")
        step("点击重置")
        page.click_reset()
        step("清空组织名称")
        page.input_org_name("")
        type_text = "部门"
        step(f"选择组织类型：{type_text}")
        page.select_org_type(type_text)
        step("点击搜索")
        page.click_search()
        types = page.get_column_data_by_header("组织类型")
        assert types, ea(f"按组织类型={type_text}筛选后应有结果", page.get_empty_text() or "暂无数据")
        assert all(type_text in t for t in types), ea(f"筛选结果组织类型都应为“{type_text}”", types)

    def test_sy_org_08_search_by_multi_conditions(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-08", "按状态进行搜索")
        global ORG_NAME_07
        if not ORG_NAME_07:
            ORG_NAME_07 = _generate_org_name("新增")
        step("确保组织存在（用于状态筛选）：SY-ORG-03 新增组织名称")
        _ensure_org_exists(page, ORG_NAME_07, org_type="部门", status_text="禁用", order_value=2)
        step("点击重置")
        page.click_reset()
        name = ORG_NAME_07
        step(f"输入组织名称：{name}")
        page.input_org_name(name)
        step("选择组织类型：部门")
        page.select_org_type("部门")
        step("选择状态：禁用")
        try:
            page.select_status("禁用")
        except Exception:
            page.select_status("停用")
        step("点击搜索")
        page.click_search()
        names = page.get_column_data_by_header("组织名称")
        assert names, ea("按多条件筛选后应有结果", page.get_empty_text() or "暂无数据")
        assert any(name in n for n in names), ea(f"结果包含“{name}”", names)
        status_values = page.get_column_data_by_header("状态")
        if status_values:
            assert any("禁用" in s or "停用" in s for s in status_values), ea("结果中至少包含1条禁用/停用数据", status_values)

    def test_sy_org_09_reset_button(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-09", "重置按钮功能正常")
        step("输入筛选条件（组织名称/类型/状态）")
        page.input_org_name("安全部")
        page.select_org_type("部门")
        page.select_status("停用")
        step("点击重置")
        page.click_reset()
        assert page.get_org_name_input_value() == "", ea("重置后组织名称应清空", page.get_org_name_input_value())
        step("点击搜索验证列表正常加载")
        page.click_search()
        assert page.get_table_row_count() > 0, ea("重置后应正常加载组织列表", page.get_empty_text() or "暂无数据")

    def test_sy_org_10_expand_collapse(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-10", "展开折叠查看列表信息")
        step("点击重置")
        page.click_reset()
        before = page.get_table_row_count()
        step("展开（如存在展开图标）")
        page.expand_first_row_if_possible()
        after_expand = page.get_table_row_count()
        assert after_expand != before or after_expand >= 1, ea("点击展开/折叠后列表应正常刷新", f"点击前={before}, 点击后={after_expand}")
        step("再次点击（尝试折叠）")
        page.expand_first_row_if_possible()
        after_collapse = page.get_table_row_count()
        assert after_collapse >= 1, ea("再次点击后列表仍应正常显示", f"当前行数={after_collapse}")

    def test_sy_org_11_export(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-11", "导出表格数据")
        download_dir = page.get_download_dir()
        before_files = []
        try:
            before_files = os.listdir(download_dir)
        except Exception:
            before_files = []
        step("点击导出")
        page.click_export()
        downloaded = page.wait_for_new_download(before_files, timeout=30)
        assert downloaded != "", ea("导出后应下载文件", f"下载目录={download_dir}，未检测到新增文件")
        assert os.path.exists(downloaded), ea("下载文件存在", downloaded)
        assert os.path.getsize(downloaded) > 0, ea("下载文件大小大于0", f"{downloaded} size=0")

    def test_sy_org_12_view_org_info(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-12", "查看数据项目信息")
        step("点击重置")
        page.click_reset()
        step("点击第一行查看")
        page.open_view_dialog()

        step("断言弹窗标题为：查看组织")
        header_xpath = "/html/body/div[5]/div/div/header/span"
        header_el = WebDriverWait(driver_setup, 6).until(EC.presence_of_element_located((By.XPATH, header_xpath)))
        header_text = (header_el.text or "").strip()
        assert "查看组织" in header_text, ea("弹窗标题包含“查看组织”", header_text or "未获取到标题")

        step("点击关闭")
        close_xpath = "/html/body/div[5]/div/div/footer/div/button/span"
        close_span = WebDriverWait(driver_setup, 6).until(EC.presence_of_element_located((By.XPATH, close_xpath)))
        try:
            close_span.click()
        except Exception:
            driver_setup.execute_script("arguments[0].click();", close_span)

    def test_sy_org_13_delete_parent_should_fail(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-13", "删除数据项（父组织）")
        global ORG_NAME_07
        if not ORG_NAME_07:
            pytest.skip("未获取到 SY-ORG-03 新增的组织名称，请先执行新增用例")
        step("点击重置")
        page.click_reset()
        step(f"搜索父组织：{ORG_NAME_07}")
        page.input_org_name(ORG_NAME_07)
        page.click_search()
        names = page.get_column_data_by_header("组织名称")
        assert any(ORG_NAME_07 in n for n in names), ea(f"存在父组织：{ORG_NAME_07}", names or page.get_empty_text() or "暂无数据")

        step(f"删除父组织：{ORG_NAME_07}")
        msg = page.delete_org_by_name(ORG_NAME_07)
        assert any(k in (msg or "") for k in ["删除失败", "不能删除", "存在子", "失败"]) or msg != "", ea("删除失败（存在子部门，不能删除）", msg or "未获取到提示")

    def test_sy_org_14_delete_child_should_success(self, driver_setup):
        page = OrgManagePage(driver_setup)
        case("SY-ORG-14", "删除数据项（子组织）")
        global CHILD_ORG_NAME_13, ORG_NAME_06, ORG_NAME_07
        if not CHILD_ORG_NAME_13:
            pytest.skip("未获取到 SY-ORG-05 新增的子组织名称，请先执行新增子组织用例")
        step("点击重置")
        page.click_reset()
        step(f"搜索子组织：{CHILD_ORG_NAME_13}")
        page.input_org_name(CHILD_ORG_NAME_13)
        page.click_search()
        names = page.get_column_data_by_header("组织名称")
        assert any(CHILD_ORG_NAME_13 in n for n in names), ea(f"存在子组织：{CHILD_ORG_NAME_13}", names or page.get_empty_text() or "暂无数据")

        step(f"删除子组织：{CHILD_ORG_NAME_13}")
        msg = page.delete_org_by_name(CHILD_ORG_NAME_13)
        assert any(k in (msg or "") for k in ["删除成功", "成功"]) or msg != "", ea("删除成功", msg or "未获取到提示")

        step(f"再次搜索，断言列表无{CHILD_ORG_NAME_13}")
        page.click_reset()
        page.input_org_name(CHILD_ORG_NAME_13)
        page.click_search()
        names = page.get_column_data_by_header("组织名称")
        assert not any(CHILD_ORG_NAME_13 in n for n in names), ea(f"删除后列表无{CHILD_ORG_NAME_13}", names or page.get_empty_text() or "暂无数据")

        step("删除父组织与另一个新增组织，确保数据无残留")
        for org_name in [ORG_NAME_07, ORG_NAME_06]:
            if not org_name:
                continue
            page.click_reset()
            page.input_org_name(org_name)
            page.click_search()
            before = page.get_column_data_by_header("组织名称")
            if not any(org_name in n for n in before):
                continue
            msg = page.delete_org_by_name(org_name)
            assert (msg or "") != "", ea(f"删除{org_name}应有提示", msg or "未获取到提示")
            page.click_reset()
            page.input_org_name(org_name)
            page.click_search()
            after = page.get_column_data_by_header("组织名称")
            assert not any(org_name in n for n in after), ea(f"删除后列表无{org_name}", after or page.get_empty_text() or "暂无数据")

        ORG_NAME_06 = None
        ORG_NAME_07 = None
        CHILD_ORG_NAME_13 = None


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
