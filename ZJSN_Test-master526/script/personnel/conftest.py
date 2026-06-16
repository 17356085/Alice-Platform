"""人事管理模块共享 fixtures

driver_setup（module 级）：
  - 每个 test_*.py 文件独立浏览器实例（与原各文件内 session fixture 行为一致）
  - 使用 JS hash 导航（window.location.hash）直接跳转目标路由
  - 比侧边栏点击更可靠：绕过 el-sub-menu 展开/定位问题，SPA 内无重载

使用方式（与改造前相同）：
    def test_xxx(self, driver_setup):
        page = CourseManagePage(driver_setup)
"""
import logging
import time

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from base.base_page import BasePage
from page.personnel_page.PostManagePage import PostManagePage
from page.personnel_page.ExamManagePage import ExamManagePage

logger = logging.getLogger(__name__)

# 测试文件 → 页面 hash 路由映射
_MODULE_HASH_ROUTES = {
    "test_course_management": "#/personnel/training/course",
    "test_employee_management": "#/personnel/employee",
    "test_question_bank": "#/personnel/training/question",
    "test_post_management": "#/personnel/post",
    "test_paper_management": "#/personnel/training/paper",
    "test_train_plan_management": "#/personnel/training/plan",
    "test_exam_management": "#/personnel/training/examArrange",
    "test_certificate_management": "#/personnel/training/certificate",
    "test_practice": "#/personnel/training/practice",
    "test_study_record": "#/personnel/training/studyRecord",
    "test_wrong_question": "#/personnel/training/wrongQuestion",
    "test_contractor_unit": "#/personnel/contractor",
    "test_contractor_personnel": "#/personnel/contractor",
    "test_entry_approval": "#/personnel/contractor/approval",
    "test_entry_record": "#/personnel/contractor/record",
    "test_entry_confirm": "#/personnel/contractor/confirm",
}


def _navigate_for_module(driver, module):
    """使用统一导航器 JS hash 跳转（含智能表格就绪等待）"""
    from base.sidebar_navigator import SidebarNavigator

    name = module.__name__.split(".")[-1]

    # 考试模块：导航前需要确保测试用户存在
    if name == "test_exam_management" and hasattr(module, "_ensure_test_user_exists"):
        try:
            module._ensure_test_user_exists(driver)
        except Exception as e:
            logger.warning("考试模块前置用户创建失败(非致命): %s", e)
        time.sleep(1)
        # _ensure_test_user_exists 把页面留在 User Management，
        # 必须用侧边栏 DOM 点击恢复导航（hash 跳转在 SPA 内可能不生效）
        try:
            from base.sidebar_navigator import SidebarNavigator
            nav = SidebarNavigator(driver)
            nav.navigate_to("人员管理", "培训管理", "考试管理")
            BasePage(driver).wait_vue_stable()
            logger.info("考试模块: 侧边栏恢复导航到考试管理")
        except Exception as e:
            logger.warning("考试模块侧边栏恢复导航失败，尝试 hash: %s", e)
            nav = SidebarNavigator(driver)
            nav._navigate_by_js_hash("#/personnel/training/examArrange", "exam-fallback")
        return

    route = _MODULE_HASH_ROUTES.get(name)
    if route:
        logger.info("导航: %s → %s", name, route)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash(route, name)
        # 承包商人员需要先展开侧边栏再点击（无独立路由，与单位共用）
        if name == "test_contractor_personnel":
            try:
                logger.info("承包商人员: JS 点击 nest-menu 切换视图")
                # JS原生事件触发Vue组件切换 + 等待内容渲染
                clicked = driver.execute_script("""
                    var items = document.querySelectorAll('.el-menu-item, .nest-menu .el-menu-item, li[role="menuitem"]');
                    for (var i = 0; i < items.length; i++) {
                        if (items[i].textContent.indexOf('承包商人员') !== -1) {
                            items[i].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                            return true;
                        }
                    }
                    return false;
                """)
                if clicked:
                    logger.info("承包商人员: nest-menu 切换成功，等待渲染")
                    time.sleep(1.5)  # 等待Vue组件切换+Ajax
                    BasePage(driver).wait_vue_stable()
                    # 验证切换：检查表格列头是否包含"身份证号"（承包商人员独有列）
                    verify = driver.execute_script("""
                        var cells = document.querySelectorAll('.el-table__header-wrapper th .cell');
                        for (var i = 0; i < cells.length; i++) {
                            if (cells[i].textContent.indexOf('身份证') !== -1) return true;
                        }
                        return false;
                    """)
                    logger.info("承包商人员: 页面验证 %s", "通过" if verify else "未通过(可能仍在单位视图)")
                else:
                    logger.warning("承包商人员: 未找到 nest-menu 项，尝试侧边栏导航")
                    nav.navigate_to("人员管理", "承包商管理", "承包商人员")
                    BasePage(driver).wait_vue_stable()
            except Exception as e:
                logger.warning("侧边栏承包商人员导航失败: %s", e)
    else:
        logger.warning("未配置导航: %s", name)


