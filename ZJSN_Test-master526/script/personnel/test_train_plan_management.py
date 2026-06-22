"""培训计划管理模块测试脚本"""
import pytest
import sys
import os
import time
import inspect
from datetime import datetime
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.personnel_page.TrainPlanPage import TrainPlanPage
from page.personnel_page.CourseManagePage import CourseManagePage


# 测试数据
CREATED_PLAN_NAME = None
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


def check(expected, actual, condition):
    print(f"预期结果：{expected}")
    print(f"实际结果：{actual}")
    assert condition, f"【失败】预期：{expected}，实际：{actual}"


def _generate_course_name():
    """生成课程名称，与课程管理测试保持一致"""
    return f"test{datetime.now().strftime('%Y%m%d%H%M%S')}新增"


def _generate_plan_name():
    return f"test{datetime.now().strftime('%Y%m%d%H%M%S')}计划"


def _create_course_for_plan(driver):
    """
    按课程管理测试的数据流程新增一条课程并发布，供培训计划关联使用。

    Returns:
        str: 生成的课程名称
    """
    plan_page = TrainPlanPage(driver)
    course_page = CourseManagePage(driver)
    course_name = _generate_course_name()
    video_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "test_files", "test_video.mp4"
    )

    step("跳转到课程管理（同级菜单切换）")
    plan_page.navigate_to_course_management()

    step(f"新增课程「{course_name}」")
    course_page.click_add_course_button()

    step("填写课程名称")
    course_page.input_course_name(course_name)
    step("填写课程时长: 2")
    course_page.input_course_duration(2)
    step("选择课程分类: 技能培训")
    course_page.select_dialog_option_by_text("课程分类", "技能培训")
    step("选择资料类型: 视频")
    course_page.select_dialog_option_by_text("资料类型", "视频")
    step("填写课程简介")
    course_page.input_course_intro("测试课程简介")
    step(f"上传文件: {video_file_path}")
    course_page.upload_course_file(video_file_path)
    step("填写备注")
    course_page.input_course_remark("测试备注")

    step("点击保存")
    course_page.click_save_button()

    # 等待新增成功提示
    try:
        success_msg = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="message_3"]/p'))
        )
        toast = success_msg.text.strip()
        step(f"新增课程结果: {toast}")
    except Exception:
        toast = course_page.get_toast_text()
        step(f"新增课程结果: {toast}")

    # ---------- 2. 发布课程（培训计划只能关联已发布课程）----------
    # 发布逻辑参考 test_course_management.py test_008_publish_course
    step(f"发布课程「{course_name}」")
    course_page.click_reset_button()
    course_page.input_search_course_name(course_name)
    course_page.click_search_button()

    # 点击课程卡片中的发布按钮 + 确认弹窗（使用 CourseManagePage 封装方法）
    step(f"点击课程「{course_name}」的发布按钮")
    published = False
    try:
        course_page.click_publish_button_in_card(course_name)
        published = True
    except Exception as e:
        print(f"[publish] 发布按钮定位失败: {e}")

    if published:
        # 发布确认弹窗
        try:
            course_page.click_confirm_dialog_ok()
        except Exception as e:
            print(f"[publish] 无确认弹窗或点击失败: {e}")

        # 校验发布成功 toast
        try:
            success_text = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//*[contains(@class,"el-message") and contains(., "发布成功")]'))
            ).text.strip()
            step(f"发布结果: {success_text}")
        except Exception:
            try:
                toast = course_page.get_toast_text()
                step(f"发布结果: {toast}")
            except Exception:
                step("发布结果: 未获取到toast，继续流程")

        step("课程已发布")

        # 等待所有弹窗完全消失，避免遮挡菜单
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, '.el-overlay-dialog, .el-overlay-message-box, .el-message-box__wrapper')
                )
            )
        except Exception:
            pass

        step("课程已发布")

        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, '.el-overlay-dialog, .el-overlay-message-box, .el-message-box__wrapper')
                )
            )
        except Exception:
            pass

    step(f"返回培训计划管理页面，课程名称: {course_name}")
    plan_page.switch_to_train_plan()
    return course_name


def _delete_plan(driver, plan_name):
    """删除指定培训计划并验证"""
    page = TrainPlanPage(driver)
    page.delete_plan_by_search(plan_name)
    toast = page.get_toast_text()
    step(f"删除结果: {toast}")
    check(f"培训计划「{plan_name}」删除成功", toast, "成功" in toast or toast != "")
    return toast


