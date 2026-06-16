"""定时任务模块测试脚本"""
import os
import sys
import time
import pytest
import allure
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.system_page.TimedTaskPage import TimedTaskPage


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


class TestTimedTask:
    @pytest.fixture(autouse=True)
    def _reset_after_each(self, driver_setup):
        yield
        try:
            TimedTaskPage(driver_setup).click_reset()
        except Exception:
            pass

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("定时任务")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_tim_01_page_display(self, driver_setup):
        page = TimedTaskPage(driver_setup)
        case("SY-TIM-01", "正常显示定时任务列表及相关字段")
        step("获取表头并校验")
        headers = page.get_table_headers()
        expected = {"任务名称", "任务类型", "Cron表达式", "Bean名称", "方法名", "状态", "下次执行时间", "操作"}
        check("正常加载定时任务列表及相关字段", headers, expected.issubset(set(headers)))
        step("校验列表有数据")
        row_count = page.get_table_row_count()
        if row_count == 0:
            check("允许暂无数据", page.get_empty_text() or "未获取到空态", "暂无数据" in (page.get_empty_text() or ""))
            return
        check("正常加载定时任务列表", row_count, row_count > 0)

    def test_sy_tim_02_add_timed_task(self, driver_setup):
        page = TimedTaskPage(driver_setup)
        case("SY-TIM-02", "添加定时任务")
        task_name = f"test{datetime.now().strftime('%Y%m%d%H%M%S')}新增"
        step("点击重置")
        page.click_reset()
        step("点击新增")
        page.click_toolbar_add()
        step("填写任务名称")
        page.dialog_input_by_label("任务名称", task_name)
        step("选择任务类型")
        page.dialog_select_by_label("任务类型", "数据备份")
        step("填写Bean名称")
        page.dialog_input_by_label("Bean名称", "testData")
        step("填写Cron表达式")
        page.dialog_input_by_label("cron执行表达式", "0 0 0 * * ?", skip_blur=True)
        step("关闭可视化生成弹窗")
        try:
            page.close_cron_visual_drawer()
        except Exception as e:
            print(f"关闭可视化弹窗失败(可能未弹出): {e}")
        step("设置执行策略")
        page.dialog_select_by_label("执行策略", "执行一次")
        step("设置是否并发")
        page.dialog_select_by_label("是否并发", "禁止")
        
        # 检查是否有表单验证错误
        errors = page.get_dialog_error_texts()
        if errors:
            print(f"表单验证错误: {errors}")
            page.dialog_cancel()  # 关闭对话框
            raise AssertionError(f"表单验证失败: {errors}")
        
        step("点击确定/保存")
        msg = page.dialog_confirm()
        print(f"dialog_confirm返回的消息: {msg}")
        if not msg:
            msg = page.wait_for_toast_text(timeout=10)
            print(f"wait_for_toast_text获取的消息: {msg}")

        if not msg:
            step("未获取到提示，回查任务是否已新增")
            page.click_reset()
            page.input_task_name(task_name)
            page.click_search()
            names = page.get_column_data_by_header("任务名称")
            print(f"回查任务名称结果: {names}")
            msg = "新增成功" if any(task_name in n for n in names) else ""

        print(f"最终获取到的提示消息: {msg}")
        check("新增成功提示", msg, "新增成功" in (msg or "") or "成功" in (msg or ""))

    def test_sy_tim_03_edit_timed_task(self, driver_setup):
        page = TimedTaskPage(driver_setup)
        case("SY-TIM-03", "修改定时任务")
        step("点击重置")
        page.click_reset()
        step("搜索任务名称：test")
        page.input_task_name("test")
        page.click_search()
        row_count = page.get_table_row_count()
        check("列表应有数据（不允许暂无数据）", row_count if row_count else (page.get_empty_text() or "暂无数据"), row_count > 0)
        step("点击第一行编辑")
        try:
            page.click_row_action("编辑", row_index=1)
        except Exception:
            page.click_row_action("修改", row_index=1)
        step("修改备注")
        try:
            page.dialog_input_by_label("备注", f"auto_edit_{int(time.time())}")
        except Exception:
            pass
        step("点击确定/保存")
        page.dialog_confirm()
        if page.is_dialog_open():
            errs = page.get_dialog_error_texts()
            page.dialog_cancel()
            check("修改弹窗应提交成功并关闭", errs or "弹窗仍打开且未获取到错误提示", False)
        msg = page.wait_for_toast_text(timeout=6)
        check(
            "修改成功或弹窗关闭",
            msg or "未获取到提示",
            ("成功" in (msg or "")) or (not page.is_dialog_open()),
        )

    def test_sy_tim_04_search_by_task_name_like(self, driver_setup):
        page = TimedTaskPage(driver_setup)
        case("SY-TIM-04", "按任务名称搜索（模糊查询）")
        step("点击重置")
        page.click_reset()
        keyword = "tes"
        step(f"输入任务名称：{keyword}")
        page.input_task_name(keyword)
        step("点击搜索")
        page.click_search()
        names = page.get_column_data_by_header("任务名称")
        empty = page.get_empty_text() or ""
        check("显示列表中的符合条件的数据项或暂无数据", names if names else (empty or "未获取到空态"), bool(names) or ("暂无数据" in empty))
        if not names:
            return
        check(f"任务名称包含{keyword}", names, all(keyword.lower() in n.lower() for n in names))

    def test_sy_tim_05_search_by_task_type(self, driver_setup):
        page = TimedTaskPage(driver_setup)
        case("SY-TIM-05", "按任务类型搜索")
        step("点击重置")
        page.click_reset()
        target = "数据备份"
        step(f"选择任务类型：{target}")
        page.select_task_type(target)
        step("点击搜索")
        page.click_search()
        types = page.get_column_data_by_header("任务类型")
        empty = page.get_empty_text() or ""
        check("显示列表中的符合条件的数据项或暂无数据", types if types else (empty or "未获取到空态"), bool(types) or ("暂无数据" in empty))
        if not types:
            return
        check(f"任务类型为{target}", types, all(target in t for t in types))

    def test_sy_tim_06_search_by_status(self, driver_setup):
        page = TimedTaskPage(driver_setup)
        case("SY-TIM-06", "按状态搜索")
        step("点击重置")
        page.click_reset()
        step("选择状态：已暂停")
        page.select_status("已暂停")
        step("点击搜索")
        page.click_search()
        statuses = page.get_column_data_by_header("状态")
        empty = page.get_empty_text() or ""
        check(
            "显示列表中的符合条件的数据项或暂无数据",
            statuses if statuses else (empty or "未获取到空态"),
            bool(statuses) or ("暂无数据" in empty),
        )
        if not statuses:
            return
        check("筛选结果状态为已暂停", statuses, all(("暂停" in s) or ("停止" in s) for s in statuses))

    def test_sy_tim_07_reset_button(self, driver_setup):
        page = TimedTaskPage(driver_setup)
        case("SY-TIM-07", "重置按钮功能正常")
        step("输入筛选条件")
        page.input_task_name("tes")
        try:
            page.select_task_type("数据备份")
        except Exception:
            pass
        try:
            page.select_status("已暂停")
        except Exception:
            pass
        step("点击重置")
        page.click_reset()
        step("点击搜索验证列表正常加载")
        page.click_search()
        row_count = page.get_table_row_count()
        check("所有筛选条件清空，正常加载定时任务", row_count if row_count else (page.get_empty_text() or "暂无数据"), row_count > 0)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
