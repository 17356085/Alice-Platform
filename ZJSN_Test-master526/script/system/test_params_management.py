"""参数设置模块测试脚本"""
import os
import sys
import pytest
import allure
from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.system_page.ParamsManagePage import ParamsManagePage


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

PARAM_03_NAME = None
PARAM_03_KEY = None
PARAM_03_TYPE = "字符串"
PARAM_03_MODULE = "安全"

PARAM_04_NAME = None
PARAM_04_KEY = None
PARAM_04_TYPE = "数值"
PARAM_04_MODULE = "安全"

PARAM_12_NAME = None
PARAM_12_KEY = None


@pytest.fixture(autouse=True)
def ensure_driver_ready(driver_setup):
    try:
        _ = driver_setup.current_url
    except InvalidSessionIdException:
        driver_setup.restart()
    except WebDriverException as e:
        if "invalid session id" in (str(e) or "").lower():
            driver_setup.restart()
        else:
            raise

    try:
        close_btns = driver_setup.find_elements(
            By.XPATH,
            '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//*[contains(@class,"el-dialog") or contains(@class,"el-drawer")]'
            '//button[.//*[normalize-space(.)="取消"] or contains(normalize-space(.),"取消")])[last()]'
            ' | (//div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//button[.//*[normalize-space(.)="取消"] or contains(normalize-space(.),"取消")])[last()]'
            ' | (//div[contains(@class,"el-drawer__wrapper") and not(contains(@style,"display: none"))]//button[.//*[normalize-space(.)="取消"] or contains(normalize-space(.),"取消")])[last()]',
        )
        for b in close_btns:
            try:
                if b.is_displayed():
                    driver_setup.execute_script("arguments[0].click();", b)
                    try:
                        WebDriverWait(driver_setup, 0.5).until(
                            EC.invisibility_of_element_located(
                                (By.CSS_SELECTOR, '.el-overlay:not([style*="display: none"])')
                            )
                        )
                    except Exception:
                        pass
            except Exception:
                continue
    except Exception:
        pass

    try:
        ParamsManagePage(driver_setup).navigate_to_params_settings()
    except Exception:
        driver_setup.restart()


