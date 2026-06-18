# -*- coding: utf-8 -*-
"""
我的档案页面 Page Object
Module: personnel
Page: my-archive

基于 PAGE_CONTEXT.md 元素清单生成

==== 页面结构 ====
1. Tab栏：个人基本信息（默认激活）、证件信息、联系方式、档案变更记录
2. 侧边栏：个人头像 + 编辑资料、修改密码快捷入口
3. 档案变更记录Tab内：筛选区（变更类型、日期范围、查询/重置按钮） + 表格 + 分页
4. 弹窗：编辑基本信息弹窗、修改密码弹窗
"""

from base.base_page import BasePage
from selenium.webdriver.common.by import By


class MyArchivePage(BasePage):
    """
    我的档案页面类
    继承BasePage，封装页面元素定位与操作方法
    """

    # ==================== Tab栏定位器 ====================
    BASIC_INFO_TAB = (By.CSS_SELECTOR, ".el-tabs .el-tab-pane:first-child")
    """基本信息Tab - 默认激活"""

    CERTIFICATE_TAB = (By.CSS_SELECTOR, ".el-tabs .el-tab-pane:nth-child(2)")
    """证件信息Tab"""

    CONTACT_TAB = (By.CSS_SELECTOR, ".el-tabs .el-tab-pane:nth-child(3)")
    """联系方式Tab"""

    ARCHIVE_TAB = (By.CSS_SELECTOR, ".el-tabs .el-tab-pane:nth-child(4)")
    """档案变更记录Tab"""

    # ==================== 侧边栏定位器 ====================
    SIDEBAR_AVATAR = (By.CSS_SELECTOR, ".sidebar .avatar")
    """个人头像区域"""

    SIDEBAR_EDIT_PROFILE_BTN = (By.XPATH, "//aside//button[.//span[text()='编辑资料']]")
    """编辑资料快捷入口按钮"""

    SIDEBAR_CHANGE_PASSWORD_BTN = (By.XPATH, "//aside//button[.//span[text()='修改密码']]")
    """修改密码快捷入口按钮"""

    # ==================== 基本信息Tab定位器 ====================
    BASIC_INFO_FORM = (By.CSS_SELECTOR, ".el-form.basic-info-form")
    """基本信息展示表单（只读模式）"""

    FIELD_EMPLOYEE_NAME = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:first-child input")
    """员工姓名输入框（只读）"""

    FIELD_DEPARTMENT = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:nth-child(2) input")
    """部门输入框（只读）"""

    FIELD_POSITION = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:nth-child(3) input")
    """职位输入框（只读）"""

    FIELD_PHONE = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:nth-child(4) input")
    """手机号输入框（只读，隐藏中间4位）"""

    FIELD_EMAIL = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-input:nth-child(5) input")
    """邮箱输入框（只读，显示完整邮箱）"""

    EDIT_BASIC_INFO_BTN = (By.CSS_SELECTOR, ".el-form.basic-info-form .el-button--primary")
    """编辑基本信息按钮"""

    # ==================== 档案变更记录Tab - 筛选区定位器 ====================
    CHANGE_TYPE_SELECT = (By.CSS_SELECTOR, ".search-wrapper .el-select")
    """变更类型筛选下拉框"""

    CHANGE_TYPE_OPTION_NEW = (By.XPATH, "//div[@class='el-select-dropdown']//span[text()='新增']")
    """变更类型选项：新增"""

    CHANGE_TYPE_OPTION_MODIFY = (By.XPATH, "//div[@class='el-select-dropdown']//span[text()='修改']")
    """变更类型选项：修改"""

    CHANGE_TYPE_OPTION_DELETE = (By.XPATH, "//div[@class='el-select-dropdown']//span[text()='删除']")
    """变更类型选项：删除"""

    CHANGE_DATE_PICKER = (By.CSS_SELECTOR, ".search-wrapper .el-date-editor--daterange input")
    """变更日期范围选择器"""

    SEARCH_BTN = (By.XPATH, "//div[@class='search-wrapper']//button[.//span[text()='查询']]")
    """查询按钮"""

    RESET_BTN = (By.XPATH, "//div[@class='search-wrapper']//button[.//span[text()='重置']]")
    """重置按钮"""

    # ==================== 档案变更记录Tab - 表格定位器 ====================
    CHANGE_TABLE = (By.CSS_SELECTOR, ".table-wrapper .el-table")
    """变更记录表格"""

    TABLE_LOADING = (By.CSS_SELECTOR, ".table-wrapper .el-loading-mask")
    """表格加载遮罩层"""

    TABLE_ROWS = (By.CSS_SELECTOR, ".table-wrapper .el-table__body-wrapper tbody tr")
    """表格数据行（使用BasePage通用定位器TABLE_ROWS保持一致性，此处保留原样式）"""

    # 表格行以BasePage通用定位器为主
    # self.TABLE_ROWS 已在BasePage中定义，使用 (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")

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
    """编辑基本信息弹窗"""

    DIALOG_NAME_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='编辑基本信息'] .el-form-item:nth-child(1) input")
    """弹窗-姓名输入框"""

    DIALOG_DEPARTMENT_SELECT = (By.CSS_SELECTOR, ".el-dialog[aria-label='编辑基本信息'] .el-form-item:nth-child(2) .el-select")
    """弹窗-部门选择器"""

    DIALOG_DEPARTMENT_DROPDOWN = (By.CSS_SELECTOR, ".el-select-dropdown")
    """部门选择器下拉菜单"""

    DIALOG_DEPARTMENT_OPTIONS = (By.CSS_SELECTOR, ".el-select-dropdown .el-select-dropdown__item")
    """部门选择器选项列表"""

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
    """修改密码弹窗"""

    DIALOG_OLD_PASSWORD_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='修改密码'] .el-form-item:nth-child(1) input")
    """弹窗-旧密码输入框"""

    DIALOG_NEW_PASSWORD_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='修改密码'] .el-form-item:nth-child(2) input")
    """弹窗-新密码输入框"""

    DIALOG_CONFIRM_PASSWORD_INPUT = (By.CSS_SELECTOR, ".el-dialog[aria-label='修改密码'] .el-form-item:nth-child(3) input")
    """弹窗-确认新密码输入框"""

    PASSWORD_DIALOG_SAVE_BTN = (By.CSS_SELECTOR, ".el-dialog[aria-label='修改密码'] .el-button--primary")
    """弹窗-保存按钮"""

    PASSWORD_DIALOG_CANCEL_BTN = (By.XPATH, "//div[@role='dialog' and .//span[text()='修改密码']]//button[.//span[text()='取消']]")
    """弹窗-取消按钮"""

    # ==================== Toast消息提示定位器（复用基类通用定位器）====================
    # 使用 BasePage 中的 TOAST / TOAST_MESSAGE 通用定位器

    def navigate(self) -> "MyArchivePage":
        """
        导航到我的档案页面

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("导航到我的档案页面")
        self.navigate_to("人员管理", "我的档案")
        self.wait_vue_stable()
        self.logger.info("我的档案页面加载完成")
        return self

    def switch_to_basic_info_tab(self) -> "MyArchivePage":
        """
        切换到个人基本信息Tab

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("切换到个人基本信息Tab")
        self.wait_element_visible(self.BASIC_INFO_TAB)
        self.click(self.BASIC_INFO_TAB)
        self.wait_vue_stable()
        return self

    def switch_to_certificate_tab(self) -> "MyArchivePage":
        """
        切换到证件信息Tab

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("切换到证件信息Tab")
        self.wait_element_visible(self.CERTIFICATE_TAB)
        self.click(self.CERTIFICATE_TAB)
        self.wait_vue_stable()
        return self

    def switch_to_contact_tab(self) -> "MyArchivePage":
        """
        切换到联系方式Tab

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("切换到联系方式Tab")
        self.wait_element_visible(self.CONTACT_TAB)
        self.click(self.CONTACT_TAB)
        self.wait_vue_stable()
        return self

    def switch_to_archive_tab(self) -> "MyArchivePage":
        """
        切换到档案变更记录Tab
        切换后将显示筛选区和变更记录表格

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("切换到档案变更记录Tab")
        self.wait_element_visible(self.ARCHIVE_TAB)
        self.click(self.ARCHIVE_TAB)
        self.wait_vue_stable()
        return self

    def click_edit_basic_info(self) -> "MyArchivePage":
        """
        点击编辑基本信息按钮，打开编辑弹窗

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击编辑基本信息按钮")
        self.wait_element_clickable(self.EDIT_BASIC_INFO_BTN)
        self.scroll_to_element(self.EDIT_BASIC_INFO_BTN)
        self.click(self.EDIT_BASIC_INFO_BTN)
        self.wait_vue_stable()
        return self

    def click_sidebar_edit_profile(self) -> "MyArchivePage":
        """
        点击侧边栏编辑资料快捷入口

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击侧边栏编辑资料快捷入口")
        self.wait_element_clickable(self.SIDEBAR_EDIT_PROFILE_BTN)
        self.click(self.SIDEBAR_EDIT_PROFILE_BTN)
        self.wait_vue_stable()
        return self

    def click_sidebar_change_password(self) -> "MyArchivePage":
        """
        点击侧边栏修改密码快捷入口，打开修改密码弹窗

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击侧边栏修改密码快捷入口")
        self.wait_element_clickable(self.SIDEBAR_CHANGE_PASSWORD_BTN)
        self.click(self.SIDEBAR_CHANGE_PASSWORD_BTN)
        self.wait_vue_stable()
        return self

    # ==================== 编辑基本信息弹窗方法 ====================

    def is_edit_dialog_visible(self) -> bool:
        """
        检查编辑基本信息弹窗是否可见

        Returns:
            bool: 弹窗可见返回True，否则返回False
        """
        return self.is_element_visible(self.EDIT_INFO_DIALOG)

    def fill_edit_dialog_name(self, name: str) -> "MyArchivePage":
        """
        在编辑基本信息弹窗中填写姓名

        Args:
            name: 姓名

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"填写姓名: {name}")
        self.wait_element_visible(self.DIALOG_NAME_INPUT)
        self.clear_input(self.DIALOG_NAME_INPUT)
        self.send_keys(self.DIALOG_NAME_INPUT, name)
        return self

    def select_dialog_department(self, department_name: str) -> "MyArchivePage":
        """
        在编辑基本信息弹窗中选择部门

        Args:
            department_name: 部门名称（如"技术部"）

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"选择部门: {department_name}")
        # 点击部门选择器展开下拉
        self.wait_element_clickable(self.DIALOG_DEPARTMENT_SELECT)
        self.click(self.DIALOG_DEPARTMENT_SELECT)
        # 等待下拉菜单出现
        self.wait_element_visible(self.DIALOG_DEPARTMENT_DROPDOWN)
        # 构造目标部门选项定位器
        dept_option = (
            By.XPATH,
            f"//div[contains(@class, 'el-select-dropdown') and not(contains(@style, 'display: none'))]"
            f"//span[text()='{department_name}']"
        )
        self.wait_element_clickable(dept_option)
        self.click(dept_option)
        return self

    def fill_edit_dialog_position(self, position: str) -> "MyArchivePage":
        """
        在编辑基本信息弹窗中填写职位

        Args:
            position: 职位

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"填写职位: {position}")
        self.wait_element_visible(self.DIALOG_POSITION_INPUT)
        self.clear_input(self.DIALOG_POSITION_INPUT)
        self.send_keys(self.DIALOG_POSITION_INPUT, position)
        return self

    def fill_edit_dialog_phone(self, phone: str) -> "MyArchivePage":
        """
        在编辑基本信息弹窗中填写手机号

        Args:
            phone: 手机号

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"填写手机号: {phone}")
        self.wait_element_visible(self.DIALOG_PHONE_INPUT)
        self.clear_input(self.DIALOG_PHONE_INPUT)
        self.send_keys(self.DIALOG_PHONE_INPUT, phone)
        return self

    def fill_edit_dialog_email(self, email: str) -> "MyArchivePage":
        """
        在编辑基本信息弹窗中填写邮箱

        Args:
            email: 邮箱

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"填写邮箱: {email}")
        self.wait_element_visible(self.DIALOG_EMAIL_INPUT)
        self.clear_input(self.DIALOG_EMAIL_INPUT)
        self.send_keys(self.DIALOG_EMAIL_INPUT, email)
        return self

    def fill_edit_dialog(self, data: dict) -> "MyArchivePage":
        """
        在编辑基本信息弹窗中填写所有字段

        Args:
            data: 字典，含以下可选键值对：
                - name: str
                - department: str
                - position: str
                - phone: str
                - email: str

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"填写编辑基本信息弹窗表单: {data}")
        if "name" in data:
            self.fill_edit_dialog_name(data["name"])
        if "department" in data:
            self.select_dialog_department(data["department"])
        if "position" in data:
            self.fill_edit_dialog_position(data["position"])
        if "phone" in data:
            self.fill_edit_dialog_phone(data["phone"])
        if "email" in data:
            self.fill_edit_dialog_email(data["email"])
        return self

    def click_dialog_save(self) -> "MyArchivePage":
        """
        点击编辑基本信息弹窗的保存按钮

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击编辑基本信息弹窗保存按钮")
        self.wait_element_clickable(self.DIALOG_SAVE_BTN)
        self.click(self.DIALOG_SAVE_BTN)
        self.wait_vue_stable()
        return self

    def click_dialog_cancel(self) -> "MyArchivePage":
        """
        点击编辑基本信息弹窗的取消按钮

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击编辑基本信息弹窗取消按钮")
        self.wait_element_clickable(self.DIALOG_CANCEL_BTN)
        self.click(self.DIALOG_CANCEL_BTN)
        self.wait_vue_stable()
        return self

    # ==================== 修改密码弹窗方法 ====================

    def is_password_dialog_visible(self) -> bool:
        """
        检查修改密码弹窗是否可见

        Returns:
            bool: 弹窗可见返回True，否则返回False
        """
        return self.is_element_visible(self.PASSWORD_DIALOG)

    def fill_password_dialog_old_password(self, old_password: str) -> "MyArchivePage":
        """
        在修改密码弹窗中填写旧密码

        Args:
            old_password: 旧密码

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("填写旧密码")
        self.wait_element_visible(self.DIALOG_OLD_PASSWORD_INPUT)
        self.clear_input(self.DIALOG_OLD_PASSWORD_INPUT)
        self.send_keys(self.DIALOG_OLD_PASSWORD_INPUT, old_password)
        return self

    def fill_password_dialog_new_password(self, new_password: str) -> "MyArchivePage":
        """
        在修改密码弹窗中填写新密码

        Args:
            new_password: 新密码

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("填写新密码")
        self.wait_element_visible(self.DIALOG_NEW_PASSWORD_INPUT)
        self.clear_input(self.DIALOG_NEW_PASSWORD_INPUT)
        self.send_keys(self.DIALOG_NEW_PASSWORD_INPUT, new_password)
        return self

    def fill_password_dialog_confirm_password(self, confirm_password: str) -> "MyArchivePage":
        """
        在修改密码弹窗中填写确认密码

        Args:
            confirm_password: 确认密码

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("填写确认密码")
        self.wait_element_visible(self.DIALOG_CONFIRM_PASSWORD_INPUT)
        self.clear_input(self.DIALOG_CONFIRM_PASSWORD_INPUT)
        self.send_keys(self.DIALOG_CONFIRM_PASSWORD_INPUT, confirm_password)
        return self

    def fill_password_dialog(self, data: dict) -> "MyArchivePage":
        """
        在修改密码弹窗中填写所有字段

        Args:
            data: 字典，包含：
                - old_password: str（必填）
                - new_password: str（必填）
                - confirm_password: str（必填）

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("填写修改密码弹窗表单")
        if "old_password" in data:
            self.fill_password_dialog_old_password(data["old_password"])
        if "new_password" in data:
            self.fill_password_dialog_new_password(data["new_password"])
        if "confirm_password" in data:
            self.fill_password_dialog_confirm_password(data["confirm_password"])
        return self

    def click_password_dialog_save(self) -> "MyArchivePage":
        """
        点击修改密码弹窗的保存按钮

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击修改密码弹窗保存按钮")
        self.wait_element_clickable(self.PASSWORD_DIALOG_SAVE_BTN)
        self.click(self.PASSWORD_DIALOG_SAVE_BTN)
        self.wait_vue_stable()
        return self

    def click_password_dialog_cancel(self) -> "MyArchivePage":
        """
        点击修改密码弹窗的取消按钮

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击修改密码弹窗取消按钮")
        self.wait_element_clickable(self.PASSWORD_DIALOG_CANCEL_BTN)
        self.click(self.PASSWORD_DIALOG_CANCEL_BTN)
        self.wait_vue_stable()
        return self

    # ==================== 档案变更记录查询方法 ====================

    def select_change_type(self, change_type: str) -> "MyArchivePage":
        """
        选择变更类型筛选条件

        Args:
            change_type: 变更类型，可选值: "新增", "修改", "删除"

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"选择变更类型：{change_type}")
        self.wait_element_clickable(self.CHANGE_TYPE_SELECT)
        self.click(self.CHANGE_TYPE_SELECT)
        self.wait_vue_stable()

        # 根据传入的文本选择对应选项
        option_locator = (
            By.XPATH,
            f"//div[@class='el-select-dropdown']//span[text()='{change_type}']"
        )
        self.wait_element_clickable(option_locator)
        self.click(option_locator)
        return self

    def select_change_date_range(self, start_date: str, end_date: str) -> "MyArchivePage":
        """
        选择变更日期范围

        Args:
            start_date: 开始日期，格式: "2026-01-01"
            end_date: 结束日期，格式: "2026-12-31"

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"选择变更日期范围：{start_date} ~ {end_date}")
        self.wait_element_clickable(self.CHANGE_DATE_PICKER)
        self.click(self.CHANGE_DATE_PICKER)
        self.wait_vue_stable()

        # 实现日期范围选择
        self.send_keys(self.CHANGE_DATE_PICKER, start_date)
        self.send_keys(self.CHANGE_DATE_PICKER, end_date)
        # 模拟按下回车确认
        from selenium.webdriver.common.keys import Keys
        self.send_keys(self.CHANGE_DATE_PICKER, Keys.ENTER)
        self.wait_vue_stable()
        return self

    def click_search(self) -> "MyArchivePage":
        """
        点击查询按钮，执行筛选查询

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击查询按钮执行查询")
        self.wait_element_clickable(self.SEARCH_BTN)
        self.click(self.SEARCH_BTN)
        self.wait_vue_stable()
        self.wait_table_loaded()
        return self

    def click_reset(self) -> "MyArchivePage":
        """
        点击重置按钮，清空筛选条件并重新加载数据

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击重置按钮")
        self.wait_element_clickable(self.RESET_BTN)
        self.click(self.RESET_BTN)
        self.wait_vue_stable()
        self.wait_table_loaded()
        return self

    # ==================== 表格相关方法 ====================

    def wait_table_loaded(self) -> "MyArchivePage":
        """
        等待表格数据加载完成（等待加载遮罩层消失）

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.debug("等待表格数据加载完成")
        self.wait_element_hidden(self.TABLE_LOADING, timeout=10)
        return self

    def get_table_row_count(self) -> int:
        """
        获取表格当前行数

        Returns:
            int: 表格行数
        """
        self.logger.debug("获取表格行数")
        # 使用BasePage通用定位器获取表格行
        rows = self.find_elements(self.TABLE_ROWS)
        count = len(rows)
        self.logger.info(f"表格行数: {count}")
        return count

    def get_table_data(self) -> list[dict]:
        """
        获取表格全部数据

        Returns:
            list[dict]: 表格数据列表，每个字典含：
                - field: str（变更字段）
                - old_value: str（原值）
                - new_value: str（新值）
                - change_time: str（变更时间）
                - operator: str（操作人）
        """
        self.logger.info("获取表格数据")
        self.wait_table_loaded()

        rows = self.find_elements(self.TABLE_ROWS)
        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 5:
                data.append({
                    "field": cells[0].text.strip(),
                    "old_value": cells[1].text.strip(),
                    "new_value": cells[2].text.strip(),
                    "change_time": cells[3].text.strip(),
                    "operator": cells[4].text.strip(),
                })
        self.logger.info(f"获取到 {len(data)} 条记录")
        return data

    def get_table_row_data(self, row_index: int) -> dict:
        """
        获取指定行的表格数据

        Args:
            row_index: 行索引（从0开始）

        Returns:
            dict: 表格行数据，含：
                - field: str
                - old_value: str
                - new_value: str
                - change_time: str
                - operator: str

        Raises:
            IndexError: 如果行索引超出范围
        """
        self.logger.info(f"获取第{row_index + 1}行数据")
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index >= len(rows):
            error_msg = f"行索引 {row_index} 超出范围，总行数 {len(rows)}"
            self.logger.error(error_msg)
            raise IndexError(error_msg)

        cells = rows[row_index].find_elements(By.TAG_NAME, "td")
        return {
            "field": cells[0].text.strip(),
            "old_value": cells[1].text.strip(),
            "new_value": cells[2].text.strip(),
            "change_time": cells[3].text.strip(),
            "operator": cells[4].text.strip(),
        }

    def get_table_column_data(self, column_locator: tuple) -> list:
        """
        获取指定列的所有数据（内部方法）

        Args:
            column_locator: 列定位器元组

        Returns:
            list: 该列所有单元格的文本列表
        """
        elements = self.find_elements(column_locator)
        return [el.text.strip() for el in elements]

    def get_field_column_data(self) -> list:
        """获取变更字段列所有数据"""
        return self.get_table_column_data(self.COL_CHANGE_FIELD)

    def get_old_value_column_data(self) -> list:
        """获取原值列所有数据"""
        return self.get_table_column_data(self.COL_OLD_VALUE)

    def get_new_value_column_data(self) -> list:
        """获取新值列所有数据"""
        return self.get_table_column_data(self.COL_NEW_VALUE)

    def get_change_time_column_data(self) -> list:
        """获取变更时间列所有数据"""
        return self.get_table_column_data(self.COL_CHANGE_TIME)

    def get_operator_column_data(self) -> list:
        """获取操作人列所有数据"""
        return self.get_table_column_data(self.COL_OPERATOR)

    # ==================== 分页相关方法 ====================

    def get_pagination_info(self) -> dict:
        """
        获取分页信息

        Returns:
            dict: 分页信息，含：
                - current_page: int
                - total: int
                - page_size: int
        """
        self.logger.info("获取分页信息")
        # 使用BasePage通用分页组件定位器
        pagination_el = self.wait_element_visible(self.PAGINATION)

        # 获取分页文本，如 "共 100 条"
        total_text = pagination_el.find_element(
            By.CSS_SELECTOR, ".el-pagination__total"
        ).text
        total = int(''.join(filter(str.isdigit, total_text)))

        # 获取当前页
        active_page = pagination_el.find_element(
            By.CSS_SELECTOR, ".el-pager .number.active"
        )
        current_page = int(active_page.text)

        # 获取每页条数
        page_size_dropdown = pagination_el.find_element(
            By.CSS_SELECTOR, ".el-pagination__sizes .el-select .el-input__inner"
        )
        page_size_text = page_size_dropdown.get_attribute("value")
        page_size = int(page_size_text) if page_size_text else 10

        info = {
            "current_page": current_page,
            "total": total,
            "page_size": page_size,
        }
        self.logger.info(f"分页信息: {info}")
        return info

    def go_to_page(self, page_number: int) -> "MyArchivePage":
        """
        跳转到指定页码

        Args:
            page_number: 目标页码

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"跳转到第{page_number}页")
        page_btn = (
            By.XPATH,
            f"//ul[contains(@class, 'el-pager')]//li[text()='{page_number}']"
        )
        self.wait_element_clickable(page_btn)
        self.click(page_btn)
        self.wait_vue_stable()
        self.wait_table_loaded()
        return self

    def click_next_page(self) -> "MyArchivePage":
        """
        点击下一页按钮

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击下一页")
        next_btn = (By.CSS_SELECTOR, ".el-pagination .btn-next")
        self.wait_element_clickable(next_btn)
        self.click(next_btn)
        self.wait_vue_stable()
        self.wait_table_loaded()
        return self

    def click_prev_page(self) -> "MyArchivePage":
        """
        点击上一页按钮

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info("点击上一页")
        prev_btn = (By.CSS_SELECTOR, ".el-pagination .btn-prev")
        self.wait_element_clickable(prev_btn)
        self.click(prev_btn)
        self.wait_vue_stable()
        self.wait_table_loaded()
        return self

    def set_page_size(self, page_size: int) -> "MyArchivePage":
        """
        设置每页显示条数

        Args:
            page_size: 每页条数（如 10, 20, 50, 100）

        Returns:
            MyArchivePage: 返回自身以支持链式调用
        """
        self.logger.info(f"设置每页显示 {page_size} 条")
        page_size_trigger = (By.CSS_SELECTOR, ".el-pagination__sizes .el-select .el-input__inner")
        self.wait_element_clickable(page_size_trigger)
        self.click(page_size_trigger)
        self.wait_vue_stable()

        option_locator = (
            By.XPATH,
            f"//div[@class='el-select-dropdown']//span[text()='{page_size}条/页']"
        )
        self.wait_element_clickable(option_locator)
        self.click(option_locator)
        self.wait_vue_stable()
        self.wait_table_loaded()
        return self


# ====== 代码自检报告 ======
# [PASS] 继承 BasePage
# [PASS] 无绝对 XPath
# [PASS] 无 time.sleep
# [PASS] 无 print()
# [PASS] 有 navigate()
# ========================