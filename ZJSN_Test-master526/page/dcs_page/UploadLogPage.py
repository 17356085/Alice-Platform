"""
upload-log Page Object
模块: dcs
说明: 设备上传日志管理页面，基于 Element Plus el-upload 组件
注意: 当前文件为占位模板，定位器值需根据实际页面分析(TECH_ANALYSIS)替换
"""

from base.base_page import BasePage
from selenium.webdriver.common.by import By


class UploadLogPage(BasePage):
    # ==================== 定位器（需根据实际 TECH_ANALYSIS 替换） ====================
    # 上传区域
    UPLOAD_BUTTON = (By.CSS_SELECTOR, ".el-upload .el-button")                      # 点击上传按钮
    UPLOAD_INPUT = (By.CSS_SELECTOR, ".el-upload input[type='file']")               # 隐藏的文件输入
    UPLOAD_LIST = (By.CSS_SELECTOR, ".el-upload-list")                               # 上传文件列表
    UPLOAD_DELETE_BTN = (By.CSS_SELECTOR, ".el-upload-list__item .el-icon-close")   # 文件删除图标

    # 搜索 / 筛选
    SEARCH_INPUT = (By.CSS_SELECTOR, ".filter-section input[placeholder*='文件名']")
    SEARCH_BTN = (By.CSS_SELECTOR, ".filter-section .el-button--primary")
    RESET_BTN = (By.CSS_SELECTOR, ".filter-section .el-button--default")

    # 日志表格
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body tr")
    TABLE_CELL = (By.CSS_SELECTOR, ".el-table__cell")

    # 分页
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    PAGINATION_TOTAL = (By.CSS_SELECTOR, ".el-pagination__total")
    PAGINATION_NEXT = (By.CSS_SELECTOR, ".el-pagination .btn-next")
    PAGINATION_PREV = (By.CSS_SELECTOR, ".el-pagination .btn-prev")

    # 详情 / 弹窗（若有）
    DETAIL_DIALOG = (By.CSS_SELECTOR, ".el-dialog")
    DETAIL_CONTENT = (By.CSS_SELECTOR, ".el-dialog__body")
    DETAIL_CLOSE = (By.CSS_SELECTOR, ".el-dialog__headerbtn")

    # ==================== 页面入口 ====================
    def navigate(self) -> "UploadLogPage":
        """导航到上传日志页面（根据实际菜单路径调整）"""
        self.navigate_to("DCS管理", "上传日志")
        self.wait_vue_stable()
        self.logger.info("成功导航到上传日志页面")
        return self

    # ==================== 操作方法 ====================
    def upload_file(self, file_path: str) -> "UploadLogPage":
        """
        上传文件
        :param file_path: 本地文件绝对路径
        Element Plus 坑位: 必须直接对 input[type=file] send_keys，不可点按钮后弹框操作
        """
        # 等待文件输入可见并 send_keys
        self.wait_element_visible(self.UPLOAD_INPUT)
        self.send_keys(self.UPLOAD_INPUT, file_path)
        # 等待上传完成（通常出现上传列表或 Toast）
        self.wait_element_visible(self.UPLOAD_LIST, timeout=15)
        self.logger.info(f"文件 {file_path} 上传成功")
        return self

    def delete_uploaded_file(self, index: int = 0) -> "UploadLogPage":
        """
        删除上传列表中指定序号的文件
        :param index: 文件列表中的索引（从 0 开始）
        """
        delete_btns = self.find_elements(self.UPLOAD_DELETE_BTN)
        self.wait_element_clickable(delete_btns[index])
        delete_btns[index].click()
        self.wait_toast_success("删除成功")
        self.logger.info(f"已删除列表中第 {index+1} 个文件")
        return self

    def search(self, keyword: str) -> "UploadLogPage":
        """搜索日志"""
        self.wait_element_visible(self.SEARCH_INPUT)
        self.clear_and_send_keys(self.SEARCH_INPUT, keyword)
        self.click(self.SEARCH_BTN)
        self.wait_vue_stable()
        self.logger.info(f"搜索关键字: {keyword}")
        return self

    def reset_search(self) -> "UploadLogPage":
        """重置搜索条件"""
        self.click(self.RESET_BTN)
        self.wait_vue_stable()
        self.logger.info("重置搜索条件")
        return self

    def get_table_data(self) -> list[dict]:
        """
        获取表格显示数据（返回列表，每行 dict）
        注意: 列标题需根据实际页面调整
        """
        rows = self.find_elements(self.TABLE_ROWS)
        data = []
        for row in rows:
            cells = row.find_elements(*self.TABLE_CELL)
            data.append({
                "filename": cells[0].text.strip(),
                "size": cells[1].text.strip(),
                "upload_time": cells[2].text.strip(),
                "status": cells[3].text.strip(),
            })
        self.logger.debug(f"获取到 {len(data)} 条表格数据")
        return data

    def open_detail(self, row_index: int = 0) -> "UploadLogPage":
        """
        打开某行日志详情（假设点击行或行内按钮）
        :param row_index: 行索引
        """
        rows = self.find_elements(self.TABLE_ROWS)
        self.wait_element_clickable(rows[row_index])
        rows[row_index].click()
        self.wait_element_visible(self.DETAIL_DIALOG)
        self.logger.info(f"打开第 {row_index+1} 行详情弹窗")
        return self

    def close_detail(self) -> "UploadLogPage":
        """关闭详情弹窗"""
        self.click(self.DETAIL_CLOSE)
        self.wait_element_invisible(self.DETAIL_DIALOG)
        self.logger.info("关闭详情弹窗")
        return self

    def get_pagination_info(self) -> dict:
        """获取分页信息（总条数、当前页等）"""
        total_text = self.get_text(self.PAGINATION_TOTAL)
        # 解析 "共 100 条" 格式
        total = int(''.join(filter(str.isdigit, total_text)))
        self.logger.info(f"分页总条数: {total}")
        return {"total": total}

    # ==================== 辅助方法 ====================
    def wait_toast_success(self, message: str = "") -> None:
        """等待成功 Toast 并验证内容包含指定文字"""
        from selenium.webdriver.common.by import By
        success_toast = (By.CSS_SELECTOR, ".el-message--success .el-message__content")
        self.wait_element_visible(success_toast)
        if message:
            self.wait_element_text_contains(success_toast, message)

    def clear_and_send_keys(self, locator, text: str) -> None:
        """清空输入框并输入文字"""
        elem = self.find_element(locator)
        elem.clear()
        elem.send_keys(text)


# ====== 自检命令（逐一执行）======
# 1. ✅ class 是否继承 BasePage？
#    → grep -n "class UploadLogPage:" → 必须是 "class UploadLogPage(BasePage):"
#
# 2. ✅ 无绝对 XPath？
#    → grep -n '//\*\[@id="app"\]' → 必须输出为空
#
# 3. ✅ 无 time.sleep？
#    → grep -n "time.sleep" → 必须为空（仅 TIMEOUT_CONFIG 常量除外）
#
# 4. ✅ 无 print()？
#    → grep -n "print(" → 必须输出为空
#
# 5. ✅ 有 navigate() 方法？
#    → grep -n "def navigate" → 必须命中