class TestParamsManage:
    TEST_PARAM_NAME = "测试人员"
    TEST_PARAM_KEY = "sys.test.001"

    def _wait_message_contains(self, driver, text, timeout=8):
        # 扩大搜索范围，不限制父容器ID
        xpath = (
            f'//*[contains(@class,"el-message__content") and contains(normalize-space(.), "{text}")]'
            f' | //p[contains(@class,"el-message__content") and contains(normalize-space(.), "{text}")]'
            f' | //div[contains(@class,"el-message") and not(contains(@style,"display: none"))]//*[contains(normalize-space(.), "{text}")]'
        )
        print(f"[DEBUG] 等待消息提示，期望文本: '{text}'")
        print(f"[DEBUG] XPath定位器: {xpath}")
        
        def check_message(d):
            try:
                elements = d.find_elements(By.XPATH, xpath)
                print(f"[DEBUG] 找到 {len(elements)} 个匹配元素")
                for i, el in enumerate(elements):
                    try:
                        el_text = (el.text or "").strip()
                        el_html = el.get_attribute("outerHTML")[:200] if el else "None"
                        is_displayed = el.is_displayed() if el else False
                        print(f"[DEBUG] 元素{i}: text='{el_text}', displayed={is_displayed}, html={el_html}")
                        if is_displayed and (text in el_text or text in (el.get_attribute("textContent") or "")):
                            print(f"[DEBUG] 找到匹配的消息元素")
                            return el
                    except Exception as e:
                        print(f"[DEBUG] 检查元素{i}时出错: {e}")
            except Exception as e:
                print(f"[DEBUG] 查找元素时出错: {e}")
            return None
        
        return WebDriverWait(driver, timeout, poll_frequency=0.1).until(check_message)

    def _search_by_key(self, page, key):
        page.click_reset()
        page.input_param_key(key)
        page.click_search()

    def _ensure_deleted(self, page, key):
        self._search_by_key(page, key)
        if page.get_table_row_count() == 0:
            return
        page.delete_first_row()
        page.wait_for_toast_text(timeout=4)
        self._search_by_key(page, key)

    def _ensure_exists(self, page, name, key):
        self._search_by_key(page, key)
        if page.get_table_row_count() > 0:
            return

        page.click_add()
        page.input_dialog_field("参数名称", name)
        page.input_dialog_field_by_candidates(["参数键名", "参数键"], key)
        page.input_dialog_field("参数值", "001")
        page.select_dialog_option("参数类型", "数值")
        page.select_dialog_option("业务模块", "安全")
        page.select_dialog_radio("状态", "启用")
        page.input_dialog_field("描述", "测试")
        page.click_dialog_confirm()
        page.wait_dialog_closed(timeout=6)
        msg = page.wait_for_toast_text(timeout=6) or page.get_dialog_error_text()
        self._search_by_key(page, key)
        assert page.get_table_row_count() > 0, ea("创建测试数据成功", f"{msg or '无提示'}；{page.get_empty_text() or '暂无数据'}")

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("参数设置")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_params_01_page_display(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-01", "正常显示参数列表及相关字段")
        step("获取表头并校验")
        headers = page.get_table_headers()
        expected = {"参数名称", "参数键", "参数值", "参数类型", "业务模块", "描述", "更新时间", "操作"}
        assert expected.issubset(set(headers)), ea(f"参数列表表头包含：{sorted(expected)}", headers)
        step("校验列表有数据")
        assert page.get_table_row_count() > 0, ea("正常加载参数列表及相关字段", page.get_empty_text() or "暂无数据")

    def test_sy_params_02_pagination(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-02", "分页查询（分页）")
        step("点击重置")
        page.click_reset()
        step("记录第一页页码与第一行参数名称")
        page1 = page.get_current_page_number()
        first1 = page.get_first_row_param_name()
        step("点击下一页")
        if not page.click_next_page():
            pytest.skip("只有一页数据，跳过分页测试")
        step("记录第二页页码与第一行参数名称")
        page2 = page.get_current_page_number()
        first2 = page.get_first_row_param_name()
        assert page2 != page1, ea("页码切换到下一页", f"{page1}->{page2}")
        if first1 and first2:
            assert first1 != first2, ea("翻页后列表数据变化", f"page1={first1}, page2={first2}")

    def test_sy_params_03_add_required(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-03", "新增参数（必选）")
        global PARAM_03_NAME, PARAM_03_KEY, PARAM_03_TYPE, PARAM_03_MODULE
        tag = datetime.now().strftime("%Y%m%d%H%M%S%f")
        PARAM_03_NAME = f"test{tag}新增"
        PARAM_03_KEY = f"sys.test.{tag}.03"
        step("点击新增")
        page.click_add()
        step(f"输入参数名称：{PARAM_03_NAME}")
        page.input_dialog_field("参数名称", PARAM_03_NAME)
        step(f"输入参数键名：{PARAM_03_KEY}")
        page.input_dialog_field_by_candidates(["参数键名", "参数键"], PARAM_03_KEY)
        step("输入参数值：001")
        page.input_dialog_field("参数值", "001")
        step(f"选择参数类型：{PARAM_03_TYPE}")
        page.select_dialog_option("参数类型", PARAM_03_TYPE)
        step(f"选择业务模块：{PARAM_03_MODULE}")
        page.select_dialog_option("业务模块", PARAM_03_MODULE)
        step("点击确定")
        page.click_dialog_confirm()
        page.wait_dialog_closed(timeout=6)
        step("按参数键搜索验证新增成功")
        self._search_by_key(page, PARAM_03_KEY)
        assert page.get_table_row_count() > 0, ea("新增成功：列表中有相关的数据项", page.get_empty_text() or "暂无数据")
        try:
            page.click_dialog_cancel()
        except Exception:
            pass

    def test_sy_params_04_add_required_optional(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-04", "新增参数（必选+非必选）")
        global PARAM_04_NAME, PARAM_04_KEY, PARAM_04_TYPE, PARAM_04_MODULE
        tag = datetime.now().strftime("%Y%m%d%H%M%S%f")
        PARAM_04_NAME = f"test{tag}新增"
        PARAM_04_KEY = f"sys.test.{tag}.04"
        step("点击新增")
        page.click_add()
        step(f"输入参数名称：{PARAM_04_NAME}")
        page.input_dialog_field("参数名称", PARAM_04_NAME)
        step(f"输入参数键名：{PARAM_04_KEY}")
        page.input_dialog_field_by_candidates(["参数键名", "参数键"], PARAM_04_KEY)
        step("输入参数值：001")
        page.input_dialog_field("参数值", "001")
        step(f"选择参数类型：{PARAM_04_TYPE}")
        page.select_dialog_option("参数类型", PARAM_04_TYPE)
        step(f"选择业务模块：{PARAM_04_MODULE}")
        page.select_dialog_option("业务模块", PARAM_04_MODULE)
        step("输入描述：测试")
        page.input_dialog_field("描述", "测试")
        step("点击确定")
        page.click_dialog_confirm()
        page.wait_dialog_closed(timeout=6)
        step("按参数键搜索验证新增成功")
        self._search_by_key(page, PARAM_04_KEY)
        assert page.get_table_row_count() > 0, ea("新增成功：列表中有相关的数据项", page.get_empty_text() or "暂无数据")
        try:
            page.click_dialog_cancel()
        except Exception:
            pass

    def test_sy_params_05_search_by_param_name_like(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-05", "按参数名称搜索（模糊查询）")
        global PARAM_03_NAME
        if not PARAM_03_NAME:
            pytest.skip("未获取到 SY-PARAMS-03 新增的参数名称，请先执行新增用例")
        step("点击重置")
        page.click_reset()
        step(f"输入参数名称：{PARAM_03_NAME}")
        page.input_param_name(PARAM_03_NAME)
        step("点击搜索")
        page.click_search()
        names = page.get_column_data_by_header("参数名称")
        assert names, ea("显示列表中的符合条件的数据项", page.get_empty_text() or "暂无数据")
        assert any(PARAM_03_NAME in n for n in names), ea(f"筛选结果包含参数名称：{PARAM_03_NAME}", names)

    def test_sy_params_06_search_by_name_and_key(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-06", "按参数名称和键名搜索")
        global PARAM_03_NAME, PARAM_03_KEY
        if not PARAM_03_NAME or not PARAM_03_KEY:
            pytest.skip("未获取到 SY-PARAMS-03 新增的参数信息，请先执行新增用例")
        step("点击重置")
        page.click_reset()
        step(f"输入参数名称：{PARAM_03_NAME}")
        page.input_param_name(PARAM_03_NAME)
        step(f"输入参数键名：{PARAM_03_KEY}")
        page.input_param_key(PARAM_03_KEY)
        step("点击搜索")
        page.click_search()
        names = page.get_column_data_by_header("参数名称")
        keys = page.get_column_data_by_headers(["参数键名", "参数键"])
        assert names and keys, ea("显示列表中的符合条件的数据项", page.get_empty_text() or "暂无数据")
        assert all(PARAM_03_NAME in n for n in names), ea(f"筛选结果参数名称包含{PARAM_03_NAME}", names)
        assert all(PARAM_03_KEY in k for k in keys), ea(f"筛选结果参数键名包含{PARAM_03_KEY}", keys)

    def test_sy_params_07_search_by_type(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-07", "按参数类型搜索")
        global PARAM_03_NAME, PARAM_03_KEY, PARAM_03_TYPE, PARAM_03_MODULE
        if not PARAM_03_NAME or not PARAM_03_KEY:
            pytest.skip("未获取到 SY-PARAMS-03 新增的参数信息，请先执行新增用例")
        step("点击重置")
        page.click_reset()
        step(f"输入参数名称：{PARAM_03_NAME}")
        page.input_param_name(PARAM_03_NAME)
        step(f"输入参数键名：{PARAM_03_KEY}")
        page.input_param_key(PARAM_03_KEY)
        step(f"输入参数类型：{PARAM_03_TYPE}")
        page.select_param_type(PARAM_03_TYPE)
        step(f"选择业务模块：{PARAM_03_MODULE}")
        page.select_business_module(PARAM_03_MODULE)
        step("点击搜索")
        page.click_search()
        types = page.get_column_data_by_header("参数类型")
        assert types, ea("显示列表中的符合条件的数据项", page.get_empty_text() or "暂无数据")
        assert all(PARAM_03_TYPE in t for t in types), ea(f"筛选结果参数类型为{PARAM_03_TYPE}", types)

    def test_sy_params_08_search_by_module(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-08", "按业务模块搜索")
        global PARAM_03_NAME, PARAM_03_KEY, PARAM_03_TYPE, PARAM_03_MODULE
        if not PARAM_03_NAME or not PARAM_03_KEY:
            pytest.skip("未获取到 SY-PARAMS-03 新增的参数信息，请先执行新增用例")
        step("点击重置")
        page.click_reset()
        step(f"输入参数名称：{PARAM_03_NAME}")
        page.input_param_name(PARAM_03_NAME)
        step(f"输入参数键名：{PARAM_03_KEY}")
        page.input_param_key(PARAM_03_KEY)
        step(f"输入参数类型：{PARAM_03_TYPE}")
        page.select_param_type(PARAM_03_TYPE)
        step(f"选择业务模块：{PARAM_03_MODULE}")
        page.select_business_module(PARAM_03_MODULE)
        step("点击搜索")
        page.click_search()
        modules = page.get_column_data_by_header("业务模块")
        assert modules, ea("显示列表中的符合条件的数据项", page.get_empty_text() or "暂无数据")
        assert all(PARAM_03_MODULE in m for m in modules), ea(f"筛选结果业务模块为{PARAM_03_MODULE}", modules)

    def test_sy_params_09_reset_button(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-09", "重置按钮功能正常")
        global PARAM_03_NAME, PARAM_03_KEY, PARAM_03_TYPE, PARAM_03_MODULE
        if not PARAM_03_NAME or not PARAM_03_KEY:
            pytest.skip("未获取到 SY-PARAMS-03 新增的参数信息，请先执行新增用例")
        step("输入筛选条件")
        page.input_param_name(PARAM_03_NAME)
        page.input_param_key(PARAM_03_KEY)
        page.select_param_type(PARAM_03_TYPE)
        page.select_business_module(PARAM_03_MODULE)
        step("点击重置")
        page.click_reset()
        step("点击搜索验证列表正常加载")
        page.click_search()
        assert page.get_table_row_count() > 0, ea("所有筛选条件清空，正常加载参数列表", page.get_empty_text() or "暂无数据")

    def test_sy_params_10_export(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-10", "导出表格数据")
        step("点击导出")
        page.click_export()
        step("点击确定")
        page.confirm_message_box_if_present(timeout=4)
        msg = page.wait_for_toast_text(timeout=8)
        # 宽松断言：只要有提示消息且不是系统错误，导出操作即已触发
        print(f"  [DEBUG] 导出Toast: {msg!r}")
        assert msg and "系统错误" not in msg, ea("导出操作已触发", msg or "未获取到提示")

    def test_sy_params_11_edit_item(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-11", "编辑数据项")
        global PARAM_04_KEY
        if not PARAM_04_KEY:
            pytest.skip("未获取到 SY-PARAMS-04 新增的参数键名，请先执行新增用例")
        step("按参数键搜索定位数据项")
        self._search_by_key(page, PARAM_04_KEY)
        step("点击编辑")
        page.click_edit_first_row()
        step("修改参数值为007")
        page.input_dialog_field("参数值", "007")
        page.input_dialog_field("描述", "测试编辑")
        step("点击确定")
        page.click_dialog_confirm()
        el = self._wait_message_contains(driver_setup, "修改成功", timeout=8)
        page.wait_dialog_closed(timeout=6)
        assert "修改成功" in ((el.text or "").strip()), ea("弹出修改成功", (el.text or "").strip() or "未获取到提示")
        step("按参数键搜索验证参数值更新")
        self._search_by_key(page, PARAM_04_KEY)
        values = page.get_column_data_by_header("参数值")
        assert values and any("007" in v for v in values), ea("编辑成功：列表中数据项信息有相应变化", values)

    def test_sy_params_12_add_after_delete(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-12", "删除后新增")
        global PARAM_12_NAME, PARAM_12_KEY
        tag = datetime.now().strftime("%Y%m%d%H%M%S%f")
        PARAM_12_NAME = f"test{tag}新增"
        PARAM_12_KEY = f"sys.test.{tag}.12"
        step("点击新增并填写表单")
        page.click_add()
        page.input_dialog_field("参数名称", PARAM_12_NAME)
        page.input_dialog_field_by_candidates(["参数键名", "参数键"], PARAM_12_KEY)
        page.input_dialog_field("参数值", "001")
        page.select_dialog_option("参数类型", "数值")
        page.select_dialog_option("业务模块", "安全")
        page.select_dialog_radio("状态", "启用")
        page.input_dialog_field("描述", "测试")
        step("点击确定")
        page.click_dialog_confirm()
        page.wait_dialog_closed(timeout=6)
        msg = page.wait_for_toast_text(timeout=6) or page.get_dialog_error_text()
        assert msg != "", ea("新增后有提示信息", msg or "未获取到提示")
        step("按参数键搜索验证新增成功")
        self._search_by_key(page, PARAM_12_KEY)
        assert page.get_table_row_count() > 0, ea("新增成功：列表中有相关的数据项", page.get_empty_text() or "暂无数据")

    def test_sy_params_13_delete_table_data(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-13", "删除表格数据")
        global PARAM_03_KEY, PARAM_04_KEY, PARAM_12_KEY
        targets = [PARAM_03_KEY, PARAM_04_KEY, PARAM_12_KEY]
        
        # 收集有效的参数键
        valid_targets = []
        for key in targets:
            if key:
                valid_targets.append(key)
        
        if not valid_targets:
            pytest.skip("没有找到前面测试用例新增的数据，请先执行新增用例（test_sy_params_03、test_sy_params_04、test_sy_params_12）")
        
        for key in valid_targets:
            step(f"按参数键搜索：{key}")
            self._search_by_key(page, key)
            
            # 如果搜索后没有数据，跳过该参数
            if page.get_table_row_count() == 0:
                continue
            
            max_rounds = 10
            rounds = 0
            while page.get_table_row_count() > 0 and rounds < max_rounds:
                rounds += 1
                step(f"删除第{rounds}次命中的数据")
                
                # 删除操作，增加重试
                delete_result = page.delete_first_row()
                if not delete_result:
                    page.wait_vue_stable()
                    delete_result = page.delete_first_row()
                
                assert delete_result, ea("点击删除成功", "未能触发删除")
                
                # 等待删除成功提示
                msg = page.wait_for_toast_text(timeout=8)
                assert msg != "", ea("删除后有提示信息", msg or "未获取到提示")
                
                self._search_by_key(page, key)
            
            assert page.get_table_row_count() == 0, ea("删除成功：列表无相关数据项", f"key={key}, row_count={page.get_table_row_count()}")

    def test_sy_params_14_refresh_cache(self, driver_setup):
        page = ParamsManagePage(driver_setup)
        case("SY-PARAMS-14", "刷新缓存")
        step("点击刷新缓存")
        page.click_refresh_cache()
        page.confirm_message_box_if_present(timeout=4)
        el = self._wait_message_contains(driver_setup, "刷新成功", timeout=8)
        assert "刷新成功" in ((el.text or "").strip()), ea("弹出刷新成功", (el.text or "").strip() or "未获取到提示")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
