"""通知管理模块测试脚本"""
import os
import sys
import pytest
import allure
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.system_page.NoticeManagePage import NoticeManagePage

NOTICE_CREATE_TITLE = None
NOTICE_EDIT_TITLE = None
NOTICE_TIME_TAG = None


def make_notice_title(action):
    return f"test{datetime.now().strftime('%Y%m%d%H%M%S')}{action}"


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


def check(expected, actual, condition):
    print(f"断言条件：{expected}")
    print(f"预期结果：{expected}")
    print(f"实际结果：{actual}")
    assert condition, ea(expected, actual)


class TestNoticeManage:
    @pytest.fixture(autouse=True)
    def _reset_after_each(self, driver_setup):
        yield
        try:
            NoticeManagePage(driver_setup).click_reset()
        except Exception:
            pass

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("通知管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_notice_01_page_display(self, driver_setup):
        page = NoticeManagePage(driver_setup)
        case("SY-NOTICE-01", "正常显示通知列表以及相关字段")
        step("获取通知列表表头并校验")
        headers = page.get_table_headers()
        expected = {"通知编号", "通知标题", "通知类型", "状态", "创建人", "创建时间", "操作"}
        check("正常加载通知列表及相关字段", headers, expected.issubset(set(headers)))
        step("校验通知列表有数据")
        row_count = page.get_table_row_count()
        if row_count == 0:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
            return
        check("正常加载通知列表", row_count, row_count > 0)

    def test_sy_notice_02_pagination(self, driver_setup):
        page = NoticeManagePage(driver_setup)
        case("SY-NOTICE-02", "分页跳转（分页）")
        step("检查当前页码")
        current_page = page.get_current_page_number()
        check("当前页码存在", current_page, bool(current_page))
        step("检查是否存在下一页")
        moved = page.click_next_page()
        if not moved:
            pytest.skip("当前数据未超过一页，暂无下一页，跳过分页测试")
        step("校验页码变化")
        next_page = page.get_current_page_number()
        check("翻页后页码应变化", next_page, next_page and next_page != current_page)

    def test_sy_notice_03_add_notice(self, driver_setup):
        page = NoticeManagePage(driver_setup)
        case("SY-NOTICE-03", "新增通知")
        global NOTICE_CREATE_TITLE, NOTICE_TIME_TAG
        NOTICE_TIME_TAG = datetime.now().strftime("%Y%m%d%H%M%S")
        NOTICE_CREATE_TITLE = f"test{NOTICE_TIME_TAG}新增"
        step("点击新增")
        page.click_add()
        step("填写通知标题")
        page.dialog_input_title(NOTICE_CREATE_TITLE)
        step("选择通知类型：通知")
        page.dialog_select_type("通知")
        step("选择状态：正常")
        page.dialog_select_status("正常")
        step("填写通知内容")
        page.dialog_input_content("测试考试取消")
        step("点击确定")
        page.dialog_confirm()
        msg = page.wait_for_toast_text(timeout=6)
        check("新增成功提示", msg, msg == "新增成功" or "新增成功" in (msg or ""))
        step("回查新增标题是否出现在列表中")
        page.click_reset()
        page.input_notice_title(NOTICE_CREATE_TITLE)
        page.click_search()
        titles = page.get_column_data_by_header("通知标题")
        check("新增后列表应存在该通知标题", titles, any(NOTICE_CREATE_TITLE in t for t in titles))

    def test_sy_notice_04_edit_notice(self, driver_setup):
        page = NoticeManagePage(driver_setup)
        case("SY-NOTICE-04", "修改通知")
        global NOTICE_EDIT_TITLE
        if not NOTICE_CREATE_TITLE:
            pytest.skip("未先执行新增通知用例，无法继续修改")
        step("搜索新增后的通知标题")
        page.click_reset()
        page.input_notice_title(NOTICE_CREATE_TITLE)
        page.click_search()
        row_count = page.get_table_row_count()
        check("列表应有刚新增的数据", row_count, row_count > 0)
        step("点击第一行编辑")
        try:
            page.click_row_action("修改", row_index=1)
        except Exception:
            page.click_row_action("编辑", row_index=1)
        NOTICE_EDIT_TITLE = f"test{NOTICE_TIME_TAG or datetime.now().strftime('%Y%m%d%H%M%S')}修改"
        step("修改通知标题")
        page.dialog_input_title(NOTICE_EDIT_TITLE)
        step("点击确定")
        page.dialog_confirm()
        msg = page.wait_for_toast_text(timeout=6)
        check("修改成功提示", msg, msg == "修改成功" or "修改成功" in (msg or ""))
        step("回查修改后的标题是否生效")
        page.click_reset()
        page.input_notice_title(NOTICE_EDIT_TITLE)
        page.click_search()
        titles = page.get_column_data_by_header("通知标题")
        check("修改后列表应存在新标题", titles, any(NOTICE_EDIT_TITLE in t for t in titles))

    def test_sy_notice_05_search_by_title(self, driver_setup):
        page = NoticeManagePage(driver_setup)
        case("SY-NOTICE-05", "按通知标题搜索（模糊查询）")
        step("点击重置")
        page.click_reset()
        keyword = "test"
        step(f"输入通知标题：{keyword}")
        page.input_notice_title(keyword)
        step("点击搜索")
        page.click_search()
        titles = page.get_column_data_by_header("通知标题")
        empty = page.get_empty_text() or ""
        check("显示列表中的符合条件的数据项或暂无数据", titles if titles else (empty or "未获取到空态"), bool(titles) or ("暂无数据" in empty))
        if not titles:
            return
        check(f"通知标题包含{keyword}", titles, all(keyword.lower() in t.lower() for t in titles))

    def test_sy_notice_06_search_by_type(self, driver_setup):
        page = NoticeManagePage(driver_setup)
        case("SY-NOTICE-06", "按通知类型搜索")
        step("点击重置")
        page.click_reset()
        target = "通知"
        step(f"选择通知类型：{target}")
        page.select_notice_type(target)
        step("点击搜索")
        page.click_search()
        types = page.get_column_data_by_header("通知类型")
        empty = page.get_empty_text() or ""
        check("显示列表中的符合条件的数据项或暂无数据", types if types else (empty or "未获取到空态"), bool(types) or ("暂无数据" in empty))
        if not types:
            return
        check(f"通知类型为{target}", types, all(target in t for t in types))

    def test_sy_notice_07_reset_button(self, driver_setup):
        page = NoticeManagePage(driver_setup)
        case("SY-NOTICE-07", "重置按钮功能正常")
        step("输入筛选条件")
        page.input_notice_title("test")
        try:
            page.select_notice_type("通知")
        except Exception:
            pass
        step("点击重置")
        page.click_reset()
        step("点击搜索验证列表正常加载")
        page.click_search()
        row_count = page.get_table_row_count()
        check("所有筛选条件清空，正常加载通知列表", row_count if row_count else (page.get_empty_text() or "暂无数据"), row_count > 0)

    def test_sy_notice_08_delete_notice(self, driver_setup):
        page = NoticeManagePage(driver_setup)
        case("SY-NOTICE-08", "删除通知")
        target_title = NOTICE_EDIT_TITLE or NOTICE_CREATE_TITLE
        if not target_title:
            pytest.skip("未先执行新增/修改通知用例，无法继续删除")
        step("搜索待删除的通知标题")
        page.click_reset()
        page.input_notice_title(target_title)
        page.click_search()
        row_count = page.get_table_row_count()
        if row_count == 0:
            check("列表应有数据", page.get_empty_text() or "暂无数据", False)
            return
        step("点击第一行删除")
        try:
            page.click_row_action("删除", row_index=1)
        except Exception:
            page.click_row_action("操作", row_index=1)
        step("确认删除")
        try:
            page.dialog_delete_confirm()
        except Exception:
            try:
                confirm_btn = page.driver.find_element(By.XPATH, '/html/body/div[7]/div/div/div[3]/button[2]/span')
                confirm_btn.click()
                WebDriverWait(page.driver, 3).until(
                    EC.invisibility_of_element_located((By.XPATH, '/html/body/div[7]'))
                )
            except Exception:
                pass
        msg = page.wait_for_toast_text(timeout=6)
        check("删除成功提示", msg, msg == "删除成功" or "删除成功" in (msg or ""))
        step("回查删除后不应再存在该标题")
        page.click_reset()
        page.input_notice_title(target_title)
        page.click_search()
        titles = page.get_column_data_by_header("通知标题")
        check("删除后列表不应存在该通知标题", titles if titles else page.get_empty_text(), not any(target_title in t for t in titles))


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
