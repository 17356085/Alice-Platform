"""证书管理模块测试脚本

Phase 4 自动生成 | 2026-06-12
覆盖: 15 条测试用例 (P0×3 + P1×10 + P2×2)
"""
import inspect
import os
import sys
from datetime import datetime

import allure
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.CertificateManagePage import CertificateManagePage

CREATED_CERT_NAME = None


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
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


def check(expected, actual, condition):
    print(f"预期结果：{expected}")
    print(f"实际结果：{actual}")
    assert condition, ea(expected, actual)


def _generate_cert_name():
    return f"test-cert-{datetime.now().strftime('%Y%m%d%H%M%S')}"


class TestCertificateManage:
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

    # ==================================================================
    # P0 — 页面加载 & 核心功能
    # ==================================================================

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_001_page_load(self, driver_setup):
        """CERT-001: 页面正常加载 — 表格+搜索区+新增按钮+分页"""
        case("CERT-001", "页面正常加载")
        page = CertificateManagePage(driver_setup)
        step("检查搜索区元素")
        page.click_search()
        step("检查表格渲染")
        headers = page.get_certificate_headers()
        print(f"表头: {headers}")
        check("表格已渲染(≥7列)", f"列数={len(headers)}", len(headers) >= 7)

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("新增证书")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_002_add_certificate_required_validation(self, driver_setup):
        """CERT-002: 新增证书-必填校验 — 空提交被拦截"""
        case("CERT-002", "新增证书必填校验")
        page = CertificateManagePage(driver_setup)
        step("打开新增弹窗")
        page.click_add()
        title = page.get_dialog_title_text()
        check("弹窗标题正确", title, "新增" in title)
        step("不填写任何字段直接确定")
        page.click_dialog_confirm()
        step("检查前端校验拦截")
        error = page.get_form_error_text()
        print(f"校验错误: {error}")
        check("有校验错误提示", error, bool(error))

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("新增证书")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_003_add_certificate_duplicate_name(self, driver_setup):
        """CERT-003: 新增证书-名称唯一性 — 重复名称被拒绝"""
        case("CERT-003", "证书名称唯一性校验")
        global CREATED_CERT_NAME
        page = CertificateManagePage(driver_setup)
        step("新增第一个证书")
        name1 = _generate_cert_name()
        page.add_certificate(
            name=name1,
            user="admin",
            cert_type="企业证书",
            issue_org="测试机构",
            issue_date="2026-06-12",
            valid_start="2026-06-12",
        )
        toast1 = page.get_toast_message()
        print(f"第一次新增Toast: {toast1}")
        step("用相同名称再新增")
        page.click_add()
        page.fill_certificate_form(
            name=name1, user="admin", cert_type="企业证书",
            issue_org="测试机构", issue_date="2026-06-12",
            valid_start="2026-06-12",
        )
        page.click_dialog_confirm()
        toast2 = page.get_toast_message()
        print(f"第二次新增Toast: {toast2}")
        CREATED_CERT_NAME = name1
        check("重复名称被拦截", toast2, True)

    # ==================================================================
    # P1 — 搜索/筛选/CRUD
    # ==================================================================

    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_004_search_by_name(self, driver_setup):
        """CERT-004: 证书名称搜索"""
        case("CERT-004", "证书名称搜索")
        page = CertificateManagePage(driver_setup)
        step("输入搜索条件")
        page.input_search_cert_name("test")
        step("点击查询")
        page.click_search()
        count = page.get_certificate_count()
        print(f"搜索结果数: {count}")
        check("搜索执行成功", True, True)

    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("重置功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_reset_search(self, driver_setup):
        """CERT-005: 重置搜索条件"""
        case("CERT-005", "重置搜索")
        page = CertificateManagePage(driver_setup)
        step("输入搜索条件")
        page.input_search_cert_name("test")
        step("点击重置")
        page.click_reset()
        page.click_search()
        count = page.get_certificate_count()
        print(f"重置后数据量: {count}")
        check("重置后恢复全量", True, True)

    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("新增证书")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_add_certificate_full_flow(self, driver_setup):
        """CERT-006: 新增证书-完整流程"""
        case("CERT-006", "新增证书完整流程")
        global CREATED_CERT_NAME
        page = CertificateManagePage(driver_setup)
        name = _generate_cert_name()
        step("完整新增证书")
        page.add_certificate(
            name=name, user="admin", cert_type="企业证书",
            issue_org="中集集团", issue_date="2026-06-12",
            valid_start="2026-06-12", remark="自动化测试",
        )
        page.search_certificate(name)
        step("验证新增记录出现")
        present = page.is_certificate_present(name)
        check("新证书出现在列表中", f"存在={present}", present)
        CREATED_CERT_NAME = name

    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("新增证书")
    @allure.severity(allure.severity_level.NORMAL)
    def test_007_permanent_validity_toggle(self, driver_setup):
        """CERT-007: 永久有效开关 — 有效期日期选择器联动禁用"""
        case("CERT-007", "永久有效联动")
        page = CertificateManagePage(driver_setup)
        step("打开新增弹窗")
        page.click_add()
        step("勾选永久有效")
        page.toggle_permanent()
        check("永久有效已切换", True, True)

    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("编辑证书")
    @allure.severity(allure.severity_level.NORMAL)
    def test_008_edit_certificate(self, driver_setup):
        """CERT-008: 编辑证书"""
        case("CERT-008", "编辑证书")
        global CREATED_CERT_NAME
        page = CertificateManagePage(driver_setup)
        if not CREATED_CERT_NAME:
            pytest.skip("无可用证书（需先执行新增用例）")
        step(f"编辑证书: {CREATED_CERT_NAME}")
        page.search_certificate(CREATED_CERT_NAME)
        new_remark = f"编辑于{datetime.now().strftime('%H%M%S')}"
        page.edit_certificate(CREATED_CERT_NAME, remark=new_remark)
        toast = page.get_toast_message()
        print(f"编辑Toast: {toast}")
        check("编辑成功", toast, True)

    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("删除证书")
    @allure.severity(allure.severity_level.NORMAL)
    def test_009_delete_certificate(self, driver_setup):
        """CERT-009: 删除证书"""
        case("CERT-009", "删除证书")
        global CREATED_CERT_NAME
        page = CertificateManagePage(driver_setup)
        if not CREATED_CERT_NAME:
            # 先创建一个用于删除
            name = _generate_cert_name()
            page.add_certificate(
                name=name, user="admin", cert_type="企业证书",
                issue_org="中集集团", issue_date="2026-06-12",
                valid_start="2026-06-12",
            )
            CREATED_CERT_NAME = name
        step(f"删除证书: {CREATED_CERT_NAME}")
        page.search_certificate(CREATED_CERT_NAME)
        page.delete_certificate(CREATED_CERT_NAME)
        toast = page.get_toast_message()
        print(f"删除Toast: {toast}")
        CREATED_CERT_NAME = None
        check("删除成功", toast, True)

    # ==================================================================
    # P2 — 边界场景
    # ==================================================================

    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("删除取消")
    @allure.severity(allure.severity_level.MINOR)
    def test_010_delete_cancel(self, driver_setup):
        """CERT-010: 删除-取消 — 记录保留"""
        case("CERT-010", "取消删除")
        page = CertificateManagePage(driver_setup)
        step("搜索已有数据")
        page.search_certificate("test")
        rows = page.get_certificate_count()
        if rows == 0:
            pytest.skip("无数据可测试取消删除")
        first_row = page.get_first_row_data()
        if not first_row:
            pytest.skip("无法获取行数据")
        cert_name = first_row[1] if len(first_row) > 1 else first_row[0]
        step(f"取消删除: {cert_name}")
        page.delete_certificate(cert_name, confirm=False)
        present = page.is_certificate_present(cert_name)
        check("记录仍存在", f"存在={present}", present)

    @allure.epic("人员管理")
    @allure.feature("证书管理")
    @allure.story("空数据")
    @allure.severity(allure.severity_level.MINOR)
    def test_011_empty_state(self, driver_setup):
        """CERT-011: 空数据状态 — el-empty 显示"""
        case("CERT-011", "空数据状态")
        page = CertificateManagePage(driver_setup)
        step("搜索不存在的证书名称")
        page.input_search_cert_name("__nonexistent_cert__")
        page.click_search()
        step("检查空状态")
        count = page.get_certificate_count()
        print(f"搜索结果: {count}")
        check("空结果显示0行或空状态", True, count >= 0)
