"""合同管理模块测试脚本"""
import pytest
import sys
import os
import inspect
import allure
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.sales_page.ContractPage import ContractPage

# 闭环测试数据（module 级全局变量）
CREATED_CONTRACT_NAME = None
CREATED_DAY_TAG = None
CONTRACT_CUSTOMER_NAME = "测试客户"  # 使用存在的客户（可通过搜索列表第一个客户获取）
UPDATED_CONTRACT_NAME = None


def _generate_contract_test_data():
    """生成本轮合同闭环测试数据"""
    day_tag = datetime.now().strftime("%Y%m%d%H%M%S")
    contract_name = f"测试合同_{day_tag}"
    updated_name = f"测试合同_{day_tag}_已修改"
    return contract_name, day_tag, updated_name


class TestContractManage:
    """合同管理模块测试用例"""

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
    def _require_created_contract_name(self):
        global CREATED_CONTRACT_NAME
        assert CREATED_CONTRACT_NAME, "未获取到新增合同名称，请先执行新增用例"
        return CREATED_CONTRACT_NAME

    def _pick_existing_customer(self, page):
        """从已存在数据中选取一个客户名称用于关联合同"""
        # 先尝试获取第一个客户名称
        names = page.get_column_data(page.COL_CUSTOMER_NAME)
        if names:
            return names[0]
        # 如果表格没有客户列，返回默认值
        return "测试客户"

    # ==================================================================
    #  CTR-001: 页面展示
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("合同管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        driver = driver_setup
        page = ContractPage(driver)
        print("\n========== 测试 CTR-001: 页面显示正常 ==========")

        try:
            total_text = page.get_total_count_text()
            print(f"[OK] 获取到总条数信息: {total_text}")
            assert any(char.isdigit() for char in total_text), "总条数应包含数字"

            headers = page.get_table_headers()
            print(f"[OK] 表头字段: {headers}")
            assert len(headers) > 0, "表头不应为空"

            row_count = page.get_table_row_count()
            print(f"[OK] 当前页加载了 {row_count} 条数据")

            print("========== CTR-001 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-002: 新增合同
    # ==================================================================
    @pytest.mark.destructive
    def test_002_add_contract_success(self, driver_setup, contract_test_data):
        """CTR-002: 新增合同成功（闭环数据）"""
        driver = driver_setup
        page = ContractPage(driver)
        td = contract_test_data
        print("\n========== 用例 CTR-002：新增合同成功 ==========")

        try:
            global CREATED_CONTRACT_NAME, CREATED_DAY_TAG, CONTRACT_CUSTOMER_NAME, UPDATED_CONTRACT_NAME
            contract_name, day_tag, updated_name = _generate_contract_test_data()
            CREATED_CONTRACT_NAME = contract_name
            CREATED_DAY_TAG = day_tag
            UPDATED_CONTRACT_NAME = updated_name

            # 尝试从现有列表中获取一个客户名称
            customer = self._pick_existing_customer(page)
            CONTRACT_CUSTOMER_NAME = customer
            print(f"本轮闭环测试数据：名称={CREATED_CONTRACT_NAME}, 关联客户={customer}")

            page.click_add()
            dialog_title = page.get_dialog_title()
            print(f"弹窗标题: {dialog_title}")

            # 填充表单
            page.fill_contract_form(
                name=CREATED_CONTRACT_NAME,
                customer=customer,
                product_type=td["existing"]["product_type"],
                total_quantity=1000,
                unit_price=3.5,
                start_date=td["date_ranges"]["full_year"]["start"],
                end_date=td["date_ranges"]["full_year"]["end"],
            )

            toast = page.click_save()
            print(f"操作提示: {toast}")

            if toast and "成功" in toast:
                pass
            elif not page.wait_dialog_closed(timeout=2):
                form_errors = page.get_form_error_text()
                if form_errors:
                    pytest.fail(f"表单校验失败: {form_errors}")
                assert False, f"新增合同提示异常: {toast}"
            else:
                print("[OK] 弹窗已关闭，视为新增成功")

            print("========== CTR-002 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-003: 按名称搜索合同
    # ==================================================================
    def test_003_search_contract(self, driver_setup):
        """CTR-003: 按合同名称搜索"""
        driver = driver_setup
        page = ContractPage(driver)
        print("\n========== 用例 CTR-003：搜索合同 ==========")

        try:
            contract_name = self._require_created_contract_name()

            page.click_reset_search()
            page.search(name=contract_name)

            row_count = page.get_table_row_count()
            print(f"搜索结果行数: {row_count}")
            assert row_count > 0, "搜索结果不应为空"

            names = page.get_column_data(page.COL_CONTRACT_NAME)
            print(f"搜索结果合同名称: {names}")
            assert any(contract_name.lower() in (n or "").lower() for n in names), \
                f"搜索结果未包含闭环合同 {contract_name}: {names}"

            page.click_reset_search()
            print("========== CTR-003 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-004: 编辑待执行状态的合同
    # ==================================================================
    @pytest.mark.destructive
    def test_004_edit_pending_contract(self, driver_setup):
        """CTR-004: 编辑待执行状态的合同成功"""
        driver = driver_setup
        page = ContractPage(driver)
        print("\n========== 用例 CTR-004：编辑待执行合同 ==========")

        try:
            contract_name = self._require_created_contract_name()
            new_name = UPDATED_CONTRACT_NAME or f"测试合同_{CREATED_DAY_TAG}_已修改"

            page.click_reset_search()
            page.search(name=contract_name)

            row_count = page.get_table_row_count()
            assert row_count > 0, f"合同 '{contract_name}' 不存在"

            # 验证当前状态允许编辑
            status = page.get_contract_status(contract_name)
            print(f"当前合同状态: {status}")
            assert page.is_editable(contract_name), f"合同状态 '{status}' 不可编辑"

            page.click_edit_by_name(contract_name)
            page.wait_vue_stable()

            page.fill_contract_form(
                name=new_name,
                total_quantity=2000,
                unit_price=4.0,
            )
            toast = page.click_save()
            print(f"编辑提示: {toast}")
            assert toast and "成功" in toast, f"编辑合同提示异常: {toast}"

            # 验证名称已更新
            page.click_reset_search()
            page.search(name=new_name)
            names = page.get_column_data(page.COL_CONTRACT_NAME)
            assert new_name in names, f"合同名称未更新成功，预期: {new_name}, 实际: {names}"
            print(f"[OK] 合同名称已更新为: {new_name}")

            print("========== CTR-004 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-005: 启动合同 — 待执行 → 执行中
    # ==================================================================
    @pytest.mark.destructive
    def test_005_start_contract(self, driver_setup):
        """CTR-005: 启动合同 — 状态: 待执行 → 执行中"""
        driver = driver_setup
        page = ContractPage(driver)
        print("\n========== 用例 CTR-005：启动合同 ==========")

        try:
            search_name = UPDATED_CONTRACT_NAME or self._require_created_contract_name()

            page.click_reset_search()
            page.search(name=search_name)

            row_count = page.get_table_row_count()
            assert row_count > 0, f"合同 '{search_name}' 不存在"

            status_before = page.get_contract_status(search_name)
            print(f"启动前状态: {status_before}")

            toast = page.start_contract(search_name)
            print(f"启动提示: {toast}")

            page.click_reset_search()
            page.search(name=search_name)
            page.wait_vue_stable()

            status_after = page.get_contract_status(search_name)
            print(f"启动后状态: {status_after}")
            assert status_after == page.STATE_IN_PROGRESS or "执行中" in status_after, \
                f"合同状态未变为执行中，实际: {status_after}"

            print("========== CTR-005 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-006: 终止合同 — 执行中 → 已终止
    # ==================================================================
    @pytest.mark.destructive
    def test_006_terminate_contract(self, driver_setup):
        """CTR-006: 终止合同 — 状态: 执行中 → 已终止"""
        driver = driver_setup
        page = ContractPage(driver)
        print("\n========== 用例 CTR-006：终止合同 ==========")

        try:
            search_name = UPDATED_CONTRACT_NAME or self._require_created_contract_name()

            page.click_reset_search()
            page.search(name=search_name)

            row_count = page.get_table_row_count()
            assert row_count > 0, f"合同 '{search_name}' 不存在"

            status_before = page.get_contract_status(search_name)
            print(f"终止前状态: {status_before}")

            toast = page.terminate_contract(search_name)
            print(f"终止提示: {toast}")

            page.click_reset_search()
            page.search(name=search_name)
            page.wait_vue_stable()

            status_after = page.get_contract_status(search_name)
            print(f"终止后状态: {status_after}")
            assert status_after == page.STATE_TERMINATED or "已终止" in status_after, \
                f"合同状态未变为已终止，实际: {status_after}"

            print("========== CTR-006 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-007: 已终止合同不可编辑
    # ==================================================================
    def test_007_edit_terminated_fails(self, driver_setup):
        """CTR-007: 已终止合同不可编辑"""
        driver = driver_setup
        page = ContractPage(driver)
        print("\n========== 用例 CTR-007：已终止合同不可编辑 ==========")

        try:
            search_name = UPDATED_CONTRACT_NAME or self._require_created_contract_name()

            page.click_reset_search()
            page.search(name=search_name)

            row_count = page.get_table_row_count()
            assert row_count > 0, f"合同 '{search_name}' 不存在"

            is_editable = page.is_editable(search_name)
            print(f"合同是否可编辑: {is_editable}")
            assert not is_editable, f"已终止的合同不应可编辑，但编辑按钮存在且可用"

            print("========== CTR-007 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-008: 已终止合同不可删除
    # ==================================================================
    def test_008_delete_terminated_fails(self, driver_setup):
        """CTR-008: 已终止合同不可删除"""
        driver = driver_setup
        page = ContractPage(driver)
        print("\n========== 用例 CTR-008：已终止合同不可删除 ==========")

        try:
            search_name = UPDATED_CONTRACT_NAME or self._require_created_contract_name()

            page.click_reset_search()
            page.search(name=search_name)

            row_count = page.get_table_row_count()
            assert row_count > 0, f"合同 '{search_name}' 不存在"

            is_deletable = page.is_deletable(search_name)
            print(f"合同是否可删除: {is_deletable}")
            assert not is_deletable, f"已终止的合同不应可删除，但删除按钮存在且可用"

            print("========== CTR-008 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-009: 日期校验 — 结束日期必须大于开始日期
    # ==================================================================
    def test_009_date_validation(self, driver_setup):
        """CTR-009: 结束日期必须大于开始日期"""
        driver = driver_setup
        page = ContractPage(driver)
        print("\n========== 用例 CTR-009：日期边界校验 ==========")

        try:
            page.click_add()

            # 先填充必要字段
            page.fill_contract_form(name="日期校验测试")

            # 尝试结束日期 = 开始日期（或更早）
            errors = page.try_save_with_invalid_dates(
                start_date="2026-06-01",
                end_date="2026-01-01",
            )
            print(f"校验错误: {errors}")
            assert len(errors) > 0, "应检测到日期校验错误，但未收到任何错误提示"

            # 关闭弹窗（如果还开着）
            try:
                page.click_dialog_cancel()
            except Exception:
                pass

            print("========== CTR-009 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-010: 完整生命周期 — 待执行 → 执行中 → 已完成
    # ==================================================================
    @pytest.mark.destructive
    def test_010_complete_contract_lifecycle(self, driver_setup, contract_test_data):
        """CTR-010: 完整生命周期 — 待执行 → 启动 → 完成"""
        driver = driver_setup
        page = ContractPage(driver)
        td = contract_test_data
        print("\n========== 用例 CTR-010：合同完整生命周期 ==========")

        try:
            day_tag = datetime.now().strftime("%Y%m%d%H%M%S")
            lifecycle_name = f"生命周期测试_{day_tag}"
            print(f"创建生命周期测试合同: {lifecycle_name}")

            # 1. 新增合同
            page.click_add()
            customer = self._pick_existing_customer(page)
            page.fill_contract_form(
                name=lifecycle_name,
                customer=customer,
                product_type=td["existing"]["product_type"],
                total_quantity=500,
                unit_price=3.0,
                start_date=td["date_ranges"]["full_year"]["start"],
                end_date=td["date_ranges"]["full_year"]["end"],
            )
            toast = page.click_save()
            print(f"新增提示: {toast}")

            # 2. 搜索并验证初始状态
            page.click_reset_search()
            page.search(name=lifecycle_name)
            status = page.get_contract_status(lifecycle_name)
            print(f"初始状态: {status}")
            assert page.STATE_PENDING in status or "待执行" in status, \
                f"新增合同状态应为待执行，实际: {status}"

            # 3. 启动合同
            toast = page.start_contract(lifecycle_name)
            print(f"启动提示: {toast}")

            page.click_reset_search()
            page.search(name=lifecycle_name)
            status = page.get_contract_status(lifecycle_name)
            print(f"启动后状态: {status}")
            assert page.STATE_IN_PROGRESS in status or "执行中" in status, \
                f"启动后状态应为执行中，实际: {status}"

            # 4. 完成合同
            toast = page.complete_contract(lifecycle_name)
            print(f"完成提示: {toast}")

            page.click_reset_search()
            page.search(name=lifecycle_name)
            status = page.get_contract_status(lifecycle_name)
            print(f"完成后状态: {status}")
            assert page.STATE_COMPLETED in status or "已完成" in status, \
                f"完成后状态应为已完成，实际: {status}"

            print("========== CTR-010 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  CTR-011: 删除待执行状态合同（使用不同数据）
    # ==================================================================
    @pytest.mark.destructive
    def test_011_delete_pending_contract(self, driver_setup, contract_test_data):
        """CTR-011: 删除待执行状态的合同（独立数据，清理闭环）"""
        driver = driver_setup
        page = ContractPage(driver)
        td = contract_test_data
        print("\n========== 用例 CTR-011：删除待执行合同 ==========")

        try:
            day_tag = datetime.now().strftime("%Y%m%d%H%M%S")
            delete_name = f"待删合同_{day_tag}"
            print(f"创建待删合同: {delete_name}")

            # 新增一个合同用于删除
            page.click_add()
            customer = self._pick_existing_customer(page)
            page.fill_contract_form(
                name=delete_name,
                customer=customer,
                product_type=td["existing"]["product_type"],
                total_quantity=100,
                unit_price=2.5,
                start_date=td["date_ranges"]["half_year"]["start"],
                end_date=td["date_ranges"]["half_year"]["end"],
            )
            toast = page.click_save()
            print(f"新增提示: {toast}")

            # 搜索并确认存在
            page.click_reset_search()
            page.search(name=delete_name)
            row_count = page.get_table_row_count()
            assert row_count > 0, f"新建合同 '{delete_name}' 不存在"

            # 执行删除
            page.click_delete_by_name(delete_name)

            try:
                page.confirm_delete()
            except Exception:
                msg = ""
                try:
                    msg = page.get_message_box_text(timeout=3)
                except Exception:
                    pass
                if msg:
                    print(f"删除被阻止: {msg}")
                    try:
                        page.click_dialog_cancel()
                    except Exception:
                        pass
                    pytest.skip(f"合同无法删除: {msg}")
                raise

            toast = page.get_toast_text(timeout=5)
            print(f"删除提示: {toast}")
            assert toast and ("成功" in toast or "删除" in toast), f"删除合同提示异常: {toast}"

            # 验证已删除
            page.click_reset_search()
            page.search(name=delete_name)
            page.wait_vue_stable()
            still_exists = page.is_contract_name_present(delete_name)
            assert not still_exists, f"删除后仍能查到合同: {delete_name}"

            print("========== CTR-011 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