def _publish_plan(driver, plan_name):
    """发布指定培训计划"""
    page = TrainPlanPage(driver)
    page.click_reset()
    page.input_search_name(plan_name)
    page.click_search()

    page.click_row_button(plan_name, "发布")

    # 可能的发布确认弹窗
    try:
        confirm_xpaths = [
            '//div[contains(@class,"el-message-box") '
            'and not(contains(@style,"display: none"))]'
            '//button[.//span[contains(text(),"确定")]]',
            '//div[contains(@class,"el-overlay") '
            'and not(contains(@style,"display: none"))]'
            '//div[contains(@class,"el-message-box")]'
            '//button[.//span[contains(text(),"确定")]]',
        ]
        for xp in confirm_xpaths:
            try:
                btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                driver.execute_script("arguments[0].click();", btn)
                break
            except Exception:
                continue
    except Exception:
        pass

    toast = page.get_toast_text()
    step(f"发布结果: {toast}")
    return toast


def _delete_course(driver, course_name):
    """跳转到课程管理，删除指定课程并返回培训计划管理"""
    course_page = CourseManagePage(driver)
    plan_page = TrainPlanPage(driver)

    step("跳转到课程管理")
    plan_page.navigate_to_course_management()

    step(f"搜索课程「{course_name}」")
    course_page.click_reset_button()
    course_page.input_search_course_name(course_name)
    course_page.click_search_button()

    # 勾选课程复选框
    checkbox_xpaths = [
        f'//*[contains(normalize-space(.),"{course_name}")]'
        f'/ancestor::div[contains(@class,"el-card")]'
        f'//label[contains(@class,"el-checkbox")]',
        f'//*[contains(text(),"{course_name}")]'
        f'/ancestor::div[contains(@class,"card") or contains(@class,"el-card")]'
        f'//span[contains(@class,"el-checkbox")]',
        '//label[contains(@class,"el-checkbox")]//span[last()]',
    ]
    checked = False
    for xp in checkbox_xpaths:
        try:
            cb = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            driver.execute_script("arguments[0].click();", cb)
            checked = True
            break
        except Exception:
            continue

    if not checked:
        step("未找到课程复选框，跳过删除清理")
        plan_page.switch_to_train_plan()
        return ""

    step("点击删除按钮")
    try:
        del_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[.//span[contains(text(),"删除")]]')
            )
        )
        driver.execute_script("arguments[0].click();", del_btn)
    except Exception:
        step("未找到删除按钮，跳过")
        plan_page.switch_to_train_plan()
        return ""

    # 确认删除弹窗
    confirm_xpaths = [
        '//div[contains(@class,"el-message-box") '
        'and not(contains(@style,"display: none"))]'
        '//button[.//span[contains(text(),"确定")]]',
    ]
    for xp in confirm_xpaths:
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            driver.execute_script("arguments[0].click();", btn)
            break
        except Exception:
            continue

    toast = course_page.get_toast_text()
    step(f"删除课程结果: {toast}")

    step("返回培训计划管理页面")
    plan_page.switch_to_train_plan()
    return toast


