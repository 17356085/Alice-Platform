"""报警配置弹窗 Page Object

注意：本页面使用 Element Plus 组件（el-dialog 弹窗表单），
通过父页面（tank/monitor）的"配置报警"按钮触发打开。
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class TankAlarmConfigPage(BasePage):
    """报警配置弹窗 — Element Plus 对话框表单"""

    # ══════════════════════════════════════════════════════════════════
    #  表单字段定位器
    # ══════════════════════════════════════════════════════════════════

    # 报警类型下拉框
    ALARM_TYPE_INPUT = (
        By.XPATH,
        '//label[text()="报警类型"]/following-sibling::div//input'
    )

    # 报警邮箱输入框
    ALARM_EMAIL_INPUT = (
        By.XPATH,
        '//label[text()="报警邮箱"]/following-sibling::div//input'
    )

    # 备注文本域
    REMARK_TEXTAREA = (
        By.XPATH,
        '//label[text()="备注"]/following-sibling::div//textarea'
    )

    # ══════════════════════════════════════════════════════════════════
    #  弹窗控制
    # ══════════════════════════════════════════════════════════════════

    def wait_dialog_open(self, timeout=10):
        """等待弹窗打开"""
        logger.info("等待报警配置弹窗打开...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.visibility_of_element_located(self.DIALOG))
            self.wait_vue_stable()
            logger.info("✅ 弹窗已打开")
            return True
        except TimeoutException:
            logger.error("❌ 弹窗打开超时")
            self.save_screenshot("alarm_config_dialog_timeout")
            return False

    def wait_dialog_close(self, timeout=10):
        """等待弹窗关闭"""
        logger.info("等待报警配置弹窗关闭...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.invisibility_of_element_located(self.DIALOG))
            logger.info("✅ 弹窗已关闭")
            return True
        except TimeoutException:
            logger.error("❌ 弹窗关闭超时")
            self.save_screenshot("alarm_config_dialog_close_timeout")
            return False

    def get_dialog_title(self):
        """获取弹窗标题"""
        try:
            title_elem = self.find_element(self.DIALOG_TITLE)
            return title_elem.text.strip()
        except NoSuchElementException:
            logger.warning("无法获取弹窗标题")
            return ""

    def is_dialog_open(self):
        """判断弹窗是否打开"""
        try:
            dialog = self.find_element(self.DIALOG)
            return dialog.is_displayed()
        except NoSuchElementException:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  表单操作
    # ══════════════════════════════════════════════════════════════════

    def select_alarm_type(self, alarm_type):
        """选择报警类型"""
        logger.info(f"选择报警类型: {alarm_type}")
        try:
            # 1. 点击下拉框
            self.click(self.ALARM_TYPE_INPUT)
            time.sleep(0.3)  # 等待下拉展开

            # 2. 等待下拉菜单出现
            wait = WebDriverWait(self.driver, 5)
            dropdown = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, '.el-select-dropdown')
                )
            )

            # 3. 查找并点击选项
            option_xpath = f'//div[contains(@class, "el-select-dropdown")]//span[text()="{alarm_type}"]'
            option = self.driver.find_element(By.XPATH, option_xpath)
            self.driver.execute_script("arguments[0].click();", option)

            # 4. 等待下拉收起
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.el-select-dropdown')))
            logger.info(f"✅ 已选择: {alarm_type}")
            return self

        except TimeoutException:
            logger.error(f"❌ 选择报警类型失败: {alarm_type}")
            self.save_screenshot("select_alarm_type_failed")
            raise

    def input_alarm_email(self, email):
        """输入报警邮箱"""
        logger.info(f"输入报警邮箱: {email}")
        self.clear_input(self.ALARM_EMAIL_INPUT)
        self.input_text(self.ALARM_EMAIL_INPUT, email)
        return self

    def input_remark(self, remark):
        """输入备注"""
        logger.info(f"输入备注: {remark}")
        self.clear_input(self.REMARK_TEXTAREA)
        self.input_text(self.REMARK_TEXTAREA, remark)
        return self

    def fill_form(self, alarm_type, email, remark=""):
        """完整填写表单"""
        logger.info("开始填写报警配置表单...")
        self.select_alarm_type(alarm_type)
        self.input_alarm_email(email)
        if remark:
            self.input_remark(remark)
        logger.info("✅ 表单填写完成")
        return self

    def clear_form(self):
        """清空表单"""
        logger.info("清空表单...")
        self.clear_input(self.ALARM_TYPE_INPUT)
        self.clear_input(self.ALARM_EMAIL_INPUT)
        self.clear_input(self.REMARK_TEXTAREA)
        return self

    # ══════════════════════════════════════════════════════════════════
    #  表单提交与验证
    # ══════════════════════════════════════════════════════════════════

    def click_save(self):
        """点击确定按钮"""
        logger.info("点击确定按钮")
        try:
            self.click(self.DIALOG_SAVE)
            logger.info("✅ 已点击确定")
            return self
        except Exception as e:
            logger.error(f"❌ 点击确定失败: {e}")
            raise

    def click_cancel(self):
        """点击取消按钮"""
        logger.info("点击取消按钮")
        try:
            self.click(self.DIALOG_CANCEL)
            logger.info("✅ 已点击取消")
            return self
        except Exception as e:
            logger.error(f"❌ 点击取消失败: {e}")
            raise

    def submit_form(self):
        """提交表单并等待响应"""
        logger.info("提交报警配置表单...")
        self.click_save()

        # 等待加载完成
        try:
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.invisibility_of_element_located(self.LOADING_MASK))
            logger.info("✅ 表单提交完成，加载结束")
        except TimeoutException:
            logger.warning("⚠️ 加载超时，继续执行")

        return self

    def get_form_errors(self):
        """获取表单验证错误信息"""
        errors = {}
        try:
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, '.el-form-item__error')
            for error_elem in error_elements:
                # 找到错误对应的字段标签
                parent = error_elem.find_element(By.XPATH, '../..')
                label = parent.find_element(By.TAG_NAME, 'label').text
                errors[label] = error_elem.text
            logger.debug(f"表单验证错误: {errors}")
        except NoSuchElementException:
            pass
        return errors

    def has_form_errors(self):
        """判断是否有表单验证错误"""
        errors = self.get_form_errors()
        return len(errors) > 0

    # ══════════════════════════════════════════════════════════════════
    #  Toast 消息处理
    # ══════════════════════════════════════════════════════════════════

    def get_toast_message(self, timeout=3):
        """获取 Toast 消息"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            toast = wait.until(EC.visibility_of_element_located(self.TOAST))
            return toast.text.strip()
        except TimeoutException:
            logger.debug("未检测到 Toast 消息")
            return ""

    def get_toast_type(self, timeout=3):
        """获取 Toast 类型 (success/error/warning/info)"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            toast_container = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, '.el-message')
                )
            )
            class_list = toast_container.get_attribute('class')
            if 'el-message--success' in class_list:
                return 'success'
            elif 'el-message--error' in class_list:
                return 'error'
            elif 'el-message--warning' in class_list:
                return 'warning'
            else:
                return 'info'
        except TimeoutException:
            return ''

    def wait_for_success_toast(self, timeout=5):
        """等待成功 Toast 出现"""
        logger.info("等待成功消息...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            toast = wait.until(
                EC.visibility_of_element_located(self.TOAST_SUCCESS)
            )
            message = toast.text
            logger.info(f"✅ 收到成功消息: {message}")
            return message
        except TimeoutException:
            logger.warning("⚠️ 未收到成功消息")
            return ""

    def wait_for_error_toast(self, timeout=5):
        """等待错误 Toast 出现"""
        logger.info("等待错误消息...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            toast = wait.until(
                EC.visibility_of_element_located(self.TOAST_ERROR)
            )
            message = toast.text
            logger.warning(f"❌ 收到错误消息: {message}")
            return message
        except TimeoutException:
            logger.warning("⚠️ 未收到错误消息")
            return ""

    # ══════════════════════════════════════════════════════════════════
    #  读取表单值
    # ══════════════════════════════════════════════════════════════════

    def get_alarm_type_value(self):
        """获取报警类型当前值"""
        try:
            input_elem = self.find_element(self.ALARM_TYPE_INPUT)
            return input_elem.get_attribute('value') or ""
        except NoSuchElementException:
            return ""

    def get_alarm_email_value(self):
        """获取报警邮箱当前值"""
        try:
            input_elem = self.find_element(self.ALARM_EMAIL_INPUT)
            return input_elem.get_attribute('value') or ""
        except NoSuchElementException:
            return ""

    def get_remark_value(self):
        """获取备注当前值"""
        try:
            textarea_elem = self.find_element(self.REMARK_TEXTAREA)
            return textarea_elem.get_attribute('value') or ""
        except NoSuchElementException:
            return ""

    def get_form_values(self):
        """获取表单所有值"""
        return {
            "alarm_type": self.get_alarm_type_value(),
            "alarm_email": self.get_alarm_email_value(),
            "remark": self.get_remark_value()
        }

    # ══════════════════════════════════════════════════════════════════
    #  辅助方法
    # ══════════════════════════════════════════════════════════════════

    def _js_click_el(self, element):
        """使用 JS 点击元素（避免 overlay 遮挡）"""
        self.driver.execute_script("arguments[0].click();", element)
        time.sleep(0.2)

    def save_screenshot(self, name):
        """保存截图"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/alarm_config_{name}_{timestamp}.png"
        self.driver.save_screenshot(filename)
        logger.info(f"📸 截图已保存: {filename}")