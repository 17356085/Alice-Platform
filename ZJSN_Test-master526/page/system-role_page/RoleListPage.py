# filename: page/system_role_page/role_list_page.py
"""
角色列表页面 Page Object
模块: system-role
页面: role-list

变更记录:
  2026-06-11: 初始化创建，遵循 page-object-generator 规范
"""
from selenium.webdriver.common.by import By

from base.base_page import BasePage


class RoleListPage(BasePage):
    """
    角色列表页面对象
    提供角色管理页面的所有可操作元素和方法。
    """

    # ==================== Locator 定义 ====================
    # --- 搜索区 ---
    # 角色名称输入框: 使用 placeholder 属性定位
    SEARCH_ROLE_NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder*='角色名称']")
    # 状态筛选下拉框: 点击展开选项列表。由于 el-select 结构复杂，使用 XPath 定位包裹它的类，更稳定
    SEARCH_STATUS_SELECT_TRIGGER = (By.XPATH, "//div[contains(@class, 'el-select') and .//input[@placeholder='角色状态']]//div[contains(@class, 'el-select__caret')]")
    # 搜索按钮: 使用按钮文本定位，是 Element Plus 常见的文字按钮
    SEARCH_BUTTON = (By.XPATH, "//button[.//span[text()='搜索']]")
    # 重置按钮: 同上
    RESET_BUTTON = (By.XPATH, "//button[.//span[text()='重置']]")

    # --- 表格区 ---
    # 表格主体: 使用 el-table 的 class
    TABLE = (By.CSS_SELECTOR, ".el-table")
    # 表格行: 获取所有行，用于确认数据是否存在
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")

    # --- 操作按钮（位于表格操作列） ---
    # 第一个用户的“编辑”按钮: 通过行内文本和按钮类型定位
    FIRST_ROW_EDIT_BUTTON = (By.XPATH, "(//div[contains(@class, 'el-table__body-wrapper')]//tr[contains(@class, 'el-table__row')])[1]//button[.//span[text()='编辑']]")
    # 第一个用户的“删除”按钮: 同上
    FIRST_ROW_DELETE_BUTTON = (By.XPATH, "(//div[contains(@class, 'el-table__body-wrapper')]//tr[contains(@class, 'el-table__row')])[1]//button[.//span[text()='删除']]")

    # --- 弹窗通用组件（继承 BasePage 的 DIALOG 等，此处额外定义弹窗内表单） ---
    # 新增加/编辑弹窗中的角色名称输入框
    DIALOG_ROLE_NAME_INPUT = (By.CSS_SELECTOR, ".el-dialog input[placeholder='请输入角色名称']")
    # 弹窗中的角色编码输入框
    DIALOG_ROLE_CODE_INPUT = (By.CSS_SELECTOR, ".el-dialog input[placeholder='请输入角色编码']")
    # 弹窗中的状态切换开关: 使用 el-switch 的 class
    DIALOG_STATUS_SWITCH = (By.CSS_SELECTOR, ".el-dialog .el-switch")

    # --- 分页区 ---
    # 分页总条数显示元素
    PAGINATION_TOTAL = (By.CSS_SELECTOR, ".el-pagination__total")

    # ==================== 操作方法 ====================

    def navigate(self) -> "RoleListPage":
        """
        导航至角色列表页面
        通过侧边栏菜单跳转，并等待页面加载稳定。
        """
        self.logger.info("导航至: 系统管理 -> 角色列表")
        # 注意: navigate_to 是基类方法，用于点击菜单
        self.navigate_to("系统管理", "角色列表")
        # 等待 Vue 渲染完毕，表格和搜索区可见
        self.wait_vue_stable()
        self.wait_element_visible(self.TABLE)
        return self

    def search(self, role_name: str = None, status: str = None) -> "RoleListPage":
        """
        搜索角色
        Args:
            role_name: 角色名称关键字，为空则不填写
            status: 状态筛选值 ("启用"/"禁用")，为空则不筛选
        """
        self.logger.info(f"搜索角色, 名称: {role_name}, 状态: {status}")
        # 如果提供了角色名称，则输入
        if role_name is not None:
            # 先清空输入框，再输入新值
            role_input = self.wait_element_visible(self.SEARCH_ROLE_NAME_INPUT)
            role_input.clear()
            role_input.send_keys(role_name)

        # 如果提供了状态，则选择
        if status is not None:
            # 点击触发框展开下拉菜单
            self.wait_element_clickable(self.SEARCH_STATUS_SELECT_TRIGGER).click()
            # 等待下拉菜单出现，并点击对应的选项（选项文本是动态的，如“启用”、“禁用”）
            # 注意: el-select 的选项会渲染在 body 末尾，XPath 需要查找 aria-hidden=false 的 panel
            option_xpath = f"//div[contains(@class, 'el-select-dropdown') and not(contains(@style, 'display: none'))]//span[text()='{status}']"
            self.wait_element_clickable((By.XPATH, option_xpath)).click()
            # 点击后可能需要一点时间让 Vue 响应，建议等待下拉菜单消失
            self.wait_element_invisible((By.XPATH, option_xpath))

        # 点击搜索按钮
        self.logger.info("点击搜索按钮")
        self.wait_element_clickable(self.SEARCH_BUTTON).click()
        # 等待表格数据刷新
        self.wait_vue_stable()
        return self

    def reset_search(self) -> "RoleListPage":
        """
        重置搜索条件
        """
        self.logger.info("重置搜索条件")
        self.wait_element_clickable(self.RESET_BUTTON).click()
        # 重置后，等待输入框为空，表格恢复
        self.wait_vue_stable()
        return self

    def get_table_data(self) -> list:
        """
        获取当前表格内所有可见行的数据（简单返回行数，实际可扩展为返回字段列表）
        Returns:
            行元素列表
        """
        self.logger.info("获取表格数据")
        row_elements = self.wait_elements_visible(self.TABLE_ROWS)
        self.logger.info(f"当前表格行数: {len(row_elements)}")
        return row_elements

    def click_add(self) -> "RoleListPage":
        """
        点击“新增角色”按钮
        注意: 通常在搜索区右侧，使用 XPath 文本定位
        """
        add_button = (By.XPATH, "//button[.//span[text()='新增角色']]")
        self.logger.info("点击“新增角色”按钮")
        self.wait_element_clickable(add_button).click()
        # 等待弹窗出现
        self.wait_element_visible(self.DIALOG)
        return self

    def fill_form(self, data: dict) -> "RoleListPage":
        """
        填写新增/编辑弹窗中的表单
        Args:
            data: 字典，支持 key: 'role_name', 'role_code', 'status'
                  示例: {'role_name': '测试角色', 'role_code': 'test', 'status': True}
        """
        self.logger.info(f"填写弹窗表单, 数据: {data}")

        if 'role_name' in data:
            name_input = self.wait_element_visible(self.DIALOG_ROLE_NAME_INPUT)
            name_input.clear()
            name_input.send_keys(data['role_name'])

        if 'role_code' in data:
            code_input = self.wait_element_visible(self.DIALOG_ROLE_CODE_INPUT)
            code_input.clear()
            code_input.send_keys(data['role_code'])

        if 'status' in data:
            # el-switch: 如果当前状态与目标状态不同，则点击切换
            switch = self.wait_element_visible(self.DIALOG_STATUS_SWITCH)
            current_class = switch.get_attribute('class')
            # el-switch 选中时会有 'is-checked' 类
            is_checked = 'is-checked' in current_class
            if data['status'] != is_checked:
                switch.click()

        return self

    def confirm_dialog(self) -> "RoleListPage":
        """
        点击弹窗中的“确定”按钮（通常为 primary 类型）
        """
        self.logger.info("确认弹窗")
        self.wait_element_clickable(self.DIALOG_SAVE).click()
        # 等待弹窗关闭
        self.wait_element_invisible(self.DIALOG)
        # 等待页面 toast 出现并消失
        self.wait_vue_stable()
        return self

    def cancel_dialog(self) -> "RoleListPage":
        """
        点击弹窗中的“取消”按钮
        """
        self.logger.info("取消弹窗")
        self.wait_element_clickable(self.DIALOG_CANCEL).click()
        self.wait_element_invisible(self.DIALOG)
        return self

    def click_edit(self, row_index: int = 0) -> "RoleListPage":
        """
        点击指定行的“编辑”按钮
        Args:
            row_index: 行索引，从0开始，默认为第一行（索引0）
        """
        self.logger.info(f"点击第 {row_index + 1} 行的编辑按钮")
        # 动态构建 XPath，定位第 row_index+1 行的编辑按钮
        edit_btn_xpath = (By.XPATH,
                          f"(//div[contains(@class, 'el-table__body-wrapper')]//tr[contains(@class, 'el-table__row')])[{row_index + 1}]//button[.//span[text()='编辑']]")
        self.wait_element_clickable(edit_btn_xpath).click()
        # 等待编辑弹窗打开
        self.wait_element_visible(self.DIALOG)
        return self

    def click_delete(self, row_index: int = 0) -> "RoleListPage":
        """
        点击指定行的“删除”按钮
        Args:
            row_index: 行索引，从0开始
        """
        self.logger.info(f"点击第 {row_index + 1} 行的删除按钮")
        del_btn_xpath = (By.XPATH,
                         f"(//div[contains(@class, 'el-table__body-wrapper')]//tr[contains(@class, 'el-table__row')])[{row_index + 1}]//button[.//span[text()='删除']]")
        self.wait_element_clickable(del_btn_xpath).click()
        # 删除操作会弹出一个确认对话框（el-message-box），等待它出现
        # 通用确认框定位器: 使用 el-message-box 的 class
        confirm_box = (By.CSS_SELECTOR, ".el-message-box")
        self.wait_element_visible(confirm_box)
        return self

    def get_pagination_info(self) -> dict:
        """
        获取分页信息
        Returns:
            包含 total, page_size, current_page 的字典
        """
        self.logger.info("获取分页信息")
        total_element = self.wait_element_visible(self.PAGINATION_TOTAL)
        total_text = total_element.text
        # 文本通常是 "共 100 条"
        total = int(total_text.replace('共 ', '').replace(' 条', '').strip())
        # 获取当前每页条数控件（el-pagination__sizes）的选中值
        page_size_trigger = self.wait_element_visible(
            (By.CSS_SELECTOR, ".el-pagination .el-select .el-input__inner"))
        page_size = int(page_size_trigger.get_attribute('value'))
        # 获取当前页高亮按钮文本（el-pager li.active）
        current_page_el = self.wait_element_visible(
            (By.CSS_SELECTOR, ".el-pagination .el-pager li.active"))
        current_page = int(current_page_el.text)

        return {
            'total': total,
            'page_size': page_size,
            'current_page': current_page
        }