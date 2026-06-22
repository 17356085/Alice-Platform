# -*- coding: utf-8 -*-
"""
我的档案页面 Page Object
Module: personnel
Page: my-archive

基于 PAGE_CONTEXT.md (v1.0) 元素清单生成

==== 页面结构 ====
1. Tab栏：个人基本信息（默认激活）、证件信息、联系方式、档案变更记录
2. 侧边栏：个人头像 + 编辑资料、修改密码快捷入口
3. 个人基本信息 Tab：只读展示表单
4. 档案变更记录 Tab：筛选区（变更类型、日期范围、查询/重置按钮） + 表格 + 分页
5. 弹窗：编辑基本信息弹窗、修改密码弹窗
"""

from base.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class MyArchivePage(BasePage):
    """
    我的档案页面类
    继承BasePage，封装页面元素定位与操作方法
    """

    # ==================== Tab栏定位器 ====================
    BASIC_INFO_TAB = (By.CSS_SELECTOR, ".el-tabs .el-tab-pane:nth-child(1)")
    """基本信息 Tab 按钮"""

    CERTIFICATE_TAB = (By.CSS_SELECTOR, ".el-tabs .el-tab-pane:nth-child(2)")
    """证件信息 Tab 按钮"""

    CONTACT_TAB = (By.CSS_SELECTOR, ".el-tabs .el-tab-pane:nth-child(3)")
    """联系方式 Tab 按钮"""

    ARCHIVE_TAB = (By.CSS_SELECTOR, ".el-tabs .el-tab-pane:nth-child(4)")
    """档案变更记录 Tab 按钮"""

    # ==================== 侧边栏定位器 ====================
    SIDEBAR_AVATAR = (By.CSS_SELECTOR, ".sidebar .avatar")
    """侧边栏个人头像"""

    SIDEBAR_EDIT_PROFILE_BTN = (By.XPATH, "//aside//button[.//span[text()='编辑资料']]")
    """侧边栏-编辑资料快捷入口"""

    SIDEBAR_CHANGE_PASSWORD_BTN = (By.XPATH, "//aside//button[.//span[text()='修改密码']]")
    """侧边栏-修改密码快捷入口"""

    # ==================== 基本信息Tab - 表单定位器 ====================
    BASIC_INFO_FORM = (By.CSS_SELECTOR, ".el-form.basic-info-form")
    """基本信息展示表单"""

    FIELD_EMPLOYEE_NAME = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:nth-child(1) input")
    """姓名输入框（只读）"""

    FIELD_DEPARTMENT = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:nth-child(2) input")
    """部门输入框（只读）"""

    FIELD_POSITION = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:nth-child(3) input")
    """职位输入框（只读）"""

    FIELD_PHONE = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:nth-child(4) input")
    """手机号输入框（只读，掩码显示）"""

    FIELD_EMAIL = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:nth-child(5) input")
    """邮箱输入框（只读）"""

    EDIT_BASIC_INFO_BTN = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-button--primary")
    """编辑基本信息按钮"""

    # ==================== 档案变更记录Tab - 筛选区定位器 ====================
    CHANGE_TYPE_SELECTOR = (By.CSS_SELECTOR, ".search-wrapper .el-select")
    """变更类型筛选器（下拉框触发）"""

    CHANGE_TYPE_OPTION_NEW = (By.XPATH, "//div[@class='el-select-dropdown' and not(contains(@style, 'display: none'))]//li//span[text()='新增']")
    """变更类型选项：新增（*防多下拉框冲突*）"""

    CHANGE_TYPE_OPTION_MODIFY = (By.XPATH, "//div[@class='el-select-dropdown' and not(contains(@style, 'display: none'))]//li//span[text()='修改']")
    """变更类型选项：修改（*防多下拉框冲突*）"""

    CHANGE_TYPE_OPTION_DELETE = (By.XPATH, "//div[@class='el-select-dropdown' and not(contains(@style, 'display: none'))]//li//span[text()='删除']")
    """变更类型选项：删除（*防多下拉框冲突*）"""

    CHANGE_DATE_PICKER = (By.CSS_SELECTOR, ".search-wrapper .el-date-editor--daterange input")
    """变更日期范围选择器输入框"""

    SEARCH_BTN = (By.XPATH, "//div[contains(@class, 'search-wrapper')]//button[.//span[text()='查询']]")
    """查询按钮"""

    RESET_BTN = (By.XPATH, "//div[contains(@class, 'search-wrapper')]//button[.//span[text()='重置']]")
    """重置按钮"""

    # ==================== 档案变更记录Tab - 表格定位器 ====================
    CHANGE_TABLE = (By.CSS_SELECTOR, ".table-wrapper .el-table")
    """变更记录表格"""

    TABLE_LOADING = (By.CSS_SELECTOR, ".table-wrapper .el-loading-mask")
    """表格加载遮罩层"""

    # 使用BasePage的通用TABLE_ROWS定位器： (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    # 以下为列元素，用于提取数据
    COL_CHANGE_FIELD = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr td:nth-child(1)")
    """变更字段列"""

    COL_OLD_VALUE = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr td:nth-child(2)")
    """原值列"""

    COL_NEW_VALUE = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr td:nth-child(3)")
    """新值列"""

    COL_CHANGE_TIME = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr td:nth-child(4)")
    """变更时间列"""

    COL_OPERATOR = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr td:nth-child(5)")
    """操作人列"""

    # ==================== 分页定位器 ====================
    PAGINATION = (By.CSS_SELECTOR, ".table-wrapper .el-pagination")
    """分页组件"""

    # ==================== 编辑基本信息弹窗定位器 ====================
    EDIT_INFO_DIALOG = (By.XPATH, "//div[@role='dialog' and .//span[text()='编辑基本信息']]")
    """编辑基本信息弹窗主体"""

    DIALOG_NAME_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='编辑基本信息'] .el-form-item:nth-child(1) input")
    """弹窗-姓名输入框"""

    DIALOG_DEPARTMENT_SELECT = (By.CSS_SELECTOR, ".el-dialog[aria-label='编辑基本信息'] .el-form-item:nth-child(2) .el-select")
    """弹窗-部门选择器"""

    DIALOG_DEPARTMENT_OPTION = (By.XPATH, "//div[@class='el-select-dropdown' and not(contains(@style, 'display: none'))]//span[text()='{}']")
    """弹窗-部门选项 (动态参数，使用format()填充)"""

    DIALOG_POSITION_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='编辑基本信息'] .el-form-item:nth-child(3) input")
    """弹窗-职位输入框"""

    DIALOG_PHONE_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='编辑基本信息'] .el-form-item:nth-child(4) input")
    """弹窗-手机号输入框"""

    DIALOG_EMAIL_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='编辑基本信息'] .el-form-item:nth-child(5) input")
    """弹窗-邮箱输入框"""

    DIALOG_SAVE_BTN = (By.CSS_SELECTOR, ".el-dialog[aria-label='编辑基本信息'] .el-button--primary")
    """弹窗-保存按钮"""

    DIALOG_CANCEL_BTN = (By.XPATH, "//div[@role='dialog' and .//span[text()='编辑基本信息']]//button[.//span[text()='取消']]")
    """弹窗-取消按钮"""

    # ==================== 修改密码弹窗定位器 ====================
    PASSWORD_DIALOG = (By.XPATH, "//div[@role='dialog' and .//span[text()='修改密码']]")
    """修改密码弹窗主体"""

    DIALOG_OLD_PASSWORD_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='修改密码'] .el-form-item:nth-child(1) input")
    """弹窗-旧密码输入框"""

    DIALOG_NEW_PASSWORD_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='修改密码'] .el-form-item:nth-child(2) input")
    """弹窗-新密码输入框"""

    DIALOG_CONFIRM_PASSWORD_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='修改密码'] .el-form-item:nth-child(3) input")
    """弹窗-确认新密码输入框"""

    DIALOG_PASSWORD_SUBMIT_BTN = (By.XPATH, "//div[@role='dialog' and .//span[text()='修改密码']]//button[.//span[text()='提交']]")
    """弹窗-提交按钮"""

    DIALOG_PASSWORD_CANCEL_BTN = (By.XPATH, "//div[@role='dialog' and .//span[text()='修改密码']]//button[.//span[text()='取消']]")
    """弹窗-取消按钮"""

    # ==================== 导航方法 ====================

    def navigate(self):
        """JS hash 导航到我的档案页面（SPA 内无刷新）"""
        logger.info("导航到: 我的档案")
        self.driver.execute_script("window.location.hash = '#/personnel/training/my-archive'")
        self.wait_vue_stable()
        try:
            self.wait_page_ready(self.CHANGE_TABLE)
        except Exception:
            pass
        return self

    # ==================== Tab切换 ====================

    def switch_to_basic_info_tab(self):
        """切换到个人基本信息 Tab"""
        logger.info("切换到个人基本信息Tab")
        self.do_click(self.BASIC_INFO_TAB)
        self.wait_vue_stable()
        return self

    def switch_to_certificate_tab(self):
        """切换到证件信息 Tab"""
        logger.info("切换到证件信息Tab")
        self.do_click(self.CERTIFICATE_TAB)
        self.wait_vue_stable()
        return self

    def switch_to_contact_tab(self):
        """切换到联系方式 Tab"""
        logger.info("切换到联系方式Tab")
        self.do_click(self.CONTACT_TAB)
        self.wait_vue_stable()
        return self

    def switch_to_archive_tab(self):
        """切换到档案变更记录 Tab"""
        logger.info("切换到档案变更记录Tab")
        self.do_click(self.ARCHIVE_TAB)
        self.wait_vue_stable()
        return self

    # ==================== 侧边栏操作 ====================

    def click_edit_profile(self):
        """点击侧边栏的编辑资料按钮"""
        logger.info("点击编辑资料按钮")
        self.do_click(self.SIDEBAR_EDIT_PROFILE_BTN)
        self.wait_vue_stable()
        return self

    def click_change_password(self):
        """点击侧边栏的修改密码按钮"""
        logger.info("点击修改密码按钮")
        self.do_click(self.SIDEBAR_CHANGE_PASSWORD_BTN)
        self.wait_vue_stable()
        return self

    # ==================== 基本信息 Tab 操作 ====================

    def get_basic_info_value(self, field_locator):
        """获取基本信息展示表单中某个字段的值"""
        element = self.wait_element_visible(field_locator)
        value = element.get_attribute('value')
        logger.info(f"获取基本信息字段值: {value}")
        return value

    def click_edit_basic_info(self):
        """点击编辑基本信息按钮"""
        logger.info("点击编辑基本信息按钮")
        self.do_click(self.EDIT_BASIC_INFO_BTN)
        self.wait_dialog_visible(self.EDIT_INFO_DIALOG)
        return self

    # ==================== 档案变更记录Tab - 筛选操作 ====================

    def select_change_type(self, option_text):
        """
        选择变更类型筛选
        :param option_text: 选项文本（新增/修改/删除）
        """
        logger.info(f"选择变更类型: {option_text}")
        # # 步骤1: 点击下拉框触发
        self.do_click(self.CHANGE_TYPE_SELECTOR)
        # # 步骤2: 根据文本选择对应选项
        option_locator = (By.XPATH, f"//div[@class='el-select-dropdown' and not(contains(@style, 'display: none'))]//li//span[text()='{option_text}']")
        self.wait_element_visible(option_locator)
        self.do_click(option_locator)
        self.wait_vue_stable()
        return self

    def input_change_date_range(self, start_date, end_date):
        """
        输入变更日期范围
        :param start_date: 开始日期，格式 'YYYY-MM-DD'
        :param end_date: 结束日期，格式 'YYYY-MM-DD'
        """
        logger.info(f"输入变更日期范围: {start_date} ~ {end_date}")
        date_input = self.wait_element_clickable(self.CHANGE_DATE_PICKER)
        self.do_click(date_input)
        # # 使用键盘操作清空并输入日期（Element Plus 日期选择器逻辑）
        date_input.send_keys(Keys.CONTROL, 'a')
        date_input.send_keys(Keys.BACKSPACE)
        date_input.send_keys(f"{start_date} ~ {end_date}")
        date_input.send_keys(Keys.ENTER)
        self.wait_vue_stable()
        return self

    def click_search(self):
        """点击查询按钮"""
        logger.info("点击查询按钮")
        self.do_click(self.SEARCH_BTN)
        self.wait_table_loaded(self.CHANGE_TABLE)
        return self

    def click_reset(self):
        """点击重置按钮"""
        logger.info("点击重置按钮")
        self.do_click(self.RESET_BTN)
        self.wait_vue_stable()
        return self

    # ==================== 档案变更记录Tab - 表格数据提取 ====================

    def get_table_row_data(self, row_index=0):
        """
        获取表格指定行的数据
        :param row_index: 行索引，从0开始
        :return: dict, 包含列字段名和值的映射
        """
        rows = self.wait_elements_visible(self.TABLE_ROWS)
        if row_index >= len(rows):
            logger.warning(f"请求的行索引 {row_index} 超出表格行数 {len(rows)}")
            return None

        row = rows[row_index]
        cells = row.find_elements(By.CSS_SELECTOR, "td")
        data = {
            "变更字段": cells[0].text,
            "原值": cells[1].text,
            "新值": cells[2].text,
            "变更时间": cells[3].text,
            "操作人": cells[4].text
        }
        logger.info(f"获取第 {row_index+1} 行数据: {data}")
        return data

    def get_all_table_data(self):
        """获取表格所有行数据"""
        rows = self.wait_elements_visible(self.TABLE_ROWS)
        data_list = []
        for i, row in enumerate(rows):
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            data_list.append({
                "变更字段": cells[0].text,
                "原值": cells[1].text,
                "新值": cells[2].text,
                "变更时间": cells[3].text,
                "操作人": cells[4].text
            })
        logger.info(f"获取表格数据，共 {len(data_list)} 行")
        return data_list

    # ==================== 分页操作 ====================

    def get_pagination_info(self):
        """获取分页信息"""
        # 使用BasePage封装的get_pagination_info方法
        return super().get_pagination_info(self.PAGINATION)

    def go_to_page(self, page_number):
        """跳转到指定页码"""
        logger.info(f"跳转到第 {page_number} 页")
        page_btn = (By.XPATH, f"//ul[contains(@class, 'el-pager')]//li[text()='{page_number}']")
        self.do_click(page_btn)
        self.wait_table_loaded(self.CHANGE_TABLE)
        return self

    # ==================== 编辑基本信息弹窗操作 ====================

    def fill_edit_info_dialog(self, data_dict):
        """
        填写编辑基本信息弹窗
        :param data_dict: 字典，包含字段名和值
              例: {'姓名': '张三', '部门': '技术部', '职位': '工程师', '手机号': '13800138000', '邮箱': 'zhangsan@test.com'}
        """
        logger.info(f"填写编辑基本信息弹窗: {data_dict}")
        if '姓名' in data_dict:
            self.do_input(self.DIALOG_NAME_INPUT, data_dict['姓名'])
        if '部门' in data_dict:
            self.do_click(self.DIALOG_DEPARTMENT_SELECT)
            option_locator = (self.DIALOG_DEPARTMENT_OPTION[0], self.DIALOG_DEPARTMENT_OPTION[1].format(data_dict['部门']))
            self.wait_element_visible(option_locator)
            self.do_click(option_locator)
        if '职位' in data_dict:
            self.do_input(self.DIALOG_POSITION_INPUT, data_dict['职位'])
        if '手机号' in data_dict:
            self.do_input(self.DIALOG_PHONE_INPUT, data_dict['手机号'])
        if '邮箱' in data_dict:
            self.do_input(self.DIALOG_EMAIL_INPUT, data_dict['邮箱'])
        return self

    def save_edit_info(self):
        """点击编辑基本信息弹窗的保存按钮"""
        logger.info("保存编辑基本信息弹窗")
        self.do_click(self.DIALOG_SAVE_BTN)
        self.wait_dialog_closed(self.EDIT_INFO_DIALOG)
        self.wait_vue_stable()
        self.log_toast("保存成功")  # 使用BasePage的日志方法记录toast
        return self

    def cancel_edit_info(self):
        """点击编辑基本信息弹窗的取消按钮"""
        logger.info("取消编辑基本信息弹窗")
        self.do_click(self.DIALOG_CANCEL_BTN)
        self.wait_dialog_closed(self.EDIT_INFO_DIALOG)
        return self

    # ==================== 修改密码弹窗操作 ====================

    def fill_password_dialog(self, old_password, new_password):
        """
        填写修改密码弹窗
        :param old_password: 旧密码
        :param new_password: 新密码
        """
        logger.info("填写修改密码弹窗")
        self.do_input(self.DIALOG_OLD_PASSWORD_INPUT, old_password)
        self.do_input(self.DIALOG_NEW_PASSWORD_INPUT, new_password)
        self.do_input(self.DIALOG_CONFIRM_PASSWORD_INPUT, new_password)
        return self

    def submit_password_change(self):
        """点击修改密码弹窗的提交按钮"""
        logger.info("提交修改密码")
        self.do_click(self.DIALOG_PASSWORD_SUBMIT_BTN)
        self.wait_dialog_closed(self.PASSWORD_DIALOG)
        self.wait_vue_stable()
        self.log_toast("密码修改成功")
        return self

    def cancel_password_change(self):
        """点击修改密码弹窗的取消按钮"""
        logger.info("取消修改密码")
        self.do_click(self.DIALOG_PASSWORD_CANCEL_BTN)
        self.wait_dialog_closed(self.PASSWORD_DIALOG)
        return self

    # ==================== 组合操作 ====================

    def search_archive_records(self, change_type=None, start_date=None, end_date=None):
        """
        组合操作：在档案变更记录Tab下执行完整搜索流程
        :param change_type: 变更类型
        :param start_date: 开始日期
        :param end_date: 结束日期
        """
        self.switch_to_archive_tab()
        if change_type:
            self.select_change_type(change_type)
        if start_date and end_date:
            self.input_change_date_range(start_date, end_date)
        self.click_search()
        return self

    def update_basic_info(self, data_dict):
        """
        组合操作：更新个人基本信息
        :param data_dict: 包含要更新的字段和值的字典
        """
        self.switch_to_basic_info_tab()
        self.click_edit_basic_info()
        self.fill_edit_info_dialog(data_dict)
        self.save_edit_info()
        return self

    def change_password(self, old_password, new_password):
        """
        组合操作：修改登录密码
        :param old_password: 旧密码
        :param new_password: 新密码
        """
        self.click_change_password()
        self.wait_dialog_visible(self.PASSWORD_DIALOG)
        self.fill_password_dialog(old_password, new_password)
        self.submit_password_change()
        return self