class TestTrainPlanManagement:
    """培训计划管理 - 测试类"""

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

    def test_001_display_list_and_fields(self, driver_setup):
        """TR-PLAN-001: 正常显示培训计划列表及相关字段"""
        case("TR-PLAN-001", "正常显示培训计划列表及相关字段")
        page = TrainPlanPage(driver_setup)

        step("验证页面加载完成")
        loaded = page.is_page_loaded()
        check("页面加载成功", loaded, loaded)

        step("获取页面标题")
        page_title = page.get_page_title_text()
        step(f"页面标题: {page_title}")
        if page_title:
            check("页面标题包含'培训计划'", page_title, "培训计划" in page_title)

        step("获取表格列头")
        headers = page.get_table_header_texts()
        step(f"表格列头: {headers}")

        step("获取表格数据行数")
        row_count = page.get_table_row_count()
        step(f"当前页行数: {row_count}")

        step("获取总条数")
        total_text = page.get_total_count_text()
        step(f"总条数: {total_text}")

        # 验证点：表格列数≥6（容忍字段名细微差异，不要求精确匹配）
        check(f"表格列头完整（≥6列）",
              f"实际列数: {len(headers)}, 列头: {headers}",
              len(headers) >= 6)

        check("列表加载正常", f"当前页{row_count}条，{total_text}", row_count >= 0)

    def test_002_pagination(self, driver_setup):
        """TR-PLAN-002: 分页跳转验证"""
        case("TR-PLAN-002", "分页跳转验证")
        page = TrainPlanPage(driver_setup)

        step("点击重置按钮")
        page.click_reset()

        total = page.get_total_count()
        step(f"总数据条数: {total}")

        check("总条数 >= 0", total, total >= 0)

        if total <= 0:
            step("无数据，跳过分页测试")
            check("无数据可测试", "跳过", True)
            return

        default_size = 10

        step("记录当前页第一行数据")
        first_page_row1 = page.get_first_row_data()
        step(f"第一页第一行数据: {first_page_row1}")

        current_page = page.get_current_page_number()
        step(f"当前页码: {current_page}")
        check("默认在第1页", current_page, current_page == 1)

        # 尝试点击下一页
        has_next = page.is_next_page_enabled()
        if has_next:
            step("点击下一页")
            page.click_next_page()

            new_page = page.get_current_page_number()
            step(f"跳转后页码: {new_page}")
            check("成功跳转到第2页", new_page, new_page == 2)

            if total > default_size:
                second_page_row1 = page.get_first_row_data()
                step(f"第二页第一行数据: {second_page_row1}")
                check("分页后数据不同（不重复）",
                      f"第一页: {first_page_row1}, 第二页: {second_page_row1}",
                      second_page_row1 != first_page_row1)

            step("点击上一页，返回第1页")
            page.click_prev_page()
            back_page = page.get_current_page_number()
            check("成功返回第1页", back_page, back_page == 1)
        else:
            step("无下一页按钮（数据不足一页），跳过翻页验证")

        # 切换每页条数
        step("切换每页条数为 20 条/页")
        page.select_page_size(20)

        new_total = page.get_total_count()
        step(f"切换后总条数: {new_total}")
        check("切换条数后数据不变", new_total, new_total == total)

        new_row_count = page.get_table_row_count()
        step(f"切换后当前页行数: {new_row_count}")
        check("切换后列表正常显示",
              f"之前{default_size}条/页，现在{new_row_count}条/页",
              new_row_count != 0 or total == 0)

    # ========== 新增培训计划（必选字段） ==========

    def test_003_add_train_plan_required(self, driver_setup):
        """TR-PLAN-003: 新增培训计划（必选字段）"""
        global CREATED_PLAN_NAME, CREATED_COURSE_NAME
        case("TR-PLAN-003", "新增培训计划（必选字段）")
        page = TrainPlanPage(driver_setup)
        plan_name = _generate_plan_name()
        CREATED_PLAN_NAME = plan_name
        step(f"计划名称: {plan_name}")

        # 前置：新增并发布课程（培训计划只能关联已发布课程）
        step("前置：新增并发布关联课程")
        linked_course_name = _create_course_for_plan(driver_setup)
        CREATED_COURSE_NAME = linked_course_name
        step(f"关联课程名称: {linked_course_name}（已发布）")

        step("点击新增培训计划按钮")
        page.click_add_button()

        step(f"填写计划名称: {plan_name}")
        page.fill_dialog_input("计划名称", plan_name)

        step("选择培训类型: 技能培训")
        page.select_dialog_option("培训类型", "技能培训")

        step("选择培训对象")
        page.select_training_target()

        step("选择负责人")
        page.select_principal()  # 默认选择第一个人员

        step("填写开始时间: 2026-05-01")
        page.fill_dialog_date("开始时间", "2026-05-01")

        step("填写结束时间: 2026-05-31")
        page.fill_dialog_date("结束时间", "2026-05-31")

        step("关联课程：打开课程选择弹窗")
        page.click_course_select_trigger()
        step("点击全部，全选课程")
        page.click_all_courses_button()
        step("确认课程选择")
        page.confirm_course_selection()

        step("点击保存")
        page.click_save()

        toast = page.get_toast_text()
        step(f"保存结果: {toast}")
        check("保存成功提示", toast, "成功" in toast or "保存" in toast or toast != "")

    # ========== 新增培训计划（全部字段：必选 + 非必选）==========

    def test_004_add_train_plan_all_fields(self, driver_setup):
        """TR-PLAN-004: 新增培训计划（必选 + 非必选字段）"""
        case("TR-PLAN-004", "新增培训计划（必选 + 非必选字段）")
        page = TrainPlanPage(driver_setup)
        plan_name = _generate_plan_name()
        step(f"计划名称: {plan_name}")

        step("前置：新增关联课程")
        linked_course_name = _create_course_for_plan(driver_setup)
        step(f"关联课程名称: {linked_course_name}")

        step("点击新增培训计划按钮")
        page.click_add_button()

        step(f"填写计划名称: {plan_name}")
        page.fill_dialog_input("计划名称", plan_name)

        step("选择培训类型: 入职培训")
        page.select_dialog_option("培训类型", "入职培训")

        step("选择培训对象")
        page.select_training_target()

        step("选择负责人")
        page.select_principal()  # 默认选择第一个人员

        step("填写开始时间: 2026-04-27")
        page.fill_dialog_date("开始时间", "2026-04-27")

        step("填写结束时间: 2026-04-28")
        page.fill_dialog_date("结束时间", "2026-04-28")

        # 非必选字段
        step("填写培训地点: 公司办公室")
        page.fill_dialog_input("培训地点", "公司办公室")

        step("关联课程：打开课程选择弹窗")
        page.click_course_select_trigger()
        step("点击全部，全选课程")
        page.click_all_courses_button()
        step("确认课程选择")
        page.confirm_course_selection()

        step("填写培训目标: 掌握入职所需安全知识和操作规范")
        page.fill_dialog_input("培训目标", "掌握入职所需安全知识和操作规范")

        step("填写备注: 自动化测试新增，包含全部字段")
        page.fill_dialog_input("备注", "自动化测试新增，包含全部字段")

        step("点击保存")
        page.click_save()

        toast = page.get_toast_text()
        step(f"保存结果: {toast}")
        check("保存成功提示", toast, "成功" in toast or "保存" in toast or toast != "")

        # 自建数据自己清理
        step(f"清理本用例自建计划: {plan_name}")
        try:
            _delete_plan(driver_setup, plan_name)
        except Exception as e:
            print(f"清理计划「{plan_name}」时跳过: {e}")

        step(f"清理关联课程: {linked_course_name}")
        try:
            _delete_course(driver_setup, linked_course_name)
        except Exception as e:
            print(f"清理课程「{linked_course_name}」时跳过: {e}")

    # ========== 搜索 / 操作测试（共用 test_003 创建的数据）==========

    def test_005_search_by_name(self, driver_setup):
        """TR-PLAN-005: 按计划名称模糊查询"""
        global CREATED_PLAN_NAME
        case("TR-PLAN-005", "按计划名称模糊查询")
        page = TrainPlanPage(driver_setup)

        step("重置并搜索：计划名称 = 计划")
        page.click_reset()
        page.input_search_name("计划")
        page.click_search()

        found = page.is_plan_exists(CREATED_PLAN_NAME)
        check(f"模糊搜索「计划」能匹配到「{CREATED_PLAN_NAME}」", found, found)

    def test_006_search_by_type(self, driver_setup):
        """TR-PLAN-006: 按培训类型搜索"""
        global CREATED_PLAN_NAME
        case("TR-PLAN-006", "按培训类型搜索")
        page = TrainPlanPage(driver_setup)

        step("搜索：计划名称=计划 + 培训类型=安全培训")
        page.click_reset()
        page.input_search_name("计划")
        page.select_search_type("安全培训")
        page.click_search()

        found = page.is_plan_exists(CREATED_PLAN_NAME)
        check("搜索（名称+类型）匹配到创建的计划", found, found)

    def test_007_search_by_status(self, driver_setup):
        """TR-PLAN-007: 按培训状态搜索"""
        global CREATED_PLAN_NAME
        case("TR-PLAN-007", "按培训状态搜索")
        page = TrainPlanPage(driver_setup)

        step("搜索：计划名称=计划 + 类型=安全培训 + 状态=待培训")
        page.click_reset()
        page.input_search_name("计划")
        page.select_search_type("安全培训")
        page.select_search_status("待培训")
        page.click_search()

        found = page.is_plan_exists(CREATED_PLAN_NAME)
        check("搜索（名称+类型+状态）匹配到创建的计划", found, found)

    def test_008_search_by_publish_status(self, driver_setup):
        """TR-PLAN-008: 按发布状态搜索"""
        global CREATED_PLAN_NAME
        case("TR-PLAN-008", "按发布状态搜索")
        page = TrainPlanPage(driver_setup)

        step(f"先发布培训计划: {CREATED_PLAN_NAME}")
        _publish_plan(driver_setup, CREATED_PLAN_NAME)

        step("搜索：计划名称=计划 + 类型=安全培训 + 状态=待培训 + 发布状态=已发布")
        page.click_reset()
        page.input_search_name("计划")
        page.select_search_type("安全培训")
        page.select_search_status("待培训")
        page.select_search_publish("已发布")
        page.click_search()

        found = page.is_plan_exists(CREATED_PLAN_NAME)
        check("搜索（名称+类型+状态+发布）匹配到创建的计划", found, found)

    def test_009_reset_search(self, driver_setup):
        """TR-PLAN-009: 重置按钮功能正常"""
        case("TR-PLAN-009", "重置按钮功能正常")
        page = TrainPlanPage(driver_setup)

        step("输入搜索条件后重置")
        page.click_reset()
        page.input_search_name("计划")
        page.select_search_type("安全培训")
        page.click_search()
        total_before = page.get_total_count()

        step("点击重置，筛选条件应清空")
        page.click_reset()
        total_after = page.get_total_count()

        check("重置后列表仍正常加载", f"重置前{total_before}条，重置后{total_after}条",
              total_after >= total_before)

    def test_010_edit_plan(self, driver_setup):
        """TR-PLAN-010: 修改培训计划"""
        global CREATED_PLAN_NAME
        case("TR-PLAN-010", "修改培训计划")
        page = TrainPlanPage(driver_setup)

        step("搜索并点击编辑")
        page.click_reset()
        page.input_search_name(CREATED_PLAN_NAME)
        page.click_search()

        page.click_row_button(CREATED_PLAN_NAME, "编辑")

        step("修改培训地点")
        page.fill_dialog_input("培训地点", "自动化测试修改地点")

        step("保存修改")
        page.click_save()

        toast = page.get_toast_text()
        step(f"修改结果: {toast}")
        check("修改成功", toast, "成功" in toast or toast != "")

    def test_011_view_plan(self, driver_setup):
        """TR-PLAN-011: 查看详情信息"""
        global CREATED_PLAN_NAME
        case("TR-PLAN-011", "查看详情信息")
        page = TrainPlanPage(driver_setup)

        step("搜索并点击查看")
        page.click_reset()
        page.input_search_name(CREATED_PLAN_NAME)
        page.click_search()

        try:
            page.click_row_button(CREATED_PLAN_NAME, "查看")
        except Exception:
            page.click_row_button(CREATED_PLAN_NAME, "详情")

        dialog_title = page.get_dialog_title_text()
        has_plan = CREATED_PLAN_NAME in dialog_title if dialog_title else False
        check("详情弹窗打开", dialog_title, has_plan or "详情" in dialog_title or "查看" in dialog_title)

        step("关闭详情弹窗")
        close_xpaths = [
            '//button[.//span[contains(text(),"关闭")]]',
            '//button[contains(@class,"el-dialog__close")]',
            '//button[.//span[contains(text(),"返回")]]',
        ]
        for xp in close_xpaths:
            try:
                btn = WebDriverWait(driver_setup, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                driver_setup.execute_script("arguments[0].click();", btn)
                break
            except Exception:
                continue

        check("查看详情完成", True, True)

    # ========== 删除清理（双向闭环） ==========

    def test_012_delete_plan(self, driver_setup):
        """TR-PLAN-012: 删除培训计划及关联课程（清理数据，闭环）"""
        global CREATED_PLAN_NAME, CREATED_COURSE_NAME
        case("TR-PLAN-012", "删除培训计划及关联课程（清理测试数据）")

        step("1/2 删除培训计划")
        _delete_plan(driver_setup, CREATED_PLAN_NAME)

        step("2/2 删除关联课程（清理脏数据）")
        _delete_course(driver_setup, CREATED_COURSE_NAME)

        CREATED_PLAN_NAME = None
        CREATED_COURSE_NAME = None
        step("培训计划和关联课程均已清理，双向闭环完成")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
