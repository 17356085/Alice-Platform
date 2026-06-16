"""
Page Object for point-config (设备点配置管理)
所属模块: dcs
"""
from base.base_page import BasePage
from selenium.webdriver.common.by import By


class PointConfigPage(BasePage):
    """
    点配置管理页面，继承 BasePage。
    对应菜单路径示例: "DCS" -> "点配置管理"
    """

    # ========== 定位器（占位，请从 TECH_ANALYSIS.md 替换） ==========
    # 搜索区域
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-area .el-input__inner")
    SEARCH_BTN = (By.XPATH, "//button[.//span[text()='搜索']]")
    RESET_BTN = (By.XPATH, "//button[.//span[text()='重置']]")

    # 操作按钮
    ADD_BTN = (By.XPATH, "//button[.//span[text()='新增']]")
    EDIT_BTN_TMPL = (By.XPATH, "//tr[{}]//button[.//span[text()='编辑']]")
    DELETE_BTN_TMPL = (By.XPATH, "//tr[{}]//button[.//span[text()='删除']]")

    # 表格
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody .el-table__row")

    # 分页（使用 BasePage 已有 PAGE_NEXT / PAGE_PREV 等，或自定义）
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    PAGE_INFO = (By.CSS_SELECTOR, ".el-pagination__total")

    # 弹窗表单（复用 BasePage.DIALOG / DIALOG_SAVE / DIALOG_CANCEL）
    FORM_DIALOG = BasePage.DIALOG
    FORM_SAVE = BasePage.DIALOG_SAVE
    FORM_CANCEL = BasePage.DIALOG_CANCEL

    # 表单字段（需根据实际情况补充）
    FORM_INPUT_NAME = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(1) .el-input__inner")
    FORM_INPUT_CODE = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(2) .el-input__inner")
    FORM_SWITCH_ENABLE = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(3) .el-switch")

    # ========== 页面入口 ==========
    def navigate(self):
        """导航到 DCS -> 点配置管理"""
        self.navigate_to("DCS", "点配置管理")
        self.wait_vue_stable()
        self.logger.info("已进入点配置管理页面")
        return self

    # ========== 搜索操作 ==========
    def search(self, keyword: str):
        """
        在搜索框中输入关键词并点击搜索
        :param keyword: 搜索关键字
        """
        self.logger.info(f"搜索点配置: {keyword}")
        self.wait_element_visible(self.SEARCH_INPUT)
        self.input_text(self.SEARCH_INPUT, keyword)
        self.wait_element_clickable(self.SEARCH_BTN)
        self.click_element(self.SEARCH_BTN)
        self.wait_vue_stable()
        return self

    def reset_search(self):
        """重置搜索条件"""
        self.logger.info("重置搜索条件")
        self.wait_element_clickable(self.RESET_BTN)
        self.click_element(self.RESET_BTN)
        self.wait_vue_stable()
        return self

    # ========== 表格数据 ==========
    def get_table_data(self):
        """
        获取当前表格所有行数据（文本）
        :return: list[dict]，每行各列文本
        """
        self.logger.info("获取表格数据")
        rows = self.find_elements(self.TABLE_ROWS)
        table_data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            table_data.append({
                "index": cells[0].text.strip() if len(cells) > 0 else "",
                "name": cells[1].text.strip() if len(cells) > 1 else "",
                "code": cells[2].text.strip() if len(cells) > 2 else "",
                "status": cells[3].text.strip() if len(cells) > 3 else "",
            })
        return table_data

    # ========== 新增 ==========
    def click_add(self):
        """点击新增按钮"""
        self.logger.info("点击新增")
        self.wait_element_clickable(self.ADD_BTN)
        self.click_element(self.ADD_BTN)
        self.wait_element_visible(self.FORM_DIALOG)
        return self

    def fill_form(self, data: dict):
        """
        填充弹窗表单（通用方法）
        :param data: dict，字段名 -> 值，如 {"name": "test", "code": "T001"}
        """
        self.logger.info(f"填充表单: {data}")
        if "name" in data:
            self.input_text(self.FORM_INPUT_NAME, data["name"])
        if "code" in data:
            self.input_text(self.FORM_INPUT_CODE, data["code"])
        if "enable" in data:
            self.set_switch_value(self.FORM_SWITCH_ENABLE, data["enable"])
        return self

    def confirm_dialog(self):
        """点击弹窗确认(保存)按钮"""
        self.logger.info("确认弹窗")
        self.wait_element_clickable(self.FORM_SAVE)
        self.click_element(self.FORM_SAVE)
        self.wait_vue_stable()
        return self

    def cancel_dialog(self):
        """点击弹窗取消按钮"""
        self.logger.info("取消弹窗")
        self.wait_element_clickable(self.FORM_CANCEL)
        self.click_element(self.FORM_CANCEL)
        self.wait_element_invisible(self.FORM_DIALOG)
        return self

    # ========== 编辑 & 删除 ==========
    def click_edit(self, row_index: int):
        """
        点击指定行的编辑按钮
        :param row_index: 行号，从0开始
        """
        self.logger.info(f"点击第 {row_index} 行编辑")
        # 使用带索引的 XPath 模板
        edit_locator = (By.XPATH, self.EDIT_BTN_TMPL[1].format(row_index + 1))
        self.wait_element_clickable(edit_locator)
        self.click_element(edit_locator)
        self.wait_element_visible(self.FORM_DIALOG)
        return self

    def click_delete(self, row_index: int):
        """
        点击指定行的删除按钮
        :param row_index: 行号，从0开始
        """
        self.logger.info(f"点击第 {row_index} 行删除")
        delete_locator = (By.XPATH, self.DELETE_BTN_TMPL[1].format(row_index + 1))
        self.wait_element_clickable(delete_locator)
        self.click_element(delete_locator)
        self.wait_element_visible(self.DIALOG_CONFIRM)  # 删除确认弹窗，使用 BasePage 通用定位器
        return self

    def confirm_delete(self):
        """确认删除操作（BasePage 已有 DIALOG_CONFIRM 定位器）"""
        self.logger.info("确认删除")
        confirm_btn = getattr(self, "DIALOG_CONFIRM", None)
        if confirm_btn:
            self.click_element(confirm_btn)
            self.wait_vue_stable()
        else:
            # 若 BasePage 未定义，可手动定位
            self.wait_element_clickable((By.XPATH, "//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]"))
            self.click_element((By.XPATH, "//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]"))
        self.wait_vue_stable()
        return self

    # ========== 分页 ==========
    def get_pagination_info(self) -> dict:
        """
        获取分页信息
        :return: {"total": int, "page_size": int, "current_page": int}
        """
        self.logger.info("获取分页信息")
        total_text = self.get_text(self.PAGE_INFO)
        # 假设格式 "共 100 条"
        total = int(total_text.replace('共', '').replace('条', '').strip())
        # 使用 BasePage 的 get_current_page / get_page_size 方法（假想，若未实现则手动获取）
        current_page = 1  # 实际应读取 el-pagination 的 active 状态
        page_size = 20    # 默认页大小
        self.logger.info(f"分页信息: total={total}, page_size={page_size}, current={current_page}")
        return {"total": total, "page_size": page_size, "current_page": current_page}

    def go_to_page(self, page_num: int):
        """跳转到指定页（需根据实际分页组件实现）"""
        self.logger.info(f"跳转到第 {page_num} 页")
        page_input = (By.CSS_SELECTOR, ".el-pagination__editor input")
        self.input_text(page_input, str(page_num))
        self.press_enter(page_input)
        self.wait_vue_stable()
        return self