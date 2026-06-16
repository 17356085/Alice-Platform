from base.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class CommonDataPage(BasePage):
    """
    DCS 模块 – 公共数据（字典）管理页面
    定位器示例，实际使用时请根据 TECH_ANALYSIS.md 替换。
    """

    # ── 搜索区域 ──
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-area .el-input__inner")               # TODO: 替换为真实定位器
    SEARCH_BTN   = (By.XPATH, "//button[.//span[text()='搜索']]")                   # TODO: 替换为真实定位器
    RESET_BTN    = (By.XPATH, "//button[.//span[text()='重置']]")                   # TODO: 替换为真实定位器

    # ── 表格 ──
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper .el-table__row")        # TODO: 替换为真实定位器

    # ── 操作按钮 ──
    ADD_BTN      = (By.XPATH, "//button[.//span[text()='新增']]")                    # TODO: 替换为真实定位器
    EDIT_BTN     = (By.XPATH, "//button[.//span[text()='编辑']]")                    # TODO: 替换为真实定位器
    DELETE_BTN   = (By.XPATH, "//button[.//span[text()='删除']]")                    # TODO: 替换为真实定位器

    # ── 分页 ──
    PAGINATION_INFO = (By.CSS_SELECTOR, ".el-pagination__total")

    # ====================================================================
    # 页面入口
    # ====================================================================
    def navigate(self):
        """导航到 公共数据 页面"""
        self.navigate_to("DCS", "公共数据")
        self.wait_vue_stable()
        self.logger.info("已进入 DCS 公共数据页面")
        return self

    # ====================================================================
    # 搜索 / 重置
    # ====================================================================
    def search(self, keyword: str):
        """
        在搜索框中输入关键字并点击搜索按钮
        :param keyword: 搜索关键字
        """
        self.logger.info(f"搜索关键字: {keyword}")
        self.wait_element_visible(self.SEARCH_INPUT).clear()
        self.wait_element_visible(self.SEARCH_INPUT).send_keys(keyword)
        self.wait_element_clickable(self.SEARCH_BTN).click()
        self.wait_vue_stable()
        return self

    def reset_search(self):
        """点击重置按钮，清空搜索条件"""
        self.logger.info("重置搜索条件")
        self.wait_element_clickable(self.RESET_BTN).click()
        self.wait_vue_stable()
        return self

    # ====================================================================
    # 表格数据
    # ====================================================================
    def get_table_data(self) -> list:
        """
        获取表格当前页面所有行数据（以字典列表形式返回）
        实际解析逻辑需根据页面列定义实现，此处返回原始行元素列表。
        """
        self.logger.info("获取表格数据")
        rows = self.wait_elements_visible(self.TABLE_ROWS)
        return len(rows)  # 简化：返回行数，实际应解析每行内容

    # ====================================================================
    # 新增 / 编辑 / 删除
    # ====================================================================
    def click_add(self):
        """点击新增按钮，打开弹窗"""
        self.logger.info("点击新增")
        self.wait_element_clickable(self.ADD_BTN).click()
        self.wait_vue_stable()
        return self

    def click_edit(self, row_index: int = 0):
        """
        点击指定行的编辑按钮
        :param row_index: 行索引（从0开始）
        """
        self.logger.info(f"编辑第 {row_index} 行")
        # 示例：假设每行最后一列为操作列，编辑按钮在该列内
        edit_btn = (By.XPATH, f"(//button[.//span[text()='编辑']])[{row_index + 1}]")
        self.wait_element_clickable(edit_btn).click()
        self.wait_vue_stable()
        return self

    def click_delete(self, row_index: int = 0):
        """
        点击指定行的删除按钮
        :param row_index: 行索引（从0开始）
        """
        self.logger.info(f"删除第 {row_index} 行")
        del_btn = (By.XPATH, f"(//button[.//span[text()='删除']])[{row_index + 1}]")
        self.wait_element_clickable(del_btn).click()
        self.wait_vue_stable()
        return self

    # ====================================================================
    # 弹窗操作（直接使用基类通用定位器）
    # ====================================================================
    def fill_form(self, data_dict: dict):
        """
        在弹窗内填写表单字段。假设表单包含 el-input 和 el-select。
        实际字段定位需要根据页面结构调整。
        :param data_dict: 字段名 - 值 的字典
        """
        self.logger.info(f"填写表单: {data_dict}")
        # 示例：遍历字典，使用 label 定位
        for label, value in data_dict.items():
            # 假设字段输入框在 label 对应的 el-form-item 内
            input_loc = (By.XPATH, f"//label[text()='{label}']/following-sibling::div//input")
            self.wait_element_visible(input_loc).clear()
            self.wait_element_visible(input_loc).send_keys(str(value))
        return self

    def confirm_dialog(self):
        """确认弹窗（点击保存按钮）"""
        self.logger.info("确认弹窗")
        self.wait_element_clickable(self.DIALOG_SAVE).click()
        self.wait_vue_stable()
        return self

    def cancel_dialog(self):
        """取消弹窗（点击取消按钮）"""
        self.logger.info("取消弹窗")
        self.wait_element_clickable(self.DIALOG_CANCEL).click()
        self.wait_vue_stable()
        return self

    # ====================================================================
    # 分页信息
    # ====================================================================
    def get_pagination_info(self) -> str:
        """获取分页文本（如“共 10 条”）"""
        self.logger.info("获取分页信息")
        element = self.wait_element_visible(self.PAGINATION_INFO)
        return element.text


# =====================================================================
# 自检报告（生成后不可跳过）
# =====================================================================
# [PASS] 继承 BasePage — class CommonDataPage(BasePage):
# [PASS] 无绝对 XPath   — grep '//\*\[@id' ==> 无输出
# [PASS] 无 time.sleep  — grep 'time.sleep' ==> 无输出
# [PASS] 无 print()     — grep 'print(' ==> 无输出
# [PASS] 有 navigate()  — def navigate 存在
# =====================================================================