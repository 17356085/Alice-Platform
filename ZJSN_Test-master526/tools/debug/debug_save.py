"""调试: 培训计划保存失败原因"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.browser_driver import BaseDriver, ensure_logged_in
from page.personnel_page.TrainPlanPage import TrainPlanPage
from page.personnel_page.CourseManagePage import CourseManagePage

base = BaseDriver()
driver = base.open_browser()
ensure_logged_in(driver)

page = TrainPlanPage(driver)
page.navigate_to_train_plan()
time.sleep(1)

# 1. 先创建并发布课程
course_page = CourseManagePage(driver)
page.navigate_to_course_management()

course_name = f"debug{time.strftime('%Y%m%d%H%M%S')}"
course_page.click_add_course_button()
course_page.input_course_name(course_name)
course_page.input_course_duration(2)
course_page.select_dialog_option_by_text("课程分类", "技能培训")
time.sleep(1.5)
course_page.select_dialog_option_by_text("资料类型", "视频")
time.sleep(1.5)
course_page.input_course_intro("调试课程")
video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_files", "test_video.mp4")
course_page.upload_course_file(video_path)
time.sleep(3)
course_page.input_course_remark("调试备注")
course_page.click_save_button()
time.sleep(3)
print(f"新增课程结果: {course_page.get_toast_text()}")

# 发布课程
course_page.click_reset_button()
course_page.input_search_course_name(course_name)
course_page.click_search_button()
time.sleep(2)
try:
    course_page.click_publish_button_in_card(course_name)
    time.sleep(1)
    course_page.click_confirm_dialog_ok()
    time.sleep(1)
except Exception as e:
    print(f"发布异常: {e}")

print(f"发布结果: {course_page.get_toast_text()}")

# 2. 回到培训计划
page.switch_to_train_plan()
time.sleep(1.5)

plan_name = f"debug{time.strftime('%Y%m%d%H%M%S')}计划"

# 3. 新增培训计划 - 逐步调试
page.click_add_button()
time.sleep(1)

# 填计划名称
page.fill_dialog_input("计划名称", plan_name)

# 选培训类型 + 检查效果
print("\n===== 调试: 选择培训类型 =====")
page.select_dialog_option("培训类型", "技能培训")
time.sleep(1)

# 检查表单是否有校验错误
try:
    err_els = driver.find_elements(By.XPATH, '//div[contains(@class,"el-form-item__error")]')
    if err_els:
        print(f"表单校验错误: {[e.text for e in err_els]}")
    else:
        print("无表单校验错误")
except Exception as e:
    print(f"检查校验错误异常: {e}")

# 选培训对象
page.select_training_target()

# 选负责人
page.select_principal()

# 填日期
page.fill_dialog_date("开始时间", "2026-05-01")
page.fill_dialog_date("结束时间", "2026-05-31")

# 关联课程
page.click_course_select_trigger()
page.click_all_courses_button()
page.confirm_course_selection()

# 保存前检查弹窗状态
print("\n===== 保存前弹窗状态 =====")
dialogs = driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")]')
for i, d in enumerate(dialogs):
    try:
        style = d.get_attribute('style') or ''
        title = d.find_element(By.XPATH, './/*[contains(@class,"el-dialog__title")]').text.strip()
        print(f"弹窗[{i}]: title='{title}', style='{style[:80]}'")
    except Exception:
        pass

# 检查表单校验错误
try:
    err_els = driver.find_elements(By.XPATH, '//div[contains(@class,"el-form-item__error")]')
    if err_els:
        print(f"保存前表单校验错误: {[e.text for e in err_els]}")
    else:
        print("保存前无表单校验错误")
except Exception as e:
    print(f"检查异常: {e}")

# 检查 save button
try:
    save_btn = driver.find_element(By.XPATH, page.SAVE_BUTTON[1])
    print(f"找到保存按钮: text='{save_btn.text}', displayed={save_btn.is_displayed()}")
    print(f"保存按钮 rect: {save_btn.rect}")
except Exception as e:
    print(f"保存按钮未找到: {e}")

print("\n===== 准备点击保存 =====")
page.click_save()
time.sleep(3)

print(f"\n保存后的 toast: '{page.get_toast_text()}'")

# 再次检查表单校验错误
try:
    err_els = driver.find_elements(By.XPATH, '//div[contains(@class,"el-form-item__error")] | //*[contains(@class,"el-form-item--error")]')
    if err_els:
        print(f"保存后表单校验错误: {[e.text for e in err_els if e.text.strip()]}")
    else:
        print("保存后无表单校验错误")
except Exception as e:
    print(f"检查异常: {e}")

# 检查是否弹窗还在
try:
    visible_dialogs = driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]')
    print(f"保存后可见弹窗数: {len(visible_dialogs)}")
    for i, d in enumerate(visible_dialogs):
        try:
            title = d.find_element(By.XPATH, './/*[contains(@class,"el-dialog__title")]').text.strip()
            print(f"  弹窗[{i}]: '{title}'")
        except Exception:
            pass
except Exception as e:
    print(f"弹窗检查异常: {e}")

input("按回车键关闭浏览器...")
base.close_browser()
