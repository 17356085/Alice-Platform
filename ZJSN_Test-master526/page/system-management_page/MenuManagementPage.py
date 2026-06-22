"""
Page Object: 菜单管理页面（Menu Management）
模块: 系统管理（System Management）
"""
from base.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from typing import List, Dict


class MenuManagementPage(BasePage):
    """
    菜单管理页面，提供对左侧菜单树、右侧菜单表格、以及新增/编辑/删除弹窗的操作方法。
    所有操作方法均返回 self，支持链式调用。
    """

    # ==================== 左侧：菜单目录树 ====================
    # 目录树容器
    MENU_TREE = (By.CSS_SELECTOR, ".menu-tree .el-tree")
    # 树节点（根据文本定位）
    TREE_NODE_BY_TEXT = (By.XPATH, "//div[contains(@class, 'el-tree')]//span[text()='{text}']/ancestor::div[contains(@class, 'el-tree-node__content')]")

    # ==================== 右侧：操作栏 ====================
    # 新增按钮（XPath：稳定）
    ADD_MENU_BTN = (By.XPATH, "//button[contains(@class, 'el-button--primary')]//span[text()='新增']")
    # 展开/折叠表格按钮
    EXPAND_COLLAPSE_BTN = (By.XPATH, "//button[.//i[contains(@class, 'el-icon-d-arrow')]]")
    # 刷新按钮
    REFRESH_BTN = (By.XPATH, "//button[.//i[contains(@class, 'el-icon-refresh')]]")

    # ==================== 右侧：菜单表格 ====================
    # 表格主体（行列表）
    TABLE_ROWS = (By.CSS_SELECTOR, ".menu-table .el-table__body-wrapper tbody tr.el-table__row")
    # 各列（基于第N个子元素）
    CELL_MENU_NAME = (By.CSS_SELECTOR, "td:nth-child(1) .cell")
    CELL_ICON = (By.CSS_SELECTOR, "td:nth-child(2) .cell")
    CELL_SORT = (By.CSS_SELECTOR, "td:nth-child(3) .cell")
    CELL_PERMS = (By.CSS_SELECTOR, "td:nth-child(4) .cell")
    CELL_COMPONENT = (By.CSS_SELECTOR, "td:nth-child(5) .cell")
    CELL_STATUS = (By.CSS_SELECTOR, "td:nth-child(6) .cell")
    CELL_CREATED_AT = (By.CSS_SELECTOR, "td:nth-child(7) .cell")
    CELL_OPERATIONS = (By.CSS_SELECTOR, "td:nth-child(8) .cell")
    # 操作列内的编辑/删除按钮（相对于行元素）
    OP_EDIT_BTN = (By.XPATH, ".//button[.//span[text()='编辑']]")
    OP_DELETE_BTN = (By.XPATH, ".//button[.//span[text()='删除']]")

    # ==================== 新增/编辑弹窗 ====================
    # 弹窗容器
    DIALOG = (By.CSS_SELECTOR, "div.el-dialog")
    # 弹窗标题
    DIALOG_TITLE = (By.CSS_SELECTOR, "div.el-dialog__title")
    # 菜单类型（radio-group）
    MENU_TYPE_RADIOS = (By.CSS_SELECTOR, "div.el-dialog .el-radio")
    # 菜单名称输入框
    MENU_NAME_INPUT = (By.XPATH, "//div[contains(@class, 'el-dialog')]//label[text()='菜单名称']/following-sibling::div//input")
    # 路由地址输入框
    ROUTE_PATH_INPUT = (By.XPATH, "//div[contains(@class, 'el-dialog')]//label[text()='路由地址']/following-sibling::div//input")
    # 排序输入框
    SORT_INPUT = (By.XPATH, "//div[contains(@class, 'el-dialog')]//label[text()='排序']/following-sibling::div//input")
    # 确定按钮（文本含空格：'确 定'）
    CONFIRM_BTN = (By.XPATH, "//div[contains(@class, 'el-dialog')]//button[contains(@class, 'el-button--primary')]//span[text()='确 定']")
    # 取消按钮
    CANCEL_BTN = (By.XPATH, "//div[contains(@class, 'el-dialog')]//button[span[text()='取 消']]")

    # ==================== 删除确认弹窗 ====================
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "div.el-message-box")
    CONFIRM_DELETE_BTN = (By.XPATH, "//div[contains(@class, 'el-message-box')]//button[contains(@class, 'el-button--primary')]//span[text()='确 定']")
    CONFIRM_CANCEL_BTN = (By.XPATH, "//div[contains(@class, 'el-message-box')]//button[span[text()='取 消']]")

    # ==================== 页面入口 ====================
    def navigate(self) -> 'MenuManagementPage':
        """导航到菜单管理页面"""
        self.navigate_to("系统管理", "菜单管理")
        self.wait_vue_stable()
        self.logger.info("成功导航到菜单管理页面")
        return self

    # ==================== 左侧树操作 ====================
    def click_tree_node(self, node_text: str) -> 'MenuManagementPage':
        """点击左侧目录树指定文本的节点"""
        locator = (By.XPATH, f"//div[contains(@class, 'el-tree')]//span[text()='{node_text}']/ancestor::div[contains(@class, 'el-tree-node__content')]")
        self.wait_to_be_clickable(locator).click()
        self.wait_vue_stable()
        self.logger.info(f"点击了左侧树节点: {node_text}")
        return self

    # ==================== 右侧操作栏 ====================
    def click_add(self) -> 'MenuManagementPage':
        """点击新增按钮"""
        self.click(self.ADD_MENU_BTN)
        self.wait_vue_stable()
        self.logger.info("点击了新增按钮")
        return self

    def toggle_expand_all(self) -> 'MenuManagementPage':
        """点击展开/折叠表格按钮"""
        self.click(self.EXPAND_COLLAPSE_BTN)
        self.wait_vue_stable()
        self.logger.info("切换表格展开/折叠状态")
        return self

    def click_refresh(self) -> 'MenuManagementPage':
        """点击刷新按钮"""
        self.click(self.REFRESH_BTN)
        self.wait_vue_stable()
        self.logger.info("点击了刷新按钮")
        return self

    # ==================== 表格数据获取 ====================
    def get_table_row_count(self) -> int:
        """获取当前表格行数"""
        rows = self.find_elements(self.TABLE_ROWS)
        return len(rows)

    def get_table_data(self) -> List[Dict[str, str]]:
        """获取表格全部数据，返回字典列表"""
        rows = self.find_elements(self.TABLE_ROWS)
        data = []
        for row in rows:
            menu_name = row.find_element(*self.CELL_MENU_NAME).text.strip()
            icon = row.find_element(*self.CELL_ICON).text.strip()
            sort_val = row.find_element(*self.CELL_SORT).text.strip()
            perms = row.find_element(*self.CELL_PERMS).text.strip()
            component = row.find_element(*self.CELL_COMPONENT).text.strip()
            status = row.find_element(*self.CELL_STATUS).text.strip()
            created = row.find_element(*self.CELL_CREATED_AT).text.strip()
            data.append({
                "menu_name": menu_name,
                "icon": icon,
                "sort": sort_val,
                "perms": perms,
                "component": component,
                "status": status,
                "created_at": created,
            })
        self.logger.info(f"获取到 {len(data)} 条菜单数据")
        return data

    def get_row_index(self, menu_name: str) -> int:
        """根据菜单名称返回行索引（从0开始），未找到返回 -1"""
        rows = self.find_elements(self.TABLE_ROWS)
        for idx, row in enumerate(rows):
            name = row.find_element(*self.CELL_MENU_NAME).text.strip()
            if name == menu_name:
                return idx
        return -1

    def _get_row_element(self, index: int) -> WebElement:
        """获取指定索引的行元素"""
        rows = self.find_elements(self.TABLE_ROWS)
        if index < 0 or index >= len(rows):
            raise IndexError(f"行索引 {index} 超出范围，共 {len(rows)} 行")
        return rows[index]

    # ==================== 行内操作 ====================
    def click_edit(self, row_index: int) -> 'MenuManagementPage':
        """点击第row_index行的编辑按钮（从0开始）"""
        row = self._get_row_element(row_index)
        btn = row.find_element(*self.OP_EDIT_BTN)
        self.wait_to_be_clickable(btn).click()
        self.wait_vue_stable()
        self.logger.info(f"点击了第 {row_index} 行的编辑按钮")
        return self

    def click_delete(self, row_index: int) -> 'MenuManagementPage':
        """点击第row_index行的删除按钮（从0开始）"""
        row = self._get_row_element(row_index)
        btn = row.find_element(*self.OP_DELETE_BTN)
        self.wait_to_be_clickable(btn).click()
        self.wait_vue_stable()
        self.logger.info(f"点击了第 {row_index} 行的删除按钮")
        return self

    # ==================== 新增/编辑弹窗操作 ====================
    def _wait_dialog_visible(self):
        """等待弹窗可见"""
        self.wait_visible(self.DIALOG)

    def select_menu_type(self, menu_type: str) -> 'MenuManagementPage':
        """在弹窗中选择菜单类型（目录/菜单/按钮）"""
        self._wait_dialog_visible()
        radio = (By.XPATH, f"//div[contains(@class, 'el-dialog')]//label[contains(@class, 'el-radio')]//span[text()='{menu_type}']/..")
        self.click(radio)
        self.logger.info(f"选择菜单类型: {menu_type}")
        return self

    def fill_menu_name(self, name: str) -> 'MenuManagementPage':
        """输入菜单名称"""
        self._wait_dialog_visible()
        self.clear_and_send_keys(self.MENU_NAME_INPUT, name)
        self.logger.info(f"输入菜单名称: {name}")
        return self

    def fill_route_path(self, path: str) -> 'MenuManagementPage':
        """输入路由地址"""
        self._wait_dialog_visible()
        self.clear_and_send_keys(self.ROUTE_PATH_INPUT, path)
        self.logger.info(f"输入路由地址: {path}")
        return self

    def fill_sort(self, sort_val: str) -> 'MenuManagementPage':
        """输入排序值"""
        self._wait_dialog_visible()
        self.clear_and_send_keys(self.SORT_INPUT, sort_val)
        self.logger.info(f"输入排序值: {sort_val}")
        return self

    def fill_form(self, data: dict) -> 'MenuManagementPage':
        """
        综合填写表单。data 支持键：
        - menu_type: 目录/菜单/按钮
        - menu_name: str
        - route_path: str
        - sort: str/int
        """
        self._wait_dialog_visible()
        if "menu_type" in data:
            self.select_menu_type(str(data["menu_type"]))
        if "menu_name" in data:
            self.fill_menu_name(str(data["menu_name"]))
        if "route_path" in data:
            self.fill_route_path(str(data["route_path"]))
        if "sort" in data:
            self.fill_sort(str(data["sort"]))
        return self

    def click_confirm(self) -> 'MenuManagementPage':
        """点击弹窗确定按钮"""
        self._wait_dialog_visible()
        self.click(self.CONFIRM_BTN)
        self.wait_vue_stable()
        self.logger.info("点击弹窗确定按钮")
        return self

    def click_cancel(self) -> 'MenuManagementPage':
        """点击弹窗取消按钮"""
        self._wait_dialog_visible()
        self.click(self.CANCEL_BTN)
        self.wait_vue_stable()
        self.logger.info("点击弹窗取消按钮")
        return self

    # ==================== 删除确认弹窗 ====================
    def confirm_delete(self) -> 'MenuManagementPage':
        """在删除确认弹窗中点击确定"""
        self.wait_visible(self.CONFIRM_DIALOG)
        self.click(self.CONFIRM_DELETE_BTN)
        self.wait_vue_stable()
        self.logger.info("确认删除")
        return self

    def cancel_delete(self) -> 'MenuManagementPage':
        """在删除确认弹窗中点击取消"""
        self.wait_visible(self.CONFIRM_DIALOG)
        self.click(self.CONFIRM_CANCEL_BTN)
        self.wait_vue_stable()
        self.logger.info("取消删除")
        return self

    # ==================== 状态切换（如有开关） ====================
    # 注：若存在 el-switch 则实现，此处作为示例
    # def toggle_status(self, row_index: int) -> 'MenuManagementPage':
    #     ...