def _teardown_for_module(driver, module):
    """模块结束时的数据清理（考试/岗位/承包商有遗留数据风险）"""
    name = module.__name__.split(".")[-1]
    if name == "test_post_management":
        _teardown_post(driver, module)
    elif name == "test_exam_management":
        _teardown_exam(driver, module)
    elif name == "test_contractor_unit":
        _teardown_contractor_unit(driver, module)
    elif name == "test_contractor_personnel":
        _teardown_contractor_personnel(driver, module)


def _teardown_post(driver, module):
    post_code = getattr(module, "CREATED_POST_CODE", None)
    if not post_code:
        return
    logger.info("岗位管理模块后置清理: %s", post_code)
    try:
        post_manage = PostManagePage(driver)
        post_manage.navigate_to_position_management()
        post_manage.click_reset()
        post_manage.input_search_name(post_code)
        post_manage.click_search()
        if post_manage.is_post_name_present(post_code):
            post_manage.click_delete_by_name(post_code)
            post_manage.confirm_message_box()
            time.sleep(1)
    except Exception as exc:
        logger.warning("岗位后置清理失败: %s", exc)


def _teardown_exam(driver, module):
    created_exam = getattr(module, "CREATED_EXAM_NAME", None)
    if not created_exam:
        return
    logger.info("考试管理模块后置清理: %s", created_exam)
    try:
        exam_page = ExamManagePage(driver)
        exam_page.navigate_to_exam_management()
        exam_page.click_reset()
        exam_page.input_search_name(created_exam)
        exam_page.click_search()
        if exam_page.is_exam_name_present(created_exam):
            exam_page.click_row_action(created_exam, "删除")
            exam_page.confirm_message_box("删除")
            time.sleep(1)
    except Exception as exc:
        logger.warning("考试后置清理失败: %s", exc)


def _teardown_contractor_unit(driver, module):
    """清理承包商单位测试数据"""
    unit_name = getattr(module, "CREATED_UNIT_NAME", None)
    updated_name = getattr(module, "UPDATED_UNIT_NAME", None)
    search_name = updated_name or unit_name
    if not search_name:
        return
    logger.info("承包商单位模块后置清理: %s", search_name)
    try:
        from page.personnel_page.ContractorUnitPage import ContractorUnitPage
        from base.sidebar_navigator import SidebarNavigator
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash("#/personnel/contractor", "cleanup")
        BasePage(driver).wait_vue_stable()
        unit_page = ContractorUnitPage(driver)
        unit_page.click_reset()
        unit_page.input_search_name(search_name)
        unit_page.click_search()
        if unit_page.is_unit_name_present(search_name):
            unit_page.click_delete_by_name(search_name)
            unit_page.confirm_message_box()
            time.sleep(1)
    except Exception as exc:
        logger.warning("承包商单位后置清理失败: %s", exc)


def _teardown_contractor_personnel(driver, module):
    """清理承包商人员测试数据"""
    personnel_name = getattr(module, "CREATED_PERSONNEL_NAME", None)
    updated_name = getattr(module, "UPDATED_PERSONNEL_NAME", None)
    search_name = updated_name or personnel_name
    if not search_name:
        return
    logger.info("承包商人员模块后置清理: %s", search_name)
    try:
        from page.personnel_page.ContractorPersonnelPage import ContractorPersonnelPage
        from base.sidebar_navigator import SidebarNavigator
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash("#/personnel/contractor", "cleanup")
        BasePage(driver).wait_vue_stable()
        # 切换侧边栏到承包商人员视图
        try:
            nav.navigate_to("人员管理", "承包商管理", "承包商人员")
        except Exception:
            pass
        BasePage(driver).wait_vue_stable()
        personnel_page = ContractorPersonnelPage(driver)
        personnel_page.click_reset()
        personnel_page.input_search_name(search_name)
        personnel_page.click_search()
        if personnel_page.is_personnel_name_present(search_name):
            personnel_page.click_delete_by_name(search_name)
            personnel_page.confirm_message_box()
            time.sleep(1)
    except Exception as exc:
        logger.warning("承包商人员后置清理失败: %s", exc)


@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级：登录 + 按当前测试文件导航（兼容原有用例参数名）"""
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        _navigate_for_module(driver, request.module)
        yield driver
    finally:
        _teardown_for_module(driver, request.module)
        base.close_browser()
