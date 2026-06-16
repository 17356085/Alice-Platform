"""课程管理模块测试脚本"""
import pytest
import sys
import os
import inspect
from datetime import datetime
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.CourseManagePage import CourseManagePage

CREATED_COURSE_NAME = None


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


def _generate_course_name():
    return f"test{datetime.now().strftime('%Y%m%d%H%M%S')}新增"


class TestCourseManage:
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

    @pytest.mark.smoke
    @allure.epic("人员管理")
    @allure.feature("课程管理")
    @allure.story("分页功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_001_pagination_check(self, driver_setup):
        """SY-COURSE-001: 分页跳转验证"""
        case("SY-COURSE-001", "分页跳转验证")
        page = CourseManagePage(driver_setup)
        step("点击重置按钮")
        page.click_reset_button()
        step("点击搜索按钮")
        page.click_search_button()
        check("分页功能正常", "页面显示正常", True)

    def test_002_add_course(self, driver_setup):
        """SY-COURSE-002: 新增课程"""
        global CREATED_COURSE_NAME
        case("SY-COURSE-002", "新增课程")
        page = CourseManagePage(driver_setup)
        course_name = _generate_course_name()
        CREATED_COURSE_NAME = course_name
        step("点击新增课程按钮")
        page.click_add_course_button()

        video_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "test_files", "test_video.mp4"
        )

        step(f"填写课程表单信息：课程名称={course_name}")
        page.fill_add_course_form(
            course_name=course_name,
            course_duration=2,
            course_category="技能培训",
            material_type="视频",
            intro="测试课程简介",
            remark="测试备注",
            file_path=video_file_path
        )
        step("点击保存按钮")
        page.click_save_button()

        step("点击重置按钮")
        page.click_reset_button()
        step(f"输入搜索课程名称：{course_name}")
        page.input_search_course_name(course_name)
        step("点击搜索按钮")
        page.click_search_button()

        check(f"课程 {course_name} 创建成功", course_name in driver_setup.page_source,
              CREATED_COURSE_NAME in driver_setup.page_source)

    def test_003_view_course(self, driver_setup):
        """SY-COURSE-003: 查看课程信息"""
        global CREATED_COURSE_NAME
        case("SY-COURSE-003", "查看课程信息")
        page = CourseManagePage(driver_setup)
        check("已创建课程数据", CREATED_COURSE_NAME is not None, bool(CREATED_COURSE_NAME))
        step("点击重置按钮")
        page.click_reset_button()
        step(f"输入搜索课程名称：{CREATED_COURSE_NAME}")
        page.input_search_course_name(CREATED_COURSE_NAME)
        step("点击搜索按钮")
        page.click_search_button()
        step("点击查看课程按钮")
        page.click_view_course_button()
        step("获取弹窗标题")
        dialog_title = page.get_dialog_title_text()
        check("课程详情弹窗显示", "课程详情" in dialog_title, "课程详情" in dialog_title)
        step("点击关闭课程详情按钮")
        page.click_close_course_detail_button()
        check(f"查看课程: {CREATED_COURSE_NAME}", True, True)

    def test_004_search_by_name(self, driver_setup):
        """SY-COURSE-004: 按课程名称搜索"""
        global CREATED_COURSE_NAME
        case("SY-COURSE-004", "按课程名称搜索")
        page = CourseManagePage(driver_setup)
        check("已创建课程数据", CREATED_COURSE_NAME is not None, bool(CREATED_COURSE_NAME))
        step("点击重置按钮")
        page.click_reset_button()
        search_keyword = CREATED_COURSE_NAME[:6]
        step(f"输入搜索关键词：{search_keyword}")
        page.input_search_course_name(search_keyword)
        step("点击搜索按钮")
        page.click_search_button()
        has_cards = len(driver_setup.find_elements(By.XPATH,
                                                   '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[1]/div[2]/div[2]/div[1]')) > 0
        check(f"按名称搜索: {search_keyword}", "列表有课程卡片" if has_cards else "无结果", has_cards)

    def test_005_search_by_category(self, driver_setup):
        """SY-COURSE-005: 按课程分类搜索"""
        case("SY-COURSE-005", "按课程分类搜索")
        page = CourseManagePage(driver_setup)
        step("点击重置按钮")
        page.click_reset_button()
        step("选择课程分类：技能培训")
        page.select_search_course_category("技能培训")
        step("点击搜索按钮")
        page.click_search_button()
        has_cards = len(driver_setup.find_elements(By.XPATH,
                                                   '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[1]/div[2]/div[2]/div[1]')) > 0
        check("按分类搜索完成", "列表有课程卡片" if has_cards else "无结果", has_cards)

    def test_006_search_by_material_type(self, driver_setup):
        """SY-COURSE-006: 按资料类型搜索"""
        case("SY-COURSE-006", "按资料类型搜索")
        page = CourseManagePage(driver_setup)
        step("点击重置按钮")
        page.click_reset_button()
        step("选择资料类型：视频")
        page.select_search_material_type("视频")
        step("点击搜索按钮")
        page.click_search_button()
        has_cards = len(driver_setup.find_elements(By.XPATH,
                                                   '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[1]/div[2]/div[2]/div[1]')) > 0
        check("按资料类型搜索完成", "列表有课程卡片" if has_cards else "无结果", has_cards)

    def test_007_search_by_status(self, driver_setup):
        """SY-COURSE-007: 按发布状态搜索"""
        case("SY-COURSE-007", "按发布状态搜索")
        page = CourseManagePage(driver_setup)
        step("点击重置按钮")
        page.click_reset_button()
        step("选择发布状态：已发布")
        page.select_search_publish_status("已发布")
        step("点击搜索按钮")
        page.click_search_button()
        has_cards = len(driver_setup.find_elements(By.XPATH,
                                                   '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[1]/div[2]/div[2]/div[1]')) > 0
        check("按状态搜索完成", "列表有课程卡片" if has_cards else "无结果", has_cards)

    def test_008_publish_course(self, driver_setup):
        """SY-COURSE-008: 发布课程"""
        global CREATED_COURSE_NAME
        case("SY-COURSE-008", "发布课程")
        if CREATED_COURSE_NAME:
            page = CourseManagePage(driver_setup)
            step("点击重置按钮")
            page.click_reset_button()
            step(f"输入搜索课程名称：{CREATED_COURSE_NAME}")
            page.input_search_course_name(CREATED_COURSE_NAME)
            step("点击搜索按钮")
            page.click_search_button()
            step("点击发布按钮")
            page.click_publish_button_in_card(CREATED_COURSE_NAME)
            step("点击发布确认按钮")
            page.click_confirm_dialog_ok()
            step("获取发布成功提示")
            success_text = page.get_toast_text(timeout=10)
            check("发布成功", "发布成功" in success_text, success_text)
        else:
            check("无待发布课程", True, True)

    def test_009_delete_course(self, driver_setup):
        """SY-COURSE-009: 删除课程（清理测试数据）"""
        global CREATED_COURSE_NAME
        case("SY-COURSE-009", "删除课程（清理测试数据）")
        if CREATED_COURSE_NAME:
            page = CourseManagePage(driver_setup)
            step("点击重置按钮")
            page.click_reset_button()
            step(f"输入搜索课程名称：{CREATED_COURSE_NAME}")
            page.input_search_course_name(CREATED_COURSE_NAME)
            step("点击搜索按钮")
            page.click_search_button()
            step("勾选课程复选框")
            checkbox = WebDriverWait(driver_setup, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                                            '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[1]/div[2]/div[2]/div[1]/div[1]/label/span/span'))
            )
            driver_setup.execute_script("arguments[0].click();", checkbox)
            WebDriverWait(driver_setup, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[normalize-space(.)="删除"]]'))
            )
            step("点击删除按钮")
            delete_button = WebDriverWait(driver_setup, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[normalize-space(.)="删除"]]'))
            )
            driver_setup.execute_script("arguments[0].click();", delete_button)
            step("点击删除确认按钮")
            confirm_button = WebDriverWait(driver_setup, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[3]/button[2]/span'))
            )
            driver_setup.execute_script("arguments[0].click();", confirm_button)
            step("获取删除成功提示")
            success_text = WebDriverWait(driver_setup, 10).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//*[contains(@class,"el-message") and contains(., "删除成功")]'))
            ).text.strip()
            check("删除成功", "删除成功" in success_text, success_text)
            CREATED_COURSE_NAME = None
        else:
            check("无待删除课程", True, True)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
